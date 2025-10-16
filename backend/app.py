"""
Flask application for BREAK debate platform.

Provides REST API endpoints with Server-Sent Events (SSE) support
for real-time debate progress streaming.
"""
import asyncio
import json
import logging
import os
import time
import uuid
from threading import Event
from typing import Dict, Any, AsyncGenerator
from flask import Flask, Response, request, jsonify, send_from_directory

from backend import debate_engine, db_manager, config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Helper function to run async coroutines in Flask request context.

    Python 3.13+ requires explicit event loop policy in threads.
    This function creates a new event loop for each call.
    """
    # Always create a new event loop for thread safety in Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up the loop after use
        loop.close()
        # Unset the event loop to avoid issues with next request
        asyncio.set_event_loop(None)

# Get the project root directory (parent of backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# Session management for ADVANCE flow control
_SESS = {}  # sid -> {"advance": Event()}

# Initialize Flask app with static folder
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
# CORS not needed for local development (frontend and backend on same origin)

# Initialize database on startup
with app.app_context():
    try:
        db_manager.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@app.route('/')
def index():
    """Serve frontend index.html."""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico."""
    return send_from_directory(FRONTEND_DIR, 'favicon.ico')


@app.route('/<path:path>')
def serve_static(path):
    """Serve frontend static files (CSS, JS)."""
    return send_from_directory(FRONTEND_DIR, path)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON: {"status": "healthy", "database": "connected"}
    """
    try:
        # Test database connection
        total_debates = db_manager.get_total_count()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "total_debates": total_debates
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500


def wait_for_advance(sid: str):
    """
    Wait for client's ADVANCE signal before proceeding to next phase.

    Args:
        sid: Session ID

    Raises:
        TimeoutError: If client doesn't send ADVANCE within 120 seconds
    """
    sess = _SESS.get(sid)
    if sess is None:
        logger.warning(f"Session {sid} not found in wait_for_advance")
        return

    ev = sess.get("advance")
    if ev is None:
        logger.warning(f"Event object not found for session {sid}")
        return

    # Wait for client's ADVANCE signal (with 120-second timeout)
    if not ev.wait(timeout=120):
        raise TimeoutError(f"Client did not send ADVANCE within 120 seconds for session {sid}")

    # Clear the event for next use
    ev.clear()
    logger.info(f"ADVANCE signal received for session {sid}")


@app.route('/api/debate', methods=['GET'])
def start_debate():
    """
    Start a debate with SSE (Server-Sent Events) streaming.

    Query parameters:
        topic (str): Debate topic
        config (str): JSON string of config object

    Response: text/event-stream
        SSE events with type: axis, round1, round2, judgment, complete, error
    """
    # EventSource uses GET, so we get params from query string
    topic = request.args.get('topic')
    config_str = request.args.get('config', '{}')

    try:
        config = json.loads(config_str)
    except json.JSONDecodeError:
        logger.error(f"Invalid config JSON: {config_str}")
        return jsonify({"error": "Invalid config format"}), 400

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    if not config.get('judge') or not config.get('ai_a') or not config.get('ai_b'):
        return jsonify({"error": "Config for judge, ai_a, and ai_b is required"}), 400

    # Generate session ID and create Event for ADVANCE control
    sid = str(uuid.uuid4())
    _SESS[sid] = {"advance": Event()}
    logger.info(f"Created session {sid} for debate")

    def event_stream():
        """SSE Generator for streaming debate progress (ADVANCE-controlled)."""
        try:
            # Phase 1: Axis selection
            logger.info(f"Starting debate: {topic}")
            axis_result = run_async(debate_engine.determine_axis(topic, config['judge']))
            yield f"data: {json.dumps({'type': 'axis', 'sid': sid, 'data': axis_result})}\n\n"
            # Comment line to force flush
            yield ": axis sent\n\n"

            # ===== WAIT FOR FRONTEND TO DISPLAY AXIS =====

            # Phase 2: Round 1 parallel execution (only execute after axis displayed)
            logger.info("Starting Round 1 execution...")
            round1_result = run_async(debate_engine.execute_round1(
                topic, axis_result, config
            ))
            # Transform Round 1 data structure for frontend
            round1_data = {
                'ai_a': round1_result['ai_a_round1'],
                'ai_b': round1_result['ai_b_round1'],
                'axis_left': axis_result['axis_left'],
                'axis_right': axis_result['axis_right']
            }
            yield f"data: {json.dumps({'type': 'round1', 'sid': sid, 'data': round1_data})}\n\n"
            # Comment line to force flush
            yield ": round1 sent\n\n"

            # Phase 3: Round 2 execution (run immediately while client reviews Round 1)
            logger.info("Starting Round 2 execution...")
            round2_result = run_async(debate_engine.execute_round2(
                topic, axis_result, round1_result, config
            ))
            # Transform Round 2 data structure for frontend
            round2_data = {
                'ai_a': round2_result['ai_a_round2'],
                'ai_b': round2_result['ai_b_round2'],
                'axis_left': axis_result['axis_left'],
                'axis_right': axis_result['axis_right']
            }
            yield f"data: {json.dumps({'type': 'round2', 'sid': sid, 'data': round2_data})}\n\n"
            # Comment line to force flush
            yield ": round2 sent\n\n"

            # Phase 4: Precompute judgment while client reviews Round 2
            logger.info("Starting Judgment execution...")
            judgment_result = run_async(debate_engine.execute_judgment(
                topic, axis_result, round1_result, round2_result, config
            ))
            judgment_data = {
                **judgment_result,
                'axis_left': axis_result['axis_left'],
                'axis_right': axis_result['axis_right'],
                'axis_reasoning': axis_result.get('axis_reasoning', '')
            }
            logger.info(f"Judgment ready for session {sid}; awaiting ADVANCE signal to stream")

            # ===== WAIT FOR CLIENT'S ADVANCE SIGNAL =====
            # Frontend displays Round 2 and waits 45 seconds with early exit option
            # Backend waits for client's ADVANCE signal (or 120s timeout)
            logger.info(f"Waiting for ADVANCE signal from session {sid} to proceed to Judgment...")
            wait_for_advance(sid)

            # Phase 4: Final judgment + synthesis (only execute after round2 timer)
            logger.info(f"ADVANCE received for session {sid}; streaming judgment")
            yield f"data: {json.dumps({'type': 'judgment', 'data': judgment_data})}\n\n"
            # Comment line to force flush
            yield ": judgment sent\n\n"

            # Save to database - flatten nested structure to match db schema
            debate_data = {
                "topic": topic,
                # Axis data
                "axis_left": axis_result["axis_left"],
                "axis_right": axis_result["axis_right"],
                "axis_reasoning": axis_result.get("axis_reasoning"),

                # Round 1 AI_A data (flatten ai_a_round1 dict)
                "ai_a_engine": round1_result.get("ai_a_engine"),
                "ai_a_model": round1_result.get("ai_a_model"),
                "ai_a_round1_claim": round1_result["ai_a_round1"].get("claim"),
                "ai_a_round1_rationale": round1_result["ai_a_round1"].get("rationale"),
                "ai_a_round1_preemptive": round1_result["ai_a_round1"].get("preemptive_counter"),
                "ai_a_round1_confidence": round1_result["ai_a_round1"].get("confidence_level"),

                # Round 1 AI_B data (flatten ai_b_round1 dict)
                "ai_b_engine": round1_result.get("ai_b_engine"),
                "ai_b_model": round1_result.get("ai_b_model"),
                "ai_b_round1_claim": round1_result["ai_b_round1"].get("claim"),
                "ai_b_round1_rationale": round1_result["ai_b_round1"].get("rationale"),
                "ai_b_round1_preemptive": round1_result["ai_b_round1"].get("preemptive_counter"),
                "ai_b_round1_confidence": round1_result["ai_b_round1"].get("confidence_level"),

                # Round 2 AI_A data (flatten ai_a_round2 dict)
                "ai_a_round2_counters": round2_result["ai_a_round2"].get("counters"),
                "ai_a_round2_final": round2_result["ai_a_round2"].get("final_statement"),
                "ai_a_round2_confidence": round2_result["ai_a_round2"].get("confidence_level"),

                # Round 2 AI_B data (flatten ai_b_round2 dict)
                "ai_b_round2_counters": round2_result["ai_b_round2"].get("counters"),
                "ai_b_round2_final": round2_result["ai_b_round2"].get("final_statement"),
                "ai_b_round2_confidence": round2_result["ai_b_round2"].get("confidence_level"),

                # Judgment data (already flattened in execute_judgment)
                "judge_engine": judgment_result.get("judge_engine"),
                "judge_model": judgment_result.get("judge_model"),
                "winner": judgment_result.get("winner"),
                "final_judgment": judgment_result,  # Store full judgment as JSON

                # Individual scores (already flattened)
                "ai_a_logic_score": judgment_result.get("ai_a_logic_score"),
                "ai_a_attack_score": judgment_result.get("ai_a_attack_score"),
                "ai_a_construct_score": judgment_result.get("ai_a_construct_score"),
                "ai_a_total_score": judgment_result.get("ai_a_total_score"),
                "ai_b_logic_score": judgment_result.get("ai_b_logic_score"),
                "ai_b_attack_score": judgment_result.get("ai_b_attack_score"),
                "ai_b_construct_score": judgment_result.get("ai_b_construct_score"),
                "ai_b_total_score": judgment_result.get("ai_b_total_score"),
                "break_shot_ai": judgment_result.get("break_shot_ai"),
                "break_shot_category": judgment_result.get("break_shot_category"),
                "break_shot_score": judgment_result.get("break_shot_score"),
                "break_shot_quote": judgment_result.get("break_shot_quote"),
                "reasoning": judgment_result.get("reasoning"),
                "synthesis": judgment_result.get("synthesis"),

                # Metadata
                "elapsed_time": (axis_result.get("elapsed_seconds", 0) +
                                round1_result.get("elapsed_seconds", 0) +
                                round2_result.get("elapsed_seconds", 0) +
                                judgment_result.get("elapsed_seconds", 0))
            }
            debate_id = db_manager.save_debate(debate_data)
            logger.info(f"Debate saved with ID: {debate_id}")

            yield f"data: {json.dumps({'type': 'complete', 'data': {'id': debate_id}})}\n\n"

        except Exception as e:
            logger.error(f"Debate error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"
        finally:
            # Cleanup session
            _SESS.pop(sid, None)
            logger.info(f"Session {sid} cleaned up")

    # Return SSE response with proper headers
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable Nginx buffering
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/debate/advance', methods=['POST'])
def debate_advance():
    """
    Receive ADVANCE signal from client to proceed to next phase.

    Request body:
        {
            "sid": str (session ID)
        }

    Returns:
        JSON: {"ok": bool, "phase": str (optional)}
    """
    try:
        data = request.get_json(force=True)
        sid = data.get('sid')

        if not sid:
            return jsonify({'ok': False, 'error': 'sid is required'}), 400

        sess = _SESS.get(sid)
        if not sess:
            logger.warning(f"Session {sid} not found in debate_advance")
            return jsonify({'ok': False, 'error': 'sid not found'}), 404

        # Set the Event to unblock wait_for_advance()
        ev = sess.get('advance')
        if ev:
            ev.set()
            logger.info(f"ADVANCE signal set for session {sid}")
            return jsonify({'ok': True}), 200
        else:
            logger.warning(f"Event object not found for session {sid}")
            return jsonify({'ok': False, 'error': 'event not found'}), 404

    except Exception as e:
        logger.error(f"Error in debate_advance: {e}", exc_info=True)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    Get debate history with pagination.

    Query parameters:
        limit (int): Number of items to return (default: 100, max: 100)
        offset (int): Offset for pagination (default: 0)

    Returns:
        JSON: {
            "total": int,
            "items": List[Dict] (with axis as nested object for frontend compatibility)
        }
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        # Enforce max limit
        limit = min(limit, 100)

        total = db_manager.get_total_count()
        debates = db_manager.get_debates(limit=limit, offset=offset)

        # Transform items to include axis as nested object (for frontend renderHistoryList)
        transformed_items = []
        for debate in debates:
            transformed_items.append({
                "id": debate["id"],
                "topic": debate["topic"],
                "created_at": debate["created_at"],
                "axis": {
                    "left": debate.get("axis_left"),
                    "right": debate.get("axis_right")
                },
                "ai_a_engine": debate.get("ai_a_engine"),
                "ai_a_model": debate.get("ai_a_model"),
                "ai_b_engine": debate.get("ai_b_engine"),
                "ai_b_model": debate.get("ai_b_model"),
                "winner": debate.get("winner")
            })

        return jsonify({
            "total": total,
            "items": transformed_items
        }), 200

    except ValueError as e:
        logger.error(f"Invalid query parameters: {e}")
        return jsonify({"error": "Invalid query parameters"}), 400
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch history"}), 500


@app.route('/api/history/<int:debate_id>', methods=['GET'])
def get_debate_by_id(debate_id: int):
    """
    Get a specific debate by ID.

    Path parameters:
        debate_id (int): Debate ID

    Returns:
        JSON: Debate data (transformed from flattened DB format to nested frontend format)
    """
    try:
        debate = db_manager.get_debate_by_id(debate_id)

        if not debate:
            return jsonify({"error": "Debate not found"}), 404

        # Transform flattened database format to nested frontend format
        transformed_data = {
            "id": debate["id"],
            "topic": debate["topic"],
            "created_at": debate["created_at"],

            # Axis as object
            "axis": {
                "left": debate.get("axis_left"),
                "right": debate.get("axis_right"),
                "reasoning": debate.get("axis_reasoning")
            },

            # Engine info
            "ai_a_engine": debate.get("ai_a_engine"),
            "ai_a_model": debate.get("ai_a_model"),
            "ai_b_engine": debate.get("ai_b_engine"),
            "ai_b_model": debate.get("ai_b_model"),
            "judge_engine": debate.get("judge_engine"),
            "judge_model": debate.get("judge_model"),

            # Round 1 data as nested object
            "round1_data": {
                "ai_a": {
                    "claim": debate.get("ai_a_round1_claim"),
                    "rationale": debate.get("ai_a_round1_rationale"),  # Already a list (deserialized by db_manager)
                    "preemptive_counter": debate.get("ai_a_round1_preemptive"),
                    "confidence_level": debate.get("ai_a_round1_confidence")
                },
                "ai_b": {
                    "claim": debate.get("ai_b_round1_claim"),
                    "rationale": debate.get("ai_b_round1_rationale"),  # Already a list
                    "preemptive_counter": debate.get("ai_b_round1_preemptive"),
                    "confidence_level": debate.get("ai_b_round1_confidence")
                }
            },

            # Round 2 data as nested object
            "round2_data": {
                "ai_a": {
                    "counters": debate.get("ai_a_round2_counters"),  # Already a list
                    "final_statement": debate.get("ai_a_round2_final"),
                    "confidence_level": debate.get("ai_a_round2_confidence")
                },
                "ai_b": {
                    "counters": debate.get("ai_b_round2_counters"),  # Already a list
                    "final_statement": debate.get("ai_b_round2_final"),
                    "confidence_level": debate.get("ai_b_round2_confidence")
                }
            },

            # Scores as nested object
            "scores": {
                "ai_a": {
                    "logic": debate.get("ai_a_logic_score"),
                    "attack": debate.get("ai_a_attack_score"),
                    "construct": debate.get("ai_a_construct_score"),
                    "total": debate.get("ai_a_total_score")
                },
                "ai_b": {
                    "logic": debate.get("ai_b_logic_score"),
                    "attack": debate.get("ai_b_attack_score"),
                    "construct": debate.get("ai_b_construct_score"),
                    "total": debate.get("ai_b_total_score")
                }
            },

            # Break shot as nested object
            "break_shot": {
                "ai": debate.get("break_shot_ai"),
                "category": debate.get("break_shot_category"),
                "score": debate.get("break_shot_score"),
                "quote": debate.get("break_shot_quote")
            },

            # Winner and other data
            "winner": debate.get("winner"),
            "reasoning": debate.get("reasoning"),
            "synthesis": debate.get("synthesis"),
            "elapsed_time": debate.get("elapsed_time")
        }

        return jsonify(transformed_data), 200

    except Exception as e:
        logger.error(f"Failed to fetch debate {debate_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch debate"}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Get current AI node configuration.

    Returns:
        JSON: {
            "ai_a": {"engine": str, "model": str},
            "ai_b": {"engine": str, "model": str},
            "judge": {"engine": str, "model": str}
        }
    """
    try:
        # Load MAGIN format config and convert to BREAK format
        magin_config = config_manager.load_user_config()

        # Convert MAGIN nodes format to BREAK format
        if "nodes" in magin_config and len(magin_config["nodes"]) >= 3:
            nodes = magin_config["nodes"]
            return jsonify({
                "ai_a": {"engine": nodes[0]["engine"], "model": nodes[0]["model"]},
                "ai_b": {"engine": nodes[1]["engine"], "model": nodes[1]["model"]},
                "judge": {"engine": nodes[2]["engine"], "model": nodes[2]["model"]}
            }), 200
        else:
            # Fallback to default
            return jsonify({
                "ai_a": {"engine": "API_Gemini", "model": "gemini-2.5-flash"},
                "ai_b": {"engine": "API_Gemini", "model": "gemini-2.5-flash"},
                "judge": {"engine": "API_Gemini", "model": "gemini-2.5-flash"}
            }), 200

    except Exception as e:
        logger.error(f"Failed to load config: {e}", exc_info=True)
        return jsonify({"error": "Failed to load config"}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """
    Save AI node configuration.

    Request body:
        {
            "ai_a": {"engine": str, "model": str},
            "ai_b": {"engine": str, "model": str},
            "judge": {"engine": str, "model": str}
        }

    Returns:
        JSON: {"success": true}
    """
    try:
        data = request.get_json()

        if not data.get('ai_a') or not data.get('ai_b') or not data.get('judge'):
            return jsonify({"error": "ai_a, ai_b, and judge are required"}), 400

        # Convert BREAK format to MAGIN nodes format
        magin_config = {
            "nodes": [
                {
                    "id": 1,
                    "name": "AI_A",
                    "engine": data['ai_a']['engine'],
                    "model": data['ai_a'].get('model'),
                    "persona_id": "neutral_ai"
                },
                {
                    "id": 2,
                    "name": "AI_B",
                    "engine": data['ai_b']['engine'],
                    "model": data['ai_b'].get('model'),
                    "persona_id": "neutral_ai"
                },
                {
                    "id": 3,
                    "name": "JUDGE",
                    "engine": data['judge']['engine'],
                    "model": data['judge'].get('model'),
                    "persona_id": "neutral_ai"
                }
            ]
        }

        config_manager.save_user_config(magin_config)

        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"Failed to save config: {e}", exc_info=True)
        return jsonify({"error": "Failed to save config"}), 500


@app.route('/api/env', methods=['GET'])
def get_env():
    """
    Get environment variables status (masked).

    Returns:
        JSON: {
            "GEMINI_API_KEY": bool,
            "OPENROUTER_API_KEY": bool,
            "OLLAMA_URL": str
        }
    """
    try:
        env_vars = config_manager.load_env()

        return jsonify({
            "GEMINI_API_KEY": bool(env_vars.get("GEMINI_API_KEY")),
            "OPENROUTER_API_KEY": bool(env_vars.get("OPENROUTER_API_KEY")),
            "OLLAMA_URL": env_vars.get("OLLAMA_URL", "http://localhost:11434")
        }), 200

    except Exception as e:
        logger.error(f"Failed to load env: {e}", exc_info=True)
        return jsonify({"error": "Failed to load environment variables"}), 500


@app.route('/api/env', methods=['POST'])
def save_env():
    """
    Save environment variables to .env file.

    Request body:
        {
            "GEMINI_API_KEY": str (optional),
            "OPENROUTER_API_KEY": str (optional),
            "OLLAMA_URL": str (optional)
        }

    Returns:
        JSON: {"success": true}
    """
    try:
        data = request.get_json()

        # Get current env vars
        env_vars = config_manager.load_env()

        # Update with new values (only if provided)
        if "GEMINI_API_KEY" in data:
            env_vars["GEMINI_API_KEY"] = data["GEMINI_API_KEY"]
        if "OPENROUTER_API_KEY" in data:
            env_vars["OPENROUTER_API_KEY"] = data["OPENROUTER_API_KEY"]
        if "OLLAMA_URL" in data:
            env_vars["OLLAMA_URL"] = data["OLLAMA_URL"]

        # Save to .env file
        config_manager.save_env(env_vars)

        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"Failed to save env: {e}", exc_info=True)
        return jsonify({"error": "Failed to save environment variables"}), 500


@app.route('/api/test-engine', methods=['POST'])
def test_single_engine():
    """
    Test connection to a single AI engine.

    Request body:
        {
            "engine": str,
            "model": str (optional)
        }

    Returns:
        JSON: {"success": bool, "engine": str, "model": str, "elapsed": float, "error": str | None}
    """
    try:
        from backend import ai_factory

        data = request.get_json()
        engine = data.get('engine')
        model = data.get('model')

        logger.info(f"[/api/test-engine] Testing single engine: {engine}, model: {model}")

        if not engine:
            return jsonify({"error": "Engine is required"}), 400

        # Test prompt - request JSON response for ai_factory compatibility
        test_prompt = 'Please respond with this exact JSON: {"status": "OK"}'

        # Execute test
        result = run_async(ai_factory.call_ai(engine, model, test_prompt, timeout=30))

        return jsonify({
            "success": result["success"],
            "engine": engine,
            "model": model or 'default',
            "elapsed": result["elapsed_seconds"],
            "error": result.get("error")
        }), 200

    except Exception as e:
        logger.error(f"Engine test failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """
    Test connection to AI engines.

    Request body:
        {
            "config": {
                "ai_a": {"engine": str, "model": str},
                "ai_b": {"engine": str, "model": str},
                "judge": {"engine": str, "model": str}
            }
        }

    Returns:
        JSON: {
            "ai_a": {"success": bool, "engine": str, "model": str, "elapsed": float, "error": str | None},
            "ai_b": {...},
            "judge": {...}
        }
    """
    try:
        from backend import ai_factory

        data = request.get_json()
        config = data.get('config', {})

        if not config.get('ai_a') or not config.get('ai_b') or not config.get('judge'):
            return jsonify({"error": "Config for ai_a, ai_b, and judge is required"}), 400

        # Test prompt - request JSON response for ai_factory compatibility
        test_prompt = 'Please respond with this exact JSON: {"status": "OK"}'

        # Test all three engines in parallel
        # Create an async function to wrap the gather call
        async def test_all_engines():
            return await asyncio.gather(
                ai_factory.call_ai(
                    config['ai_a']['engine'],
                    config['ai_a'].get('model'),
                    test_prompt,
                    timeout=30
                ),
                ai_factory.call_ai(
                    config['ai_b']['engine'],
                    config['ai_b'].get('model'),
                    test_prompt,
                    timeout=30
                ),
                ai_factory.call_ai(
                    config['judge']['engine'],
                    config['judge'].get('model'),
                    test_prompt,
                    timeout=30
                )
            )

        results = run_async(test_all_engines())

        ai_a_result, ai_b_result, judge_result = results

        return jsonify({
            "ai_a": {
                "success": ai_a_result["success"],
                "engine": config['ai_a']['engine'],
                "model": config['ai_a'].get('model', 'default'),
                "elapsed": ai_a_result["elapsed_seconds"],
                "error": ai_a_result.get("error")
            },
            "ai_b": {
                "success": ai_b_result["success"],
                "engine": config['ai_b']['engine'],
                "model": config['ai_b'].get('model', 'default'),
                "elapsed": ai_b_result["elapsed_seconds"],
                "error": ai_b_result.get("error")
            },
            "judge": {
                "success": judge_result["success"],
                "engine": config['judge']['engine'],
                "model": config['judge'].get('model', 'default'),
                "elapsed": judge_result["elapsed_seconds"],
                "error": judge_result.get("error")
            }
        }), 200

    except Exception as e:
        logger.error(f"Connection test failed: {e}", exc_info=True)
        return jsonify({"error": "Connection test failed"}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Get port from environment variable, default to 5000
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting BREAK Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

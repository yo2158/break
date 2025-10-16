"""
Debate Engine for BREAK application.

Orchestrates the complete debate flow:
1. Axis selection (Judge AI)
2. Round 1 parallel execution (AI_A and AI_B)
3. Round 2 parallel execution (AI_A and AI_B)
4. Final judgment + synthesis (Judge AI)

Uses asyncio for parallel execution to optimize performance.
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List

from backend import ai_factory, prompt_builder, axis_patterns


logger = logging.getLogger(__name__)


# JSON parsing helper
def extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON data from AI response text.

    AI responses may be wrapped in markdown code blocks or contain
    explanatory text. This function attempts to extract the JSON portion.

    Args:
        text: Raw AI response text

    Returns:
        Parsed JSON dict if found, None otherwise

    Example:
        >>> extract_json_from_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        >>> extract_json_from_response('{"key": "value"}')
        {'key': 'value'}
    """
    if not text:
        return None

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block with proper greedy matching
    # Match everything between ```json and ``` (including nested braces)
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text (properly handle nested braces)
    # Find first { and matching }
    start = text.find('{')
    if start >= 0:
        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found matching closing brace
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        pass
                    break

    return None


async def determine_axis(topic: str, judge_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the most appropriate debate axis for the topic using Judge AI.

    Args:
        topic: Debate topic provided by user
        judge_config: Judge AI configuration with keys:
            - engine (str): AI engine name
            - model (Optional[str]): Model name

    Returns:
        Dictionary containing:
            - axis_left (str): Left side of the debate axis
            - axis_right (str): Right side of the debate axis
            - ai_a_stance (str): Concrete stance for AI_A on the topic
            - ai_b_stance (str): Concrete stance for AI_B on the topic
            - axis_reasoning (str): Reasoning for axis selection
            - elapsed_seconds (float): Time taken for axis selection

    Raises:
        Exception: If AI call fails or JSON parsing fails after retries

    Example:
        >>> config = {"engine": "API_Gemini", "model": "gemini-2.5-flash"}
        >>> result = await determine_axis("AIによる雇用代替は良いことか？", config)
        >>> "axis_left" in result
        True
    """
    start_time = time.time()

    # Build axis selection prompt
    prompt = prompt_builder.build_axis_prompt(topic)

    # Call Judge AI
    logger.info(f"Determining axis for topic: {topic}")
    response = await ai_factory.call_ai(
        engine=judge_config["engine"],
        model=judge_config.get("model"),
        prompt=prompt,
        timeout=60
    )

    if not response["success"]:
        logger.error(f"Axis determination failed: {response.get('error')}")
        raise Exception(f"Axis determination failed: {response.get('error')}")

    # Parse JSON response (use full_output if available, fallback to raw_output)
    output_text = response.get("full_output", response["raw_output"])
    ai_response = extract_json_from_response(output_text)
    if not ai_response:
        logger.error("Failed to parse axis response as JSON")
        # Fallback to default axis
        logger.warning("Using default axis: 効率最適化 vs 人間中心主義")
        return {
            "axis_left": "効率最適化",
            "axis_right": "人間中心主義",
            "ai_a_stance": "効率化を最優先し、目標達成を重視する立場",
            "ai_b_stance": "人間の幸福と尊厳を最優先し、プロセスを重視する立場",
            "axis_reasoning": "JSON解析失敗のため、デフォルト軸を使用",
            "elapsed_seconds": time.time() - start_time
        }

    elapsed = time.time() - start_time

    # Check if topic is not suitable for debate (axis_id == 0)
    axis_id = ai_response.get("axis_id", -1)
    if axis_id == 0:
        logger.warning(f"Topic not suitable for debate: {topic}")
        raise ValueError("NOT_APPLICABLE: このトピックは議論に適していません。議論可能なテーマを入力してください。")

    logger.info(f"Axis determined in {elapsed:.2f}s: {ai_response.get('axis_left')} vs {ai_response.get('axis_right')}")
    logger.info(f"Stances - AI_A: {ai_response.get('ai_a_stance', 'N/A')[:50]}... | AI_B: {ai_response.get('ai_b_stance', 'N/A')[:50]}...")

    return {
        "axis_left": ai_response.get("axis_left", "効率最適化"),
        "axis_right": ai_response.get("axis_right", "人間中心主義"),
        "ai_a_stance": ai_response.get("ai_a_stance", "効率化を最優先し、目標達成を重視する立場"),
        "ai_b_stance": ai_response.get("ai_b_stance", "人間の幸福と尊厳を最優先し、プロセスを重視する立場"),
        "axis_reasoning": ai_response.get("reasoning", ""),
        "elapsed_seconds": elapsed
    }


async def execute_round1(
    topic: str,
    axis_result: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Round 1 debate with parallel AI calls.

    Args:
        topic: Debate topic
        axis_result: Dictionary containing axis_left and axis_right
        config: Configuration dictionary with keys:
            - ai_a: {engine: str, model: Optional[str]}
            - ai_b: {engine: str, model: Optional[str]}

    Returns:
        Dictionary containing:
            - ai_a_round1: {claim, rationale, preemptive_counter, confidence_level}
            - ai_b_round1: {claim, rationale, preemptive_counter, confidence_level}
            - ai_a_engine: str
            - ai_a_model: str
            - ai_b_engine: str
            - ai_b_model: str
            - elapsed_seconds: float

    Example:
        >>> axis = {"axis_left": "効率最適化", "axis_right": "人間中心主義"}
        >>> config = {
        ...     "ai_a": {"engine": "API_Gemini", "model": "gemini-2.5-flash"},
        ...     "ai_b": {"engine": "API_Gemini", "model": "gemini-2.5-flash"}
        ... }
        >>> result = await execute_round1("AIによる雇用代替", axis, config)
        >>> "ai_a_round1" in result
        True
    """
    start_time = time.time()

    # Build prompts for both AIs using concrete stances
    prompt_a = prompt_builder.build_round1_prompt(
        topic,
        axis_result["ai_a_stance"],  # AI_A's concrete stance on the topic
        axis_result["ai_b_stance"]   # AI_B's concrete stance (opponent)
    )
    prompt_b = prompt_builder.build_round1_prompt(
        topic,
        axis_result["ai_b_stance"],  # AI_B's concrete stance on the topic
        axis_result["ai_a_stance"]   # AI_A's concrete stance (opponent)
    )

    logger.info("Executing Round 1 in parallel...")

    # Execute AI calls in parallel
    results = await asyncio.gather(
        ai_factory.call_ai(
            engine=config["ai_a"]["engine"],
            model=config["ai_a"].get("model"),
            prompt=prompt_a,
            timeout=60
        ),
        ai_factory.call_ai(
            engine=config["ai_b"]["engine"],
            model=config["ai_b"].get("model"),
            prompt=prompt_b,
            timeout=60
        )
    )

    ai_a_response, ai_b_response = results

    # Parse AI_A response
    if not ai_a_response["success"]:
        logger.error(f"AI_A Round 1 failed: {ai_a_response.get('error')}")
        raise Exception(f"AI_A Round 1 failed: {ai_a_response.get('error')}")

    # Use already-parsed JSON from ai_factory
    ai_a_data = ai_a_response.get("response")
    if not ai_a_data:
        logger.warning("AI_A Round 1: No JSON response from ai_factory, using fallback")
        output_a = ai_a_response.get("full_output", ai_a_response["raw_output"])
        ai_a_data = {
            "claim": output_a[:200],
            "rationale": ["JSON解析失敗"],
            "preemptive_counter": "",
            "confidence_level": "low"
        }

    # Parse AI_B response
    if not ai_b_response["success"]:
        logger.error(f"AI_B Round 1 failed: {ai_b_response.get('error')}")
        raise Exception(f"AI_B Round 1 failed: {ai_b_response.get('error')}")

    # Use already-parsed JSON from ai_factory
    ai_b_data = ai_b_response.get("response")
    if not ai_b_data:
        logger.warning("AI_B Round 1: No JSON response from ai_factory, using fallback")
        output_b = ai_b_response.get("full_output", ai_b_response["raw_output"])
        ai_b_data = {
            "claim": output_b[:200],
            "rationale": ["JSON解析失敗"],
            "preemptive_counter": "",
            "confidence_level": "low"
        }

    elapsed = time.time() - start_time
    logger.info(f"Round 1 completed in {elapsed:.2f}s")

    return {
        "ai_a_round1": ai_a_data,
        "ai_b_round1": ai_b_data,
        "ai_a_engine": config["ai_a"]["engine"],
        "ai_a_model": config["ai_a"].get("model", "default"),
        "ai_b_engine": config["ai_b"]["engine"],
        "ai_b_model": config["ai_b"].get("model", "default"),
        "elapsed_seconds": elapsed
    }


async def execute_round2(
    topic: str,
    axis_result: Dict[str, Any],
    round1_result: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Round 2 debate with parallel AI calls.

    Args:
        topic: Debate topic
        axis_result: Dictionary containing axis_left and axis_right
        round1_result: Dictionary containing ai_a_round1 and ai_b_round1
        config: Configuration dictionary with keys:
            - ai_a: {engine: str, model: Optional[str]}
            - ai_b: {engine: str, model: Optional[str]}

    Returns:
        Dictionary containing:
            - ai_a_round2: {counters, final_statement, confidence_level}
            - ai_b_round2: {counters, final_statement, confidence_level}
            - elapsed_seconds: float

    Example:
        >>> result = await execute_round2(topic, axis, round1, config)
        >>> "ai_a_round2" in result
        True
    """
    start_time = time.time()

    # Build prompts for both AIs using concrete stances (each AI counters the opponent's Round 1)
    prompt_a = prompt_builder.build_round2_prompt(
        topic,
        axis_result["ai_a_stance"],  # AI_A's concrete stance on the topic
        axis_result["ai_b_stance"],  # AI_B's concrete stance (opponent)
        round1_result["ai_b_round1"]  # AI_A counters AI_B's Round 1
    )
    prompt_b = prompt_builder.build_round2_prompt(
        topic,
        axis_result["ai_b_stance"],  # AI_B's concrete stance on the topic
        axis_result["ai_a_stance"],  # AI_A's concrete stance (opponent)
        round1_result["ai_a_round1"]  # AI_B counters AI_A's Round 1
    )

    logger.info("Executing Round 2 in parallel...")

    # Execute AI calls in parallel
    results = await asyncio.gather(
        ai_factory.call_ai(
            engine=config["ai_a"]["engine"],
            model=config["ai_a"].get("model"),
            prompt=prompt_a,
            timeout=60
        ),
        ai_factory.call_ai(
            engine=config["ai_b"]["engine"],
            model=config["ai_b"].get("model"),
            prompt=prompt_b,
            timeout=60
        )
    )

    ai_a_response, ai_b_response = results

    logger.info(f"Round 2 AI_A success={ai_a_response['success']}, error='{ai_a_response.get('error')}'")
    logger.info(f"Round 2 AI_B success={ai_b_response['success']}, error='{ai_b_response.get('error')}'")

    # Parse AI_A response
    if not ai_a_response["success"]:
        logger.error(f"AI_A Round 2 failed: {ai_a_response.get('error')}")
        raise Exception(f"AI_A Round 2 failed: {ai_a_response.get('error')}")

    # Use already-parsed JSON from ai_factory
    ai_a_data = ai_a_response.get("response")
    if not ai_a_data:
        logger.warning("AI_A Round 2: No JSON response from ai_factory, using fallback")
        output_a = ai_a_response.get("full_output", ai_a_response["raw_output"])
        ai_a_data = {
            "counters": ["JSON解析失敗"],
            "final_statement": output_a[:200],
            "confidence_level": "low"
        }

    # Parse AI_B response
    if not ai_b_response["success"]:
        logger.error(f"AI_B Round 2 failed: {ai_b_response.get('error')}")
        raise Exception(f"AI_B Round 2 failed: {ai_b_response.get('error')}")

    # Use already-parsed JSON from ai_factory
    ai_b_data = ai_b_response.get("response")
    if not ai_b_data:
        logger.warning("AI_B Round 2: No JSON response from ai_factory, using fallback")
        output_b = ai_b_response.get("full_output", ai_b_response["raw_output"])
        ai_b_data = {
            "counters": ["JSON解析失敗"],
            "final_statement": output_b[:200],
            "confidence_level": "low"
        }

    elapsed = time.time() - start_time
    logger.info(f"Round 2 completed in {elapsed:.2f}s")

    return {
        "ai_a_round2": ai_a_data,
        "ai_b_round2": ai_b_data,
        "elapsed_seconds": elapsed
    }


async def execute_judgment(
    topic: str,
    axis_result: Dict[str, Any],
    round1_result: Dict[str, Any],
    round2_result: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute final judgment and synthesis using Judge AI.

    Args:
        topic: Debate topic
        axis_result: Dictionary containing axis_left and axis_right
        round1_result: Dictionary containing ai_a_round1 and ai_b_round1
        round2_result: Dictionary containing ai_a_round2 and ai_b_round2
        config: Configuration dictionary with keys:
            - judge: {engine: str, model: Optional[str]}

    Returns:
        Dictionary containing:
            - winner (str): "AI_A" or "AI_B"
            - scores (Dict): {ai_a: {logic, attack, construct, total}, ai_b: {...}}
            - break_shot (Dict): {ai, category, score, quote}
            - reasoning (str): Judgment reasoning (30 chars max)
            - synthesis (str): Integrated conclusion (100-150 chars)
            - judge_engine (str): Judge AI engine used
            - judge_model (str): Judge AI model used
            - elapsed_seconds (float): Time taken for judgment

    Example:
        >>> result = await execute_judgment(topic, axis, round1, round2, config)
        >>> result["winner"] in ["AI_A", "AI_B"]
        True
    """
    start_time = time.time()

    # Build judgment prompt with all debate data
    all_data = {
        "topic": topic,
        "axis_left": axis_result["axis_left"],
        "axis_right": axis_result["axis_right"],
        "ai_a_round1": round1_result["ai_a_round1"],
        "ai_a_round2": round2_result["ai_a_round2"],
        "ai_b_round1": round1_result["ai_b_round1"],
        "ai_b_round2": round2_result["ai_b_round2"]
    }

    prompt = prompt_builder.build_judgment_prompt(all_data)

    logger.info("Executing final judgment...")

    # Call Judge AI
    response = await ai_factory.call_ai(
        engine=config["judge"]["engine"],
        model=config["judge"].get("model"),
        prompt=prompt,
        timeout=60
    )

    if not response["success"]:
        logger.error(f"Judgment failed: {response.get('error')}")
        raise Exception(f"Judgment failed: {response.get('error')}")

    # Use already-parsed JSON from ai_factory
    judgment_data = response.get("response")
    if not judgment_data:
        logger.error("Failed to parse judgment response as JSON")
        # Fallback judgment
        return {
            "winner": "AI_A",
            "scores": {
                "ai_a": {"logic": 5, "attack": 5, "construct": 5, "total": 15},
                "ai_b": {"logic": 5, "attack": 5, "construct": 5, "total": 15}
            },
            "break_shot": {
                "ai": "AI_A",
                "category": "LOGIC",
                "score": 5,
                "quote": "JSON解析失敗のため、判定不能"
            },
            "reasoning": "JSON解析失敗",
            "synthesis": "議論の統合結論を生成できませんでした。",
            "judge_engine": config["judge"]["engine"],
            "judge_model": config["judge"].get("model", "default"),
            "elapsed_seconds": time.time() - start_time
        }

    elapsed = time.time() - start_time
    logger.info(f"Judgment completed in {elapsed:.2f}s: Winner = {judgment_data.get('winner')}")

    # Extract score data with proper fallback structure
    scores = judgment_data.get("scores", {})

    # Ensure scores has proper structure even if JSON parsing was incomplete
    if not scores or "ai_a" not in scores or "ai_b" not in scores:
        logger.warning("Judgment scores incomplete, using fallback structure")
        scores = {
            "ai_a": {"logic": 5, "attack": 5, "construct": 5, "total": 15},
            "ai_b": {"logic": 5, "attack": 5, "construct": 5, "total": 15}
        }

    ai_a_scores = scores.get("ai_a", {})
    ai_b_scores = scores.get("ai_b", {})

    # Extract break_shot with proper fallback structure
    break_shot = judgment_data.get("break_shot", {})
    if not break_shot or "ai" not in break_shot or "quote" not in break_shot:
        logger.warning("Judgment break_shot incomplete, using fallback structure")
        break_shot = {
            "ai": "AI_A",
            "category": "LOGIC",
            "score": 5,
            "quote": "JSON解析失敗のため、判定不能"
        }

    return {
        "winner": judgment_data.get("winner", "AI_A"),
        "scores": scores,
        "ai_a_logic_score": ai_a_scores.get("logic", 0),
        "ai_a_attack_score": ai_a_scores.get("attack", 0),
        "ai_a_construct_score": ai_a_scores.get("construct", 0),
        "ai_a_total_score": ai_a_scores.get("total", 0),
        "ai_b_logic_score": ai_b_scores.get("logic", 0),
        "ai_b_attack_score": ai_b_scores.get("attack", 0),
        "ai_b_construct_score": ai_b_scores.get("construct", 0),
        "ai_b_total_score": ai_b_scores.get("total", 0),
        "break_shot": break_shot,
        "break_shot_ai": break_shot.get("ai", "AI_A"),
        "break_shot_category": break_shot.get("category", "LOGIC"),
        "break_shot_score": break_shot.get("score", 0),
        "break_shot_quote": break_shot.get("quote", ""),
        "reasoning": judgment_data.get("reasoning", ""),
        "synthesis": judgment_data.get("synthesis", ""),
        "judge_engine": config["judge"]["engine"],
        "judge_model": config["judge"].get("model", "default"),
        "elapsed_seconds": elapsed
    }

"""
Database manager for BREAK application.

Handles SQLite database operations including initialization, saving debates,
and retrieving history.
"""
import sqlite3
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import json


logger = logging.getLogger(__name__)

# Default database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "debates.db")


def init_db(db_path: str = DB_PATH) -> None:
    """
    Initialize SQLite database and create tables if they don't exist.

    Creates the data/ directory if it doesn't exist and sets up the
    debates table with proper schema and indexes.

    Args:
        db_path: Path to SQLite database file (default: data/debates.db)
    """
    # Create data directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")

    # Connect and create table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create debates table (design.md line 1-57 完全準拠)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,

            -- 議論軸
            axis_left TEXT NOT NULL,
            axis_right TEXT NOT NULL,
            axis_reasoning TEXT,

            -- AI_A データ
            ai_a_engine TEXT,
            ai_a_model TEXT,
            ai_a_round1_claim TEXT,
            ai_a_round1_rationale TEXT,
            ai_a_round1_preemptive TEXT,
            ai_a_round1_confidence TEXT,
            ai_a_round2_counters TEXT,
            ai_a_round2_final TEXT,
            ai_a_round2_confidence TEXT,

            -- AI_B データ
            ai_b_engine TEXT,
            ai_b_model TEXT,
            ai_b_round1_claim TEXT,
            ai_b_round1_rationale TEXT,
            ai_b_round1_preemptive TEXT,
            ai_b_round1_confidence TEXT,
            ai_b_round2_counters TEXT,
            ai_b_round2_final TEXT,
            ai_b_round2_confidence TEXT,

            -- 判定結果
            judge_engine TEXT,
            judge_model TEXT,
            winner TEXT,
            final_judgment TEXT,

            -- 個別スコアカラム（互換性のため保持）
            ai_a_logic_score INTEGER,
            ai_a_attack_score INTEGER,
            ai_a_construct_score INTEGER,
            ai_a_total_score INTEGER,
            ai_b_logic_score INTEGER,
            ai_b_attack_score INTEGER,
            ai_b_construct_score INTEGER,
            ai_b_total_score INTEGER,
            break_shot_ai TEXT,
            break_shot_category TEXT,
            break_shot_score INTEGER,
            break_shot_quote TEXT,
            reasoning TEXT,
            synthesis TEXT,

            -- メタデータ
            elapsed_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_debates_created_at
        ON debates(created_at DESC)
    """)

    conn.commit()
    conn.close()

    logger.info(f"Database initialized successfully at {db_path}")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Get a SQLite database connection with row factory enabled.

    Args:
        db_path: Path to SQLite database file

    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def save_debate(debate_data: Dict[str, Any], db_path: str = DB_PATH) -> int:
    """
    Save a debate result to the database.

    Args:
        debate_data: Dictionary containing debate data with structure:
            {
                "topic": str,
                "axis_left": str,
                "axis_right": str,
                "axis_reasoning": str,

                "ai_a_engine": str,
                "ai_a_model": str,
                "ai_a_round1_claim": str,
                "ai_a_round1_rationale": str (JSON string),
                "ai_a_round1_preemptive": str,
                "ai_a_round1_confidence": str,
                "ai_a_round2_counters": str (JSON string),
                "ai_a_round2_final": str,
                "ai_a_round2_confidence": str,

                "ai_b_engine": str,
                "ai_b_model": str,
                "ai_b_round1_claim": str,
                "ai_b_round1_rationale": str (JSON string),
                "ai_b_round1_preemptive": str,
                "ai_b_round1_confidence": str,
                "ai_b_round2_counters": str (JSON string),
                "ai_b_round2_final": str,
                "ai_b_round2_confidence": str,

                "judge_engine": str,
                "judge_model": str,
                "winner": str ("AI_A" | "AI_B"),
                "final_judgment": str (JSON string),

                "ai_a_logic_score": int,
                "ai_a_attack_score": int,
                "ai_a_construct_score": int,
                "ai_a_total_score": int,
                "ai_b_logic_score": int,
                "ai_b_attack_score": int,
                "ai_b_construct_score": int,
                "ai_b_total_score": int,
                "break_shot_ai": str,
                "break_shot_category": str,
                "break_shot_score": int,
                "break_shot_quote": str,
                "reasoning": str,
                "synthesis": str,

                "elapsed_time": float
            }
        db_path: Path to SQLite database file (default: data/debates.db)

    Returns:
        ID of the inserted row

    Raises:
        Exception: If database operation fails (logged but not suppressed)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Helper function to serialize lists/dicts to JSON
        def serialize_json(data: Any) -> Optional[str]:
            if data is None:
                return None
            if isinstance(data, (list, dict)):
                return json.dumps(data)
            return str(data)

        # Get current JST time (UTC+9)
        jst = timezone(timedelta(hours=9))
        now_jst = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO debates (
                topic, axis_left, axis_right, axis_reasoning,
                ai_a_engine, ai_a_model, ai_a_round1_claim, ai_a_round1_rationale,
                ai_a_round1_preemptive, ai_a_round1_confidence,
                ai_a_round2_counters, ai_a_round2_final, ai_a_round2_confidence,
                ai_b_engine, ai_b_model, ai_b_round1_claim, ai_b_round1_rationale,
                ai_b_round1_preemptive, ai_b_round1_confidence,
                ai_b_round2_counters, ai_b_round2_final, ai_b_round2_confidence,
                judge_engine, judge_model, winner, final_judgment,
                ai_a_logic_score, ai_a_attack_score, ai_a_construct_score, ai_a_total_score,
                ai_b_logic_score, ai_b_attack_score, ai_b_construct_score, ai_b_total_score,
                break_shot_ai, break_shot_category, break_shot_score, break_shot_quote,
                reasoning, synthesis, elapsed_time, created_at
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?
            )
        """, (
            debate_data["topic"],
            debate_data["axis_left"],
            debate_data["axis_right"],
            debate_data.get("axis_reasoning"),

            debate_data.get("ai_a_engine"),
            debate_data.get("ai_a_model"),
            debate_data.get("ai_a_round1_claim"),
            serialize_json(debate_data.get("ai_a_round1_rationale")),
            debate_data.get("ai_a_round1_preemptive"),
            debate_data.get("ai_a_round1_confidence"),
            serialize_json(debate_data.get("ai_a_round2_counters")),
            debate_data.get("ai_a_round2_final"),
            debate_data.get("ai_a_round2_confidence"),

            debate_data.get("ai_b_engine"),
            debate_data.get("ai_b_model"),
            debate_data.get("ai_b_round1_claim"),
            serialize_json(debate_data.get("ai_b_round1_rationale")),
            debate_data.get("ai_b_round1_preemptive"),
            debate_data.get("ai_b_round1_confidence"),
            serialize_json(debate_data.get("ai_b_round2_counters")),
            debate_data.get("ai_b_round2_final"),
            debate_data.get("ai_b_round2_confidence"),

            debate_data.get("judge_engine"),
            debate_data.get("judge_model"),
            debate_data.get("winner"),
            serialize_json(debate_data.get("final_judgment")),

            debate_data.get("ai_a_logic_score"),
            debate_data.get("ai_a_attack_score"),
            debate_data.get("ai_a_construct_score"),
            debate_data.get("ai_a_total_score"),
            debate_data.get("ai_b_logic_score"),
            debate_data.get("ai_b_attack_score"),
            debate_data.get("ai_b_construct_score"),
            debate_data.get("ai_b_total_score"),
            debate_data.get("break_shot_ai"),
            debate_data.get("break_shot_category"),
            debate_data.get("break_shot_score"),
            debate_data.get("break_shot_quote"),
            debate_data.get("reasoning"),
            debate_data.get("synthesis"),
            debate_data.get("elapsed_time"),
            now_jst
        ))

        row_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Debate saved successfully with ID: {row_id}")
        return row_id

    except Exception as e:
        logger.error(f"Failed to save debate: {e}", exc_info=True)
        raise


def get_debates(limit: int = 100, offset: int = 0, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """
    Retrieve paginated debate history from the database.

    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        db_path: Path to SQLite database file (default: data/debates.db)

    Returns:
        List of debate records (dictionaries)
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        # Get paginated items (most recent first)
        cursor.execute("""
            SELECT * FROM debates
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()

        # Convert rows to dictionaries
        items = []
        for row in rows:
            item = dict(row)

            # Deserialize JSON strings back to lists/dicts
            for key in ["ai_a_round1_rationale", "ai_a_round2_counters",
                       "ai_b_round1_rationale", "ai_b_round2_counters", "final_judgment"]:
                if item.get(key):
                    try:
                        item[key] = json.loads(item[key])
                    except json.JSONDecodeError:
                        item[key] = None

            items.append(item)

        conn.close()

        logger.info(f"Retrieved {len(items)} debate items (offset: {offset}, limit: {limit})")
        return items

    except Exception as e:
        logger.error(f"Failed to retrieve debates: {e}", exc_info=True)
        raise


def get_debate_by_id(debate_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific debate by its ID.

    Args:
        debate_id: ID of the debate to retrieve
        db_path: Path to SQLite database file (default: data/debates.db)

    Returns:
        Dictionary containing debate data, or None if not found
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM debates WHERE id = ?", (debate_id,))
        row = cursor.fetchone()

        conn.close()

        if row is None:
            logger.warning(f"Debate ID {debate_id} not found")
            return None

        # Convert row to dictionary
        item = dict(row)

        # Deserialize JSON strings back to lists/dicts
        for key in ["ai_a_round1_rationale", "ai_a_round2_counters",
                   "ai_b_round1_rationale", "ai_b_round2_counters", "final_judgment"]:
            if item.get(key):
                try:
                    item[key] = json.loads(item[key])
                except json.JSONDecodeError:
                    item[key] = None

        logger.info(f"Retrieved debate ID {debate_id}")
        return item

    except Exception as e:
        logger.error(f"Failed to retrieve debate {debate_id}: {e}", exc_info=True)
        raise


def get_total_count(db_path: str = DB_PATH) -> int:
    """
    Get the total number of debates in the database.

    Args:
        db_path: Path to SQLite database file (default: data/debates.db)

    Returns:
        Total number of debate records
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM debates")
        total = cursor.fetchone()["count"]

        conn.close()

        logger.info(f"Total debates count: {total}")
        return total

    except Exception as e:
        logger.error(f"Failed to get total count: {e}", exc_info=True)
        raise

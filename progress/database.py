"""SQLite Database persistence layer for Skillora AI."""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


DEFAULT_DB_FILENAME = "skillora.db"


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Resolve active SQLite database path."""
    if custom_path:
        return custom_path
    env_path = os.getenv("SKILLORA_DB_PATH")
    if env_path:
        return env_path
    return os.path.join(os.getcwd(), DEFAULT_DB_FILENAME)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a configured SQLite database connection."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database schema with required tables and indexes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. User Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            target_role TEXT NOT NULL DEFAULT 'Python Developer',
            skill_level TEXT NOT NULL DEFAULT 'Beginner',
            preferred_language TEXT NOT NULL DEFAULT 'English',
            daily_goal_minutes INTEGER NOT NULL DEFAULT 30,
            updated_at TEXT NOT NULL
        );
    """)

    # 2. Completed Lessons table with UNIQUE constraint preventing duplicate completions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completed_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            lesson_title TEXT NOT NULL,
            lesson_type TEXT NOT NULL DEFAULT 'roadmap_step',
            completed_date TEXT NOT NULL,  -- YYYY-MM-DD
            completed_timestamp TEXT NOT NULL,  -- ISO-8601
            notes TEXT,
            UNIQUE(skill_name, lesson_title)
        );
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_completed_date 
        ON completed_lessons(completed_date);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_completed_skill 
        ON completed_lessons(skill_name);
    """)

    # 3. Learning Streak table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streak_record (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_streak INTEGER NOT NULL DEFAULT 0,
            best_streak INTEGER NOT NULL DEFAULT 0,
            last_activity_date TEXT, -- YYYY-MM-DD
            total_active_days INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
    """)

    # 4. Custom Skill Overrides (confirmed or manually added skills)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_overrides (
            skill_name TEXT PRIMARY KEY,
            is_included INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        );
    """)

    # Populate default profile if empty
    cursor.execute("SELECT id FROM user_profile WHERE id = 1;")
    if not cursor.fetchone():
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO user_profile (id, target_role, skill_level, preferred_language, daily_goal_minutes, updated_at)
            VALUES (1, 'Python Developer', 'Beginner', 'English', 30, ?);
        """, (now_str,))

    # Populate default streak record if empty
    cursor.execute("SELECT id FROM streak_record WHERE id = 1;")
    if not cursor.fetchone():
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO streak_record (id, current_streak, best_streak, last_activity_date, total_active_days, updated_at)
            VALUES (1, 0, 0, NULL, 0, ?);
        """, (now_str,))

    conn.commit()
    conn.close()


def get_profile(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve saved student profile."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "target_role": "Python Developer",
        "skill_level": "Beginner",
        "preferred_language": "English",
        "daily_goal_minutes": 30
    }


def save_profile(
    target_role: str,
    skill_level: str,
    preferred_language: str,
    daily_goal_minutes: int,
    db_path: Optional[str] = None
) -> None:
    """Save or update student profile."""
    init_db(db_path)
    conn = get_connection(db_path)
    now_str = datetime.now().isoformat()
    conn.execute("""
        UPDATE user_profile
        SET target_role = ?,
            skill_level = ?,
            preferred_language = ?,
            daily_goal_minutes = ?,
            updated_at = ?
        WHERE id = 1;
    """, (target_role, skill_level, preferred_language, daily_goal_minutes, now_str))
    conn.commit()
    conn.close()


def add_completed_lesson(
    skill_name: str,
    lesson_title: str,
    lesson_type: str = "roadmap_step",
    completed_date: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Record lesson completion.
    Returns (success: bool, message: str).
    Guarantees no duplicate records via database constraints.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    now = datetime.now()
    date_str = completed_date or now.strftime("%Y-%m-%d")
    iso_timestamp = now.isoformat()

    try:
        conn.execute("""
            INSERT INTO completed_lessons (skill_name, lesson_title, lesson_type, completed_date, completed_timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (skill_name, lesson_title, lesson_type, date_str, iso_timestamp, notes))
        conn.commit()
        success = True
        message = f"Marked '{lesson_title}' ({skill_name}) as completed!"
    except sqlite3.IntegrityError:
        # Already completed
        success = False
        message = f"'{lesson_title}' for {skill_name} is already marked as completed."
    finally:
        conn.close()

    return success, message


def remove_completed_lesson(
    skill_name: str,
    lesson_title: str,
    db_path: Optional[str] = None
) -> bool:
    """Remove a completion record (undo)."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM completed_lessons
        WHERE skill_name = ? AND lesson_title = ?;
    """, (skill_name, lesson_title))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


def get_completed_lessons(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all completed lessons ordered by most recent."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, skill_name, lesson_title, lesson_type, completed_date, completed_timestamp, notes
        FROM completed_lessons
        ORDER BY completed_date DESC, id DESC;
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streak_record(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Fetch streak record."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM streak_record WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "current_streak": 0,
        "best_streak": 0,
        "last_activity_date": None,
        "total_active_days": 0
    }


def update_streak_record(
    current_streak: int,
    best_streak: int,
    last_activity_date: str,
    total_active_days: int,
    db_path: Optional[str] = None
) -> None:
    """Update streak metrics in the database."""
    init_db(db_path)
    conn = get_connection(db_path)
    now_str = datetime.now().isoformat()
    conn.execute("""
        UPDATE streak_record
        SET current_streak = ?,
            best_streak = ?,
            last_activity_date = ?,
            total_active_days = ?,
            updated_at = ?
        WHERE id = 1;
    """, (current_streak, best_streak, last_activity_date, total_active_days, now_str))
    conn.commit()
    conn.close()


def save_skill_override(skill_name: str, is_included: bool, db_path: Optional[str] = None) -> None:
    """Save manual skill confirmation or exclusion."""
    init_db(db_path)
    conn = get_connection(db_path)
    now_str = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO skill_overrides (skill_name, is_included, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(skill_name) DO UPDATE SET
            is_included = excluded.is_included,
            updated_at = excluded.updated_at;
    """, (skill_name, 1 if is_included else 0, now_str))
    conn.commit()
    conn.close()


def get_skill_overrides(db_path: Optional[str] = None) -> Dict[str, bool]:
    """Fetch all saved skill overrides."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT skill_name, is_included FROM skill_overrides;")
    rows = cursor.fetchall()
    conn.close()
    return {r["skill_name"]: bool(r["is_included"]) for r in rows}


def reset_all_progress(db_path: Optional[str] = None) -> None:
    """Reset all completion and streak history for a fresh start."""
    init_db(db_path)
    conn = get_connection(db_path)
    now_str = datetime.now().isoformat()
    conn.execute("DELETE FROM completed_lessons;")
    conn.execute("DELETE FROM skill_overrides;")
    conn.execute("""
        UPDATE streak_record
        SET current_streak = 0,
            best_streak = 0,
            last_activity_date = NULL,
            total_active_days = 0,
            updated_at = ?
        WHERE id = 1;
    """, (now_str,))
    conn.commit()
    conn.close()

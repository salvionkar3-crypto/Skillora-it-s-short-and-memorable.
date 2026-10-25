"""Progress tracking package for SQLite persistence, completions, and streaks."""

from .database import (
    init_db,
    get_profile,
    save_profile,
    get_completed_lessons,
    add_completed_lesson,
    remove_completed_lesson,
    reset_all_progress,
    get_db_path,
)
from .tracker import ProgressTracker, StreakInfo, ProgressSummary

__all__ = [
    "init_db",
    "get_profile",
    "save_profile",
    "get_completed_lessons",
    "add_completed_lesson",
    "remove_completed_lesson",
    "reset_all_progress",
    "get_db_path",
    "ProgressTracker",
    "StreakInfo",
    "ProgressSummary",
]

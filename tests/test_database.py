"""Tests for SQLite persistence, profile storage, and data integrity."""

import os
import pytest
from progress.database import (
    init_db,
    get_profile,
    save_profile,
    add_completed_lesson,
    get_completed_lessons,
    remove_completed_lesson,
    reset_all_progress,
    save_skill_override,
    get_skill_overrides,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_persistence.db")
    init_db(db_file)
    return db_file


def test_profile_persistence(temp_db):
    default_profile = get_profile(temp_db)
    assert default_profile["target_role"] == "Python Developer"

    # Update profile
    save_profile(
        target_role="AI Engineer",
        skill_level="Intermediate",
        preferred_language="Hindi",
        daily_goal_minutes=45,
        db_path=temp_db
    )

    updated = get_profile(temp_db)
    assert updated["target_role"] == "AI Engineer"
    assert updated["skill_level"] == "Intermediate"
    assert updated["preferred_language"] == "Hindi"
    assert updated["daily_goal_minutes"] == 45


def test_lesson_completion_persistence_and_deletion(temp_db):
    # Add lesson
    success, _ = add_completed_lesson(
        skill_name="Docker",
        lesson_title="Container Lifecycle",
        completed_date="2026-10-20",
        notes="Understood port forwarding",
        db_path=temp_db
    )
    assert success

    lessons = get_completed_lessons(temp_db)
    assert len(lessons) == 1
    assert lessons[0]["skill_name"] == "Docker"
    assert lessons[0]["lesson_title"] == "Container Lifecycle"
    assert lessons[0]["notes"] == "Understood port forwarding"

    # Delete lesson (undo)
    deleted = remove_completed_lesson("Docker", "Container Lifecycle", db_path=temp_db)
    assert deleted
    assert len(get_completed_lessons(temp_db)) == 0


def test_skill_overrides_persistence(temp_db):
    save_skill_override("Kubernetes", True, db_path=temp_db)
    save_skill_override("PHP", False, db_path=temp_db)

    overrides = get_skill_overrides(temp_db)
    assert overrides["Kubernetes"] is True
    assert overrides["PHP"] is False


def test_reset_all_progress(temp_db):
    add_completed_lesson("SQL", "Joins", db_path=temp_db)
    save_skill_override("Git", True, db_path=temp_db)

    reset_all_progress(temp_db)

    assert len(get_completed_lessons(temp_db)) == 0
    assert len(get_skill_overrides(temp_db)) == 0

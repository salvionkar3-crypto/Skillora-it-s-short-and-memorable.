"""Tests for lesson completion tracking, duplicate prevention, and streak boundary cases."""

import os
from datetime import date, timedelta
import pytest

from progress.database import init_db, get_completed_lessons, get_streak_record
from progress.tracker import ProgressTracker


@pytest.fixture
def temp_tracker(tmp_path):
    db_file = str(tmp_path / "test_tracker.db")
    init_db(db_file)
    return ProgressTracker(db_path=db_file)


def test_mark_lesson_completion_success(temp_tracker):
    success, message, streak = temp_tracker.record_lesson_completion(
        skill_name="Python",
        lesson_title="Python Variables and Types",
        completion_date="2026-10-20"
    )
    assert success
    assert "Marked" in message
    assert streak.current_streak == 1
    assert streak.best_streak == 1
    assert streak.total_active_days == 1


def test_prevent_accidental_duplicate_completion(temp_tracker):
    # First time completing the lesson
    success1, msg1, _ = temp_tracker.record_lesson_completion(
        skill_name="Python",
        lesson_title="Functions and Scopes",
        completion_date="2026-10-20"
    )
    assert success1

    # Second attempt to complete the exact same lesson for the skill
    success2, msg2, streak = temp_tracker.record_lesson_completion(
        skill_name="Python",
        lesson_title="Functions and Scopes",
        completion_date="2026-10-20"
    )
    assert not success2
    assert "already marked as completed" in msg2

    # Database must contain exactly 1 completion record
    completed = get_completed_lessons(temp_tracker.db_path)
    assert len(completed) == 1


def test_same_day_completion_does_not_increment_streak(temp_tracker):
    today_str = "2026-10-20"

    # Complete lesson 1 on today
    s1, _, streak1 = temp_tracker.record_lesson_completion("Python", "Lesson 1", completion_date=today_str)
    assert s1
    assert streak1.current_streak == 1
    assert streak1.total_active_days == 1

    # Complete lesson 2 on the SAME day
    s2, _, streak2 = temp_tracker.record_lesson_completion("SQL", "Lesson 2", completion_date=today_str)
    assert s2
    # Streak and active days must remain 1!
    assert streak2.current_streak == 1
    assert streak2.total_active_days == 1


def test_consecutive_days_increase_streak(temp_tracker):
    # Day 1
    day1 = date(2026, 10, 20)
    temp_tracker.record_lesson_completion("Python", "Lesson Day 1", completion_date=day1)

    # Day 2 (Consecutive)
    day2 = date(2026, 10, 21)
    _, _, streak_day2 = temp_tracker.record_lesson_completion("SQL", "Lesson Day 2", completion_date=day2)
    assert streak_day2.current_streak == 2
    assert streak_day2.best_streak == 2
    assert streak_day2.total_active_days == 2

    # Day 3 (Consecutive)
    day3 = date(2026, 10, 22)
    _, _, streak_day3 = temp_tracker.record_lesson_completion("Git", "Lesson Day 3", completion_date=day3)
    assert streak_day3.current_streak == 3
    assert streak_day3.best_streak == 3
    assert streak_day3.total_active_days == 3


def test_missed_day_resets_streak_when_next_activity_occurs(temp_tracker):
    # Day 1: User active
    day1 = date(2026, 10, 20)
    temp_tracker.record_lesson_completion("Python", "Lesson 1", completion_date=day1)

    # Day 2: User active
    day2 = date(2026, 10, 21)
    temp_tracker.record_lesson_completion("Python", "Lesson 2", completion_date=day2)

    # Day 3 was missed!
    # Day 4: User completes lesson after missing day 3
    day4 = date(2026, 10, 23)
    _, _, streak_day4 = temp_tracker.record_lesson_completion("Docker", "Lesson Day 4", completion_date=day4)

    # Current streak must reset to 1
    assert streak_day4.current_streak == 1
    # Best streak must be preserved at 2!
    assert streak_day4.best_streak == 2
    # Total active days must be 3 (Day 1, Day 2, Day 4)
    assert streak_day4.total_active_days == 3


def test_streak_status_lapsed_when_viewed_after_missed_day(temp_tracker):
    # Day 1 activity
    day1 = date(2026, 10, 20)
    temp_tracker.record_lesson_completion("Python", "Lesson 1", completion_date=day1)

    # Viewing on Day 2: streak is active from yesterday
    status_day2 = temp_tracker.get_streak_info(current_date=date(2026, 10, 21))
    assert status_day2.current_streak == 1
    assert not status_day2.is_active_today
    assert "keep it burning" in status_day2.streak_status_text.lower()

    # Viewing on Day 3 without having done day 2 or day 3: streak has lapsed to 0
    status_day3 = temp_tracker.get_streak_info(current_date=date(2026, 10, 22))
    assert status_day3.current_streak == 0
    assert "lapsed" in status_day3.streak_status_text.lower()

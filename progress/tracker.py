"""Learning progress and streak calculation logic with date-boundary safety."""

from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .database import (
    get_completed_lessons,
    add_completed_lesson,
    remove_completed_lesson,
    get_streak_record,
    update_streak_record,
    get_profile,
    save_profile,
)


@dataclass
class StreakInfo:
    """Detailed daily streak metrics."""
    current_streak: int
    best_streak: int
    total_active_days: int
    last_activity_date: Optional[str]
    is_active_today: bool
    streak_status_text: str


@dataclass
class ProgressSummary:
    """Comprehensive progress summary."""
    total_lessons_target: int
    completed_lessons_count: int
    remaining_lessons_count: int
    progress_percentage: float
    skills_completed: List[str] = field(default_factory=list)
    skills_in_progress: List[str] = field(default_factory=list)
    completed_today_count: int = 0
    daily_goal_minutes: int = 30


class ProgressTracker:
    """Manages lesson completion tracking and streak accounting."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def parse_date(self, date_input: Optional[date | str]) -> date:
        """Helper to parse a date object or YYYY-MM-DD string."""
        if date_input is None:
            return date.today()
        if isinstance(date_input, date):
            return date_input
        return datetime.strptime(date_input, "%Y-%m-%d").date()

    def record_lesson_completion(
        self,
        skill_name: str,
        lesson_title: str,
        lesson_type: str = "roadmap_step",
        completion_date: Optional[date | str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, StreakInfo]:
        """
        Record that a student has completed a lesson, preventing duplicates
        and updating the daily learning streak.
        
        Returns:
            (success: bool, message: str, streak_info: StreakInfo)
        """
        target_date = self.parse_date(completion_date)
        date_str = target_date.strftime("%Y-%m-%d")

        # 1. Attempt database insert with unique constraint
        success, message = add_completed_lesson(
            skill_name=skill_name,
            lesson_title=lesson_title,
            lesson_type=lesson_type,
            completed_date=date_str,
            notes=notes,
            db_path=self.db_path
        )

        if success:
            # 2. Update streak accounting for this qualifying completion
            streak_info = self._process_streak_update(target_date)
        else:
            streak_info = self.get_streak_info(current_date=target_date)

        return success, message, streak_info

    def _process_streak_update(self, completion_date: date) -> StreakInfo:
        """Update streak values in database according to strict date rules."""
        record = get_streak_record(self.db_path)
        cur_streak = record["current_streak"]
        best_streak = record["best_streak"]
        total_days = record["total_active_days"]
        last_date_str = record["last_activity_date"]

        date_str = completion_date.strftime("%Y-%m-%d")

        if last_date_str is None:
            # First activity ever
            cur_streak = 1
            best_streak = 1
            total_days = 1
        else:
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            diff_days = (completion_date - last_date).days

            if diff_days == 0:
                # Same calendar day: do not increase streak or total days
                pass
            elif diff_days == 1:
                # Consecutive day: increment streak
                cur_streak += 1
                best_streak = max(best_streak, cur_streak)
                total_days += 1
            elif diff_days > 1:
                # Missed one or more days: reset streak to 1
                cur_streak = 1
                total_days += 1
            else:
                # Past date backfill: do not alter ongoing forward streak
                pass

        update_streak_record(
            current_streak=cur_streak,
            best_streak=best_streak,
            last_activity_date=date_str,
            total_active_days=total_days,
            db_path=self.db_path
        )

        return self.get_streak_info(current_date=completion_date)

    def get_streak_info(self, current_date: Optional[date | str] = None) -> StreakInfo:
        """
        Calculate current streak status taking into account today's date.
        If today is 2 or more days after the last activity, the streak is currently broken
        and will show 0 until the user completes an activity today.
        """
        today = self.parse_date(current_date)
        record = get_streak_record(self.db_path)

        stored_current = record["current_streak"]
        stored_best = record["best_streak"]
        total_days = record["total_active_days"]
        last_date_str = record["last_activity_date"]

        if not last_date_str:
            return StreakInfo(
                current_streak=0,
                best_streak=stored_best,
                total_active_days=total_days,
                last_activity_date=None,
                is_active_today=False,
                streak_status_text="No lessons completed yet. Complete a lesson to ignite your streak!"
            )

        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        diff = (today - last_date).days

        if diff == 0:
            # Active today
            return StreakInfo(
                current_streak=stored_current,
                best_streak=stored_best,
                total_active_days=total_days,
                last_activity_date=last_date_str,
                is_active_today=True,
                streak_status_text=f"🔥 {stored_current} Day Streak! Great job learning today!"
            )
        elif diff == 1:
            # Last active yesterday: streak is alive, waiting for today's activity
            return StreakInfo(
                current_streak=stored_current,
                best_streak=stored_best,
                total_active_days=total_days,
                last_activity_date=last_date_str,
                is_active_today=False,
                streak_status_text=f"⏳ {stored_current} Day Streak active! Complete a lesson today to keep it burning!"
            )
        else:
            # Missed at least one day: streak has lapsed to 0
            return StreakInfo(
                current_streak=0,
                best_streak=stored_best,
                total_active_days=total_days,
                last_activity_date=last_date_str,
                is_active_today=False,
                streak_status_text=f"Streak lapsed ({diff} days since last lesson). Complete a lesson today to start a new 1-day streak!"
            )

    def get_progress_summary(
        self,
        roadmap_skills: List[str],
        current_date: Optional[date | str] = None
    ) -> ProgressSummary:
        """
        Compile full progress report against a set of roadmap skills.
        """
        today_str = self.parse_date(current_date).strftime("%Y-%m-%d")
        all_completed = get_completed_lessons(self.db_path)
        profile = get_profile(self.db_path)

        # Count completed by skill
        completed_skills_map: Dict[str, int] = {}
        completed_today_count = 0

        for item in all_completed:
            s_name = item["skill_name"]
            completed_skills_map[s_name] = completed_skills_map.get(s_name, 0) + 1
            if item["completed_date"] == today_str:
                completed_today_count += 1

        total_target = len(roadmap_skills)
        completed_count = len(all_completed)
        remaining_count = max(0, total_target - completed_count)

        if total_target > 0:
            pct = round(min(100.0, (completed_count / total_target) * 100), 1)
        else:
            pct = 100.0 if completed_count > 0 else 0.0

        skills_completed = []
        skills_in_progress = []

        for skill in roadmap_skills:
            if completed_skills_map.get(skill, 0) > 0:
                skills_completed.append(skill)
            else:
                skills_in_progress.append(skill)

        return ProgressSummary(
            total_lessons_target=total_target,
            completed_lessons_count=completed_count,
            remaining_lessons_count=remaining_count,
            progress_percentage=pct,
            skills_completed=skills_completed,
            skills_in_progress=skills_in_progress,
            completed_today_count=completed_today_count,
            daily_goal_minutes=profile.get("daily_goal_minutes", 30)
        )

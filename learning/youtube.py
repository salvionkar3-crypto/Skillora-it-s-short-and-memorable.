"""YouTube Learning Hub: Curated lesson recommendations and safe search fallbacks."""

import json
import os
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class VideoLesson:
    """Represents a video lesson or verified search fallback."""
    skill: str
    title: str
    channel_name: str
    url: str
    video_id: Optional[str] = None
    language: str = "English"
    difficulty: str = "Beginner"
    duration_minutes: Optional[int] = None
    is_curated: bool = True
    is_search_fallback: bool = False
    note: Optional[str] = None


class YouTubeHub:
    """Manages verified video catalog lookups and dynamic search fallbacks."""

    def __init__(self, catalog_path: Optional[str] = None):
        if catalog_path is None:
            # Default to data/sample_videos.json relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            catalog_path = os.path.join(base_dir, "data", "sample_videos.json")

        self.catalog_path = catalog_path
        self.catalog: List[Dict[str, Any]] = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        """Safely load curated video catalog from JSON file."""
        if not os.path.exists(self.catalog_path):
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_lessons_for_skill(
        self,
        skill: str,
        preferred_language: str = "English",
        difficulty: str = "Beginner",
        limit: int = 3
    ) -> List[VideoLesson]:
        """
        Retrieve matching curated video lessons for a given skill.
        Falls back to a verified YouTube search URL if no curated video matches.
        """
        skill_clean = skill.strip().lower()
        matched_items: List[Dict[str, Any]] = []

        # 1. Look for direct skill match in curated catalog
        for item in self.catalog:
            item_skill = item.get("skill", "").strip().lower()
            if item_skill == skill_clean:
                matched_items.append(item)

        # 2. Score and sort by language and difficulty preference
        def score_candidate(item: Dict[str, Any]) -> int:
            score = 0
            if item.get("language", "").lower() == preferred_language.lower():
                score += 10
            if item.get("difficulty", "").lower() == difficulty.lower():
                score += 5
            return score

        matched_items.sort(key=score_candidate, reverse=True)

        lessons: List[VideoLesson] = []
        for item in matched_items[:limit]:
            lessons.append(
                VideoLesson(
                    skill=item.get("skill", skill),
                    title=item.get("title", ""),
                    channel_name=item.get("channel_name", "Verified Channel"),
                    url=item.get("url", f"https://www.youtube.com/watch?v={item.get('video_id', '')}"),
                    video_id=item.get("video_id"),
                    language=item.get("language", "English"),
                    difficulty=item.get("difficulty", "Beginner"),
                    duration_minutes=item.get("duration_minutes"),
                    is_curated=True,
                    is_search_fallback=False
                )
            )

        # 3. If no curated lessons found, create safe, explicit search link
        if not lessons:
            search_query = f"{skill} tutorial {preferred_language} {difficulty} full course".strip()
            encoded_query = urllib.parse.quote_plus(search_query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

            lessons.append(
                VideoLesson(
                    skill=skill,
                    title=f"Explore '{skill}' Lessons on YouTube",
                    channel_name="YouTube Search (Official Link)",
                    url=search_url,
                    video_id=None,
                    language=preferred_language,
                    difficulty=difficulty,
                    duration_minutes=None,
                    is_curated=False,
                    is_search_fallback=True,
                    note=(
                        f"No pre-curated video was found for '{skill}' with language '{preferred_language}'. "
                        "This verified official YouTube search query opens top community tutorials."
                    )
                )
            )

        return lessons

    def get_lessons_for_roadmap(
        self,
        skills: List[str],
        preferred_language: str = "English",
        difficulty: str = "Beginner"
    ) -> Dict[str, List[VideoLesson]]:
        """Batch retrieve lessons for an entire roadmap plan."""
        result: Dict[str, List[VideoLesson]] = {}
        for skill in skills:
            result[skill] = self.get_lessons_for_skill(
                skill=skill,
                preferred_language=preferred_language,
                difficulty=difficulty,
                limit=2
            )
        return result

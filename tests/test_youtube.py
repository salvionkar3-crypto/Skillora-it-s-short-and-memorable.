"""Tests for YouTube Learning Hub: curated video lookups and safe search fallback."""

import pytest
from learning.youtube import YouTubeHub, VideoLesson


@pytest.fixture
def youtube_hub():
    return YouTubeHub()


def test_matching_curated_video_english(youtube_hub):
    lessons = youtube_hub.get_lessons_for_skill("Python", preferred_language="English", difficulty="Beginner")
    assert len(lessons) > 0
    first = lessons[0]
    assert first.skill == "Python"
    assert first.is_curated
    assert not first.is_search_fallback
    assert first.video_id is not None
    assert "youtube.com/watch?v=" in first.url
    assert first.channel_name != ""


def test_matching_curated_video_hindi(youtube_hub):
    lessons = youtube_hub.get_lessons_for_skill("Python", preferred_language="Hindi", difficulty="Beginner")
    assert len(lessons) > 0
    # The top recommended video should match Hindi language preference
    assert lessons[0].language == "Hindi"
    assert lessons[0].is_curated


def test_matching_curated_video_marathi(youtube_hub):
    lessons = youtube_hub.get_lessons_for_skill("Python", preferred_language="Marathi", difficulty="Beginner")
    assert len(lessons) > 0
    assert lessons[0].language == "Marathi"
    assert lessons[0].is_curated


def test_safe_search_fallback_when_no_video_curated(youtube_hub):
    # Search for an unlisted/obscure technology not in sample_videos.json
    rare_skill = "Assembly x86_64 Architecture"
    lessons = youtube_hub.get_lessons_for_skill(rare_skill, preferred_language="English", difficulty="Beginner")

    assert len(lessons) == 1
    fallback = lessons[0]
    assert not fallback.is_curated
    assert fallback.is_search_fallback
    assert fallback.video_id is None
    assert "https://www.youtube.com/results?search_query=" in fallback.url
    assert fallback.note is not None
    assert "No pre-curated video was found" in fallback.note


def test_batch_roadmap_lessons_retrieval(youtube_hub):
    skills = ["Python", "SQL", "Git"]
    batch = youtube_hub.get_lessons_for_roadmap(skills, preferred_language="English")
    assert "Python" in batch
    assert "SQL" in batch
    assert "Git" in batch
    assert len(batch["Python"]) > 0

"""Tests for learning roadmap generation, priority sequencing, and prerequisites."""

import pytest
from learning.roadmap import RoadmapGenerator


@pytest.fixture
def generator():
    return RoadmapGenerator()


def test_roadmap_empty_missing_skills(generator):
    plan = generator.generate_roadmap([], target_role="Python Developer", skill_level="Beginner")
    assert plan.total_steps == 0
    assert plan.total_estimated_hours == 0
    assert len(plan.steps) == 0


def test_roadmap_priority_and_prerequisite_ordering(generator):
    # Candidate lacks Python, Django, Docker, and Git
    missing = ["Django", "Python", "Docker", "Git"]
    plan = generator.generate_roadmap(missing, target_role="Python Developer", skill_level="Beginner")

    assert plan.total_steps == 4
    step_skills = [s.skill_name for s in plan.steps]

    # Python must precede Django because Python is a prerequisite for Django
    py_index = step_skills.index("Python")
    django_index = step_skills.index("Django")
    assert py_index < django_index

    # Python must have High priority for Python Developer role
    py_step = plan.steps[py_index]
    assert py_step.priority == "High"
    assert len(py_step.learning_objectives) >= 3
    assert py_step.mini_project != ""


def test_roadmap_frontend_prerequisites(generator):
    # Candidate needs React, JavaScript, HTML5, CSS3
    missing = ["React", "CSS3", "JavaScript", "HTML5"]
    plan = generator.generate_roadmap(missing, target_role="Web Developer (Full Stack)", skill_level="Beginner")

    step_skills = [s.skill_name for s in plan.steps]
    html_idx = step_skills.index("HTML5")
    css_idx = step_skills.index("CSS3")
    js_idx = step_skills.index("JavaScript")
    react_idx = step_skills.index("React")

    # HTML5 & CSS3 before JavaScript before React
    assert html_idx < js_idx
    assert js_idx < react_idx


def test_duration_scaling_by_skill_level(generator):
    missing = ["Python", "SQL"]
    beginner_plan = generator.generate_roadmap(missing, target_role="Python Developer", skill_level="Beginner")
    advanced_plan = generator.generate_roadmap(missing, target_role="Python Developer", skill_level="Advanced")

    # Beginner hours should be higher than Advanced hours
    assert beginner_plan.total_estimated_hours > advanced_plan.total_estimated_hours

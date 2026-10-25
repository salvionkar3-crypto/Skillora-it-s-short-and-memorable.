"""Tests for deterministic skill matching, aliases, gap detection, and transparent scoring."""

import pytest
from analyzer.matcher import SkillMatcher


@pytest.fixture
def matcher():
    return SkillMatcher()


def test_exact_and_case_insensitive_matching(matcher):
    text = "Proficient in Python, SQL, and Docker with hands-on Git experience."
    skills = matcher.extract_skills_from_text(text)
    assert "Python" in skills
    assert "SQL" in skills
    assert "Docker" in skills
    assert "Git" in skills


def test_alias_resolution(matcher):
    # k8s -> Kubernetes, postgres -> PostgreSQL, js -> JavaScript, py -> Python
    text = "Built web apps with js and reactjs. Deployed to k8s using postgres database and gh actions."
    skills = matcher.extract_skills_from_text(text)
    assert "JavaScript" in skills
    assert "React" in skills
    assert "Kubernetes" in skills
    assert "PostgreSQL" in skills
    assert "GitHub Actions" in skills


def test_special_symbols_handling(matcher):
    text = "Experience with C++, C#, and .NET core frameworks."
    skills = matcher.extract_skills_from_text(text)
    assert "C++" in skills
    assert "C#" in skills


def test_role_gap_analysis_python_developer(matcher):
    # Candidate knows Python, Git, and SQL (Core skills for Python Dev), but misses pytest and REST APIs
    resume = "Passionate developer skilled in Python, SQL, and Git."
    result = matcher.analyze_gaps(resume, target_role="Python Developer")

    assert "Python" in result.matched_skills
    assert "SQL" in result.matched_skills
    assert "Git" in result.matched_skills
    
    # Missing core skills
    assert "REST APIs" in result.missing_skills
    assert "pytest" in result.missing_skills

    # Match score should be strictly between 0 and 100
    assert 0 < result.match_score < 100
    assert "Formula:" in result.score_breakdown
    assert "NOT an automated hiring decision" in result.score_breakdown


def test_job_description_incorporation(matcher):
    resume = "Experienced in Python and SQL."
    jd = "Looking for a Python Developer who knows Redis and Docker."
    result = matcher.analyze_gaps(resume, target_role="Python Developer", job_description=jd)

    assert "Docker" in result.missing_skills
    assert "Redis" in result.missing_skills
    assert "Docker" in result.jd_skills_detected or "Redis" in result.jd_skills_detected


def test_manual_overrides(matcher):
    resume = "Experienced in Python."
    # Candidate manually confirms they know SQL even if not on resume, and unchecks Python
    overrides = {
        "SQL": True,
        "Python": False
    }
    result = matcher.analyze_gaps(resume, target_role="Python Developer", manual_overrides=overrides)

    assert "SQL" in result.matched_skills
    assert "Python" in result.missing_skills

"""Analyzer package for resume extraction and skill gap matching."""

from .parser import extract_text_from_file, ResumeParseResult
from .skills_db import SKILL_TAXONOMY, ROLE_REQUIREMENTS, SKILL_ALIASES, ROLE_METADATA
from .matcher import SkillMatcher, GapAnalysisResult

__all__ = [
    "extract_text_from_file",
    "ResumeParseResult",
    "SKILL_TAXONOMY",
    "ROLE_REQUIREMENTS",
    "SKILL_ALIASES",
    "ROLE_METADATA",
    "SkillMatcher",
    "GapAnalysisResult",
]

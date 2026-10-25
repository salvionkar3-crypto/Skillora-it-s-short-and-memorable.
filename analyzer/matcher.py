"""Deterministic Skill Matching, Gap Analysis, and Transparent Scoring."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional

from .skills_db import (
    SKILL_TAXONOMY,
    ROLE_REQUIREMENTS,
    SKILL_ALIASES,
    ROLE_METADATA,
)


@dataclass
class GapAnalysisResult:
    """Detailed skill gap analysis result."""
    target_role: str
    match_score: float
    score_breakdown: str
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    needs_review: List[str] = field(default_factory=list)
    additional_skills: List[str] = field(default_factory=list)
    core_matched: List[str] = field(default_factory=list)
    core_missing: List[str] = field(default_factory=list)
    recommended_matched: List[str] = field(default_factory=list)
    recommended_missing: List[str] = field(default_factory=list)
    jd_skills_detected: List[str] = field(default_factory=list)


class SkillMatcher:
    """Deterministic extractor and skill gap comparator."""

    def __init__(self):
        # Build master dictionary of all canonical skills and their patterns
        self.all_canonical_skills: Set[str] = set()
        for cat_skills in SKILL_TAXONOMY.values():
            self.all_canonical_skills.update(cat_skills)

        # Precompile patterns for fast and accurate extraction
        self.skill_patterns = self._compile_skill_patterns()

    def _compile_skill_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Pre-compile regex patterns for canonical skills and their known aliases."""
        patterns: Dict[str, List[re.Pattern]] = {}

        # 1. Patterns for canonical names
        for skill in self.all_canonical_skills:
            patterns[skill] = [self._build_regex(skill)]

        # 2. Add alias patterns pointing to canonical names
        for alias, canonical in SKILL_ALIASES.items():
            if canonical not in patterns:
                patterns[canonical] = []
            patterns[canonical].append(self._build_regex(alias))

        return patterns

    def _build_regex(self, term: str) -> re.Pattern:
        """Build regex with safe word boundaries, handling symbols like +, #, ., /."""
        escaped = re.escape(term)
        # If term starts/ends with alphanumeric, use \b boundary, else use non-alphanumeric or start/end
        start_bound = r"\b" if re.match(r"^\w", term) else r"(?:(?<=\s)|(?<=[(\[,;:])|^)"
        end_bound = r"\b" if re.search(r"\w$", term) else r"(?:(?=\s)|(?=[)\],;:.?!])|$)"
        pattern_str = f"{start_bound}{escaped}{end_bound}"
        return re.compile(pattern_str, re.IGNORECASE)

    def extract_skills_from_text(self, text: str) -> Set[str]:
        """Extract detected canonical skills from any freeform text string."""
        if not text:
            return set()

        detected = set()
        for canonical_name, pattern_list in self.skill_patterns.items():
            for pat in pattern_list:
                if pat.search(text):
                    detected.add(canonical_name)
                    break  # Found this canonical skill, move to next

        return detected

    def analyze_gaps(
        self,
        resume_text: str,
        target_role: str = "Python Developer",
        job_description: Optional[str] = None,
        manual_overrides: Optional[Dict[str, bool]] = None
    ) -> GapAnalysisResult:
        """
        Perform deterministic skill gap analysis comparing resume against role requirements.
        
        Args:
            resume_text: Raw or cleaned text extracted from resume.
            target_role: Target job profile name.
            job_description: Optional text of a specific job posting.
            manual_overrides: Optional dict of {skill_name: True (force include) / False (force exclude)}.
        """
        # 1. Extract skills from resume
        extracted_from_resume = self.extract_skills_from_text(resume_text)

        # 2. Apply user manual adjustments if present
        if manual_overrides:
            for skill, included in manual_overrides.items():
                if included:
                    extracted_from_resume.add(skill)
                else:
                    extracted_from_resume.discard(skill)

        # 3. Determine role requirements
        role_reqs = ROLE_REQUIREMENTS.get(target_role, {
            "core": ["Python", "SQL", "Git"],
            "recommended": ["Docker", "REST APIs", "Linux"]
        })

        core_set = set(role_reqs.get("core", []))
        rec_set = set(role_reqs.get("recommended", []))

        # 4. Extract JD skills if provided
        jd_skills: Set[str] = set()
        if job_description and job_description.strip():
            jd_skills = self.extract_skills_from_text(job_description)
            # Add JD skills to recommended set if not already in core
            for s in jd_skills:
                if s not in core_set:
                    rec_set.add(s)

        # 5. Categorize skills
        core_matched = sorted(list(core_set.intersection(extracted_from_resume)))
        core_missing = sorted(list(core_set.difference(extracted_from_resume)))

        rec_matched = sorted(list(rec_set.intersection(extracted_from_resume)))
        rec_missing = sorted(list(rec_set.difference(extracted_from_resume)))

        all_matched = sorted(list(set(core_matched + rec_matched)))
        all_missing = sorted(list(set(core_missing + rec_missing)))

        # Candidate skills not required by this specific role (strengths / bonus)
        required_union = core_set.union(rec_set)
        additional_skills = sorted(list(extracted_from_resume.difference(required_union)))

        # Needs Review: skills found in JD that were not in standard role, or ambiguous
        needs_review = []
        for s in jd_skills:
            if s not in extracted_from_resume:
                needs_review.append(f"{s} (Required by Job Description)")

        # 6. Calculate Transparent Match Score
        # Core skills weight: 1.5, Recommended skills weight: 1.0
        core_weight = 1.5
        rec_weight = 1.0

        total_possible = (len(core_set) * core_weight) + (len(rec_set) * rec_weight)
        earned_score = (len(core_matched) * core_weight) + (len(rec_matched) * rec_weight)

        if total_possible > 0:
            match_score = round((earned_score / total_possible) * 100, 1)
        else:
            match_score = 0.0

        breakdown = (
            f"Formula: (Matched Core [{len(core_matched)}/{len(core_set)}] × 1.5 + "
            f"Matched Recommended [{len(rec_matched)}/{len(rec_set)}] × 1.0) / "
            f"Total Target Weights ({total_possible:.1f}) × 100 = {match_score}%. "
            "Note: This score reflects keyword alignment with the target role syllabus. "
            "It is NOT an automated hiring decision or probability."
        )

        return GapAnalysisResult(
            target_role=target_role,
            match_score=match_score,
            score_breakdown=breakdown,
            matched_skills=all_matched,
            missing_skills=all_missing,
            needs_review=needs_review,
            additional_skills=additional_skills,
            core_matched=core_matched,
            core_missing=core_missing,
            recommended_matched=rec_matched,
            recommended_missing=rec_missing,
            jd_skills_detected=sorted(list(jd_skills))
        )

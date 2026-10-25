"""
Reusable local AI service module interfacing Gemma 3:1B via Ollama's HTTP API.

Provides:
- Health checking and model discovery on http://localhost:11434
- Safe generation with timeout, connection error, and invalid response handling
- Resume evidence extraction (grounded strictly in resume text)
- Job description context extraction without hallucination
- Personalized roadmap mentor guidance connecting existing skills to skill gaps
- Deterministic fallbacks when Ollama is offline or unavailable
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma3:1b"
DEFAULT_TIMEOUT = 25  # seconds for generation
DEFAULT_HEALTH_TIMEOUT = 3.5  # seconds for quick ping


@dataclass
class AIHealthStatus:
    """Current health and readiness status of the local Ollama Gemma instance."""
    is_connected: bool
    model_available: bool
    model_name: str
    base_url: str
    available_models: List[str] = field(default_factory=list)
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    @property
    def status_summary(self) -> str:
        if self.is_connected and self.model_available:
            ms_str = f" ({self.response_time_ms:.0f}ms)" if self.response_time_ms else ""
            return f"🟢 Gemma 3:1B Ready{ms_str}"
        elif self.is_connected and not self.model_available:
            return f"🟡 Ollama Active, '{self.model_name}' not loaded"
        else:
            return "⚪ Ollama Offline (Deterministic Fallback Active)"


@dataclass
class AIGenerationResult:
    """Standardized output wrapper for AI generation calls."""
    success: bool
    text: str
    is_fallback: bool = False
    model_used: str = "none"
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class GemmaService:
    """Client for local Ollama HTTP API with robust fallbacks and error handling."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL") or DEFAULT_MODEL
        try:
            self.timeout = int(timeout or os.getenv("OLLAMA_TIMEOUT") or DEFAULT_TIMEOUT)
        except ValueError:
            self.timeout = DEFAULT_TIMEOUT

    def check_health(self) -> AIHealthStatus:
        """
        Check if Ollama is running and whether the specified model is installed.
        Guaranteed not to raise an exception or hang the application.
        """
        tags_url = f"{self.base_url}/api/tags"
        start_time = time.time()

        try:
            response = requests.get(tags_url, timeout=DEFAULT_HEALTH_TIMEOUT)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return AIHealthStatus(
                    is_connected=False,
                    model_available=False,
                    model_name=self.model_name,
                    base_url=self.base_url,
                    error_message=f"Ollama returned HTTP status {response.status_code}"
                )

            data = response.json()
            models_info = data.get("models", [])
            model_names = [m.get("name", "") for m in models_info]

            # Match model name exactly or prefix (e.g. 'gemma3:1b' matches 'gemma3:1b' or 'gemma3:1b-instruct')
            target_clean = self.model_name.lower().split(":")[0]
            model_found = any(
                m.lower() == self.model_name.lower() or
                m.lower().startswith(f"{target_clean}:") or
                m.lower() == target_clean
                for m in model_names
            )

            return AIHealthStatus(
                is_connected=True,
                model_available=model_found,
                model_name=self.model_name,
                base_url=self.base_url,
                available_models=model_names,
                response_time_ms=elapsed_ms,
                error_message=None if model_found else f"Model '{self.model_name}' is not in Ollama. Found: {model_names}"
            )

        except requests.exceptions.ConnectionError:
            return AIHealthStatus(
                is_connected=False,
                model_available=False,
                model_name=self.model_name,
                base_url=self.base_url,
                error_message="Cannot connect to Ollama. Ensure Ollama is running locally on Windows (e.g. `ollama run gemma3:1b`)."
            )
        except requests.exceptions.Timeout:
            return AIHealthStatus(
                is_connected=False,
                model_available=False,
                model_name=self.model_name,
                base_url=self.base_url,
                error_message=f"Health check timed out after {DEFAULT_HEALTH_TIMEOUT}s."
            )
        except Exception as e:
            return AIHealthStatus(
                is_connected=False,
                model_available=False,
                model_name=self.model_name,
                base_url=self.base_url,
                error_message=f"Unexpected health check error: {str(e)}"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> AIGenerationResult:
        """
        Send a generation request to the local Gemma model via Ollama.
        Catches timeouts, connection errors, and invalid responses gracefully.
        """
        gen_url = f"{self.base_url}/api/generate"
        options: Dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.time()
        try:
            response = requests.post(gen_url, json=payload, timeout=self.timeout)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return AIGenerationResult(
                    success=False,
                    text="",
                    is_fallback=True,
                    error=f"Ollama returned HTTP error {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            generated_text = (data.get("response") or "").strip()

            return AIGenerationResult(
                success=True,
                text=generated_text,
                is_fallback=False,
                model_used=self.model_name,
                response_time_ms=elapsed_ms,
                raw_response=data
            )

        except requests.exceptions.ConnectionError:
            return AIGenerationResult(
                success=False,
                text="",
                is_fallback=True,
                error="Local Ollama is offline or unreachable. Using deterministic fallback."
            )
        except requests.exceptions.Timeout:
            return AIGenerationResult(
                success=False,
                text="",
                is_fallback=True,
                error=f"Local Gemma 3:1B request timed out after {self.timeout}s. Using fallback."
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                text="",
                is_fallback=True,
                error=f"AI generation encountered an error: {str(e)}"
            )

    # -------------------------------------------------------------
    # Specialized Connected Features with Guaranteed Safe Fallbacks
    # -------------------------------------------------------------

    def explain_skill_evidence(
        self,
        resume_text: str,
        skill_name: str
    ) -> Dict[str, Any]:
        """
        Explain the context and evidence behind a verified matched skill.
        If Gemma is reachable, extracts the exact sentence/project context.
        If offline, extracts lines deterministically via keyword matching.
        """
        # 1. Deterministic line extraction (Ground Truth Baseline)
        deterministic_lines = self._extract_deterministic_evidence(resume_text, skill_name)

        # 2. Check if model is available
        health = self.check_health()
        if not health.is_connected or not health.model_available:
            return {
                "skill": skill_name,
                "evidence_text": deterministic_lines,
                "ai_summary": None,
                "is_ai_generated": False,
                "status_note": "Extracted via deterministic pattern matching (Ollama offline)."
            }

        # 3. Prompt Gemma 3:1B with strict grounding guardrails
        prompt = (
            f"You are an objective technical recruiter analyzing a resume.\n"
            f"Skill to locate: '{skill_name}'\n\n"
            f"Resume Text:\n\"\"\"\n{resume_text[:2500]}\n\"\"\"\n\n"
            f"Task: In 1 or 2 concise sentences, summarize the exact projects, responsibilities, or bullet points "
            f"in this resume that demonstrate experience with '{skill_name}'. "
            f"RULES:\n"
            f"- Strictly quote or paraphrase only what is explicitly written in the resume.\n"
            f"- Do NOT fabricate, assume, or invent any years of experience, tools, or achievements.\n"
            f"- If the skill is only listed as a keyword with no project details, state: 'Listed in technical skills without specific project elaboration.'\n"
            f"Summary:"
        )

        result = self.generate(prompt=prompt, temperature=0.1, max_tokens=150)
        if result.success and result.text:
            return {
                "skill": skill_name,
                "evidence_text": deterministic_lines,
                "ai_summary": result.text,
                "is_ai_generated": True,
                "status_note": f"Context summarized by local Gemma 3:1B ({result.response_time_ms:.0f}ms)."
            }
        else:
            return {
                "skill": skill_name,
                "evidence_text": deterministic_lines,
                "ai_summary": None,
                "is_ai_generated": False,
                "status_note": f"Fallback used: {result.error}"
            }

    def _extract_deterministic_evidence(self, resume_text: str, skill_name: str) -> str:
        """Deterministically extract resume lines containing the skill term."""
        if not resume_text:
            return "No resume text provided."

        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        matched_lines = []
        pattern = re.compile(rf"\b{re.escape(skill_name)}\b", re.IGNORECASE)

        for line in lines:
            if pattern.search(line):
                matched_lines.append(f"• {line}")

        if matched_lines:
            return "\n".join(matched_lines[:4])
        return f"Verified via keyword index for '{skill_name}'."

    def extract_job_insights(
        self,
        job_description: str,
        target_role: str,
        detected_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a job description to extract role emphasis, soft skills, or domain focus.
        Strictly distinguishes verified catalog skills from AI observations.
        """
        if not job_description or not job_description.strip():
            return {
                "has_jd": False,
                "insights": "No Job Description provided.",
                "is_ai_generated": False
            }

        health = self.check_health()
        if not health.is_connected or not health.model_available:
            return {
                "has_jd": True,
                "insights": (
                    f"Job Description detected ({len(job_description.split())} words). "
                    f"Deterministic matching identified requirements: {', '.join(detected_skills) if detected_skills else 'No catalog skills detected'}."
                ),
                "is_ai_generated": False,
                "status_note": "Deterministic fallback (Ollama offline)."
            }

        prompt = (
            f"You are a technical hiring analyst. Review this job description for a {target_role} position.\n\n"
            f"Job Description:\n\"\"\"\n{job_description[:2500]}\n\"\"\"\n\n"
            f"Already verified technical skills: {', '.join(detected_skills)}\n\n"
            f"Task: Provide a concise 2-bullet summary:\n"
            f"1. Core Domain Focus (e.g. backend scale, cloud automation, data analytics)\n"
            f"2. Implicit Team & Collaboration Needs (e.g. cross-functional communication, Agile)\n"
            f"RULES:\n"
            f"- Strictly ground all points in the text above.\n"
            f"- Do NOT invent required qualifications or certifications not mentioned.\n"
            f"Bullets:"
        )

        result = self.generate(prompt=prompt, temperature=0.1, max_tokens=180)
        if result.success and result.text:
            return {
                "has_jd": True,
                "insights": result.text,
                "is_ai_generated": True,
                "status_note": f"Analyzed by local Gemma 3:1B ({result.response_time_ms:.0f}ms)."
            }
        else:
            return {
                "has_jd": True,
                "insights": f"Deterministic requirement detection: {', '.join(detected_skills)}",
                "is_ai_generated": False,
                "status_note": f"Fallback: {result.error}"
            }

    def generate_mentor_guidance(
        self,
        target_role: str,
        matched_skills: List[str],
        missing_skills: List[str],
        skill_level: str
    ) -> Dict[str, Any]:
        """
        Generate contextual mentor advice explaining how candidate's current skills
        accelerate learning their missing skills.
        """
        if not missing_skills:
            return {
                "guidance": "🎉 Excellent! You possess all primary technical skills required for this role.",
                "is_ai_generated": False
            }

        health = self.check_health()
        if not health.is_connected or not health.model_available:
            # Deterministic curated guidance
            top_missing = missing_skills[:3]
            fallback_text = (
                f"**Strategic Focus for {target_role} ({skill_level} Level):**\n\n"
                f"You already have verified foundation in **{', '.join(matched_skills[:4]) if matched_skills else 'programming basics'}**. "
                f"Your highest-priority milestone is to focus on **{', '.join(top_missing)}**. "
                f"Begin with the core concepts outlined in your roadmap steps and build the portfolio mini-projects to demonstrate mastery."
            )
            return {
                "guidance": fallback_text,
                "is_ai_generated": False,
                "status_note": "Curated blueprint guidance (Ollama offline)."
            }

        prompt = (
            f"You are an encouraging senior software engineering mentor.\n"
            f"Target Role: {target_role} ({skill_level} Level)\n"
            f"Candidate Verified Skills: {', '.join(matched_skills) if matched_skills else 'Foundational coding'}\n"
            f"Key Skills to Learn: {', '.join(missing_skills[:4])}\n\n"
            f"Task: Write 2 brief, actionable mentor paragraphs:\n"
            f"1. Explain how their existing skills help them learn the missing skills faster (e.g. transferrable concepts).\n"
            f"2. Suggest the best project-based strategy to bridge the gap without feeling overwhelmed.\n"
            f"Keep it realistic, practical, and under 150 words. Do NOT praise nonexistent skills."
        )

        result = self.generate(prompt=prompt, temperature=0.3, max_tokens=220)
        if result.success and result.text:
            return {
                "guidance": result.text,
                "is_ai_generated": True,
                "status_note": f"Personalized by local Gemma 3:1B ({result.response_time_ms:.0f}ms)."
            }
        else:
            top_missing = missing_skills[:3]
            return {
                "guidance": (
                    f"Focus first on mastering **{', '.join(top_missing)}** using your "
                    f"existing foundation in **{', '.join(matched_skills[:3]) if matched_skills else 'core fundamentals'}**."
                ),
                "is_ai_generated": False,
                "status_note": f"Fallback: {result.error}"
            }


# Singleton helper
_global_service: Optional[GemmaService] = None


def get_ai_service() -> GemmaService:
    """Retrieve shared GemmaService instance."""
    global _global_service
    if _global_service is None:
        _global_service = GemmaService()
    return _global_service

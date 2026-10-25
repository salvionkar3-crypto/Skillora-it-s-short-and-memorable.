"""Unit and integration tests for local Gemma 3:1B AI service and Ollama fallbacks."""

import pytest
from unittest.mock import patch, MagicMock
import requests

from ai.gemma_service import (
    GemmaService,
    AIHealthStatus,
    AIGenerationResult,
    get_ai_service,
    DEFAULT_OLLAMA_URL,
    DEFAULT_MODEL,
)


@pytest.fixture
def offline_service():
    """GemmaService pointed to a non-existent port to verify offline resilience."""
    return GemmaService(base_url="http://localhost:59999", timeout=2)


@pytest.fixture
def mock_service():
    """GemmaService with standard configurations for unit testing."""
    return GemmaService(base_url="http://localhost:11434", model_name="gemma3:1b", timeout=5)


def test_service_initialization():
    svc = GemmaService()
    assert svc.base_url == DEFAULT_OLLAMA_URL
    assert svc.model_name == DEFAULT_MODEL
    assert svc.timeout > 0

    custom = GemmaService(base_url="http://127.0.0.1:11434/", model_name="custom:1b", timeout=10)
    assert custom.base_url == "http://127.0.0.1:11434"
    assert custom.model_name == "custom:1b"
    assert custom.timeout == 10


def test_offline_health_check_resilience(offline_service):
    """Verify that an unreachable Ollama instance never raises an unhandled exception."""
    health = offline_service.check_health()
    assert health.is_connected is False
    assert health.model_available is False
    assert "Offline" in health.status_summary
    assert health.error_message is not None


def test_offline_generate_fallback(offline_service):
    """Verify that generation against an offline instance returns a fallback result gracefully."""
    res = offline_service.generate("Say hello")
    assert res.success is False
    assert res.is_fallback is True
    assert "offline or unreachable" in res.error.lower()


def test_mock_successful_health_check(mock_service):
    """Verify health check correctly identifies available models."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "models": [
            {"name": "gemma3:1b"},
            {"name": "llama3:latest"}
        ]
    }

    with patch("requests.get", return_value=fake_response):
        health = mock_service.check_health()
        assert health.is_connected is True
        assert health.model_available is True
        assert "gemma3:1b" in health.available_models
        assert "🟢 Gemma 3:1B Ready" in health.status_summary


def test_mock_model_missing_health_check(mock_service):
    """Verify health check alerts when Ollama is running but target model is missing."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "models": [{"name": "mistral:latest"}]
    }

    with patch("requests.get", return_value=fake_response):
        health = mock_service.check_health()
        assert health.is_connected is True
        assert health.model_available is False
        assert "not loaded" in health.status_summary


def test_mock_successful_generation(mock_service):
    """Verify generation parses Ollama response payload correctly."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "model": "gemma3:1b",
        "response": "Python is a versatile language.",
        "done": True
    }

    with patch("requests.post", return_value=fake_response):
        res = mock_service.generate("Explain Python")
        assert res.success is True
        assert res.text == "Python is a versatile language."
        assert res.is_fallback is False


def test_explain_skill_evidence_deterministic_fallback(offline_service):
    """Ensure evidence explanation provides ground-truth lines even when AI is offline."""
    sample_resume = (
        "SARAH CONNOR\n"
        "Experience:\n"
        "- Built backend microservices using Python and Docker.\n"
        "- Designed database schemas in PostgreSQL."
    )
    result = offline_service.explain_skill_evidence(sample_resume, "Python")

    assert result["skill"] == "Python"
    assert "Python" in result["evidence_text"]
    assert "Docker" in result["evidence_text"]
    assert result["is_ai_generated"] is False
    assert result["ai_summary"] is None
    assert "deterministic" in result["status_note"].lower()


def test_extract_job_insights_fallback(offline_service):
    """Ensure job description analysis falls back gracefully when AI is offline."""
    jd = "Seeking a Python developer with experience in Docker and Kubernetes."
    result = offline_service.extract_job_insights(jd, "Python Developer", ["Docker", "Kubernetes"])

    assert result["has_jd"] is True
    assert result["is_ai_generated"] is False
    assert "Deterministic" in result["insights"] or "Docker" in result["insights"]


def test_generate_mentor_guidance_fallback(offline_service):
    """Ensure mentor guidance provides curated advice when offline."""
    result = offline_service.generate_mentor_guidance(
        target_role="Python Developer",
        matched_skills=["Python", "SQL"],
        missing_skills=["FastAPI", "Docker"],
        skill_level="Beginner"
    )
    assert result["is_ai_generated"] is False
    assert "Python Developer" in result["guidance"]
    assert "FastAPI" in result["guidance"]


def test_live_local_ollama_if_running():
    """Live test that connects to local Ollama if active on http://localhost:11434."""
    live_service = GemmaService()
    health = live_service.check_health()
    if health.is_connected and health.model_available:
        res = live_service.generate("Respond with 'Skillora Ready' in two words.", temperature=0.1)
        assert res.success is True
        assert len(res.text) > 0
        assert res.response_time_ms is not None

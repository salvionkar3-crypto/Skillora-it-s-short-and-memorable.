"""Skillora AI — Reusable local AI service module interfacing Gemma 3:1B via Ollama."""

from .gemma_service import (
    GemmaService,
    AIHealthStatus,
    AIGenerationResult,
    get_ai_service,
)

__all__ = [
    "GemmaService",
    "AIHealthStatus",
    "AIGenerationResult",
    "get_ai_service",
]

"""STT provider registry — factory and discovery."""

from __future__ import annotations

from .base import ModelInfo, STTProvider
from .qwen import Qwen3STTProvider
from .vosk import VoskSTTProvider

_providers: dict[str, STTProvider] = {}


def get_stt_provider(provider_id: str) -> STTProvider:
    """Return (or create) the singleton STT provider for *provider_id*."""
    if provider_id not in _providers:
        if provider_id == "vosk":
            _providers[provider_id] = VoskSTTProvider()
        elif provider_id == "qwen3":
            _providers[provider_id] = Qwen3STTProvider()
        else:
            raise ValueError(f"Unknown STT provider: {provider_id}")
    return _providers[provider_id]


def list_stt_providers() -> list[dict]:
    """Return metadata for every known STT provider."""
    return [
        {"id": "vosk", "display_name": "Vosk", "active": "vosk" in _providers},
        {"id": "qwen3", "display_name": "Qwen3-ASR", "active": "qwen3" in _providers},
    ]


__all__ = [
    "STTProvider",
    "ModelInfo",
    "VoskSTTProvider",
    "Qwen3STTProvider",
    "get_stt_provider",
    "list_stt_providers",
]

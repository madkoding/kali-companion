"""STTProvider — the interface every STT backend implements.

Kali talks to STT exclusively through this Protocol, so the rest of the
codebase is agnostic to whether transcription happens via Vosk (offline
Kaldi models) or Qwen3-ASR (HuggingFace transformers).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ModelInfo:
    """Metadata for an STT model available to a provider."""

    id: str
    display_name: str
    estimated_vram_mb: int
    available: bool = False
    loaded: bool = False
    device: str | None = None
    supported_languages: list[str] = field(default_factory=list)


@runtime_checkable
class STTProvider(Protocol):
    """Transcribe speech from raw PCM audio chunks.

    Providers manage their own model lifecycle (load / unload) and expose
    a streaming-friendly accept/finish interface that mirrors the Vosk
    KaldiRecognizer contract so the Connection handler stays simple.
    """

    provider_name: str

    # ── model management ──────────────────────────────────────

    def list_models(self) -> list[ModelInfo]:
        """Return every model this provider knows about."""
        ...

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        """Load *model_id* onto *device* (blocking, call in executor)."""
        ...

    def unload_model(self) -> None:
        """Release the currently loaded model from memory / VRAM."""
        ...

    # ── state ─────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """True when a model is loaded and ready to transcribe."""
        ...

    @property
    def device(self) -> str | None:
        """Device the loaded model lives on (e.g. 'cuda:0', 'cpu')."""
        ...

    @property
    def loaded_model(self) -> str | None:
        """Model id currently loaded, or None."""
        ...

    # ── transcription session ─────────────────────────────────

    def start_session(self, language: str) -> None:
        """Begin a new recognition session for *language*."""
        ...

    def accept(self, chunk: bytes) -> dict | None:
        """Feed a raw 16-bit PCM chunk.

        Returns a dict with ``"partial"`` or ``"text"`` when a result is
        available, or ``None`` when more audio is needed.
        """
        ...

    def finish(self) -> dict:
        """End the session and return the final ``{"text": "..."}`` dict."""
        ...

    @property
    def session_active(self) -> bool:
        """True while a recognition session is in progress."""
        ...

    # ── streaming mode ───────────────────────────────────────

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider can emit partial results."""
        ...

    def set_streaming(self, enabled: bool) -> None:
        """Toggle streaming (partial results) on or off."""
        ...

"""TTSProvider — the interface every TTS backend implements.

Kali talks to TTS exclusively through this Protocol, so the rest of the
codebase is agnostic to whether synthesis happens in-process (Piper) or
via an external HTTP / C++ subprocess service (Qwen3-TTS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class StartupError(Exception):
    """Raised when a required component is missing or fails to start."""


@dataclass
class TTSModelVoice:
    """A selectable voice within a TTS model."""

    id: str
    name: str
    gender: str | None = None
    source: str = "config"


@dataclass
class TTSModelInfo:
    """Metadata for a TTS model available to a provider."""

    id: str
    display_name: str
    estimated_vram_mb: int
    available: bool = False
    loaded: bool = False
    device: str | None = None
    supported_languages: list[str] = field(default_factory=list)
    voices: list[TTSModelVoice] = field(default_factory=list)
    variant: str | None = None


@runtime_checkable
class TTSProvider(Protocol):
    """Synthesize text into audio bytes (WAV) plus metadata.

    Providers manage their own model lifecycle (load / unload) and expose
    state so the UI and the pipeline can tell whether synthesis is ready.
    """

    provider_name: str

    async def synthesize(
        self,
        text: str,
        voice: str,
        mode: str = "normal",
        language: str = "auto",
    ) -> "TTSResult":
        ...

    async def list_voices(self) -> list[dict]:
        ...

    def list_models(self) -> list[TTSModelInfo]:
        ...

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        ...

    def unload_model(self) -> None:
        ...

    @property
    def is_loaded(self) -> bool:
        ...

    @property
    def device(self) -> str | None:
        ...

    @property
    def loaded_model(self) -> str | None:
        ...

    @property
    def is_available(self) -> bool:
        ...

    @property
    def last_error(self) -> str | None:
        ...


class TTSResult:
    """Output of a single synthesis call."""

    __slots__ = ("audio", "sample_rate", "duration", "mode", "segment")

    def __init__(
        self,
        audio: bytes,
        sample_rate: int,
        duration: float,
        mode: str = "normal",
        segment: int = 0,
    ) -> None:
        self.audio = audio
        self.sample_rate = sample_rate
        self.duration = duration
        self.mode = mode
        self.segment = segment
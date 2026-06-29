"""VoskSTTProvider — adapts the existing Vosk StreamingSTT to the STTProvider Protocol.

Vosk models are lightweight (~40 MB), CPU-only, and support native
streaming. This provider wraps the existing ``StreamingSTT`` and
``STTManager`` classes so the Connection handler can treat Vosk and
Qwen3 identically.
"""

from __future__ import annotations

import logging
import os

from kali_core.ear.manager import STTManager, model_for_language
from kali_core.ear.vosk_engine import DEFAULT_MODEL_DIR, get_model
from kali_core.lang_map import normalize

from .base import ModelInfo

logger = logging.getLogger("kali_core.ear.vosk_provider")

VOSK_LANG_MAP: dict[str, str] = {
    "es": "vosk-model-small-es-0.42",
    "en": "vosk-model-small-en-us-0.15",
}


def _discover_vosk_models() -> list[str]:
    """Scan the models directory for Vosk model folders."""
    found: list[str] = []
    if not os.path.isdir(DEFAULT_MODEL_DIR):
        return found
    for entry in os.listdir(DEFAULT_MODEL_DIR):
        path = os.path.join(DEFAULT_MODEL_DIR, entry)
        if not os.path.isdir(path):
            continue
        am_path = os.path.join(path, "am", "final.mdl")
        if os.path.exists(am_path):
            found.append(entry)
            continue
        for sub in os.listdir(path):
            sub_path = os.path.join(path, sub)
            if os.path.isdir(sub_path) and os.path.exists(
                os.path.join(sub_path, "am", "final.mdl")
            ):
                found.append(entry)
                break
    return found


def _guess_language(model_name: str) -> list[str]:
    """Heuristic: extract language codes from a Vosk model name."""
    name_lower = model_name.lower()
    langs: list[str] = []
    for code in ("es", "en", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"):
        if code in name_lower:
            langs.append(code)
    return langs or ["en"]


class VoskSTTProvider:
    """Vosk-backed STT provider — wraps the existing StreamingSTT pipeline."""

    provider_name = "vosk"

    def __init__(self) -> None:
        self._manager: STTManager | None = None
        self._loaded_model_id: str | None = None
        self._session_active = False
        self._streaming = True
        self._models_dir = ""

    # ── model management ──────────────────────────────────────

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for name in _discover_vosk_models():
            models.append(
                ModelInfo(
                    id=name,
                    display_name=name,
                    estimated_vram_mb=40,
                    available=True,
                    loaded=(name == self._loaded_model_id),
                    device="cpu" if name == self._loaded_model_id else None,
                    supported_languages=_guess_language(name),
                )
            )
        return models

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        _ = get_model(model_id)
        self._loaded_model_id = model_id
        logger.info("Vosk model loaded: %s", model_id)

    def unload_model(self) -> None:
        self._loaded_model_id = None

    # ── state ─────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._loaded_model_id is not None

    @property
    def device(self) -> str | None:
        return "cpu" if self._loaded_model_id else None

    @property
    def loaded_model(self) -> str | None:
        return self._loaded_model_id

    # ── transcription session ─────────────────────────────────

    def start_session(self, language: str) -> None:
        lang = normalize(language)
        model_name = model_for_language(lang)
        self._manager = STTManager(lang)
        self._manager.model_name = model_name
        self._manager.start_session()
        self._session_active = True

    def accept(self, chunk: bytes) -> dict | None:
        if self._manager is None:
            return None
        stt = self._manager.current()
        if stt is None or not stt.active:
            return None
        return stt.accept(chunk)

    def finish(self) -> dict:
        if self._manager is None:
            self._session_active = False
            return {"text": ""}
        stt = self._manager.current()
        if stt is None:
            self._session_active = False
            return {"text": ""}
        result = stt.finish()
        self._manager.end_session()
        self._session_active = False
        return result

    @property
    def session_active(self) -> bool:
        return self._session_active

    # ── streaming mode ───────────────────────────────────────

    @property
    def supports_streaming(self) -> bool:
        return True

    def set_streaming(self, enabled: bool) -> None:
        pass

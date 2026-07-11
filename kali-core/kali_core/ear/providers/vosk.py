"""VoskSTTProvider — adapts the existing Vosk StreamingSTT to the STTProvider Protocol.

Vosk models are lightweight (~40 MB), CPU-only, and support native
streaming. This provider wraps the existing ``StreamingSTT`` and
``STTManager`` classes so the Connection handler can treat Vosk and
Qwen3 identically.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kali_core.ear.manager import STTManager, model_for_language
from kali_core.ear.vosk_engine import DEFAULT_MODEL_DIR, get_model
from kali_core.lang_map import normalize

from .base import ModelInfo

logger = logging.getLogger("kali_core.ear.vosk_provider")

_INTERNAL_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def _discover_vosk_models() -> list[str]:
    """Scan the models directory for Vosk model folders."""
    found: set[str] = set()
    
    dirs_to_scan = [Path(DEFAULT_MODEL_DIR)]
    if _INTERNAL_MODELS_DIR.exists():
        dirs_to_scan.append(_INTERNAL_MODELS_DIR)

    for base_dir in dirs_to_scan:
        if not base_dir.is_dir():
            continue
        for entry in base_dir.iterdir():
            if not entry.is_dir():
                continue
            am_path = entry / "am" / "final.mdl"
            if am_path.exists():
                found.add(entry.name)
                continue
            # Some models are nested
            for sub in entry.iterdir():
                if sub.is_dir() and (sub / "am" / "final.mdl").exists():
                    found.add(entry.name)
                    break
    return sorted(list(found))


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

    def delete_model(self, model_id: str) -> None:
        """Unload and delete model files from disk."""
        if self._loaded_model_id == model_id:
            self.unload_model()
        
        import shutil
        for base in (Path(DEFAULT_MODEL_DIR), _INTERNAL_MODELS_DIR):
            path = base / model_id
            if path.is_dir():
                shutil.rmtree(path)
                logger.info("Vosk model deleted: %s from %s", model_id, path)

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

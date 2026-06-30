"""Model catalog — downloadable models for Vosk STT, Piper TTS, and Qwen3-TTS.

Provides a unified interface for the frontend to discover, list, and trigger
downloads of models. Each catalog entry includes:
  - id: unique identifier
  - provider: "vosk" | "piper" | "qwen3"
  - display_name: human-readable name
  - language: English name of the language (e.g. "Spanish")
  - language_code: ISO code (e.g. "es", "en_US")
  - size_mb: approximate download size in MB
  - quality: "small" | "medium" | "big" (Vosk) / "low" | "medium" | "high" (Piper)
  - url: download URL (or URL builder for Piper)
  - downloaded: whether the model files exist on disk

Piper voices are loaded from a static snapshot of voices.json (data/piper_voices.json)
that can be updated by replacing the file.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("kali_core.model_catalog")

_BASE_DIR = Path(__file__).resolve().parent
_PIPER_VOICES_JSON = _BASE_DIR / "data" / "piper_voices.json"
_PIPER_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


@dataclass
class CatalogEntry:
    id: str
    provider: str
    display_name: str
    language: str
    language_code: str
    size_mb: int
    quality: str
    downloaded: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "language": self.language,
            "language_code": self.language_code,
            "size_mb": self.size_mb,
            "quality": self.quality,
            "downloaded": self.downloaded,
        }


# ── Vosk STT catalog ──────────────────────────────────────────────────────
# Source: https://alphacephei.com/vosk/models
# All models listed on the page, tagged by language.

VOSK_MODELS: list[dict] = [
    # Spanish
    {"id": "vosk-model-small-es-0.42", "language": "Spanish", "language_code": "es", "size_mb": 39, "quality": "small"},
    {"id": "vosk-model-es-0.42", "language": "Spanish", "language_code": "es", "size_mb": 1400, "quality": "big"},
    # English US
    {"id": "vosk-model-small-en-us-0.15", "language": "English", "language_code": "en_US", "size_mb": 40, "quality": "small"},
    {"id": "vosk-model-en-us-0.22", "language": "English", "language_code": "en_US", "size_mb": 1800, "quality": "big"},
    {"id": "vosk-model-en-us-0.22-lgraph", "language": "English", "language_code": "en_US", "size_mb": 128, "quality": "medium"},
    {"id": "vosk-model-en-us-0.42-gigaspeech", "language": "English", "language_code": "en_US", "size_mb": 2300, "quality": "big"},
    {"id": "vosk-model-en-us-daanzu-20200905", "language": "English", "language_code": "en_US", "size_mb": 1000, "quality": "big"},
    {"id": "vosk-model-en-us-daanzu-20200905-lgraph", "language": "English", "language_code": "en_US", "size_mb": 129, "quality": "medium"},
    {"id": "vosk-model-small-en-us-zamia-0.5", "language": "English", "language_code": "en_US", "size_mb": 49, "quality": "small"},
    # Indian English
    {"id": "vosk-model-en-in-0.5", "language": "Indian English", "language_code": "en_IN", "size_mb": 1000, "quality": "big"},
    {"id": "vosk-model-small-en-in-0.4", "language": "Indian English", "language_code": "en_IN", "size_mb": 36, "quality": "small"},
    # Chinese
    {"id": "vosk-model-small-cn-0.22", "language": "Chinese", "language_code": "zh", "size_mb": 42, "quality": "small"},
    {"id": "vosk-model-cn-0.22", "language": "Chinese", "language_code": "zh", "size_mb": 1300, "quality": "big"},
    {"id": "vosk-model-cn-kaldi-multicn-0.15", "language": "Chinese", "language_code": "zh", "size_mb": 1500, "quality": "big"},
    # Russian
    {"id": "vosk-model-ru-0.42", "language": "Russian", "language_code": "ru", "size_mb": 1800, "quality": "big"},
    {"id": "vosk-model-small-ru-0.22", "language": "Russian", "language_code": "ru", "size_mb": 45, "quality": "small"},
    {"id": "vosk-model-ru-0.22", "language": "Russian", "language_code": "ru", "size_mb": 1500, "quality": "big"},
    {"id": "vosk-model-ru-0.10", "language": "Russian", "language_code": "ru", "size_mb": 2500, "quality": "big"},
    # French
    {"id": "vosk-model-small-fr-0.22", "language": "French", "language_code": "fr", "size_mb": 41, "quality": "small"},
    {"id": "vosk-model-fr-0.22", "language": "French", "language_code": "fr", "size_mb": 1400, "quality": "big"},
    {"id": "vosk-model-small-fr-pguyot-0.3", "language": "French", "language_code": "fr", "size_mb": 39, "quality": "small"},
    {"id": "vosk-model-fr-0.6-linto-2.2.0", "language": "French", "language_code": "fr", "size_mb": 1500, "quality": "big"},
    # German
    {"id": "vosk-model-de-0.21", "language": "German", "language_code": "de", "size_mb": 1900, "quality": "big"},
    {"id": "vosk-model-de-tuda-0.6-900k", "language": "German", "language_code": "de", "size_mb": 4400, "quality": "big"},
    {"id": "vosk-model-small-de-zamia-0.3", "language": "German", "language_code": "de", "size_mb": 49, "quality": "small"},
    {"id": "vosk-model-small-de-0.15", "language": "German", "language_code": "de", "size_mb": 45, "quality": "small"},
    # Portuguese
    {"id": "vosk-model-small-pt-0.3", "language": "Portuguese", "language_code": "pt", "size_mb": 31, "quality": "small"},
    {"id": "vosk-model-pt-fb-v0.1.1-20220516_2113", "language": "Portuguese", "language_code": "pt", "size_mb": 1600, "quality": "big"},
    # Italian
    {"id": "vosk-model-small-it-0.22", "language": "Italian", "language_code": "it", "size_mb": 48, "quality": "small"},
    {"id": "vosk-model-it-0.22", "language": "Italian", "language_code": "it", "size_mb": 1200, "quality": "big"},
    # Dutch
    {"id": "vosk-model-small-nl-0.22", "language": "Dutch", "language_code": "nl", "size_mb": 39, "quality": "small"},
    {"id": "vosk-model-nl-spraakherkenning-0.6", "language": "Dutch", "language_code": "nl", "size_mb": 860, "quality": "big"},
    {"id": "vosk-model-nl-spraakherkenning-0.6-lgraph", "language": "Dutch", "language_code": "nl", "size_mb": 100, "quality": "medium"},
    # Catalan
    {"id": "vosk-model-small-ca-0.4", "language": "Catalan", "language_code": "ca", "size_mb": 42, "quality": "small"},
    # Arabic
    {"id": "vosk-model-ar-mgb2-0.4", "language": "Arabic", "language_code": "ar", "size_mb": 318, "quality": "medium"},
    {"id": "vosk-model-ar-0.22-linto-1.1.0", "language": "Arabic", "language_code": "ar", "size_mb": 1300, "quality": "big"},
    # Arabic Tunisian
    {"id": "vosk-model-small-ar-tn-0.1-linto", "language": "Arabic (Tunisian)", "language_code": "ar_TN", "size_mb": 158, "quality": "small"},
    {"id": "vosk-model-ar-tn-0.1-linto", "language": "Arabic (Tunisian)", "language_code": "ar_TN", "size_mb": 517, "quality": "medium"},
    # Farsi/Persian
    {"id": "vosk-model-fa-0.42", "language": "Persian", "language_code": "fa", "size_mb": 1600, "quality": "big"},
    {"id": "vosk-model-small-fa-0.42", "language": "Persian", "language_code": "fa", "size_mb": 53, "quality": "small"},
    {"id": "vosk-model-fa-0.5", "language": "Persian", "language_code": "fa", "size_mb": 1000, "quality": "big"},
    {"id": "vosk-model-small-fa-0.5", "language": "Persian", "language_code": "fa", "size_mb": 60, "quality": "small"},
    # Turkish
    {"id": "vosk-model-small-tr-0.3", "language": "Turkish", "language_code": "tr", "size_mb": 35, "quality": "small"},
    # Vietnamese
    {"id": "vosk-model-small-vn-0.4", "language": "Vietnamese", "language_code": "vi", "size_mb": 32, "quality": "small"},
    {"id": "vosk-model-vn-0.4", "language": "Vietnamese", "language_code": "vi", "size_mb": 78, "quality": "medium"},
    # Greek
    {"id": "vosk-model-el-gr-0.7", "language": "Greek", "language_code": "el", "size_mb": 1100, "quality": "big"},
    # Japanese
    {"id": "vosk-model-small-ja-0.22", "language": "Japanese", "language_code": "ja", "size_mb": 48, "quality": "small"},
    {"id": "vosk-model-ja-0.22", "language": "Japanese", "language_code": "ja", "size_mb": 1000, "quality": "big"},
    # Korean
    {"id": "vosk-model-small-ko-0.22", "language": "Korean", "language_code": "ko", "size_mb": 82, "quality": "small"},
    # Polish
    {"id": "vosk-model-small-pl-0.22", "language": "Polish", "language_code": "pl", "size_mb": 50, "quality": "small"},
    # Czech
    {"id": "vosk-model-small-cs-0.4-rhasspy", "language": "Czech", "language_code": "cs", "size_mb": 44, "quality": "small"},
    # Esperanto
    {"id": "vosk-model-small-eo-0.42", "language": "Esperanto", "language_code": "eo", "size_mb": 42, "quality": "small"},
    # Hindi
    {"id": "vosk-model-small-hi-0.22", "language": "Hindi", "language_code": "hi", "size_mb": 42, "quality": "small"},
    {"id": "vosk-model-hi-0.22", "language": "Hindi", "language_code": "hi", "size_mb": 1500, "quality": "big"},
    # Ukrainian
    {"id": "vosk-model-small-uk-v3-nano", "language": "Ukrainian", "language_code": "uk", "size_mb": 73, "quality": "small"},
    {"id": "vosk-model-small-uk-v3-small", "language": "Ukrainian", "language_code": "uk", "size_mb": 133, "quality": "small"},
    {"id": "vosk-model-uk-v3", "language": "Ukrainian", "language_code": "uk", "size_mb": 343, "quality": "medium"},
    {"id": "vosk-model-uk-v3-lgraph", "language": "Ukrainian", "language_code": "uk", "size_mb": 325, "quality": "medium"},
    # Kazakh
    {"id": "vosk-model-small-kz-0.42", "language": "Kazakh", "language_code": "kk", "size_mb": 58, "quality": "small"},
    {"id": "vosk-model-kz-0.42", "language": "Kazakh", "language_code": "kk", "size_mb": 1300, "quality": "big"},
    # Swedish
    {"id": "vosk-model-small-sv-rhasspy-0.15", "language": "Swedish", "language_code": "sv", "size_mb": 289, "quality": "small"},
    # Breton
    {"id": "vosk-model-br-0.8", "language": "Breton", "language_code": "br", "size_mb": 70, "quality": "small"},
    # Gujarati
    {"id": "vosk-model-gu-0.42", "language": "Gujarati", "language_code": "gu", "size_mb": 700, "quality": "big"},
    {"id": "vosk-model-small-gu-0.42", "language": "Gujarati", "language_code": "gu", "size_mb": 100, "quality": "small"},
    # Tajik
    {"id": "vosk-model-tg-0.22", "language": "Tajik", "language_code": "tg", "size_mb": 327, "quality": "medium"},
    {"id": "vosk-model-small-tg-0.22", "language": "Tajik", "language_code": "tg", "size_mb": 50, "quality": "small"},
    # Telugu
    {"id": "vosk-model-small-te-0.42", "language": "Telugu", "language_code": "te", "size_mb": 58, "quality": "small"},
    # Kyrgyz
    {"id": "vosk-model-small-ky-0.42", "language": "Kyrgyz", "language_code": "ky", "size_mb": 49, "quality": "small"},
    {"id": "vosk-model-ky-0.42", "language": "Kyrgyz", "language_code": "ky", "size_mb": 1100, "quality": "big"},
    # Georgian
    {"id": "vosk-model-small-ka-0.42", "language": "Georgian", "language_code": "ka", "size_mb": 45, "quality": "small"},
    {"id": "vosk-model-ka-0.42", "language": "Georgian", "language_code": "ka", "size_mb": 700, "quality": "big"},
    # Filipino
    {"id": "vosk-model-tl-ph-generic-0.6", "language": "Filipino", "language_code": "fil", "size_mb": 320, "quality": "medium"},
]

VOSK_URL_BASE = "https://alphacephei.com/vosk/models"


def _vosk_url(model_id: str) -> str:
    return f"{VOSK_URL_BASE}/{model_id}.zip"


def _vosk_is_downloaded(model_id: str, stt_models_dir: str | Path) -> bool:
    d = Path(stt_models_dir).expanduser().resolve() / model_id
    if d.exists() and (d / "am" / "final.mdl").exists():
        return True
    
    # Fallback to source tree models
    fallback = Path(__file__).resolve().parent / "ear" / "models" / model_id
    if fallback.exists() and (fallback / "am" / "final.mdl").exists():
        return True
        
    return False


def _vosk_catalog(stt_models_dir: str | Path) -> list[CatalogEntry]:
    entries = []
    for m in VOSK_MODELS:
        entries.append(CatalogEntry(
            id=m["id"],
            provider="vosk",
            display_name=m["id"],
            language=m["language"],
            language_code=m["language_code"],
            size_mb=m["size_mb"],
            quality=m["quality"],
            downloaded=_vosk_is_downloaded(m["id"], stt_models_dir),
        ))
    return entries


# ── Piper TTS catalog ──────────────────────────────────────────────────────

_piper_voices_cache: dict | None = None


def _load_piper_voices() -> dict:
    global _piper_voices_cache
    if _piper_voices_cache is not None:
        return _piper_voices_cache
    try:
        with open(_PIPER_VOICES_JSON, "r", encoding="utf-8") as fh:
            _piper_voices_cache = json.load(fh)
        logger.info("Loaded Piper voices catalog: %d voices", len(_piper_voices_cache))
    except Exception as exc:
        logger.warning("Failed to load piper_voices.json: %s", exc)
        _piper_voices_cache = {}
    return _piper_voices_cache


def get_piper_voices() -> dict:
    """Return the loaded Piper voices catalog."""
    return _load_piper_voices()


def _piper_is_downloaded(voice_key: str, voices_dir: str | Path) -> bool:
    d = Path(voices_dir).expanduser().resolve()
    onnx = d / f"{voice_key}.onnx"
    js = d / f"{voice_key}.onnx.json"
    return onnx.exists() and js.exists()


def _piper_catalog(voices_dir: str | Path) -> list[CatalogEntry]:
    voices = _load_piper_voices()
    entries = []
    for key, info in sorted(voices.items()):
        lang = info.get("language", {})
        files = info.get("files", {})
        onnx_file = next((f for f in files if f.endswith(".onnx")), None)
        if not onnx_file:
            continue
        size_bytes = files[onnx_file].get("size_bytes", 0)
        size_mb = round(size_bytes / (1024 * 1024))
        entries.append(CatalogEntry(
            id=key,
            provider="piper",
            display_name=key,
            language=lang.get("name_english", "Unknown"),
            language_code=lang.get("code", ""),
            size_mb=size_mb,
            quality=info.get("quality", ""),
            downloaded=_piper_is_downloaded(key, voices_dir),
        ))
    return entries


def piper_voice_urls(voice_key: str) -> list[str]:
    """Return the download URLs for a Piper voice (.onnx + .onnx.json)."""
    voices = _load_piper_voices()
    info = voices.get(voice_key)
    if not info:
        return []
    urls = []
    for fpath in info.get("files", {}):
        if fpath.endswith(".onnx") or fpath.endswith(".onnx.json"):
            urls.append(f"{_PIPER_HF_BASE}/{fpath}")
    return urls


def piper_voice_filenames(voice_key: str) -> list[str]:
    """Return the local filenames for a Piper voice (.onnx + .onnx.json)."""
    voices = _load_piper_voices()
    info = voices.get(voice_key)
    if not info:
        return []
    names = []
    for fpath in info.get("files", {}):
        if fpath.endswith(".onnx") or fpath.endswith(".onnx.json"):
            names.append(Path(fpath).name)
    return names


# ── Qwen3-TTS catalog ──────────────────────────────────────────────────────

QWEN3_MODELS = [
    {
        "id": "qwen3-tts-0.6b-customvoice",
        "display_name": "Qwen3-TTS 0.6B CustomVoice",
        "filename": "qwen-talker-0.6b-customvoice-Q4_K_M.gguf",
        "size_mb": 605,
        "quality": "Q4_K_M",
    },
    {
        "id": "qwen3-tts-1.7b-voicedesign",
        "display_name": "Qwen3-TTS 1.7B VoiceDesign",
        "filename": "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf",
        "size_mb": 1200,
        "quality": "Q4_K_M",
    },
]

QWEN3_HF_BASE = "https://huggingface.co/Serveurperso/Qwen3-TTS-GGUF/resolve/main"


def _qwen3_is_downloaded(model_id: str, tts_models_dir: str | Path) -> bool:
    d = Path(tts_models_dir).expanduser().resolve()
    model = next((m for m in QWEN3_MODELS if m["id"] == model_id), None)
    if not model:
        return False
    # Check if the file exists in the directory. 
    # Also check if it's in the common models dir as a fallback.
    path = d / model["filename"]
    if path.exists():
        return True
    
    # Fallback: check ~/.local/share/kali/models
    fallback_dir = Path.home() / ".local" / "share" / "kali" / "models"
    if fallback_dir != d and (fallback_dir / model["filename"]).exists():
        return True
        
    return False


def _qwen3_catalog(tts_models_dir: str | Path) -> list[CatalogEntry]:
    entries = []
    for m in QWEN3_MODELS:
        entries.append(CatalogEntry(
            id=m["id"],
            provider="qwen3",
            display_name=m["display_name"],
            language="Multi",
            language_code="multi",
            size_mb=m["size_mb"],
            quality=m["quality"],
            downloaded=_qwen3_is_downloaded(m["id"], tts_models_dir),
        ))
    return entries


# ── Qwen3-ASR catalog ──────────────────────────────────────────────────────

QWEN3_ASR_MODELS = [
    {
        "id": "qwen3-asr-0.6b",
        "display_name": "Qwen3-ASR 0.6B",
        "hf_id": "Qwen/Qwen3-ASR-0.6B-hf",
        "size_mb": 1600,
    },
    {
        "id": "qwen3-asr-1.7b",
        "display_name": "Qwen3-ASR 1.7B",
        "hf_id": "Qwen/Qwen3-ASR-1.7B-hf",
        "size_mb": 3400,
    },
]


def _qwen3_asr_is_downloaded(model_id: str, stt_models_dir: str | Path) -> bool:
    model = next((m for m in QWEN3_ASR_MODELS if m["id"] == model_id), None)
    if not model:
        return False
    
    # Check physical existence of the repo folder in HF cache
    try:
        from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
        
        # Use provided dir or default HF cache
        cache_dir = Path(stt_models_dir).expanduser().resolve() if stt_models_dir else Path(HUGGINGFACE_HUB_CACHE)
        
        # Repository folder pattern in HF cache: hub/models--user--repo
        repo_id = model["hf_id"]
        folder_name = f"models--{repo_id.replace('/', '--')}"
        repo_path = cache_dir / folder_name
        
        # It's downloaded if the folder exists and has at least one snapshot with a config.json
        if repo_path.is_dir():
            snapshots_dir = repo_path / "snapshots"
            if snapshots_dir.is_dir():
                for snapshot in snapshots_dir.iterdir():
                    if (snapshot / "config.json").exists():
                        return True
        return False
    except Exception:
        return False


def _qwen3_asr_catalog(stt_models_dir: str | Path) -> list[CatalogEntry]:
    entries = []
    for m in QWEN3_ASR_MODELS:
        entries.append(CatalogEntry(
            id=m["id"],
            provider="qwen3-asr",
            display_name=m["display_name"],
            language="Multi",
            language_code="multi",
            size_mb=m["size_mb"],
            quality="HF",
            downloaded=_qwen3_asr_is_downloaded(m["id"], stt_models_dir),
        ))
    return entries


# ── Unified API ────────────────────────────────────────────────────────────

def get_catalog(
    provider: str,
    *,
    stt_models_dir: str | Path = "",
    voices_dir: str | Path = "",
    tts_models_dir: str | Path = "",
) -> list[CatalogEntry]:
    if provider == "vosk":
        return _vosk_catalog(stt_models_dir)
    if provider == "piper":
        return _piper_catalog(voices_dir)
    if provider == "qwen3":
        return _qwen3_catalog(tts_models_dir)
    if provider == "qwen3-asr":
        return _qwen3_asr_catalog(stt_models_dir)
    return []


def get_catalog_dict(provider: str, **kwargs) -> list[dict]:
    return [e.to_dict() for e in get_catalog(provider, **kwargs)]


def get_all_languages(provider: str) -> list[str]:
    """Return sorted unique language names for a provider."""
    if provider == "vosk":
        return sorted({m["language"] for m in VOSK_MODELS})
    if provider == "piper":
        voices = _load_piper_voices()
        return sorted({v.get("language", {}).get("name_english", "Unknown") for v in voices.values()})
    if provider == "qwen3" or provider == "qwen3-asr":
        return ["Multi"]
    return []


__all__ = [
    "CatalogEntry",
    "VOSK_MODELS",
    "QWEN3_MODELS",
    "VOSK_URL_BASE",
    "get_catalog",
    "get_catalog_dict",
    "get_all_languages",
    "get_piper_voices",
    "piper_voice_urls",
    "piper_voice_filenames",
]
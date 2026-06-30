"""PiperTTSProvider — in-process Piper TTS with model management.

Each .onnx file in voices_dir is a TTS model. A model's voices combine
internal .onnx speakers (when num_speakers > 1) and voice_configs/*.json
profiles that reference the model. Loading a model precaches the .onnx
in PiperEngine; unloading drops it. All CPU, no subprocess.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from kali_core.config import settings
from kali_core.voice.audio_utils import (
    get_wav_duration,
    numpy_to_wav_bytes,
    wav_bytes_to_numpy,
)
from kali_core.voice.effects import apply_chain
from kali_core.voice.engine import PiperEngine
from kali_core.voice.voice_config import VoiceConfigManager

from .base import TTSModelInfo, TTSModelVoice, TTSResult

logger = logging.getLogger("kali_core.voice.piper")


class PiperTTSProvider:
    """In-process Piper TTS with .onnx-model management."""

    _provider_name = "piper"

    def __init__(
        self,
        voices_dir: Path | None = None,
        voice_configs_dir: Path | None = None,
    ) -> None:
        self.voices_dir = voices_dir or settings.voices_dir
        self.voice_configs_dir = voice_configs_dir or settings.voice_configs_dir
        self._engine = PiperEngine(self.voices_dir)
        self._config_manager = VoiceConfigManager(self.voice_configs_dir)
        self._loaded_model_id: str | None = None

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def is_loaded(self) -> bool:
        return self._loaded_model_id is not None

    @property
    def device(self) -> str | None:
        return "cpu" if self._loaded_model_id else None

    @property
    def loaded_model(self) -> str | None:
        return self._loaded_model_id

    @property
    def is_available(self) -> bool:
        return True

    @property
    def last_error(self) -> str | None:
        return None

    def _read_onnx_json(self, onnx_stem: str) -> dict[str, Any]:
        path = self.voices_dir / f"{onnx_stem}.onnx.json"
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _group_voice_configs_by_model(self) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {}
        for voice in self._config_manager.list_voices(include_inactive=True):
            model = voice.get("model", "")
            groups.setdefault(model, []).append(voice)
        return groups

    def list_models(self) -> list[TTSModelInfo]:
        if not self.voices_dir.exists():
            return []
        configs_by_model = self._group_voice_configs_by_model()
        models: list[TTSModelInfo] = []
        for onnx_file in sorted(self.voices_dir.glob("*.onnx")):
            stem = onnx_file.stem
            meta = self._read_onnx_json(stem)
            num_speakers = meta.get("num_speakers", 1)
            speaker_map: dict = meta.get("speaker_id_map", {})
            lang_code = meta.get("language", {}).get("family") or meta.get("espeak", {}).get("voice", "")
            languages = [lang_code] if lang_code else []
            voices: list[TTSModelVoice] = []
            for spk_name in speaker_map:
                voices.append(TTSModelVoice(
                    id=f"{stem}::{spk_name}",
                    name=spk_name,
                    source="speaker",
                ))
            for vc in configs_by_model.get(stem, []):
                voices.append(TTSModelVoice(
                    id=vc["voice_id"],
                    name=vc.get("name", vc["voice_id"]),
                    source="config",
                ))
            models.append(TTSModelInfo(
                id=stem,
                display_name=stem,
                estimated_vram_mb=0,
                available=True,
                loaded=(stem == self._loaded_model_id),
                device="cpu" if stem == self._loaded_model_id else None,
                supported_languages=languages,
                voices=voices,
            ))
        return models

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        if self._loaded_model_id == model_id:
            return
        self._engine.load_voice(model_id)
        self._loaded_model_id = model_id
        logger.info("Piper model loaded: %s", model_id)

    def unload_model(self) -> None:
        if self._loaded_model_id:
            self._engine.unload_voice(self._loaded_model_id)
            self._loaded_model_id = None

    async def synthesize(self, text: str, voice: str, mode: str = "normal", language: str = "auto") -> TTSResult:
        config = self._config_manager.get_voice(voice)
        if config is None:
            raise ValueError(
                f"Voice config '{voice}' not found. "
                f"Available: {[v['voice_id'] for v in self._config_manager.list_voices()]}"
            )
        model = config["model"]
        params = self._config_manager.get_params(voice)
        active_mode = mode or config.get("default_mode", "normal")
        effects = self._config_manager.get_effects_for_mode(voice, active_mode)
        wav_bytes = await asyncio.to_thread(
            self._engine.synthesize,
            model,
            text,
            length_scale=params.get("length_scale", 1.0),
            noise_scale=params.get("noise_scale", 0.667),
            noise_w_scale=params.get("noise_w_scale", 0.8),
        )
        if effects:
            audio_np, sr = wav_bytes_to_numpy(wav_bytes)
            processed = await asyncio.to_thread(apply_chain, audio_np, sr, effects)
            wav_bytes = numpy_to_wav_bytes(processed, sr)
        duration = get_wav_duration(wav_bytes)
        return TTSResult(
            audio=wav_bytes,
            sample_rate=22050,
            duration=duration,
            mode=mode or config.get("default_mode", "normal"),
        )

    async def list_voices(self) -> list[dict]:
        return self._config_manager.list_voices()

    async def preview(self, voice_id: str, text: str, language: str = "en", mode: str = "normal") -> bytes:
        result = await self.synthesize(text, voice_id, mode=mode)
        return result.audio
"""HTTP TTS provider — forwards synthesis to an external TTS HTTP service.

Useful for users who already run lapis-tts or any service exposing a
compatible `/v1/text-to-speech/<voice>` endpoint. Configured via
`KALI_TTS_HTTP_URL`.
"""

from __future__ import annotations

import logging

import httpx

from kali_core.config import settings

from .base import TTSResult

logger = logging.getLogger("kali_core.voice.http")


class HTTPTTSProvider:
    """External TTS via HTTP (lapis-tts compatible)."""

    provider_name = "http"

    def __init__(self) -> None:
        self.url = settings.tts_http_url
        self._client = httpx.AsyncClient(timeout=30.0)

    async def synthesize(
        self,
        text: str,
        voice: str,
        mode: str = "normal",
        language: str = "auto",
    ) -> TTSResult:
        resp = await self._client.post(
            f"{self.url}/v1/text-to-speech/{voice}",
            json={"text": text, "output_format": "wav"},
        )
        resp.raise_for_status()
        return TTSResult(
            audio=resp.content,
            sample_rate=22050,
            duration=0.0,
            mode=mode,
        )

    async def list_voices(self) -> list[dict]:
        try:
            resp = await self._client.get(f"{self.url}/v1/voices")
            resp.raise_for_status()
            data = resp.json()
            return data.get("voices", data) if isinstance(data, dict) else data
        except Exception:
            logger.exception("list_voices failed")
            return []

    async def preview(self, voice_id: str, text: str, language: str = "en", mode: str = "normal") -> bytes:
        result = await self.synthesize(text, voice_id, mode=mode)
        return result.audio

    @property
    def is_loaded(self) -> bool:
        return True

    @property
    def device(self) -> str | None:
        return "cpu"

    @property
    def loaded_model(self) -> str | None:
        return "remote"

    @property
    def is_available(self) -> bool:
        return True

    @property
    def last_error(self) -> str | None:
        return None

    def list_models(self) -> list:
        from .base import TTSModelInfo
        return [TTSModelInfo(
            id="remote",
            display_name="Remote HTTP Service",
            estimated_vram_mb=0,
            available=True,
            loaded=True,
            device="cpu",
        )]

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        pass

    def unload_model(self) -> None:
        pass
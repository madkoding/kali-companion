"""Tests for the extended TTSProvider Protocol and model-management dataclasses."""

from dataclasses import asdict
from kali_core.voice.providers.base import (
    TTSModelInfo,
    TTSModelVoice,
    TTSProvider,
    StartupError,
)


def test_tts_model_info_defaults():
    m = TTSModelInfo(id="es_ES-glados-medium", display_name="GLaDOS ES", estimated_vram_mb=0)
    assert m.available is False
    assert m.loaded is False
    assert m.device is None
    assert m.supported_languages == []
    assert m.voices == []
    assert m.variant is None


def test_tts_model_voice_defaults():
    v = TTSModelVoice(id="glados-es", name="GLaDOS ES")
    assert v.gender is None
    assert v.source == "config"


def test_tts_model_info_with_voices_and_variant():
    v = TTSModelVoice(id="serena", name="Serena", gender="female", source="speaker")
    m = TTSModelInfo(
        id="qwen3-tts-0.6b-customvoice",
        display_name="Qwen3-TTS 0.6B CustomVoice",
        estimated_vram_mb=600,
        available=True,
        loaded=True,
        device="cpu",
        variant="customvoice",
        voices=[v],
    )
    d = asdict(m)
    assert d["voices"][0]["source"] == "speaker"
    assert d["variant"] == "customvoice"


def test_startup_error_is_exception():
    assert issubclass(StartupError, Exception)
    err = StartupError("missing binary")
    assert str(err) == "missing binary"


def test_tts_provider_protocol_is_runtime_checkable():
    class Dummy:
        provider_name = "dummy"
        async def synthesize(self, text, voice, mode="normal"): ...
        async def list_voices(self): ...
        def list_models(self): ...
        def load_model(self, model_id, device="cpu"): ...
        def unload_model(self): ...
        @property
        def is_loaded(self): ...
        @property
        def device(self): ...
        @property
        def loaded_model(self): ...
        @property
        def is_available(self): ...
        @property
        def last_error(self): ...
    assert isinstance(Dummy(), TTSProvider)
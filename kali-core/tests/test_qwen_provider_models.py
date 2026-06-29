"""Tests for QwenTTSProvider model management (subprocess respawn on switch)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from kali_core.voice.providers.qwen import QwenTTSProvider, QWEN_MODELS
from kali_core.voice.providers.base import TTSModelInfo


@pytest.fixture
def fake_models_dir(tmp_path):
    d = tmp_path / "qwen_models"
    d.mkdir()
    (d / "qwen-talker-0.6b-customvoice-Q4_K_M.gguf").write_bytes(b"fake 0.6b")
    (d / "qwen-talker-1.7b-voicedesign-Q4_K_M.gguf").write_bytes(b"fake 1.7b")
    (d / "qwen-tokenizer-12hz-Q4_K_M.gguf").write_bytes(b"fake codec")
    return d


def test_qwen_provider_name_is_always_qwen3():
    assert QwenTTSProvider._provider_name == "qwen3"


def test_qwen_models_catalog_has_two_variants():
    assert "qwen3-tts-0.6b-customvoice" in QWEN_MODELS
    assert "qwen3-tts-1.7b-voicedesign" in QWEN_MODELS
    assert QWEN_MODELS["qwen3-tts-0.6b-customvoice"]["variant"] == "customvoice"
    assert QWEN_MODELS["qwen3-tts-1.7b-voicedesign"]["variant"] == "voicedesign"


def test_qwen_list_models_reports_availability(fake_models_dir):
    with patch.object(QwenTTSProvider, "_validate_and_spawn"), \
         patch.object(QwenTTSProvider, "_wait_for_health"):
        provider = QwenTTSProvider(
            binary=Path("/fake/binary"),
            talker_models_dir=fake_models_dir,
            codec_model=fake_models_dir / "qwen-tokenizer-12hz-Q4_K_M.gguf",
            port=8870,
            backend="CPU",
        )
        provider._loaded_model_id = "qwen3-tts-0.6b-customvoice"
        provider._proc = MagicMock()
        provider._proc.poll.return_value = None
        provider._client = MagicMock()
        models = provider.list_models()
        by_id = {m.id: m for m in models}
        assert by_id["qwen3-tts-0.6b-customvoice"].available is True
        assert by_id["qwen3-tts-1.7b-voicedesign"].available is True
        assert by_id["qwen3-tts-0.6b-customvoice"].loaded is True
        assert by_id["qwen3-tts-1.7b-voicedesign"].loaded is False
        assert by_id["qwen3-tts-0.6b-customvoice"].variant == "customvoice"


def test_qwen_tts_variant_reflects_loaded_model(fake_models_dir):
    with patch.object(QwenTTSProvider, "_validate_and_spawn"), \
         patch.object(QwenTTSProvider, "_wait_for_health"):
        provider = QwenTTSProvider(
            binary=Path("/fake/binary"),
            talker_models_dir=fake_models_dir,
            codec_model=fake_models_dir / "qwen-tokenizer-12hz-Q4_K_M.gguf",
            port=8870,
            backend="CPU",
        )
        provider._voice_design = False
        provider._loaded_model_id = "qwen3-tts-0.6b-customvoice"
        assert provider.tts_variant == "customvoice"
        provider._voice_design = True
        provider._loaded_model_id = "qwen3-tts-1.7b-voicedesign"
        assert provider.tts_variant == "voicedesign"


def test_qwen_load_model_respawns_subprocess(fake_models_dir):
    with patch.object(QwenTTSProvider, "_validate_and_spawn") as mock_spawn, \
         patch.object(QwenTTSProvider, "_wait_for_health"):
        provider = QwenTTSProvider(
            binary=Path("/fake/binary"),
            talker_models_dir=fake_models_dir,
            codec_model=fake_models_dir / "qwen-tokenizer-12hz-Q4_K_M.gguf",
            port=8870,
            backend="CPU",
        )
        mock_spawn.reset_mock()
        provider._loaded_model_id = "qwen3-tts-0.6b-customvoice"
        provider._voice_design = False
        provider._proc = MagicMock()
        provider._proc.poll.return_value = None
        provider._client = MagicMock()
        provider.shutdown = MagicMock()
        provider.load_model("qwen3-tts-1.7b-voicedesign")
        provider.shutdown.assert_called_once()
        assert provider._voice_design is True
        assert provider._loaded_model_id == "qwen3-tts-1.7b-voicedesign"
        mock_spawn.assert_called_once()


def test_qwen_load_model_same_model_is_noop(fake_models_dir):
    with patch.object(QwenTTSProvider, "_validate_and_spawn"), \
         patch.object(QwenTTSProvider, "_wait_for_health"):
        provider = QwenTTSProvider(
            binary=Path("/fake/binary"),
            talker_models_dir=fake_models_dir,
            codec_model=fake_models_dir / "qwen-tokenizer-12hz-Q4_K_M.gguf",
            port=8870,
            backend="CPU",
        )
        provider._loaded_model_id = "qwen3-tts-0.6b-customvoice"
        provider._proc = MagicMock()
        provider._proc.poll.return_value = None
        provider._client = MagicMock()
        provider.shutdown = MagicMock()
        provider.load_model("qwen3-tts-0.6b-customvoice")
        provider.shutdown.assert_not_called()


def test_qwen_unload_model_kills_subprocess(fake_models_dir):
    with patch.object(QwenTTSProvider, "_validate_and_spawn"), \
         patch.object(QwenTTSProvider, "_wait_for_health"):
        provider = QwenTTSProvider(
            binary=Path("/fake/binary"),
            talker_models_dir=fake_models_dir,
            codec_model=fake_models_dir / "qwen-tokenizer-12hz-Q4_K_M.gguf",
            port=8870,
            backend="CPU",
        )
        provider._loaded_model_id = "qwen3-tts-0.6b-customvoice"
        provider._proc = MagicMock()
        provider._proc.poll.return_value = None
        provider._client = MagicMock()
        provider.shutdown = MagicMock()
        provider.unload_model()
        provider.shutdown.assert_called_once()
        assert provider.is_loaded is False
        assert provider.loaded_model is None
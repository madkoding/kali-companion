"""Tests for PiperTTSProvider model management."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from kali_core.voice.providers.piper import PiperTTSProvider
from kali_core.voice.providers.base import TTSModelInfo, TTSModelVoice


@pytest.fixture
def piper_provider(tmp_path):
    voices_dir = tmp_path / "voices"
    configs_dir = tmp_path / "voice_configs"
    voices_dir.mkdir()
    configs_dir.mkdir()

    onnx_glados = voices_dir / "es_ES-glados-medium.onnx"
    onnx_glados.write_bytes(b"fake onnx")
    (voices_dir / "es_ES-glados-medium.onnx.json").write_text(json.dumps({
        "audio": {"sample_rate": 22050},
        "espeak": {"voice": "es"},
        "num_speakers": 1,
        "speaker_id_map": {},
        "language": {"code": "es_ES", "family": "es"},
    }))

    onnx_davefx = voices_dir / "es_ES-davefx-medium.onnx"
    onnx_davefx.write_bytes(b"fake onnx")
    (voices_dir / "es_ES-davefx-medium.onnx.json").write_text(json.dumps({
        "audio": {"sample_rate": 22050},
        "espeak": {"voice": "es"},
        "num_speakers": 2,
        "speaker_id_map": {"speaker_a": 0, "speaker_b": 1},
    }))

    (configs_dir / "glados-es.json").write_text(json.dumps({
        "voice_id": "glados-es", "name": "GLaDOS ES", "model": "es_ES-glados-medium",
        "params": {"length_scale": 1.0, "noise_scale": 0.667, "noise_w_scale": 0.8},
        "modes": {"normal": {"effects": []}},
    }))
    (configs_dir / "robot-es.json").write_text(json.dumps({
        "voice_id": "robot-es", "name": "Robot ES", "model": "es_ES-glados-medium",
        "params": {"length_scale": 1.0, "noise_scale": 0.667, "noise_w_scale": 0.8},
        "modes": {"robotic": {"effects": ["robotic"]}},
    }))

    with patch("kali_core.voice.providers.piper.PiperEngine") as mock_engine:
        mock_engine.return_value.load_voice.return_value = object()
        provider = PiperTTSProvider(voices_dir=voices_dir, voice_configs_dir=configs_dir)
    return provider


def test_piper_provider_name():
    assert PiperTTSProvider._provider_name == "piper"


def test_piper_list_models_discovers_onnx_files(piper_provider):
    models = piper_provider.list_models()
    ids = [m.id for m in models]
    assert "es_ES-glados-medium" in ids
    assert "es_ES-davefx-medium" in ids


def test_piper_list_models_includes_voice_configs(piper_provider):
    models = {m.id: m for m in piper_provider.list_models()}
    glados = models["es_ES-glados-medium"]
    voice_ids = [v.id for v in glados.voices]
    assert "glados-es" in voice_ids
    assert "robot-es" in voice_ids


def test_piper_list_models_includes_internal_speakers_for_multi(piper_provider):
    models = {m.id: m for m in piper_provider.list_models()}
    davefx = models["es_ES-davefx-medium"]
    speaker_ids = [v.id for v in davefx.voices if v.source == "speaker"]
    assert "es_ES-davefx-medium::speaker_a" in speaker_ids
    assert "es_ES-davefx-medium::speaker_b" in speaker_ids


def test_piper_list_models_reports_language(piper_provider):
    models = {m.id: m for m in piper_provider.list_models()}
    assert "es" in models["es_ES-glados-medium"].supported_languages


def test_piper_load_model_sets_loaded(piper_provider):
    piper_provider.load_model("es_ES-glados-medium")
    assert piper_provider.is_loaded is True
    assert piper_provider.loaded_model == "es_ES-glados-medium"
    assert piper_provider.device == "cpu"


def test_piper_unload_model_clears_state(piper_provider):
    piper_provider.load_model("es_ES-glados-medium")
    piper_provider.unload_model()
    assert piper_provider.is_loaded is False
    assert piper_provider.loaded_model is None


def test_piper_is_available_always_true(piper_provider):
    assert piper_provider.is_available is True
    assert piper_provider.last_error is None
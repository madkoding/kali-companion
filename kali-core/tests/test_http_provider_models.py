"""Tests for HTTPTTSProvider model management (no-op surface)."""

from kali_core.voice.providers.http import HTTPTTSProvider


def test_http_provider_name():
    p = HTTPTTSProvider()
    assert p.provider_name == "http"


def test_http_is_loaded_always_true():
    p = HTTPTTSProvider()
    assert p.is_loaded is True
    assert p.device == "cpu"
    assert p.loaded_model == "remote"
    assert p.is_available is True
    assert p.last_error is None


def test_http_list_models_one_remote():
    p = HTTPTTSProvider()
    models = p.list_models()
    assert len(models) == 1
    assert models[0].id == "remote"
    assert models[0].loaded is True


def test_http_load_unload_noop():
    p = HTTPTTSProvider()
    p.load_model("remote")
    p.unload_model()
    assert p.is_loaded is True
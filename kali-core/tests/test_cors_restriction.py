"""Contract test for CORS origin restriction (F0-6).

Pins the guarantee: the server does not use allow_origins=['*'] with
allow_credentials=True. Origins must be explicitly listed via the
KALI_CORS_ORIGINS env var.
"""

from __future__ import annotations

import os
from unittest.mock import patch


def test_cors_origins_comes_from_settings() -> None:
    """CORS must be wired from settings.cors_origins, not hardcoded ['*']."""
    from starlette.middleware.cors import CORSMiddleware

    # Reload the module so CORSMiddleware is re-imported.
    import importlib
    import kali_core.server
    importlib.reload(kali_core.server)

    with patch("fastapi.FastAPI.add_middleware") as mock_add:
        from kali_core.server import Server
        srv = Server(host="127.0.0.1", port=8901)
        # Find the CORSMiddleware call.
        cors_call = None
        for call in mock_add.call_args_list:
            if call.args and call.args[0] is CORSMiddleware:
                cors_call = call
                break
        assert cors_call is not None, "CORSMiddleware was not added"
        kwargs = cors_call.kwargs
        origins = kwargs.get("allow_origins")
        assert origins != ["*"], "CORS must not be wildcard"
        assert "http://localhost:5173" in origins


def test_cors_origins_override_via_env(monkeypatch) -> None:
    """KALI_CORS_ORIGINS env var must override the default origins."""
    monkeypatch.setenv("KALI_CORS_ORIGINS", "https://my-app.example.com")
    import importlib
    import kali_core.config
    importlib.reload(kali_core.config)
    assert "https://my-app.example.com" in kali_core.config.cors_origins
    assert "http://localhost:5173" not in kali_core.config.cors_origins

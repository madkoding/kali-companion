"""Compatibility shim — InProcTTSProvider is now PiperTTSProvider.

Kept so existing imports (server.py, tests) do not break during the
transition. Will be removed once all imports are updated.
"""

from .piper import PiperTTSProvider as InProcTTSProvider

__all__ = ["InProcTTSProvider"]
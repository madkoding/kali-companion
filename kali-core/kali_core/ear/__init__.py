"""kali-ear — STT engine (the cat's ears).

Real-time offline speech-to-text with multi-language support. Supports
multiple backends via the STTProvider Protocol:

  - Vosk (default): lightweight Kaldi models, CPU-only, native streaming
  - Qwen3-ASR: HuggingFace transformers models (0.6B / 1.7B), GPU-accelerated,
    emulated streaming

Also provides wake word detection ("Hey Kali" / "Oye Kali") via Vosk
grammar mode — a lightweight always-on listener that triggers the main
STT session when the wake phrase is heard.
"""

from .manager import STTManager, WakeWordDetector
from .providers import (
    ModelInfo,
    Qwen3STTProvider,
    STTProvider,
    VoskSTTProvider,
    get_stt_provider,
    list_stt_providers,
)
from .vosk_engine import StreamingSTT

__all__ = [
    "StreamingSTT",
    "STTManager",
    "WakeWordDetector",
    "STTProvider",
    "ModelInfo",
    "VoskSTTProvider",
    "Qwen3STTProvider",
    "get_stt_provider",
    "list_stt_providers",
]

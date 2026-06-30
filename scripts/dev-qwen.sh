#!/usr/bin/env bash
# Dev launcher with Qwen3-TTS (0.6B CustomVoice mode).
#
# Sets KALI_TTS_PROVIDER=qwen3 and validates that the binary and model
# are present before starting. If they are missing, prints clear
# setup instructions.
#
# Usage: scripts/dev-qwen.sh
#
# Requires (in addition to dev.sh requirements):
#   - scripts/build-qwen-cpp.sh cpu       # compile the C++ binary
#   - scripts/download-qwen-models.sh     # download models
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
QWEN_TTS_PROVIDER="qwen3"

# ── Qwen3-TTS validation ───────────────────────────────────
QWEN_CPP_DIR="$ROOT/kali-core/kali_core/voice/qwen_cpp"
QWEN_MODEL="${KALI_QWEN_TALKER_MODEL:-$ROOT/kali-core/kali_core/voice/qwen_models/qwen-talker-0.6b-customvoice-Q4_K_M.gguf}"
QWEN_CODEC="${KALI_QWEN_CODEC_MODEL:-$ROOT/kali-core/kali_core/voice/qwen_models/qwen-tokenizer-12hz-Q4_K_M.gguf}"
QWEN_BINARY="$QWEN_CPP_DIR/build/tts-server"

if [ ! -x "$QWEN_BINARY" ]; then
  echo "ERROR: Qwen3-TTS CPU binary not found or not executable:"
  echo "  $QWEN_BINARY"
  echo ""
  echo "Run the following to set it up:"
  echo "  1. scripts/build-qwen-cpp.sh cpu"
  echo ""
  exit 1
fi

if [ ! -f "$QWEN_MODEL" ]; then
  echo "ERROR: Qwen3-TTS talker model not found:"
  echo "  $QWEN_MODEL"
  echo ""
  echo "Run the following to download it:"
  echo "  scripts/download-qwen-models.sh 0.6b-customvoice"
  echo ""
  exit 1
fi

if [ ! -f "$QWEN_CODEC" ]; then
  echo "ERROR: Qwen3-TTS codec/tokenizer model not found:"
  echo "  $QWEN_CODEC"
  echo ""
  echo "Run the following to download it:"
  echo "  scripts/download-qwen-models.sh --tokenizer"
  echo ""
  exit 1
fi

echo "[dev-qwen] Qwen3-TTS binary and models OK"
echo "           provider=qwen3"

# ── Launch via dev.sh with qwen3 provider ───────────────────
export KALI_TTS_PROVIDER="$QWEN_TTS_PROVIDER"
export KALI_QWEN_TALKER_MODEL="$QWEN_MODEL"
export KALI_QWEN_CODEC_MODEL="$QWEN_CODEC"

exec "$SCRIPT_DIR/dev.sh"

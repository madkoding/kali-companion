#!/usr/bin/env bash
# Full-app launcher with Qwen3-TTS (1.7B VoiceDesign mode).
#
# Usage: scripts/prod-qwen-vd.sh
#
# Requires (same as prod.sh plus):
#   - scripts/build-qwen-cpp.sh cpu       # compile the C++ binary
#   - scripts/download-qwen-models.sh 1.7b-voicedesign   # download VoiceDesign model
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
QWEN_TTS_PROVIDER="qwen3-voicedesign"

# ── Qwen3-TTS VoiceDesign validation ─────────────────────────
QWEN_CPP_DIR="$ROOT/kali-core/kali_core/voice/qwen_cpp"
QWEN_MODEL="${KALI_QWEN_VOICEDESIGN_MODEL:-$ROOT/kali-core/kali_core/voice/qwen_models/qwen-talker-1.7b-voicedesign-Q4_K_M.gguf}"
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
  echo "ERROR: Qwen3-TTS VoiceDesign model not found:"
  echo "  $QWEN_MODEL"
  echo ""
  echo "Run the following to download it:"
  echo "  scripts/download-qwen-models.sh 1.7b-voicedesign"
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

echo "[prod-qwen-vd] Qwen3-TTS VoiceDesign binary and models OK"
echo "               provider=qwen3-voicedesign"

# ── Launch via prod.sh with qwen3-voicedesign provider ─────────
export KALI_TTS_PROVIDER="$QWEN_TTS_PROVIDER"
export KALI_QWEN_VOICEDESIGN_MODEL="$QWEN_MODEL"
export KALI_QWEN_CODEC_MODEL="$QWEN_CODEC"

exec "$SCRIPT_DIR/prod.sh"

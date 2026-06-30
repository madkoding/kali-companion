#!/usr/bin/env bash
# Build qwen-tts-cpp-server C++ binary (tts-server).
#
# Usage:
#   ./scripts/build-qwen-cpp.sh cpu              # CPU build
#   ./scripts/build-qwen-cpp.sh cuda             # GPU CUDA (auto-detect arch)
#   ./scripts/build-qwen-cpp.sh cuda 86          # GPU CUDA (sm_86 only, RTX 30/40)
#   ./scripts/build-qwen-cpp.sh cuda --all       # GPU CUDA (all supported archs)
#
# The C++ source is cloned from github.com/fr4j4/qwen-tts-cpp-server (voicedesign branch)
# into kali-core/kali_core/voice/qwen_cpp/ if not already present.
#
# Output binaries:
#   cpu:  kali-core/kali_core/voice/qwen_cpp/build/tts-server
#   cuda: kali-core/kali_core/voice/qwen_cpp/build-gpu/tts-server

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."
CPP_DIR="$ROOT/kali-core/kali_core/voice/qwen_cpp"

BACKEND="${1:-cpu}"
ARCH="${2:-}"

usage() {
  echo "Usage: $0 {cpu|cuda} [arch|--all]"
  echo ""
  echo "Backends:"
  echo "  cpu   CPU build (with OpenBLAS if available)"
  echo "  cuda  GPU build with CUDA (auto-detects GPU arch)"
  echo ""
  echo "Architecture (cuda only):"
  echo "  --all    build for all supported architectures (slower)"
  echo "  75       Turing (T4, RTX 20)"
  echo "  80       Ampere (A100)"
  echo "  86       Ampere (RTX 30/40)"
  echo "  89       Ada (RTX 40 Ada)"
  echo "  120a     Blackwell (B100/B200)"
  echo "  121a     Blackwell (newer)"
  echo ""
  echo "Examples:"
  echo "  $0 cpu"
  echo "  $0 cuda"
  echo "  $0 cuda 86"
  echo "  $0 cuda --all"
}

if [ "$BACKEND" != "cpu" ] && [ "$BACKEND" != "cuda" ]; then
  usage
  exit 1
fi

# ── Clone / update repo ──────────────────────────────────────────────
if [ -d "$CPP_DIR/.git" ]; then
  echo "[INFO] qwen-tts-cpp-server already present at $CPP_DIR"
else
  echo "[INFO] Cloning qwen-tts-cpp-server..."
  git clone --branch voicedesign --depth 1 \
    https://github.com/fr4j4/qwen-tts-cpp-server.git "$CPP_DIR"
fi

cd "$CPP_DIR"

# Ensure submodule is present
if [ ! -f "ggml/CMakeLists.txt" ]; then
  echo "[INFO] Initializing ggml submodule..."
  git submodule update --init --recursive
fi

# ── Build ─────────────────────────────────────────────────────────────
build_dir="build"
build_args=()

if [ "$BACKEND" = "cpu" ]; then
  echo "[BUILD] CPU mode"
  build_dir="build"
  rm -rf "$build_dir"
  mkdir "$build_dir"
  cd "$build_dir"

  if pkg-config --exists openblas 2>/dev/null; then
    echo "[INFO] OpenBLAS detected, enabling BLAS acceleration..."
    cmake .. -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS
  else
    echo "[INFO] No BLAS found, building without..."
    cmake .. -DGGML_BLAS=OFF
  fi

elif [ "$BACKEND" = "cuda" ]; then
  echo "[BUILD] CUDA GPU mode"
  build_dir="build-gpu"
  rm -rf "$build_dir"
  mkdir "$build_dir"
  cd "$build_dir"

  # Find nvcc
  NVCC=""
  for path in /opt/cuda/bin/nvcc /usr/local/cuda/bin/nvcc "$(command -v nvcc 2>/dev/null)"; do
    if [ -x "$path" ]; then
      NVCC="$path"
      break
    fi
  done
  if [ -z "$NVCC" ]; then
    echo "ERROR: CUDA toolkit (nvcc) not found."
    echo "Install CUDA toolkit or use CPU mode: $0 cpu"
    exit 1
  fi
  echo "[INFO] Using nvcc: $NVCC"
  CUDA_DIR=$(dirname "$(dirname "$NVCC")")

  # Determine architectures
  ARCHS=""
  if [ "$ARCH" = "--all" ]; then
    ARCHS="75;80;86;89;120a;121a"
    echo "[INFO] Building for all supported CUDA architectures"
  elif [ -n "$ARCH" ]; then
    ARCHS="$ARCH"
    echo "[INFO] Building for architecture sm_$ARCH"
  else
    echo "[INFO] Auto-detecting GPU architecture..."
    if command -v nvidia-smi &>/dev/null; then
      ARCHS=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | \
        sort -u | \
        while read cc; do
          arch=$(echo "$cc" | tr -d '.')
          echo "$arch"
        done | paste -sd ';')
      if [ -n "$ARCHS" ]; then
        echo "[INFO] Detected GPU architectures: sm_${ARCHS//;/, sm_}"
      fi
    fi
    if [ -z "$ARCHS" ]; then
      echo "[WARN] Could not auto-detect GPU arch. Defaulting to sm_86 (RTX 30/40)."
      echo "[WARN] Override with: $0 cuda 86"
      ARCHS="86"
    fi
  fi

  cmake .. \
    -DGGML_CUDA=ON \
    -DCMAKE_CUDA_COMPILER="$NVCC" \
    -DCMAKE_CUDA_ARCHITECTURES="$ARCHS" \
    -DCMAKE_CUDA_HOST_COMPILER="$(command -v g++ 2>/dev/null || command -v c++)"
fi

echo "[BUILD] Compiling (this may take several minutes)..."
cmake --build . --config Release -j "$(nproc)"

BINARY="$CPP_DIR/$build_dir/tts-server"
if [ -x "$BINARY" ]; then
  echo ""
  echo "=== Build complete ==="
  echo "Binary: $BINARY"
  echo ""
  echo "The binary is auto-resolved by kali based on KALI_QWEN_BACKEND:"
  echo "  CPU build  -> build/tts-server     (when KALI_QWEN_BACKEND=CPU)"
  echo "  GPU build  -> build-gpu/tts-server (when KALI_QWEN_BACKEND=CUDA0)"
else
  echo "ERROR: Build failed - tts-server binary not found at $BINARY"
  exit 1
fi
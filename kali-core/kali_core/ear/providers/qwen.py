"""Qwen3STTProvider — Qwen3-ASR via HuggingFace transformers.

Supports two models:
  - qwen3-asr-0.6b  (Qwen/Qwen3-ASR-0.6B-hf, ~1.6 GB VRAM)
  - qwen3-asr-1.7b  (Qwen/Qwen3-ASR-1.7B-hf, ~3.4 GB VRAM)

Streaming is emulated via chunk-based re-transcription with prefix reuse
(2-second chunks). Batch mode transcribes the full utterance at once.
"""

from __future__ import annotations

import contextlib
import logging
import time
from pathlib import Path

import numpy as np

from .base import ModelInfo

logger = logging.getLogger("kali_core.ear.qwen_provider")

SAMPLE_RATE = 16000
DTYPE = "float16"

MODEL_CONFIGS: dict[str, dict] = {
    "qwen3-asr-0.6b": {
        "hf_id": "Qwen/Qwen3-ASR-0.6B-hf",
        "display_name": "Qwen3-ASR 0.6B",
        "estimated_vram_mb": 1600,
    },
    "qwen3-asr-1.7b": {
        "hf_id": "Qwen/Qwen3-ASR-1.7B-hf",
        "display_name": "Qwen3-ASR 1.7B",
        "estimated_vram_mb": 3400,
    },
}

LANG_MAP: dict[str, str | None] = {
    "auto": None,
    "es-ES": "es", "es-US": "es", "es": "es",
    "en-US": "en", "en-GB": "en", "en": "en",
    "de-DE": "de", "fr-FR": "fr",
    "it-IT": "it", "pt-BR": "pt", "pt-PT": "pt",
    "ja-JP": "ja", "ko-KR": "ko", "zh-CN": "zh",
    "ru-RU": "ru", "hi-IN": "hi", "ar-SA": "ar",
    "tr-TR": "tr", "nl-NL": "nl", "pl-PL": "pl",
    "uk-UA": "uk",
}

SUPPORTED_LANGUAGES = sorted(set(v for v in LANG_MAP.values() if v is not None))


def _check_deps() -> None:
    try:
        import huggingface_hub  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Qwen3-ASR requires torch, transformers, and huggingface_hub.\n"
            "Install with:\n"
            "  pip install kali-core[qwen-stt]"
        ) from exc


def is_qwen3_asr_available(model_id: str, models_dir: str | Path) -> bool:
    cfg = MODEL_CONFIGS.get(model_id)
    if not cfg:
        return False
    try:
        from huggingface_hub import try_to_load_from_cache
        return (
            try_to_load_from_cache(cfg["hf_id"], "config.json", cache_dir=str(models_dir))
            is not None
        )
    except Exception:
        return False


def _parse_asr_output(raw_text: str, user_language: str | None = None) -> tuple[str, str]:
    text = raw_text.strip()
    lang = ""
    if "<asr_text>" in text:
        before, after = text.split("<asr_text>", 1)
        before = before.strip()
        if before.startswith("language "):
            lang = before[len("language "):].strip()
        elif user_language:
            lang = user_language
        text = after.strip()
    elif user_language:
        lang = user_language
    return lang, text


class Qwen3STTProvider:
    """Qwen3-ASR provider — loads models via HuggingFace transformers."""

    provider_name = "qwen3"

    def __init__(self, models_dir: str | Path = "~/.cache/huggingface/hub") -> None:
        self._models_dir = Path(models_dir).expanduser().resolve()
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._model: object | None = None
        self._processor: object | None = None
        self._device: str | None = None
        self._loaded_model_id: str | None = None
        self._force_math_backend = False
        self._streaming = True
        self._streaming_state: dict | None = None
        self._batch_buffer: np.ndarray = np.zeros(0, dtype=np.float32)
        self._session_active = False
        self._session_language = "en"

    def configure(self, models_dir: str | Path) -> None:
        self._models_dir = Path(models_dir).expanduser().resolve()
        self._models_dir.mkdir(parents=True, exist_ok=True)

    # ── model management ──────────────────────────────────────

    def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        for mid, cfg in MODEL_CONFIGS.items():
            models.append(
                ModelInfo(
                    id=mid,
                    display_name=cfg["display_name"],
                    estimated_vram_mb=cfg["estimated_vram_mb"],
                    available=is_qwen3_asr_available(mid, self._models_dir),
                    loaded=(mid == self._loaded_model_id),
                    device=self._device if mid == self._loaded_model_id else None,
                    supported_languages=SUPPORTED_LANGUAGES,
                )
            )
        return models

    def load_model(self, model_id: str, device: str = "cpu") -> None:
        _check_deps()
        import torch
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        cfg = MODEL_CONFIGS[model_id]
        logger.info("Loading %s (%s) on %s...", cfg["display_name"], cfg["hf_id"], device)

        kwargs: dict = dict(cache_dir=str(self._models_dir))
        try:
            self._processor = AutoProcessor.from_pretrained(
                cfg["hf_id"], **kwargs, local_files_only=True
            )
            self._model = AutoModelForMultimodalLM.from_pretrained(
                cfg["hf_id"],
                dtype=getattr(torch, DTYPE),
                attn_implementation="sdpa",
                **kwargs,
                local_files_only=True,
            )
        except OSError:
            logger.warning(
                "%s not found in cache, attempting download...", cfg["display_name"]
            )
            self._processor = AutoProcessor.from_pretrained(
                cfg["hf_id"], **kwargs
            )
            self._model = AutoModelForMultimodalLM.from_pretrained(
                cfg["hf_id"],
                dtype=getattr(torch, DTYPE),
                attn_implementation="sdpa",
                **kwargs,
            )
        self._model = self._model.to(device)
        self._model.eval()
        self._device = device
        self._loaded_model_id = model_id
        self._force_math_backend = self._detect_pre_ampere(device)

        if self._force_math_backend:
            logger.warning(
                "%s: GPU pre-Ampere detected on %s. Forcing SDPA=MATH backend.",
                cfg["display_name"], device,
            )

        logger.info("%s loaded on %s", cfg["display_name"], device)

    def unload_model(self) -> None:
        import torch
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        self._device = None
        self._loaded_model_id = None
        self._force_math_backend = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Qwen3-ASR model unloaded")

    def delete_model(self, model_id: str) -> None:
        """Unload and delete model files from disk."""
        if self._loaded_model_id == model_id:
            self.unload_model()
        
        cfg = MODEL_CONFIGS.get(model_id)
        if not cfg:
            return
        
        try:
            import shutil
            repo_id = cfg["hf_id"]
            folder_name = f"models--{repo_id.replace('/', '--')}"
            repo_path = self._models_dir / folder_name
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info("Deleted Qwen3-ASR model directory: %s", repo_path)
        except Exception as e:
            logger.error("Error deleting Qwen3-ASR model %s: %s", model_id, e)

    # ── state ─────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    @property
    def device(self) -> str | None:
        return self._device

    @property
    def loaded_model(self) -> str | None:
        return self._loaded_model_id

    # ── transcription session ─────────────────────────────────

    def start_session(self, language: str) -> None:
        mapped = LANG_MAP.get(language, "en") or "en"
        self._session_language = mapped
        self._session_active = True

        if self._streaming:
            self._streaming_state = self._init_streaming_state(mapped)
        else:
            self._batch_buffer = np.zeros(0, dtype=np.float32)

    def accept(self, chunk: bytes) -> dict | None:
        if not self.is_loaded or not self._session_active:
            return None

        samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

        if self._streaming:
            return self._accept_streaming(samples)
        return self._accept_batch(samples)

    def finish(self) -> dict:
        if not self.is_loaded or not self._session_active:
            self._session_active = False
            return {"text": ""}

        result = self._finish_streaming() if self._streaming else self._finish_batch()

        self._session_active = False
        return result

    @property
    def session_active(self) -> bool:
        return self._session_active

    # ── streaming mode ───────────────────────────────────────

    @property
    def supports_streaming(self) -> bool:
        return True

    def set_streaming(self, enabled: bool) -> None:
        self._streaming = enabled

    # ── internal: streaming emulation ─────────────────────────

    def _init_streaming_state(self, language: str | None, chunk_size_sec: float = 2.0) -> dict:
        prompt_raw = self._build_prompt(language)
        return {
            "chunk_id": 0,
            "buffer": np.zeros(0, dtype=np.float32),
            "audio_accum": np.zeros(0, dtype=np.float32),
            "prompt_raw": prompt_raw,
            "force_language": language,
            "language": "",
            "text": "",
            "_raw_decoded": "",
            "chunk_size_samples": int(round(chunk_size_sec * SAMPLE_RATE)),
            "unfixed_chunk_num": 2,
            "unfixed_token_num": 5,
        }

    def _build_prompt(self, language: str | None) -> str:
        msgs = [
            {"role": "system", "content": [{"type": "text", "text": ""}]},
            {"role": "user", "content": [{"type": "audio", "audio": ""}]},
        ]
        base = self._processor.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=False
        )
        if language:
            base = base + f"language {language}{'<asr_text>'}"
        return base

    def _accept_streaming(self, samples: np.ndarray) -> dict | None:
        import torch
        state = self._streaming_state
        if state is None:
            return None

        x = samples.reshape(-1)
        if x.shape[0] > 0:
            state["buffer"] = np.concatenate([state["buffer"], x])

        prev_text = state["text"]

        while state["buffer"].shape[0] >= state["chunk_size_samples"]:
            chunk = state["buffer"][:state["chunk_size_samples"]]
            state["buffer"] = state["buffer"][state["chunk_size_samples"]:]

            if state["audio_accum"].shape[0] == 0:
                state["audio_accum"] = chunk
            else:
                state["audio_accum"] = np.concatenate([state["audio_accum"], chunk])

            prefix = ""
            if state["chunk_id"] >= state["unfixed_chunk_num"]:
                cur_ids = self._processor.tokenizer.encode(state["_raw_decoded"])
                k = int(state["unfixed_token_num"])
                while True:
                    end_idx = max(0, len(cur_ids) - k)
                    prefix = (
                        self._processor.tokenizer.decode(cur_ids[:end_idx])
                        if end_idx > 0
                        else ""
                    )
                    if "\ufffd" not in prefix:
                        break
                    if end_idx == 0:
                        prefix = ""
                        break
                    k += 1

            prompt = state["prompt_raw"] + prefix
            inputs = self._processor(
                text=prompt, audio=state["audio_accum"], return_tensors="pt"
            )
            inputs = inputs.to(self._model.device, self._model.dtype)

            with torch.no_grad(), self._sdpa_context():
                output_ids = self._model.generate(**inputs, max_new_tokens=256)

            generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
            gen_text = self._processor.decode(generated_ids[0], skip_special_tokens=True)

            state["_raw_decoded"] = (prefix + gen_text) if prefix else gen_text
            lang_parsed, text_parsed = _parse_asr_output(
                state["_raw_decoded"], state["force_language"]
            )
            state["language"] = lang_parsed
            state["text"] = text_parsed
            state["chunk_id"] += 1

        if state["text"] and state["text"] != prev_text:
            return {"partial": state["text"]}
        return None

    def _finish_streaming(self) -> dict:
        import torch
        state = self._streaming_state
        if state is None:
            return {"text": ""}

        if state["buffer"].shape[0] > 0:
            tail = state["buffer"]
            state["buffer"] = np.zeros(0, dtype=np.float32)

            if state["audio_accum"].shape[0] == 0:
                state["audio_accum"] = tail
            else:
                state["audio_accum"] = np.concatenate([state["audio_accum"], tail])

            prefix = ""
            if state["chunk_id"] >= state["unfixed_chunk_num"]:
                cur_ids = self._processor.tokenizer.encode(state["_raw_decoded"])
                end_idx = max(1, len(cur_ids) - int(state["unfixed_token_num"]))
                prefix = self._processor.tokenizer.decode(cur_ids[:end_idx])

            prompt = state["prompt_raw"] + prefix
            inputs = self._processor(
                text=prompt, audio=state["audio_accum"], return_tensors="pt"
            )
            inputs = inputs.to(self._model.device, self._model.dtype)

            with torch.no_grad(), self._sdpa_context():
                output_ids = self._model.generate(**inputs, max_new_tokens=256)

            generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
            gen_text = self._processor.decode(generated_ids[0], skip_special_tokens=True)

            state["_raw_decoded"] = (prefix + gen_text) if prefix else gen_text
            lang_parsed, text_parsed = _parse_asr_output(
                state["_raw_decoded"], state["force_language"]
            )
            state["language"] = lang_parsed
            state["text"] = text_parsed
            state["chunk_id"] += 1

        self._streaming_state = None
        return {"text": state["text"]}

    # ── internal: batch mode ──────────────────────────────────

    def _accept_batch(self, samples: np.ndarray) -> None:
        self._batch_buffer = np.concatenate([self._batch_buffer, samples.reshape(-1)])
        return None

    def _finish_batch(self) -> dict:
        import torch
        if self._batch_buffer.shape[0] == 0:
            return {"text": ""}

        t0 = time.perf_counter()
        inputs = self._processor.apply_transcription_request(
            audio=self._batch_buffer,
            language=self._session_language,
        )
        inputs = inputs.to(self._model.device, self._model.dtype)

        with torch.no_grad(), self._sdpa_context():
            output_ids = self._model.generate(**inputs, max_new_tokens=256)

        generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
        text = self._processor.decode(generated_ids, return_format="transcription_only")[0]
        t1 = time.perf_counter()

        logger.info(
            "Batch transcription: %.2fs (%.1fs audio)",
            t1 - t0, len(self._batch_buffer) / SAMPLE_RATE,
        )
        self._batch_buffer = np.zeros(0, dtype=np.float32)
        return {"text": text.strip() if text else ""}

    # ── internal: GPU helpers ─────────────────────────────────

    def _detect_pre_ampere(self, device: str) -> bool:
        import torch
        if not device.startswith("cuda"):
            return False
        if not torch.cuda.is_available():
            return False
        try:
            idx = int(device.split(":")[1]) if ":" in device else 0
            major, _ = torch.cuda.get_device_capability(idx)
            return major < 8
        except Exception:
            return False

    def _sdpa_context(self):
        try:
            from torch.nn.attention import SDPBackend, sdpa_kernel
            if self._force_math_backend:
                return sdpa_kernel(SDPBackend.MATH)
        except ImportError:
            pass
        return contextlib.nullcontext()

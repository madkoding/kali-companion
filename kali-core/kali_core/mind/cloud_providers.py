"""Curated catalog of cloud LLM providers exposed to the UI.

The frontend uses this list to render a searchable picker when the user
creates a new cloud connection.  Each entry has enough metadata to:
  - prefill `api_url` on the form (so the user only types the API key)
  - show a `docs_url` link for "where do I get a key?"
  - display a one-liner `notes` for context (model quirks, rate limits)

We deliberately keep this list static and curated: any provider that
exposes an OpenAI-compatible `/v1/chat/completions` endpoint fits here.
Vendors that only speak a non-OAI dialect (Anthropic native, Google
Gemini native, Cohere native) need a translator — out of scope for the
initial release; we point users to OpenRouter-style proxies instead.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CloudProvider:
    id: str
    name: str
    api_url: str
    docs_url: str
    notes: str


CLOUD_PROVIDERS: list[CloudProvider] = [
    CloudProvider(
        id="openai",
        name="OpenAI",
        api_url="https://api.openai.com/v1",
        docs_url="https://platform.openai.com/api-keys",
        notes="GPT-4o, GPT-4.1, o-series. Standard reference implementation.",
    ),
    CloudProvider(
        id="openrouter",
        name="OpenRouter",
        api_url="https://openrouter.ai/api/v1",
        docs_url="https://openrouter.ai/keys",
        notes="Routes to 100+ models from a single key. /api/v1 prefix required.",
    ),
    CloudProvider(
        id="anthropic",
        name="Anthropic (via OpenAI proxy)",
        api_url="https://api.anthropic.com/v1",
        docs_url="https://console.anthropic.com/settings/keys",
        notes="Claude 3.x / 4.x. Use only via OpenAI-compatible proxy endpoints.",
    ),
    CloudProvider(
        id="mistral",
        name="Mistral AI",
        api_url="https://api.mistral.ai/v1",
        docs_url="https://console.mistral.ai/api-keys",
        notes="Mistral Large, Codestral, Pixtral. OpenAI-compatible since 2024.",
    ),
    CloudProvider(
        id="groq",
        name="Groq",
        api_url="https://api.groq.com/openai/v1",
        docs_url="https://console.groq.com/keys",
        notes="Ultra-low-latency inference. /openai/v1 prefix required.",
    ),
    CloudProvider(
        id="together",
        name="Together AI",
        api_url="https://api.together.xyz/v1",
        docs_url="https://api.together.ai/settings/api-keys",
        notes="Open-source models (Llama, Qwen, DeepSeek) hosted. Pay-as-you-go.",
    ),
    CloudProvider(
        id="fireworks",
        name="Fireworks AI",
        api_url="https://api.fireworks.ai/inference/v1",
        docs_url="https://fireworks.ai/account/api-keys",
        notes="Fast open-source inference. /inference/v1 prefix required.",
    ),
    CloudProvider(
        id="deepseek",
        name="DeepSeek",
        api_url="https://api.deepseek.com/v1",
        docs_url="https://platform.deepseek.com/api_keys",
        notes="DeepSeek-V3, R1. OpenAI-compatible chat completions.",
    ),
    CloudProvider(
        id="ollama_cloud",
        name="Ollama Cloud",
        api_url="https://ollama.com/v1",
        docs_url="https://ollama.com/settings/keys",
        notes="Hosted Ollama models behind an API key. Same /v1 namespace.",
    ),
    CloudProvider(
        id="perplexity",
        name="Perplexity",
        api_url="https://api.perplexity.ai",
        docs_url="https://www.perplexity.ai/settings/api",
        notes="Online-augmented chat (sonar models). Base URL has no /v1.",
    ),
    CloudProvider(
        id="openai_compatible",
        name="OpenAI-compatible (custom URL)",
        api_url="",
        docs_url="",
        notes="Any server speaking the OpenAI /v1/chat/completions dialect.",
    ),
]


def find_cloud_provider(provider_id: str) -> CloudProvider | None:
    for p in CLOUD_PROVIDERS:
        if p.id == provider_id:
            return p
    return None
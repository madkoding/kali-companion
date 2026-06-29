"""Port scanner for local LLM API endpoints.

Two-phase scan: first a fast socket-level sweep to find open ports,
then HTTP GET /v1/models only on those open ports.  This is orders of
magnitude faster than probing every port with HTTP (socket sweep of
4000 ports takes ~0.5s; HTTP probing takes 60s+).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger("kali_core.mind.scanner")

DEFAULT_PORT_FROM = 8000
DEFAULT_PORT_TO = 12300
SOCKET_TIMEOUT_MS = 200
HTTP_TIMEOUT_S = 3.0
SOCKET_CONCURRENCY = 500

_PATHS = ("/v1/models", "/models")


@dataclass
class LocalEndpoint:
    port: int
    url: str
    vendor: str
    models: list[str]


def _guess_vendor(data: dict, text: str, url: str = "") -> str:
    obj = str(data.get("object", ""))
    combined = f"{obj} {text}".lower()
    if "ollama" in combined:
        return "ollama"
    if "llama.cpp" in combined or "llama-cpp" in combined:
        return "llama.cpp"
    if "lmstudio" in combined or "lm studio" in combined:
        return "lmstudio"
    if "vllm" in combined:
        return "vllm"
    if "unsloth" in combined:
        return "unsloth"
    # Heuristic for OpenRouter: non-standard path prefix and namespace-shaped ids.
    if "/api/v1" in url:
        return "openrouter"
    return "openai-compatible"


def _parse_models(data: dict) -> list[str]:
    raw = data.get("data", data.get("models", []))
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for m in raw:
        if isinstance(m, dict) and "id" in m:
            out.append(str(m["id"]))
        elif isinstance(m, str):
            out.append(m)
    return out


async def _socket_open(host: str, port: int, timeout: float) -> bool:
    """Return True if a TCP connection can be opened on host:port."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
        return False
    except Exception:
        return False


async def _http_probe(client: httpx.AsyncClient, host: str, port: int, timeout: float) -> LocalEndpoint | None:
    """Probe a single open port for OpenAI-compatible /models endpoints."""
    for path in _PATHS:
        url = f"http://{host}:{port}{path}"
        try:
            resp = await client.get(url, timeout=timeout)
            if resp.status_code != 200:
                continue
            try:
                data = resp.json()
            except Exception:
                continue
            models = _parse_models(data)
            vendor = _guess_vendor(data, resp.text[:4096], url)
            return LocalEndpoint(
                port=port,
                url=f"http://{host}:{port}/v1",
                vendor=vendor,
                models=models,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError):
            continue
        except Exception:
            continue
    return None


async def scan_local(
    host: str = "127.0.0.1",
    port_from: int = DEFAULT_PORT_FROM,
    port_to: int = DEFAULT_PORT_TO,
    timeout_ms: float = SOCKET_TIMEOUT_MS,
    max_concurrency: int = SOCKET_CONCURRENCY,
) -> list[LocalEndpoint]:
    """Two-phase scan: fast socket sweep, then HTTP probe only open ports."""
    ports = list(range(port_from, port_to + 1))
    if not ports:
        return []

    socket_timeout = timeout_ms / 1000.0
    sem = asyncio.Semaphore(max_concurrency)

    # Phase 1: fast socket sweep
    async def _wrapped_socket(port: int) -> bool:
        async with sem:
            return await _socket_open(host, port, socket_timeout)

    open_results = await asyncio.gather(
        *[_wrapped_socket(p) for p in ports], return_exceptions=True
    )
    open_ports = [p for p, ok in zip(ports, open_results) if ok is True]
    logger.info("Socket sweep: %d open ports in range %d-%d: %s", len(open_ports), port_from, port_to, open_ports)

    if not open_ports:
        return []

    # Phase 2: HTTP probe only open ports
    results: list[LocalEndpoint] = []
    async with httpx.AsyncClient() as client:
        found = await asyncio.gather(
            *[_http_probe(client, host, p, HTTP_TIMEOUT_S) for p in open_ports],
            return_exceptions=True,
        )
        for endpoint in found:
            if isinstance(endpoint, LocalEndpoint):
                results.append(endpoint)
                logger.debug("Found LLM endpoint at %s:%d — %s", host, endpoint.port, endpoint.vendor)

    results.sort(key=lambda e: e.port)
    return results


@dataclass
class EndpointProbe:
    ok: bool
    vendor: str
    models: list[str]
    detail: str = ""


async def probe_endpoint(api_url: str, api_key: str = "") -> EndpointProbe:
    """Probe an arbitrary OpenAI-compatible URL for reachability + vendor.

    Returns a structured result so the caller can show the user a precise
    diagnostic (vendor, model count, or failure reason) without having to
    duplicate the HTTP plumbing.
    """
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    base = api_url.rstrip("/")
    last_err = ""
    for path in ("/v1/models", "/models"):
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=10.0)
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            continue
        if resp.status_code in (401, 403):
            return EndpointProbe(
                ok=False, vendor="", models=[],
                detail=f"API key rejected ({resp.status_code} {resp.reason_phrase})",
            )
        if resp.status_code != 200:
            last_err = f"HTTP {resp.status_code} at {url}"
            continue
        try:
            data = resp.json()
        except Exception as exc:
            last_err = f"invalid JSON at {url} ({exc})"
            continue
        models = _parse_models(data)
        vendor = _guess_vendor(data, resp.text[:4096], url)
        return EndpointProbe(ok=True, vendor=vendor, models=models, detail="ok")
    return EndpointProbe(ok=False, vendor="", models=[], detail=last_err or "no /v1/models endpoint")


async def verify_api_key(api_url: str, api_key: str) -> tuple[bool, str]:
    """Verify an API key by attempting a minimal chat completion.

    Tries multiple path layouts so both of these work:
      api_url=http://localhost:11434/v1  →  POST /chat/completions
      api_url=http://localhost:11434     →  POST /v1/chat/completions

    Returns (ok, detail) where:
      ok=True  — the key was accepted (auth passed, even if model not found)
      ok=False — the key was rejected (401/403) or all attempts failed
    """
    if not api_key:
        return False, "no API key provided"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    base = api_url.rstrip("/")
    payload = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}],
    }

    # Build unique candidate URLs so we handle both /v1-prefixed and bare bases.
    candidates: list[str] = []
    for suffix in ("/chat/completions", "/v1/chat/completions"):
        candidates.append(f"{base}{suffix}")
        # If base already has a /v1 segment, also try without it and vice versa.
        if base.endswith("/v1"):
            bare = base[:-3]
            candidates.append(f"{bare}{suffix}")
        elif not base.endswith("/v1"):
            candidates.append(f"{base}/v1{suffix}")

    seen: set[str] = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
        except Exception:
            continue

        # 401 / 403 → auth definitively rejected
        if resp.status_code in (401, 403):
            return False, f"API key rejected ({resp.status_code} {resp.reason_phrase})"

        # 200 → key valid, endpoint works
        if resp.status_code == 200:
            return True, "API key is valid"

        # 404 → auth passed (server checked key THEN said model not found)
        if resp.status_code == 404:
            return True, "API key accepted (model not found, but auth passed)"

        # 405 or any other non-2xx → try next candidate
        continue

    return False, "could not reach chat completions endpoint on any known path"


async def list_models(api_url: str, api_key: str = "") -> list[str]:
    """Fetch the model list from an arbitrary OpenAI-compatible endpoint."""
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    base = api_url.rstrip("/")
    for path in ("/v1/models", "/models"):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base}{path}", headers=headers, timeout=10.0)
            if resp.status_code != 200:
                continue
            data = resp.json()
            models = _parse_models(data)
            if models:
                return models
        except Exception:
            continue
    return []
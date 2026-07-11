"""Saved LLM connections store.

Persists user-defined LLM endpoint configurations in JSON so they survive
restarts.  Same trust boundary as `ai_config.json`: api_key is stored in
plaintext next to other connection metadata.  If/when the project gets a
secrets boundary, swap this for `keyring` or an encrypted blob — the rest of
the app only reads/writes via `ConnectionsStore`.

Schema version `1`.  Unknown future fields are kept on disk and ignored
by the dataclass filter (forward-compatible), while unknown fields we do
not understand at all are silently dropped to keep the file clean.
"""

from __future__ import annotations

import copy
import json
import logging
import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger("kali_core.mind.connections_store")

_SCHEMA_VERSION = 1

_CONFIG_DIRNAME = "kali"
_CONFIG_FILENAME = "connections.json"


def _config_path() -> Path:
    """Return the user-wide config path.  Falls back to repo root on test envs
    where $HOME is unset or points somewhere pathological.
    """
    home = Path.home() if Path.home().exists() else Path.cwd()
    return home / ".config" / _CONFIG_DIRNAME / _CONFIG_FILENAME


ConnectionKind = Literal["local", "cloud"]
ApiFormat = Literal["openai", "ollama", "llamacpp", "lmstudio", "vllm", "custom"]

_VALID_FORMATS: tuple[str, ...] = ("openai", "ollama", "llamacpp", "lmstudio", "vllm", "custom")
_VALID_KINDS: tuple[str, ...] = ("local", "cloud")


@dataclass
class Connection:
    """A saved LLM endpoint the user can later activate as the active provider."""

    id: str
    name: str
    kind: str  # "local" | "cloud"
    api_url: str
    api_format: str = "openai"
    api_key: str = ""
    vendor_detected: str = ""
    models: list[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0


def _new_id() -> str:
    """8-char URL-safe id, enough for a list of thousands without collision."""
    return secrets.token_urlsafe(6)[:8]


def _ensure_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_raw(path: Path) -> dict:
    if not path.exists():
        return {"version": _SCHEMA_VERSION, "connections": []}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning("Could not read %s (%s) — starting from empty list", path, exc)
        return {"version": _SCHEMA_VERSION, "connections": []}


def _write_raw(path: Path, payload: dict) -> None:
    _ensure_path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    tmp.replace(path)


def _coerce_conn(raw: dict) -> Connection:
    """Build a Connection from raw JSON, ignoring unknown keys and clamping
    enums to known values so a hand-edited file can't crash the app.
    """
    allowed = set(Connection.__dataclass_fields__.keys())
    cleaned = {k: v for k, v in raw.items() if k in allowed}
    fmt = cleaned.get("api_format", "openai")
    if fmt not in _VALID_FORMATS:
        fmt = "openai"
    cleaned["api_format"] = fmt
    kind = cleaned.get("kind", "local")
    if kind not in _VALID_KINDS:
        kind = "local"
    cleaned["kind"] = kind
    if not isinstance(cleaned.get("models", []), list):
        cleaned["models"] = []
    return Connection(**cleaned)


class ConnectionsStore:
    """JSON-backed CRUD store for saved LLM connections."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _config_path()
        self._cache: list[Connection] | None = None

    # ── Internal ────────────────────────────────────────────────

    def _load(self) -> list[Connection]:
        if self._cache is not None:
            return self._cache
        raw = _read_raw(self._path)
        items = raw.get("connections", [])
        self._cache = [_coerce_conn(item) for item in items]
        return self._cache

    def _flush(self) -> None:
        if self._cache is None:
            return
        payload = {
            "version": _SCHEMA_VERSION,
            "connections": [asdict(c) for c in self._cache],
        }
        _write_raw(self._path, payload)

    def invalidate(self) -> None:
        self._cache = None

    # ── Public API ──────────────────────────────────────────────

    def list(self) -> list[Connection]:
        """Return a deep copy so callers can't mutate cached dataclasses."""
        return [copy.deepcopy(c) for c in self._load()]

    def get(self, conn_id: str) -> Connection | None:
        for c in self._load():
            if c.id == conn_id:
                return copy.deepcopy(c)
        return None

    def create(
        self,
        name: str,
        kind: str,
        api_url: str,
        api_format: str = "openai",
        api_key: str = "",
        vendor_detected: str = "",
        models: list[str] | None = None,
    ) -> Connection:
        if not name.strip():
            raise ValueError("name is required")
        if kind not in _VALID_KINDS:
            raise ValueError(f"kind must be one of {_VALID_KINDS}")
        if not api_url.strip():
            raise ValueError("api_url is required")
        if api_format not in _VALID_FORMATS:
            raise ValueError(f"api_format must be one of {_VALID_FORMATS}")
        now = time.time()
        conn = Connection(
            id=_new_id(),
            name=name.strip(),
            kind=kind,
            api_url=api_url.strip(),
            api_format=api_format,
            api_key=api_key,
            vendor_detected=vendor_detected,
            models=list(models or []),
            created_at=now,
            updated_at=now,
        )
        conns = self._load()
        conns.append(conn)
        self._flush()
        logger.info("Connection created: id=%s name=%s kind=%s", conn.id, conn.name, conn.kind)
        return copy.deepcopy(conn)

    def update(self, conn_id: str, patch: dict) -> Connection | None:
        conns = self._load()
        for idx, existing in enumerate(conns):
            if existing.id != conn_id:
                continue
            data = asdict(existing)
            for k, v in patch.items():
                if k in ("id", "created_at"):
                    continue  # immutable
                if k == "api_format" and v not in _VALID_FORMATS:
                    continue
                if k == "kind" and v not in _VALID_KINDS:
                    continue
                data[k] = v
            data["updated_at"] = time.time()
            updated = _coerce_conn(data)
            conns[idx] = updated
            self._flush()
            logger.info("Connection updated: id=%s", updated.id)
            return copy.deepcopy(updated)
        return None

    def delete(self, conn_id: str) -> bool:
        conns = self._load()
        next_list = [c for c in conns if c.id != conn_id]
        if len(next_list) == len(conns):
            return False
        self._cache = next_list
        self._flush()
        logger.info("Connection deleted: id=%s", conn_id)
        return True

    def set_models(self, conn_id: str, models: list[str]) -> Connection | None:
        return self.update(conn_id, {"models": list(models)})

    def set_vendor(self, conn_id: str, vendor: str) -> Connection | None:
        return self.update(conn_id, {"vendor_detected": vendor})
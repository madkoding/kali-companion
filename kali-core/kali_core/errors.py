"""Error categorization and sanitization for the kali-core.

Centralized place for:
- ErrorCategory: stable enum of error kinds (auth, rate_limit, server, etc.)
- CATEGORY_TO_I18N_KEY: maps categories to i18n keys the frontend can localize
- RETRYABLE: set of categories where a retry is meaningful
- redact_secrets(): removes API key prefixes and other secrets from any text
  before it is forwarded to the client or persisted in session history

Ponytail: a single helper for the whole codebase — no more ad-hoc str(exc)
that leaks API key prefixes like "sk-your-****here" to the user.
"""

from __future__ import annotations

import re
from enum import Enum


class ErrorCategory(str, Enum):
    AUTH = "auth"  # 401 invalid/expired API key
    BILLING = "billing"  # 403 billing/plan
    RATE_LIMIT = "rate_limit"  # 429
    NOT_FOUND = "not_found"  # 404 model
    BAD_REQUEST = "bad_request"  # 400
    CONTENT_FILTER = "content_filter"  # 422
    SERVER = "server"  # 5xx provider error
    NETWORK = "network"  # connection refused / timeout
    TOOL = "tool"  # tool execution failure
    CONFIG = "config"  # missing/invalid config
    INTERNAL = "internal"  # unexpected


CATEGORY_TO_I18N_KEY: dict[ErrorCategory, str] = {
    ErrorCategory.AUTH: "error.llm.invalid_key",
    ErrorCategory.BILLING: "error.llm.billing",
    ErrorCategory.RATE_LIMIT: "error.llm.rate_limit",
    ErrorCategory.NOT_FOUND: "error.llm.model_not_found",
    ErrorCategory.BAD_REQUEST: "error.llm.bad_request",
    ErrorCategory.CONTENT_FILTER: "error.llm.content_filter",
    ErrorCategory.SERVER: "error.llm.server_error",
    ErrorCategory.NETWORK: "error.llm.unreachable",
    ErrorCategory.TOOL: "error.tool.failed",
    ErrorCategory.CONFIG: "error.config.invalid",
    ErrorCategory.INTERNAL: "error.unknown",
}


RETRYABLE: frozenset[ErrorCategory] = frozenset(
    {ErrorCategory.RATE_LIMIT, ErrorCategory.SERVER, ErrorCategory.NETWORK}
)


# Patterns for secrets. Order matters: more specific patterns first.
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-or-v1-[A-Za-z0-9_-]+"), "sk-or-v1-…"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]+"), "Bearer …"),
    (re.compile(r"sk-[A-Za-z0-9*_\-]{8,}"), "sk-…"),
    (
        re.compile(r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9._\-]{8,}['\"]?"),
        "api_key=…",
    ),
]


_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def redact_secrets(text: str) -> str:
    """Remove API key prefixes and ANSI escape codes from text.

    Safe to call on any string before forwarding to the client or
    persisting in session history. Does not raise.
    """
    if not text:
        return text
    out = _ANSI_ESCAPE.sub("", text)
    for pattern, repl in _SECRET_PATTERNS:
        out = pattern.sub(repl, out)
    return out

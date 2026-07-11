"""Contract tests for kali_core.errors (Fase 0 helper)."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import openai

from kali_core.errors import (
    CATEGORY_TO_I18N_KEY,
    RETRYABLE,
    ErrorCategory,
    redact_secrets,
)


class TestRedactSecrets:
    def test_masks_sk_prefix(self) -> None:
        assert redact_secrets("sk-proj-abc123def456ghi789") == "sk-…"

    def test_masks_openrouter_prefix(self) -> None:
        assert redact_secrets("sk-or-v1-abc123def456") == "sk-or-v1-…"

    def test_masks_bearer_token(self) -> None:
        assert (
            redact_secrets("Authorization: Bearer abc123def456ghi789")
            == "Authorization: Bearer …"
        )

    def test_masks_api_key_param(self) -> None:
        assert (
            redact_secrets('api_key="abc123def456ghi789"')
            == "api_key=…"
        )

    def test_preserves_short_strings(self) -> None:
        # Short sk- strings (less than 8 chars after "sk-") are NOT masked
        # to avoid false positives like "sk-test" in error messages.
        assert redact_secrets("sk-test") == "sk-test"

    def test_strips_ansi_escape_codes(self) -> None:
        assert (
            redact_secrets("\x1b[31mError\x1b[0m in module")
            == "Error in module"
        )

    def test_handles_empty_string(self) -> None:
        assert redact_secrets("") == ""

    def test_handles_none_like(self) -> None:
        assert redact_secrets("") == ""
        assert redact_secrets("") == ""

    def test_does_not_mask_unrelated_strings(self) -> None:
        s = "Connection refused to localhost:8900"
        assert redact_secrets(s) == s

    def test_realistic_openai_error(self) -> None:
        # Simulates the actual str(AuthenticationError) output.
        s = (
            "Error code: 401 - {'error': {'message': 'Incorrect API key provided: "
            "sk-your-****here. You can find your API key at "
            "https://platform.openai.com/account/api-keys.', "
            "'type': 'invalid_request_error', 'code': 'invalid_api_key', "
            "'param': None}, 'status': 401}"
        )
        result = redact_secrets(s)
        assert "sk-…" in result
        assert "sk-your-****here" not in result
        assert "https://platform.openai.com" in result  # URLs are not secrets


class TestCategoryMapping:
    def test_all_categories_have_i18n_key(self) -> None:
        for cat in ErrorCategory:
            assert cat in CATEGORY_TO_I18N_KEY
            assert CATEGORY_TO_I18N_KEY[cat].startswith("error.")

    def test_retryable_is_subset(self) -> None:
        assert ErrorCategory.RATE_LIMIT in RETRYABLE
        assert ErrorCategory.SERVER in RETRYABLE
        assert ErrorCategory.NETWORK in RETRYABLE
        assert ErrorCategory.AUTH not in RETRYABLE
        assert ErrorCategory.BILLING not in RETRYABLE

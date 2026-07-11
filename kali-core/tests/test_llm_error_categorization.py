"""Contract tests for LLM error categorization in DirectLLMProvider (Fase 2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import openai

from kali_core.errors import ErrorCategory
from kali_core.mind.llm.direct import _categorize_llm_error


class TestCategorizeLlmError:
    def test_authentication_error_is_auth(self) -> None:
        exc = openai.AuthenticationError(
            message="Incorrect API key",
            response=MagicMock(status_code=401),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.AUTH

    def test_permission_denied_is_billing(self) -> None:
        exc = openai.PermissionDeniedError(
            message="Forbidden",
            response=MagicMock(status_code=403),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.BILLING

    def test_rate_limit_is_rate_limit(self) -> None:
        exc = openai.RateLimitError(
            message="Too many requests",
            response=MagicMock(status_code=429),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.RATE_LIMIT

    def test_not_found_is_not_found(self) -> None:
        exc = openai.NotFoundError(
            message="Model not found",
            response=MagicMock(status_code=404),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.NOT_FOUND

    def test_unprocessable_is_content_filter(self) -> None:
        exc = openai.UnprocessableEntityError(
            message="Content filter",
            response=MagicMock(status_code=422),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.CONTENT_FILTER

    def test_internal_server_error_is_server(self) -> None:
        exc = openai.InternalServerError(
            message="Server error",
            response=MagicMock(status_code=500),
            body={"error": {"message": "x", "type": "y", "code": "z", "param": None}},
        )
        assert _categorize_llm_error(exc) == ErrorCategory.SERVER

    def test_connection_error_is_network(self) -> None:
        exc = openai.APIConnectionError(request=MagicMock())
        assert _categorize_llm_error(exc) == ErrorCategory.NETWORK

    def test_timeout_error_is_network(self) -> None:
        exc = openai.APITimeoutError(request=MagicMock())
        assert _categorize_llm_error(exc) == ErrorCategory.NETWORK

    def test_generic_exception_falls_back_to_internal(self) -> None:
        assert _categorize_llm_error(ValueError("???")) == ErrorCategory.INTERNAL

    def test_context_length_in_message_is_bad_request(self) -> None:
        exc = ValueError("context_length exceeded")
        assert _categorize_llm_error(exc) == ErrorCategory.BAD_REQUEST

    def test_connection_in_message_is_network(self) -> None:
        exc = ValueError("connection refused")
        assert _categorize_llm_error(exc) == ErrorCategory.NETWORK

    def test_timeout_in_message_is_network(self) -> None:
        exc = ValueError("timeout while reading")
        assert _categorize_llm_error(exc) == ErrorCategory.NETWORK

    def test_httpx_connect_error_is_network(self) -> None:
        exc = httpx.ConnectError("refused")
        assert _categorize_llm_error(exc) == ErrorCategory.NETWORK

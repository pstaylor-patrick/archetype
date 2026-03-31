"""Tests for the LLM engine module — client creation and error handling."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from archetype.engine import MissingAPIKeyError, _get_client


class TestGetClient:
    def test_raises_missing_api_key_error_when_no_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingAPIKeyError, match="No API key found"):
                _get_client(api_key=None)

    def test_raises_missing_api_key_error_with_empty_string(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
            with pytest.raises(MissingAPIKeyError, match="No API key found"):
                _get_client(api_key=None)

    def test_creates_client_with_explicit_key(self) -> None:
        client = _get_client(api_key="test-key-123")
        assert client.api_key == "test-key-123"

    def test_creates_client_from_env_var(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key-456"}):
            client = _get_client(api_key=None)
            assert client.api_key == "env-key-456"

    def test_explicit_key_takes_precedence_over_env(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            client = _get_client(api_key="explicit-key")
            assert client.api_key == "explicit-key"


class TestMissingAPIKeyError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(MissingAPIKeyError, Exception)

    def test_carries_message(self) -> None:
        exc = MissingAPIKeyError("custom message")
        assert str(exc) == "custom message"

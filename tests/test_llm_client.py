"""Tests for app.llm_client — model selection, JSON validation, mocked summarize."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from app.models import LLMError

# ---------------------------------------------------------------------------
# select_model
# ---------------------------------------------------------------------------


class TestSelectModel:
    """Model tier selection logic."""

    def test_small_digest(self) -> None:
        from app.llm_client import select_model

        assert select_model(5_000) == "Meta/Llama-3.1-8B-Instruct"

    def test_medium_digest(self) -> None:
        from app.llm_client import select_model

        assert select_model(50_000) == "Qwen/Qwen3-32B"

    def test_large_digest(self) -> None:
        from app.llm_client import select_model

        assert select_model(100_000) == "Meta/Llama-3.3-70B-Instruct"

    def test_over_max_falls_back_to_largest(self) -> None:
        from app.llm_client import select_model

        assert select_model(200_000) == "Meta/Llama-3.3-70B-Instruct"

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEBIUS_MODEL", "custom-model")
        # Reimport to pick up env change
        import importlib

        import app.config

        importlib.reload(app.config)

        from app.llm_client import select_model

        assert select_model(5_000) == "custom-model"

        # Reset
        monkeypatch.delenv("NEBIUS_MODEL")
        importlib.reload(app.config)


# ---------------------------------------------------------------------------
# _parse_and_validate
# ---------------------------------------------------------------------------


class TestParseAndValidate:
    """JSON parsing and schema validation."""

    def test_valid_json(self) -> None:
        from app.llm_client import _parse_and_validate

        result = _parse_and_validate(
            '{"summary": "A lib", "technologies": ["Python"], "structure": "flat"}'
        )
        assert result is not None
        assert result["summary"] == "A lib"

    def test_invalid_json(self) -> None:
        from app.llm_client import _parse_and_validate

        assert _parse_and_validate("not json at all") is None

    def test_missing_keys(self) -> None:
        from app.llm_client import _parse_and_validate

        assert _parse_and_validate('{"summary": "A lib"}') is None

    def test_wrong_types(self) -> None:
        from app.llm_client import _parse_and_validate

        result = _parse_and_validate(
            '{"summary": 123, "technologies": "Python", "structure": "flat"}'
        )
        assert result is None


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------


class TestSummarize:
    """Mocked LLM calls."""

    async def test_success(self) -> None:
        from app.llm_client import summarize

        good_json = '{"summary": "A lib", "technologies": ["Python"], "structure": "flat"}'
        mock_choice = MagicMock()
        mock_choice.message.content = good_json
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.llm_client.AsyncOpenAI", return_value=mock_client):
            result = await summarize("some digest")
        assert result["summary"] == "A lib"

    async def test_retry_on_bad_first_response(self) -> None:
        from app.llm_client import summarize

        bad_choice = MagicMock()
        bad_choice.message.content = "not json"
        bad_response = MagicMock()
        bad_response.choices = [bad_choice]

        good_json = '{"summary": "OK", "technologies": ["Go"], "structure": "mono"}'
        good_choice = MagicMock()
        good_choice.message.content = good_json
        good_response = MagicMock()
        good_response.choices = [good_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[bad_response, good_response])

        with patch("app.llm_client.AsyncOpenAI", return_value=mock_client):
            result = await summarize("some digest")
        assert result["summary"] == "OK"

    async def test_raises_after_two_failures(self) -> None:
        from app.llm_client import summarize

        bad_choice = MagicMock()
        bad_choice.message.content = "not json"
        bad_response = MagicMock()
        bad_response.choices = [bad_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=bad_response)

        with patch("app.llm_client.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(LLMError):
                await summarize("some digest")

    async def test_openai_api_error_raises_llm_error(self) -> None:
        from app.llm_client import summarize

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIError(
                message="Service unavailable",
                request=MagicMock(),
                body=None,
            )
        )

        with patch("app.llm_client.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(LLMError, match="LLM provider error"):
                await summarize("some digest")

    async def test_empty_choices_raises_llm_error(self) -> None:
        from app.llm_client import summarize

        mock_response = MagicMock()
        mock_response.choices = []

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.llm_client.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(LLMError, match="no response choices"):
                await summarize("some digest")

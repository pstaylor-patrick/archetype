"""Tests for LLM response parsing logic."""

from __future__ import annotations

import pytest

from archetype.parsing import extract_json_text


class TestExtractJsonText:
    def test_plain_json(self) -> None:
        raw = '{"key": "value"}'
        assert extract_json_text(raw) == '{"key": "value"}'

    def test_strips_whitespace(self) -> None:
        raw = '  \n  {"key": "value"}  \n  '
        assert extract_json_text(raw) == '{"key": "value"}'

    def test_strips_json_fences(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        assert extract_json_text(raw) == '{"key": "value"}'

    def test_strips_plain_fences(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        assert extract_json_text(raw) == '{"key": "value"}'

    def test_preserves_multiline_json_in_fences(self) -> None:
        raw = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        result = extract_json_text(raw)
        assert result == '{\n  "a": 1,\n  "b": 2\n}'

    def test_no_fences_returns_stripped(self) -> None:
        raw = '  {"items": [1, 2, 3]}  '
        assert extract_json_text(raw) == '{"items": [1, 2, 3]}'

    def test_fences_with_surrounding_whitespace(self) -> None:
        raw = '  \n```json\n{"x": 1}\n```\n  '
        assert extract_json_text(raw) == '{"x": 1}'

    def test_empty_string(self) -> None:
        assert extract_json_text("") == ""

    def test_only_fences_no_content(self) -> None:
        raw = "```json\n```"
        assert extract_json_text(raw) == ""

    def test_incomplete_closing_fence(self) -> None:
        raw = '```json\n{"key": "value"}\nsome text'
        result = extract_json_text(raw)
        assert result == '{"key": "value"}\nsome text'

    def test_backticks_in_middle_not_treated_as_fence(self) -> None:
        raw = '{"code": "use ```triple``` backticks"}'
        assert extract_json_text(raw) == '{"code": "use ```triple``` backticks"}'

    @pytest.mark.parametrize(
        "fence_lang",
        ["```json", "```JSON", "```javascript", "```"],
    )
    def test_various_fence_languages(self, fence_lang: str) -> None:
        raw = f'{fence_lang}\n{{"val": 42}}\n```'
        assert extract_json_text(raw) == '{"val": 42}'

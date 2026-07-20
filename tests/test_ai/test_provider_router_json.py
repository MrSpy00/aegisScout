"""Tests for ProviderRouter.extract_json helper used by chat_json and chat_outreach_message."""
import pytest
from aegisScout.ai.provider_router import extract_json, ProviderParseError


class TestExtractJson:
    """Robust JSON extraction from LLM responses (markdown-wrapped, conversational, malformed)."""

    def test_plain_json(self):
        text = '{"analysis": "ok", "opening_message": "hi"}'
        result = extract_json(text)
        assert result == {"analysis": "ok", "opening_message": "hi"}

    def test_markdown_fenced_json(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_markdown_fenced_no_lang(self):
        text = '```\n{"k": 1}\n```'
        result = extract_json(text)
        assert result == {"k": 1}

    def test_conversational_wrapper(self):
        text = 'Sure! Here is the result: {"analysis": "ok", "opening_message": "Hi!"}'
        result = extract_json(text)
        assert result["analysis"] == "ok"

    def test_nested_braces(self):
        text = '```json\n{"a": {"b": {"c": 1}}, "d": [1,2,3]}\n```'
        result = extract_json(text)
        assert result["a"]["b"]["c"] == 1
        assert result["d"] == [1, 2, 3]

    def test_top_level_array(self):
        text = '[{"x": 1}, {"y": 2}]'
        result = extract_json(text)
        assert isinstance(result, list)
        assert result[0]["x"] == 1

    def test_fenced_array(self):
        text = '```json\n[1, 2, 3]\n```'
        result = extract_json(text)
        assert result == [1, 2, 3]

    def test_malformed_raises_with_truncated_raw(self):
        text = "This is not JSON at all, just plain text from a confused LLM."
        with pytest.raises(ProviderParseError) as exc:
            extract_json(text)
        # Raw must be in error but truncated
        assert "This is not JSON" in str(exc.value)
        # Ensure no prompt-like content (should not be huge)
        assert len(str(exc.value)) < 2000

    def test_unbalanced_braces_raises(self):
        text = '{"key": "value", "unclosed": "nope'  # no closing brace
        with pytest.raises(ProviderParseError):
            extract_json(text)

    def test_empty_raises(self):
        with pytest.raises(ProviderParseError):
            extract_json("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ProviderParseError):
            extract_json("   \n\t  ")

    def test_extra_whitespace_around_json(self):
        text = '\n\n  {"a": 1}  \n\n'
        result = extract_json(text)
        assert result == {"a": 1}

    def test_returns_list_for_top_level_array(self):
        text = '```json\n[{"a": 1}]\n```'
        result = extract_json(text)
        assert isinstance(result, list)

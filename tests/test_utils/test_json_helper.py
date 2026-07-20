import pytest
from aegisScout.utils.json_helper import extract_json


class TestExtractJson:
    """
    json_helper.extract_json icin cesitli format senaryolari.
    """

    def test_clean_json(self):
        text = '{"analysis": "good", "opening_message": "Merhaba!"}'
        result = extract_json(text)
        assert result["analysis"] == "good"
        assert result["opening_message"] == "Merhaba!"

    def test_markdown_fenced_json(self):
        text = '`json\n{"key": "value"}\n`'
        result = extract_json(text)
        assert result["key"] == "value"

    def test_markdown_fenced_no_lang(self):
        text = '`\n{"key": "value"}\n`'
        result = extract_json(text)
        assert result["key"] == "value"

    def test_json_wrapped_in_text(self):
        text = 'Sure! Here is the result: {"analysis": "ok", "opening_message": "Hi!"}'
        result = extract_json(text)
        assert result["analysis"] == "ok"

    def test_json_with_nested_objects(self):
        text = '{"outer": {"inner": 42}}'
        result = extract_json(text)
        assert result["outer"]["inner"] == 42

    def test_no_json_raises_value_error(self):
        with pytest.raises(ValueError, match="No valid JSON"):
            extract_json("Bu bir JSON degil, sadece metin.")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            extract_json("")

    def test_extra_whitespace_and_newlines(self):
        text = "\n\n  {\"a\": 1}  \n\n"
        result = extract_json(text)
        assert result["a"] == 1

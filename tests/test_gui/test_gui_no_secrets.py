"""
GUI security tests.

The audit found that `get_settings()` was leaking every API key, password
and token to the PyWebView JS bridge. This test enforces the new contract:
the JS bridge MUST NOT return any substring that resembles a key, password
or token value.
"""

import json
import re
try:
    import tomllib as toml_module
except ImportError:
    import toml as toml_module
import pytest


def test_gui_is_configured_does_not_leak_secrets(monkeypatch):
    """
    GuiApi.is_configured() (and the backward-compat get_settings()) must
    NEVER return API keys, passwords, or tokens.
    """
    from aegisScout.gui import GuiApi
    from aegisScout.core.config import settings

    # Plant some recognizable fake secrets in settings (simulating real .env)
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-fake-deepseek-AAAA-BBBB-CCCC", raising=False)
    monkeypatch.setattr(settings, "openai_api_key", "sk-fakeopenai-XXXX-YYYY-ZZZZ", raising=False)
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-fakeANTHROPIC-DDDD-EEEE", raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaFakeGEMINI-FFFF-GGGG", raising=False)
    monkeypatch.setattr(settings, "groq_api_key", "gsk_fakeGROQ-HHHH", raising=False)
    monkeypatch.setattr(settings, "mistral_api_key", "ms-fake-mistral", raising=False)
    monkeypatch.setattr(settings, "instagram_password", "super-secret-IG-password", raising=False)
    monkeypatch.setattr(settings, "telegram_bot_token", "1234567890:AAFakeTELEGRAM", raising=False)
    monkeypatch.setattr(settings, "notify_email_password", "email-pass-XYZ", raising=False)
    monkeypatch.setattr(settings, "instagram_session_encryption_key", "FernetKEY12345==", raising=False)
    monkeypatch.setattr(settings, "google_places_api_key", "AIzaFakeGOOGLE-Places", raising=False)
    monkeypatch.setattr(settings, "google_custom_search_api_key", "GOOGLE-CSE-FAKE", raising=False)
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or-fakeOPENROUTER", raising=False)

    api = GuiApi()
    snapshot = api.is_configured()
    # Backward compat alias must return the SAME sanitized shape
    legacy = api.get_settings()

    # Serialize both to JSON for substring scanning
    snapshot_text = json.dumps(snapshot, default=str).lower()
    legacy_text = json.dumps(legacy, default=str).lower()

    forbidden_substrings = [
        "sk-fake-deepseek",
        "sk-fakeopenai",
        "sk-ant-fakeanthropic",
        "aizafakegemini",
        "gsk_fakegroq",
        "ms-fake-mistral",
        "super-secret-ig-password",
        "aafaketelegram",
        "email-pass-xyz",
        "fernetkey12345",
        "aizafakegoogle-places",
        "google-cse-fake",
        "sk-or-fakeopenrouter",
    ]
    for needle in forbidden_substrings:
        assert needle not in snapshot_text, (
            f"is_configured() LEAKED secret: {needle!r}\nFull payload: {snapshot}"
        )
        assert needle not in legacy_text, (
            f"get_settings() (backward compat) LEAKED secret: {needle!r}\n"
            f"Full payload: {legacy}"
        )

    # Structural assertions: only booleans in `configured` sub-dict
    assert "configured" in snapshot
    for k, v in snapshot["configured"].items():
        assert isinstance(v, bool), (
            f"configured.{k} must be bool, got {type(v).__name__}: {v!r}"
        )

    # Top-level safe fields exist
    for k in (
        "llm_primary_provider",
        "llm_fallback_provider",
        "discovery_primary_provider",
        "outreach_mode",
        "max_daily_outreach",
        "mod_b_acknowledged",
        "automation_authorized",
    ):
        assert k in snapshot, f"Missing expected key: {k}"


def test_gui_save_settings_accepts_secret_keys():
    """
    When the user enters secret API keys in Settings, save_settings must accept them
    and save them directly to .env with success: True.
    """
    from aegisScout.gui import GuiApi

    api = GuiApi()
    payload = {
        "deepseek_api_key": "sk-leak",
        "openai_api_key": "sk-leak2",
        "llm_primary_provider": "openai",
    }
    result = api.save_settings(payload)
    assert result.get("success") is True
    applied_keys = [item["key"] for item in result.get("applied", [])]
    assert "deepseek_api_key" in applied_keys
    assert "openai_api_key" in applied_keys


def test_gui_set_config_value_writes_toml_non_sensitive():
    """
    set_config_value('outreach.tone', 'casual') should succeed and write to
    config.toml. (Test uses tmp config to avoid polluting the user's real one.)
    """
    from aegisScout.gui import GuiApi
    import aegisScout.gui as gui_module
    from aegisScout.core import toml_config
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        cfg_dir = Path(tmp) / "config"
        cfg_dir.mkdir()
        cfg_file = cfg_dir / "config.toml"
        cfg_file.write_text('[outreach]\nlanguage = "tr"\n', encoding="utf-8")

        # Patch CONFIG_FILE and toml_config.config_data to point at tmp
        orig_config_file = toml_config.CONFIG_FILE
        orig_config_data = dict(toml_config.config_data)
        toml_config.CONFIG_FILE = cfg_file
        with open(toml_config.CONFIG_FILE, "rb") as f:
            toml_config.config_data = toml_module.load(f)
        try:
            api = GuiApi()
            res = api.set_config_value("outreach.tone", "casual")
            assert res.get("success") is True, res
            assert res.get("target") == "config.toml"
            # Reload to verify persistence
            with open(cfg_file, "rb") as f:
                reloaded = toml_module.load(f)
            assert reloaded["outreach"]["tone"] == "casual"
        finally:
            toml_config.CONFIG_FILE = orig_config_file
            toml_config.config_data = orig_config_data

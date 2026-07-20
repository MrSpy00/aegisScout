"""
T12 SMTP timeout tests:
- smtplib.SMTP() called with timeout=15s default
- timeout sourced from env NOTIFY_SMTP_TIMEOUT
- timeout threaded through to .login() and .starttls() (i.e. None for those is OK,
  we focus on the connect timeout which is the only one that prevents hangs)
"""
import os
from unittest.mock import patch, MagicMock

import pytest

from aegisScout.monitoring.notifier import Notifier


def _settings():
    s = MagicMock()
    s.telegram_bot_token = "FAKE_BOT_TOKEN"
    s.telegram_chat_id = "FAKE_CHAT_ID"
    s.notify_email_smtp_host = "smtp.fake.com"
    s.notify_email_smtp_port = 587
    s.notify_email_username = "sender@x.com"
    s.notify_email_password = "fake"
    s.notify_email_recipient = "owner@x.com"
    s.notify_smtp_timeout = 15
    return s


class TestSmtpTimeout:
    @patch("smtplib.SMTP")
    def test_default_smtp_timeout_is_15(self, mock_smtp_class):
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        with patch("aegisScout.monitoring.notifier.settings", _settings()):
            notifier = Notifier()
            notifier.send_email("S", "B", to="owner@x.com")

        # The first positional arg of SMTP() is host, second is port, third is timeout
        assert mock_smtp_class.called, "smtplib.SMTP was never called"
        call = mock_smtp_class.call_args
        # Accept both signatures: SMTP(host, port, timeout=...) or positional
        timeout_value = None
        if "timeout" in call.kwargs:
            timeout_value = call.kwargs["timeout"]
        elif len(call.args) >= 3:
            timeout_value = call.args[2]
        assert timeout_value == 15, (
            f"smtplib.SMTP must be called with timeout=15, got {timeout_value!r}"
        )

    @patch("smtplib.SMTP")
    def test_smtp_timeout_overridable_via_env(self, mock_smtp_class, monkeypatch):
        monkeypatch.setenv("NOTIFY_SMTP_TIMEOUT", "7")
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        # settings.notify_smtp_timeout returns default 15 from env if not set
        # But the explicit env var should win if we wire NOTIFY_SMTP_TIMEOUT
        # via the settings class — since we don't modify settings, the
        # notifier must read it from os.environ as a fallback.
        s = _settings()
        # settings has no notify_smtp_timeout set in test (None)
        s.notify_smtp_timeout = None
        with patch("aegisScout.monitoring.notifier.settings", s):
            notifier = Notifier()
            notifier.send_email("S", "B", to="owner@x.com")

        call = mock_smtp_class.call_args
        timeout_value = call.kwargs.get("timeout") or (
            call.args[2] if len(call.args) >= 3 else None
        )
        assert timeout_value == 7, (
            f"NOTIFY_SMTP_TIMEOUT env var must propagate, got {timeout_value!r}"
        )

    @patch("smtplib.SMTP")
    def test_smtp_starttls_and_login_called(self, mock_smtp_class):
        """Regression: existing flow must still hold under timeout fix."""
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        with patch("aegisScout.monitoring.notifier.settings", _settings()):
            notifier = Notifier()
            notifier.send_email("S", "B", to="owner@x.com")

        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("sender@x.com", "fake")
        smtp_instance.sendmail.assert_called_once()
        smtp_instance.quit.assert_called_once()

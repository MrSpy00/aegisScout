"""
T12 notifier channel tests:
- 3-channel dispatch: telegram + email + instagram_dm
- async non-blocking (dispatched via asyncio.to_thread)
- email To=recipient, NOT smtp_user
- instagram_dm dry-run default (returns True, logs DRY RUN)

These tests are FAILING RED at the time of writing — notifier.py still:
- sends email To=self
- has no send_instagram_dm
- calls send_email() synchronously from notify_all
"""
import asyncio
import os
import threading
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import respx
import httpx

from aegisScout.monitoring.notifier import Notifier


def _make_settings(
    *,
    smtp_user: str = "sender@aegisscout.local",
    recipient: str | None = None,
    timeout: int | None = None,
    mod_b_acknowledged: bool = False,
    instagram_dry_run: bool = True,
):
    s = MagicMock()
    s.telegram_bot_token = "FAKE_BOT_TOKEN"
    s.telegram_chat_id = "FAKE_CHAT_ID"
    s.notify_email_smtp_host = "smtp.fake.com"
    s.notify_email_smtp_port = 587
    s.notify_email_username = smtp_user
    s.notify_email_password = "fake_password"
    # The new attributes (settings may or may not have them — get-or-default pattern)
    s.notify_email_recipient = recipient
    s.notify_smtp_timeout = timeout
    s.mod_b_acknowledged = mod_b_acknowledged
    s.instagram_dry_run = instagram_dry_run
    return s


class TestNotifierChannels:
    """3-channel dispatch: telegram + email + instagram_dm."""

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_notify_all_dispatches_three_channels(self, mock_smtp_class):
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        s = _make_settings(recipient="owner@aegisscout.local")
        with patch("aegisScout.monitoring.notifier.settings", s):
            with respx.mock:
                respx.post(
                    "https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage"
                ).mock(return_value=httpx.Response(200, json={"ok": True}))
                notifier = Notifier()
                result = await notifier.notify_all(
                    "Subject Line", "Body line 1\nBody line 2"
                )

        # Email path was hit
        smtp_instance.sendmail.assert_called_once()
        # Returns per-channel dict
        assert isinstance(result, dict)
        assert "telegram" in result
        assert "email" in result
        assert "instagram_dm" in result
        # Each entry is bool
        for v in result.values():
            assert isinstance(v, bool)

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_email_recipient_is_not_smtp_user(self, mock_smtp_class):
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        s = _make_settings(
            smtp_user="sender@aegisscout.local",
            recipient="owner@elsewhere.com",
        )
        with patch("aegisScout.monitoring.notifier.settings", s):
            with respx.mock:
                respx.post(
                    "https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage"
                ).mock(return_value=httpx.Response(200, json={"ok": True}))
                notifier = Notifier()
                await notifier.notify_all("S", "B")

        # Verify sendmail was called with recipient as one of the to_addrs
        call_args = smtp_instance.sendmail.call_args
        # sendmail(from_addr, to_addrs, msg)
        assert call_args is not None
        from_addr = call_args.args[0]
        to_addrs = call_args.args[1]
        assert from_addr == "sender@aegisscout.local"
        # CRITICAL: the recipient must NOT be the smtp user
        assert "owner@elsewhere.com" in to_addrs
        assert "sender@aegisscout.local" not in to_addrs

    @pytest.mark.asyncio
    async def test_instagram_dm_dry_run_default_returns_true(self):
        """No acknowledged, no dry_run flag — must be safe dry-run default."""
        s = _make_settings(
            mod_b_acknowledged=False,
            instagram_dry_run=True,  # explicit
        )
        with patch("aegisScout.monitoring.notifier.settings", s):
            notifier = Notifier()
            result = await notifier.send_instagram_dm("some_user", "hello")

        assert result is True

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_email_dispatch_runs_in_thread(self, mock_smtp_class):
        """The smtp sendmail call must NOT be on the asyncio main thread."""
        smtp_instance = MagicMock()
        mock_smtp_class.return_value = smtp_instance

        main_thread = threading.current_thread().name
        smtp_thread_holder: dict[str, str] = {}

        original_sendmail = smtp_instance.sendmail

        def capture_thread(*args, **kwargs):
            smtp_thread_holder["name"] = threading.current_thread().name
            return original_sendmail(*args, **kwargs)

        smtp_instance.sendmail.side_effect = capture_thread

        s = _make_settings(recipient="owner@aegisscout.local")
        with patch("aegisScout.monitoring.notifier.settings", s):
            with respx.mock:
                respx.post(
                    "https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage"
                ).mock(return_value=httpx.Response(200, json={"ok": True}))
                notifier = Notifier()
                await notifier.notify_all("S", "B")

        assert smtp_thread_holder.get("name") != main_thread, (
            f"smtp sendmail ran on main thread ({main_thread}); "
            f"expected a worker thread. Off-thread dispatch broken."
        )

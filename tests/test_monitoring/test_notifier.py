import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock
from aegisScout.monitoring.notifier import Notifier


class TestNotifier:
    """
    Notifier modulu (Telegram ve SMTP Email) testleri.
    """

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        with patch("aegisScout.monitoring.notifier.settings") as mock_cfg:
            mock_cfg.telegram_bot_token = "FAKE_BOT_TOKEN"
            mock_cfg.telegram_chat_id = "FAKE_CHAT_ID"
            mock_cfg.notify_email_smtp_host = "smtp.fake.com"
            mock_cfg.notify_email_smtp_port = 587
            mock_cfg.notify_email_username = "user@fake.com"
            mock_cfg.notify_email_password = "fake_password"
            mock_cfg.notify_email_recipient = "owner@fake.com"
            mock_cfg.notify_smtp_timeout = 15
            mock_cfg.mod_b_acknowledged = False
            mock_cfg.instagram_dry_run = True
            yield mock_cfg

    @pytest.mark.asyncio
    async def test_send_telegram_success(self):
        notifier = Notifier()

        with respx.mock:
            respx.post("https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )

            success = await notifier.send_telegram("Merhaba")

        assert success is True

    @pytest.mark.asyncio
    async def test_send_telegram_failure(self):
        notifier = Notifier()

        with respx.mock:
            respx.post("https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage").mock(
                return_value=httpx.Response(400, text="Bad Request")
            )

            success = await notifier.send_telegram("Merhaba")

        assert success is False

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class):
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        notifier = Notifier()
        success = notifier.send_email("Konu", "<h2>Icerik</h2>", to="owner@fake.com")

        assert success is True
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("user@fake.com", "fake_password")
        mock_smtp_instance.sendmail.assert_called_once()
        mock_smtp_instance.quit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_failure(self, mock_smtp_class):
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.login.side_effect = Exception("SMTP login failed")
        mock_smtp_class.return_value = mock_smtp_instance

        notifier = Notifier()
        success = notifier.send_email("Konu", "<h2>Icerik</h2>", to="owner@fake.com")

        assert success is False

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_notify_all(self, mock_smtp_class):
        mock_smtp_instance = MagicMock()
        mock_smtp_class.return_value = mock_smtp_instance

        notifier = Notifier()

        with respx.mock:
            respx.post("https://api.telegram.org/botFAKE_BOT_TOKEN/sendMessage").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )

            result = await notifier.notify_all("Title", "Body Line 1\nLine 2")

        mock_smtp_instance.sendmail.assert_called_once()
        assert isinstance(result, dict)
        assert "telegram" in result and "email" in result and "instagram_dm" in result

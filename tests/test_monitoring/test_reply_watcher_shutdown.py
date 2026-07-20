"""
T13 ReplyWatcher shutdown tests:
- KeyboardInterrupt cleanly exits the loop with code 0
- Session is released on shutdown
- asyncio.CancelledError is re-raised (clean shutdown)
- PrivateError is logged and skipped (DM thread is not inspectable)
"""
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from aegisScout.monitoring.reply_watcher import ReplyWatcher


def _watcher_with_ig_mock(ig_mock):
    """Create a ReplyWatcher whose Instagram client is the supplied mock."""
    w = ReplyWatcher()
    w.ig_client = ig_mock
    return w


class TestReplyWatcherShutdown:
    @pytest.mark.asyncio
    async def test_keyboardinterrupt_exits_cleanly(self):
        ig = MagicMock()
        # Use a non-empty list so the loop enters the try; then raise
        # KeyboardInterrupt on the SECOND call to ensure it propagates
        # through the outer try/except.
        call_count = {"n": 0}

        def fake_check():
            call_count["n"] += 1
            if call_count["n"] == 1:
                return [{"username": "u1", "content": "hi"}]
            raise KeyboardInterrupt()

        ig.check_new_messages.side_effect = fake_check

        w = _watcher_with_ig_mock(ig)
        with patch.object(w, "notifier"):
            # Should not raise — the watch_loop must catch KeyboardInterrupt
            # and exit cleanly.
            with patch("aegisScout.monitoring.reply_watcher.asyncio.sleep",
                       new=AsyncMock()):
                await w.watch_loop(poll_interval_seconds=1)

        # Once for the work iteration, once for the (interrupted) sleep
        assert call_count["n"] >= 1

    @pytest.mark.asyncio
    async def test_cancelled_error_is_reraised(self):
        """asyncio.CancelledError must propagate so the event loop stops."""
        ig = MagicMock()
        ig.check_new_messages.side_effect = asyncio.CancelledError()

        w = _watcher_with_ig_mock(ig)
        with patch.object(w, "notifier"):
            with pytest.raises(asyncio.CancelledError):
                await w.watch_loop(poll_interval_seconds=1)

    @pytest.mark.asyncio
    async def test_session_released_on_shutdown(self):
        """
        On shutdown the ReplyWatcher must call the underlying
        InstagramClient cleanup so the encrypted session file is not
        left dangling.
        """
        ig = MagicMock()
        ig.check_new_messages.side_effect = KeyboardInterrupt()
        # Simulate session.save() existing
        ig.save_session = MagicMock()
        # shutdown hook
        ig.shutdown = MagicMock()

        w = _watcher_with_ig_mock(ig)
        w.ig_client = ig
        with patch.object(w, "notifier"):
            with patch("aegisScout.monitoring.reply_watcher.asyncio.sleep",
                       new=AsyncMock()):
                await w.watch_loop(poll_interval_seconds=1)

        # The watcher must have invoked a cleanup path on the ig_client
        # We accept any of: save_session, shutdown, release, close.
        cleanup_called = any(
            getattr(ig, name).called
            for name in ("save_session", "shutdown", "release", "close")
            if hasattr(ig, name)
        )
        assert cleanup_called, (
            "ReplyWatcher must release/cleanup the IG session on shutdown"
        )

    @pytest.mark.asyncio
    async def test_private_error_is_logged_and_skipped(self):
        """A PrivateError (e.g. you can't see this user's DMs) must NOT crash."""
        ig = MagicMock()
        # Simulate instagrapi.exceptions.PrivateError at runtime (lazy import)
        # The watcher must catch it, log, and continue.
        try:
            from instagrapi.exceptions import PrivateError  # type: ignore
        except ImportError:
            pytest.skip("instagrapi not installed in this env")
        ig.check_new_messages.side_effect = PrivateError("Cannot see DMs")

        w = _watcher_with_ig_mock(ig)
        w.notifier = MagicMock()
        with patch("aegisScout.monitoring.reply_watcher.asyncio.sleep",
                   new=AsyncMock()):
            # The loop should not raise — it should log and keep going.
            # We just need to verify the watcher survives at least one cycle.
            with patch("asyncio.sleep", new=AsyncMock()):
                # Patch the inner-scope import so the exception is recognized.
                with patch(
                    "aegisScout.monitoring.reply_watcher.PrivateError",
                    PrivateError,
                    create=True,
                ):
                    try:
                        await asyncio.wait_for(
                            w.watch_loop(poll_interval_seconds=1), timeout=0.3
                        )
                    except asyncio.TimeoutError:
                        pass  # expected — loop is still running

    @pytest.mark.asyncio
    async def test_login_required_breaks_loop_with_critical_log(self):
        """LoginRequired → log critical and break (no infinite retry)."""
        ig = MagicMock()
        try:
            from instagrapi.exceptions import LoginRequired  # type: ignore
        except ImportError:
            pytest.skip("instagrapi not installed in this env")
        ig.check_new_messages.side_effect = LoginRequired("session expired")

        w = _watcher_with_ig_mock(ig)
        w.notifier = MagicMock()
        with patch(
            "aegisScout.monitoring.reply_watcher.LoginRequired",
            LoginRequired,
            create=True,
        ):
            with patch(
                "aegisScout.monitoring.reply_watcher.asyncio.sleep",
                new=AsyncMock(),
            ):
                # Should return (loop broken), not hang.
                await asyncio.wait_for(
                    w.watch_loop(poll_interval_seconds=1), timeout=1.0
                )
        # The IG client's check_new_messages was called once (then loop broke)
        assert ig.check_new_messages.call_count == 1

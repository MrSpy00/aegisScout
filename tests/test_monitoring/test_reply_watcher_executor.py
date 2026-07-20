"""
T13 ReplyWatcher executor test:
- check_new_messages() (sync, blocking) is dispatched in a thread executor
  by the watch_loop, NOT on the asyncio main thread.
"""
import asyncio
import threading
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from aegisScout.monitoring.reply_watcher import ReplyWatcher


class TestReplyWatcherExecutor:
    @pytest.mark.asyncio
    async def test_check_new_messages_runs_in_executor(self):
        ig = MagicMock()
        main_thread = threading.current_thread().name
        observed: dict[str, str] = {}

        def fake_check():
            observed["name"] = threading.current_thread().name
            return []  # no new messages, loop will sleep then re-check

        ig.check_new_messages.side_effect = fake_check

        w = ReplyWatcher()
        w.ig_client = ig
        w.notifier = MagicMock()

        with patch(
            "aegisScout.monitoring.reply_watcher.asyncio.sleep",
            new=AsyncMock(side_effect=KeyboardInterrupt),
        ):
            try:
                await w.watch_loop(poll_interval_seconds=1)
            except KeyboardInterrupt:
                pass

        # The check must NOT have run on the asyncio main thread
        assert "name" in observed, "check_new_messages was never called"
        assert observed["name"] != main_thread, (
            f"check_new_messages ran on main thread ({main_thread}); "
            f"expected a worker thread. Sync I/O not off-loaded to executor."
        )

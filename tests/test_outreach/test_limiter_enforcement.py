import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestRateLimiterEnforcement:
    """
    Rate Limiter enforcement testleri.
    DB sorgusu mock'lanarak gunluk/saatlik limit kontrolu test edilir.
    """

    def test_daily_limit_not_exceeded(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=5):
            can, remaining = limiter.check_daily_limit()
        assert can is True
        assert remaining == limiter.daily_limit - 5

    def test_daily_limit_exactly_at_limit(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=limiter.daily_limit):
            can, remaining = limiter.check_daily_limit()
        assert can is False
        assert remaining == 0

    def test_hourly_limit_not_exceeded(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=2):
            can, remaining = limiter.check_hourly_limit()
        assert can is True
        assert remaining == limiter.hourly_limit - 2

    def test_hourly_limit_exceeded(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=limiter.hourly_limit):
            can, remaining = limiter.check_hourly_limit()
        assert can is False
        assert remaining == 0

    def test_can_send_both_ok(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=1):
            ok, reason = limiter.can_send()
        assert ok is True
        assert reason == ""

    def test_can_send_daily_blocked(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()

        with patch.object(limiter, "_count_sends_since", return_value=limiter.daily_limit):
            ok, reason = limiter.can_send()
        assert ok is False
        assert "gunluk" in reason.lower() or "limit" in reason.lower()

    def test_config_defaults(self):
        from aegisScout.outreach.rate_limiter import RateLimiter
        limiter = RateLimiter()
        assert limiter.daily_limit == 15
        assert limiter.hourly_limit == 5
        assert limiter.min_delay == 3
        assert limiter.max_delay == 8

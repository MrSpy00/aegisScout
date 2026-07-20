import pytest
from aegisScout.outreach.rate_limiter import RateLimiter

def test_rate_limiter_pacing():
    limiter = RateLimiter()
    # Check if limits loaded correctly
    assert limiter.daily_limit == 15
    assert limiter.hourly_limit == 5
    assert limiter.min_delay == 3
    assert limiter.max_delay == 8

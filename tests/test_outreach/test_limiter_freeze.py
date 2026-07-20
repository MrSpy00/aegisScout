from unittest.mock import patch
from datetime import datetime
from aegisScout.outreach.rate_limiter import RateLimiter
from aegisScout.core.models import ActivityLog
from aegisScout.core.database import init_db, engine
from sqlmodel import Session, select

def test_limiter_daily_and_hourly_with_mocked_time():
    init_db(engine)
    
    # Pre-test cleanup
    with Session(engine) as session:
        for log in session.exec(select(ActivityLog)).all():
            session.delete(log)
        session.commit()
        
    limiter = RateLimiter()
    
    # 1. Manually insert activity logs with explicit timestamps
    # Log 1: 2026-07-11 12:00:00
    # Log 2: 2026-07-11 12:30:00
    with Session(engine) as session:
        log1 = ActivityLog(action="instagram_send", timestamp=datetime(2026, 7, 11, 12, 0, 0))
        log2 = ActivityLog(action="instagram_send", timestamp=datetime(2026, 7, 11, 12, 30, 0))
        session.add(log1)
        session.add(log2)
        session.commit()

    # 2. Test at 2026-07-11 12:45:00 (both logs should be counted in daily and hourly)
    frozen_now = datetime(2026, 7, 11, 12, 45, 0)
    
    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            return frozen_now.replace(tzinfo=tz) if tz else frozen_now
            
    with patch("aegisScout.outreach.rate_limiter.datetime", MockDatetime):
        daily_ok, daily_rem = limiter.check_daily_limit()
        assert daily_rem == limiter.daily_limit - 2
        
        hourly_ok, hourly_rem = limiter.check_hourly_limit()
        assert hourly_rem == limiter.hourly_limit - 2

    # 3. Test at 2026-07-11 13:31:00 (both logs should be counted in daily, but hourly count should be 0)
    frozen_now = datetime(2026, 7, 11, 13, 31, 0)
    with patch("aegisScout.outreach.rate_limiter.datetime", MockDatetime):
        daily_ok, daily_rem = limiter.check_daily_limit()
        assert daily_rem == limiter.daily_limit - 2
        
        hourly_ok, hourly_rem = limiter.check_hourly_limit()
        assert hourly_rem == limiter.hourly_limit

    # 4. Test at 2026-07-12 00:05:00 (next day: daily and hourly count should both be 0)
    frozen_now = datetime(2026, 7, 12, 0, 5, 0)
    with patch("aegisScout.outreach.rate_limiter.datetime", MockDatetime):
        daily_ok, daily_rem = limiter.check_daily_limit()
        assert daily_rem == limiter.daily_limit
        
        hourly_ok, hourly_rem = limiter.check_hourly_limit()
        assert hourly_rem == limiter.hourly_limit

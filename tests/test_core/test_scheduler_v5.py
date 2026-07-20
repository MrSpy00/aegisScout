"""
Tests for AegisScheduler and High-Score Lead Alerts.
"""
import pytest
import asyncio
from aegisScout.core.scheduler import AegisScheduler
from aegisScout.core.models import Lead


@pytest.mark.asyncio
async def test_scheduler_lifecycle_and_alerts():
    scheduler = AegisScheduler(interval_seconds=1)

    jobs_executed = []

    def mock_discovery_job():
        jobs_executed.append(True)
        return [
            Lead(id=1, business_name="Top Lead", score=95.0),
            Lead(id=2, business_name="Low Lead", score=40.0),
        ]

    scheduler.start(mock_discovery_job, min_alert_score=80.0)
    assert scheduler.is_running is True

    await asyncio.sleep(1.2)
    scheduler.stop()

    assert scheduler.is_running is False
    assert len(jobs_executed) >= 1

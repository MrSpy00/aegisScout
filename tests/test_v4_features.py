"""
Unit and Integration Tests for aegisScout V4 Feature Modules.
"""
import os
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlmodel import Session, SQLModel

from aegisScout.core.database import make_engine
from aegisScout.core.models import Lead, Message, Campaign
from aegisScout.core.deduplicator import find_duplicates, merge_leads
from aegisScout.core.lead_scorer import score_lead
from aegisScout.ai.reply_classifier import classify_reply, ReplyClassification
from aegisScout.core.cron_manager import CronManager
from aegisScout.outreach.sms_client import SMSClient
from aegisScout.core.screen_gallery import get_lead_screenshot, get_gallery_comparison
from aegisScout.utils.export_engine import export_leads
from aegisScout.core.campaign_analytics import get_campaign_analytics
from aegisScout.outreach.scheduler import OutreachScheduler
from aegisScout.ai.cache import AIResponseCache
from aegisScout.utils.key_vault import AegisKeyVault

@pytest.fixture
def temp_db():
    engine = make_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine

def test_lead_scorer_v2():
    lead = Lead(
        business_name="Test Kuaför",
        sector="kuaför",
        email="info@testkuafor.com",
        phone="+905551234567",
        instagram_handle="test_kuafor",
        website_url="https://testkuafor.com",
        review_count=60,
        rating=4.8
    )
    score = score_lead(lead)
    assert score.total >= 75.0
    assert score.label == "Hot Lead"

@pytest.mark.asyncio
async def test_reply_classifier():
    res = await classify_reply("Fiyat listenizi gönderebilir misiniz?")
    assert res.category in ("QUESTION", "INTERESTED")

def test_cron_manager():
    manager = CronManager.get_instance()
    job = manager.add_job(sector="berber", location="Kadıköy", radius_km=3.0, interval_hours=12)
    assert job.sector == "berber"
    jobs = manager.list_jobs()
    assert len(jobs) >= 1

@pytest.mark.asyncio
async def test_sms_client():
    client = SMSClient(provider="mock")
    res = await client.send_sms("+905551234567", "Test SMS Mesajı")
    assert res["success"] is True

def test_ai_cache():
    cache = AIResponseCache(ttl_hours=1)
    cache.set("hello", "world")
    assert cache.get("hello") == "world"
    assert cache.get("nonexistent") is None

def test_key_vault():
    vault = AegisKeyVault()
    assert vault.store("TEST_KEY", "12345") is True
    assert vault.retrieve("TEST_KEY") == "12345"

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

def test_clean_location_for_search():
    from aegisScout.discovery.instagram_finder import _clean_location_for_search
    addr = '"Erkek Kuaförü Osman" Fevzi Paşa Caddesi No: 5, Beykoz, İstanbul, 34820'
    cleaned = _clean_location_for_search(addr)
    assert "Beykoz" in cleaned or "İstanbul" in cleaned
    assert "34820" not in cleaned
    assert "No:" not in cleaned
    assert '"' not in cleaned

def test_email_verifier_valid_format():
    from aegisScout.utils.email_verifier import verify_email
    res = verify_email("invalid-email-format")
    assert res["success"] is False
    assert res["status"] == "invalid"

@pytest.mark.asyncio
async def test_capture_screenshot_async_loop_safety(tmp_path):
    from aegisScout.core.screen_audit import capture_screenshot
    # Must not raise "Playwright Sync API inside the asyncio loop" exception
    target_file = tmp_path / "test.png"
    res = capture_screenshot("https://httpbin.org/get", target_file)
    assert isinstance(res, bool)

@pytest.mark.asyncio
async def test_run_website_screen_audit_thread_safety(temp_db):
    from aegisScout.core.screen_audit import run_website_screen_audit
    with Session(temp_db) as session:
        lead = Lead(business_name="Test Business", website_url="https://example.com")
        session.add(lead)
        session.commit()
        session.refresh(lead)
        lead_id = lead.id

    # Running screen audit inside active asyncio loop should run smoothly without Playwright sync exception
    res = await run_website_screen_audit(lead_id)
    assert "quality_score" in res or "error" not in res



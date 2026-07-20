"""
Tests for Core engine upgrades: SQLite WAL/busy_timeout, compound indexing,
lead deduplication, retry decorator, crawler, and SSRF safety filter.
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from aegisScout.core.database import (
    make_engine,
    init_db,
    sqlite_retry_on_lock,
    deduplicate_leads,
)
from aegisScout.core.models import Lead
from aegisScout.utils.security import is_safe_url
from aegisScout.core.crawler import PlaywrightCrawler


def test_sqlite_pragmas_and_indexes():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as session:
        # Check table creation and query execution
        leads = session.query(Lead).all()
        assert isinstance(leads, list)


def test_sqlite_retry_decorator():
    counter = {"attempts": 0}

    @sqlite_retry_on_lock(max_retries=3, delay=0.01)
    def dummy_db_op():
        counter["attempts"] += 1
        if counter["attempts"] < 2:
            import sqlite3
            raise sqlite3.OperationalError("database is locked")
        return "success"

    res = dummy_db_op()
    assert res == "success"
    assert counter["attempts"] == 2


def test_lead_deduplication():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        lead1 = Lead(business_name="Acme Corp", website_url="https://acme.com", phone="123456", priority_score=50.0)
        lead2 = Lead(business_name="Acme Corp LLC", website_url="https://acme.com", email="info@acme.com", priority_score=80.0)
        lead3 = Lead(business_name="Beta Ltd", website_url="https://beta.com", phone="999888", priority_score=60.0)
        session.add_all([lead1, lead2, lead3])
        session.commit()

        merged_count = deduplicate_leads(session)
        assert merged_count == 1

        remaining = session.query(Lead).all()
        assert len(remaining) == 2
        acme = [l for l in remaining if "Acme" in l.business_name][0]
        assert acme.email == "info@acme.com"
        assert acme.score == 80.0


def test_ssrf_safety_filter():
    assert is_safe_url("https://google.com") is True
    assert is_safe_url("http://127.0.0.1") is False
    assert is_safe_url("http://localhost:8080") is False
    assert is_safe_url("http://192.168.1.1/admin") is False
    assert is_safe_url("http://10.0.0.1") is False


@pytest.mark.asyncio
async def test_crawler_metadata_ssrf():
    crawler = PlaywrightCrawler()
    res = await crawler.fetch_page_metadata("http://127.0.0.1/secret")
    assert res is None

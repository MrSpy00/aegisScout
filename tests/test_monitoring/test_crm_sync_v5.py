"""
Tests for CRM Sync & Webhook Export.
"""
import pytest
import respx
import httpx
from aegisScout.monitoring.crm_sync import CRMSyncManager
from aegisScout.core.models import Lead


def test_crm_payload_formatting():
    lead = Lead(
        id=10,
        business_name="Scout CRM Inc",
        domain="scoutcrm.io",
        email="hello@scoutcrm.io",
        phone="5551234",
        city="Ankara",
        score=88.0,
    )

    hubspot_data = CRMSyncManager.format_lead_for_hubspot(lead)
    assert hubspot_data["properties"]["company"] == "Scout CRM Inc"
    assert hubspot_data["properties"]["aegis_score"] == 88.0

    sf_data = CRMSyncManager.format_lead_for_salesforce(lead)
    assert sf_data["Company"] == "Scout CRM Inc"
    assert sf_data["Rating"] == "Hot"


@pytest.mark.asyncio
async def test_webhook_post_success():
    lead = Lead(id=1, business_name="Webhook Test LLC", domain="test.org")
    manager = CRMSyncManager()

    webhook_url = "https://api.zapier.com/v1/hooks/catch/12345"
    with respx.mock:
        respx.post(webhook_url).respond(status_code=200, json={"status": "ok"})
        success = await manager.post_webhook(webhook_url, [lead])
        assert success is True


@pytest.mark.asyncio
async def test_webhook_post_ssrf_blocked():
    lead = Lead(id=1, business_name="Local Test")
    manager = CRMSyncManager()
    success = await manager.post_webhook("http://127.0.0.1:8000/webhook", [lead])
    assert success is False

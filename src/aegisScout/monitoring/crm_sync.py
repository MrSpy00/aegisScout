"""
CRM Export & Webhook Integration Manager for aegisScout.
Exports lead data to Zapier, Make, N8N, HubSpot, and Salesforce.
"""
import httpx
from typing import List, Dict, Any, Optional
from aegisScout.core.models import Lead
from aegisScout.utils.security import is_safe_url
from aegisScout.utils.logger import get_logger

logger = get_logger("monitoring.crm_sync")


class CRMSyncManager:
    """Handles CRM integrations and Webhook lead exports."""

    @staticmethod
    def format_lead_for_hubspot(lead: Lead) -> Dict[str, Any]:
        """Format lead into HubSpot Contacts API payload structure."""
        return {
            "properties": {
                "company": lead.business_name or "",
                "website": lead.website_url or (f"https://{lead.domain}" if lead.domain else ""),
                "email": lead.email or "",
                "phone": lead.phone or "",
                "city": lead.city or "",
                "industry": lead.category or "",
                "aegis_score": lead.score or 0.0,
                "aegis_status": lead.status or "new",
            }
        }

    @staticmethod
    def format_lead_for_salesforce(lead: Lead) -> Dict[str, Any]:
        """Format lead into Salesforce Lead object payload structure."""
        return {
            "Company": lead.business_name or "Bilinmeyen Şirket",
            "LastName": lead.business_name or "Yetkili",
            "Email": lead.email or "",
            "Phone": lead.phone or "",
            "City": lead.city or "",
            "Website": lead.website_url or (f"https://{lead.domain}" if lead.domain else ""),
            "LeadSource": "AegisScout AI",
            "Rating": "Hot" if (lead.score or 0) >= 75 else "Warm",
        }

    async def post_webhook(self, webhook_url: str, leads: List[Lead]) -> bool:
        """Send leads to Zapier / Make / Custom Webhook endpoint via HTTP POST."""
        if not is_safe_url(webhook_url):
            logger.warning(f"CRM Webhook blocked due to unsafe URL: {webhook_url}")
            return False

        payload = {
            "source": "aegisScout",
            "count": len(leads),
            "leads": [lead.dict() for lead in leads],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                if resp.status_code in (200, 201, 202, 204):
                    logger.info(f"Successfully posted {len(leads)} leads to webhook {webhook_url}")
                    return True
                else:
                    logger.error(f"Webhook returned status code {resp.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to post leads to webhook: {e}")
            return False

"""
Campaigns Panel Handlers for GUI.
"""
from typing import Dict, Any
from sqlmodel import Session, select
from aegisScout.core.database import engine
from aegisScout.core.models import Campaign

def handle_get_campaigns() -> Dict[str, Any]:
    """Fetch all outreach campaigns."""
    try:
        with Session(engine) as session:
            campaigns = session.exec(select(Campaign)).all()
            return {"success": True, "campaigns": [c.dict() for c in campaigns]}
    except Exception as e:
        return {"success": False, "error": str(e)}

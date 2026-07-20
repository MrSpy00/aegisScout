"""
Leads Panel Handlers for GUI.
"""
from typing import Dict, Any, List
from sqlmodel import Session, select
from aegisScout.core.database import engine
from aegisScout.core.models import Lead

def handle_get_leads(limit: int = 100, offset: int = 0, status_filter: str = "all") -> Dict[str, Any]:
    """Fetch stored leads from SQLite database."""
    try:
        with Session(engine) as session:
            stmt = select(Lead)
            if status_filter != "all":
                stmt = stmt.where(Lead.status == status_filter)
            stmt = stmt.offset(offset).limit(limit)
            leads = session.exec(stmt).all()
            return {"success": True, "leads": [l.dict() for l in leads]}
    except Exception as e:
        return {"success": False, "error": str(e)}

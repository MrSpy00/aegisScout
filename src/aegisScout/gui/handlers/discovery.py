"""
Discovery Panel Handlers for GUI.
"""
import asyncio
from typing import Dict, Any, List
from aegisScout.cli.commands import discover_leads

def handle_start_discovery(sector: str, location: str, radius_km: float = 5.0, provider: str = "all") -> Dict[str, Any]:
    """Execute discovery pipeline for given parameters."""
    try:
        leads = asyncio.run(discover_leads(sector=sector, location=location, radius_km=radius_km, provider_name=provider))
        return {"success": True, "count": len(leads), "leads": [l.dict() for l in leads]}
    except Exception as e:
        return {"success": False, "error": str(e)}

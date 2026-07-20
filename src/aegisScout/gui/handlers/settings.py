"""
Settings Panel Handlers for GUI.
"""
from typing import Dict, Any
from aegisScout.core.config import settings
from aegisScout.core.toml_config import config_data

def handle_get_settings() -> Dict[str, Any]:
    """Retrieve application settings."""
    try:
        return {
            "success": True,
            "settings": {
                "llm_primary_provider": settings.llm_primary_provider,
                "llm_fallback_provider": settings.llm_fallback_provider,
                "outreach_mode": settings.outreach_mode,
                "max_daily_outreach": settings.max_daily_outreach,
                "config_toml": config_data
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

"""
Auto-Update Mechanism for aegisScout (I3).
Checks GitHub releases for latest version updates.
"""
from dataclasses import dataclass
from typing import Optional
import httpx
from aegisScout import __version__
from aegisScout.utils.logger import get_logger

logger = get_logger("core.updater")

@dataclass
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str

async def check_for_updates() -> Optional[UpdateInfo]:
    """Check GitHub Releases for newer version of aegisScout."""
    repo_url = "https://api.github.com/repos/MrSpy00/aegisScout/releases/latest"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(repo_url)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                if latest_tag and latest_tag > __version__:
                    assets = data.get("assets", [])
                    dl_url = assets[0]["browser_download_url"] if assets else data.get("html_url", "")
                    return UpdateInfo(
                        version=latest_tag,
                        download_url=dl_url,
                        release_notes=data.get("body", "")
                    )
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
    return None

"""
Centralized path resolution helper for aegisScout.
Ensures correct path resolution whether running from source or as a PyInstaller frozen executable.
"""
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Return project root directory or executable parent directory when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # src/aegisScout/utils/paths.py -> project root is parents[3]
    return Path(__file__).resolve().parents[3]

def get_data_dir() -> Path:
    """Return the absolute path to the data directory, creating it if missing."""
    data_dir = get_base_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_logs_dir() -> Path:
    """Return the absolute path to the logs directory, creating it if missing."""
    logs_dir = get_base_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def get_assets_dir() -> Path:
    """Return the absolute path to static assets directory."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = Path(meipass) / "aegisScout" / "assets"
            if candidate.exists():
                return candidate
        return Path(sys.executable).parent / "assets"
    return Path(__file__).resolve().parents[1] / "assets"

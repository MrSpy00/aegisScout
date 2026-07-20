"""
Dynamic GUI Asset Loader for aegisScout.
Loads static HTML/CSS/JS assets from disk instead of embedding base64 in Python byte code.
"""
from pathlib import Path
from aegisScout.utils.paths import get_assets_dir

def get_html_content() -> str:
    """Read index.html dynamically from assets directory."""
    index_path = get_assets_dir() / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<html><body><h1>Error: index.html not found</h1></body></html>"

def __getattr__(name: str):
    if name == "HTML_CONTENT":
        return get_html_content()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

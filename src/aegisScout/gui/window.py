"""
PyWebView Window Launcher for aegisScout GUI.
"""
import sys
from pathlib import Path
from aegisScout.gui_assets import get_html_content
from aegisScout.utils.paths import get_assets_dir

def create_app_window(api_instance=None):
    """Create and configure the PyWebView desktop window."""
    try:
        import webview
    except ImportError:
        raise RuntimeError("pywebview is required for GUI mode. Install with `pip install pywebview` or `pip install aegisScout[gui]`.")

    icon_path = get_assets_dir() / "logo.ico"
    html_content = get_html_content()

    window = webview.create_window(
        title="aegisScout — Business Discovery & Sales Automation",
        html=html_content,
        js_api=api_instance,
        width=1400,
        height=900,
        min_size=(1024, 700),
        resizable=True,
    )
    return window

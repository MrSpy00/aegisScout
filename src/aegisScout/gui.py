"""
aegisScout GUI — PyWebView bridge module (re-exports from aegisScout.gui_impl).
"""

from aegisScout.gui_impl import (
    GuiApi,
    start_gui,
    set_console_visibility,
    close_console_window,
    _get_icon_path,
    _start_window,
    _patch_pywebview_js_path,
    _utcnow,
    _ALLOWED_JS_SET_KEYS,
    _SENSITIVE_ENV_KEYS,
)

__all__ = [
    "GuiApi",
    "start_gui",
    "set_console_visibility",
    "close_console_window",
    "_get_icon_path",
    "_start_window",
    "_patch_pywebview_js_path",
    "_utcnow",
    "_ALLOWED_JS_SET_KEYS",
    "_SENSITIVE_ENV_KEYS",
]

if __name__ == "__main__":
    start_gui()

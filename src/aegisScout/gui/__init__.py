"""
aegisScout GUI Package.
"""
from aegisScout.core import database as db_module
from aegisScout.gui_impl import GuiApi, start_gui, _get_icon_path
from aegisScout.gui.window import create_app_window

# Expose engine so test fixtures can patch gui.engine
def __getattr__(name: str):
    if name == "engine":
        return db_module.engine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def launch_gui(api_instance=None):
    """Launch the PyWebView desktop application."""
    import webview
    window = create_app_window(api_instance)
    webview.start(debug=False)

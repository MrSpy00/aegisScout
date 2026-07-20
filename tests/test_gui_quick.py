"""Quick test: verify GUI can start and API works."""
import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test 1: Import all GUI dependencies
print("=== Test 1: Import dependencies ===")
from aegisScout.gui import GuiApi, start_gui, _get_icon_path
from aegisScout.gui_assets import HTML_CONTENT
print(f"  HTML length: {len(HTML_CONTENT)} chars")
print(f"  Icon path: {_get_icon_path()}")
print("  OK")

# Test 2: Initialize API
print("\n=== Test 2: Initialize GuiApi ===")
api = GuiApi()
print(f"  Active session: {api.active_session_id}")
print(f"  Stats: {api.get_stats()}")
print(f"  Configured: {api.is_configured()['configured']}")
print("  OK")

# Test 3: Check pywebview is functional
print("\n=== Test 3: pywebview create_window ===")
import webview
import inspect

# Verify create_window signature matches our usage
sig = inspect.signature(webview.create_window)
params = list(sig.parameters.keys())
print(f"  create_window params: {params}")
assert 'html' in params, "html param missing!"
assert 'js_api' in params, "js_api param missing!"
print("  All required params present")

# Verify webview.start signature
sig2 = inspect.signature(webview.start)
params2 = list(sig2.parameters.keys())
print(f"  webview.start params: {params2}")
assert 'gui' in params2, "gui param missing!"
assert 'private_mode' in params2, "private_mode missing!"
assert 'icon' in params2, "icon param missing!"
print("  All required start params present")

# Test 4: Verify bottle is importable (critical for BottleServer)
print("\n=== Test 4: Bottle dependency ===")
import bottle
import proxy_tools
print(f"  bottle: {bottle.__file__}")
print(f"  proxy_tools: {proxy_tools.__file__}")
print("  OK")

print("\n=== ALL TESTS PASSED ===")

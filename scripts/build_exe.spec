# -*- mode: python ; coding: utf-8 -*-
"""aegisScout PyInstaller spec - optimized for size and speed."""
import os
import sys

try:
    import webview
    webview_lib = os.path.join(os.path.dirname(webview.__file__), 'lib')
except ImportError:
    webview_lib = None
    print("[!] webview (pywebview) not installed. GUI feature will not work in EXE.")
    print("    Install with: pip install pywebview")
is_win = sys.platform.startswith("win")

a = Analysis(
    ['../src/aegisScout/main.py'],
    pathex=[],
    binaries=[],
    datas=[x for x in [
        ('../config/config.example.toml', 'config'),
        ('../src/aegisScout/assets/logo.png', 'aegisScout/assets'),
        ('../src/aegisScout/assets/logo.ico', 'aegisScout/assets'),
        (webview_lib, 'webview/lib') if webview_lib else None,
    ] if x is not None],
    hiddenimports=[
        # Core dependencies
        'clr', 'cffi',
        # SQLAlchemy / typing (typing_extensions MUST be here, NOT in excludes)
        'typing_extensions',
        'sqlalchemy', 'sqlalchemy.sql.default_comparator',
        # pywebview runtime dependencies (NOT optional — needed for GUI)
        'bottle', 'proxy_tools',
        # Runtime export formats (openpyxl, reportlab)
        'openpyxl', 'openpyxl.cell', 'openpyxl.styles',
        'reportlab', 'reportlab.lib', 'reportlab.platypus',
        # Async / encoding
        'asyncio', 'idna', 'charset_normalizer',
        # Cryptography
        'cryptography', 'cryptography.fernet',
        # HTML/parsing
        'bs4', 'soupsieve',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI toolkits not needed
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx', 'gi',
        # Heavy science/data libs not needed
        'numpy', 'matplotlib', 'pandas', 'scipy', 'sympy', 'networkx',
        'scikit', 'sklearn', 'statsmodels', 'cv2', 'PIL', 'Pillow',
        # Dev/doc tools not needed
        'unittest', 'pydoc', 'pdb', 'docutils', 'sphinx', 'setuptools',
        'distutils', 'pip', 'jupyter', 'IPython', 'ipykernel', 'jedi',
        'parso', 'black', 'isort', 'mypy', 'ruff',
        # Web servers / browsers not needed
        'weasyprint', 'tornado', 'flask', 'django',
        # Cloud SDKs not needed
        'boto3', 'botocore', 'azure', 'google', 'kubernetes',
        # Testing not needed
        'pytest', 'nose', 'tox', 'coverage',
        # Misc heavy deps not needed
        'cv2', 'tensorflow', 'torch', 'transformers', 'datasets',
        'huggingface', 'wandb', 'mlflow',
        # MS / Windows-specific not needed
        'win32com', 'win32ctypes',
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='aegisScout',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # strip not available on Windows; macOS/Linux have it
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../src/aegisScout/assets/logo.ico',
)

"""
Loader for ``config/config.toml``.

Resolution order for ``CONFIG_DIR`` (the directory that may contain
``config.toml`` or ``config.example.toml``):

  1. ``$AEGISSCout_CONFIG_DIR`` (env var override, useful for tests)
  2. ``sys._MEIPASS / "config"``  (when frozen via PyInstaller)
  3. Walk up from ``Path(__file__).parent`` until a ``config/`` dir is
     found next to the project root (i.e. ``parents[k] / "config"``).
  4. ``Path.cwd() / "config"``     (last-resort fallback)

The loader is test-friendly: ``load_toml_config`` accepts an explicit
``config_path`` argument so tests can point it at a temp directory.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import tomllib


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _resolve_config_dir() -> Path:
    """Return the most likely on-disk config directory.

    Resolution order:
      1. ``$AEGISSCout_CONFIG_DIR`` (explicit override; tests use this)
      2. Frozen/PyInstaller bundle: ``sys._MEIPASS / "config"``
      3. Walk up from this file's parent to find a ``config/`` dir
         (covers the dev layout: ``.../project_root/config/``)
      4. ``Path.cwd() / "config"``  (final fallback)
    """
    env_dir = os.environ.get("AEGISSCout_CONFIG_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        if p.exists() and p.is_dir():
            return p
        # Env var set but invalid: still return it so error surfaces
        # upstream with a useful message.
        return p

    # Frozen (PyInstaller): the config dir should be next to the executable
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config"

    # Dev: walk up parents to find the project-root ``config/`` dir.
    # toml_config.py lives at  src/aegisScout/core/toml_config.py
    # so the project root is parents[3]. We walk up to parents[5] to
    # tolerate the file being moved around within the package.
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "config"
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Last-resort fallback (CWD).
    return Path.cwd() / "config"


CONFIG_DIR: Path = _resolve_config_dir()
CONFIG_FILE: Path = CONFIG_DIR / "config.toml"


def _set_config_dir(path: Path) -> None:
    """Override the resolved config dir + file (used by tests)."""
    global CONFIG_DIR, CONFIG_FILE
    CONFIG_DIR = Path(path)
    CONFIG_FILE = CONFIG_DIR / "config.toml"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def dumps_toml(data: dict) -> str:
    """Simple TOML serializer for config structures."""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"\n[{key}]")
            for sub_k, sub_v in value.items():
                if isinstance(sub_v, bool):
                    lines.append(f"{sub_k} = {str(sub_v).lower()}")
                elif isinstance(sub_v, (int, float)):
                    lines.append(f"{sub_k} = {sub_v}")
                elif isinstance(sub_v, list):
                    lines.append(f"{sub_k} = {sub_v!r}")
                else:
                    lines.append(f'{sub_k} = "{sub_v}"')
        elif isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
        elif isinstance(value, list):
            lines.append(f"{key} = {value!r}")
        else:
            lines.append(f'{key} = "{value}"')
    return "\n".join(lines) + "\n"


def dump_toml(data: dict, f) -> None:
    """Write dict to file as TOML."""
    content = dumps_toml(data)
    if hasattr(f, "write"):
        f.write(content)
    else:
        with open(f, "w", encoding="utf-8") as out:
            out.write(content)


def load_toml_config(config_path: Optional[Path] = None) -> dict:
    """Load and return the project's TOML config as a dict."""
    target = Path(config_path) if config_path else CONFIG_FILE
    target_dir = target.parent

    if target.exists():
        with open(target, "rb") as f:
            return tomllib.load(f)

    # Try the example fallback in the same dir.
    example = target_dir / "config.example.toml"
    if example.exists():
        with open(example, "rb") as f:
            return tomllib.load(f)

    # Try the bundle fallback (PyInstaller): example next to the exe.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundle_example = Path(meipass) / "config" / "config.example.toml"
        if bundle_example.exists():
            with open(bundle_example, "rb") as f:
                return tomllib.load(f)

    # No config at all — caller must tolerate empty config.
    return {}


# Eagerly populate the module-level singleton.
config_data: dict = load_toml_config()

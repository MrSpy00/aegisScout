"""
Fernet-based encryption helpers for aegisScout.

Design goals
------------
1.  No plaintext fallback. If `Fernet.decrypt` fails for ANY reason, we raise
    `ValueError("Cannot decrypt: invalid key or corrupted data")`. The
    previous version silently returned the original bytes when decryption
    failed — that was a critical security hole.
2.  The encryption key is resolved from one of:
      - ``AEGIS_FERNET_KEY`` env var (URL-safe base64, 32 bytes when decoded)
      - ``data/.fernet_key`` file (auto-created on first use with ``0o600``
        permissions on POSIX, restrictive ACL on Windows)
    The env var always wins.
3.  Two public APIs are exposed:
      - :func:`encrypt_bytes` / :func:`decrypt_bytes` — raw bytes in/out
      - :func:`encrypt_string` / :func:`decrypt_string` — str in/out
        (base64-encoded token for safe text storage)
4.  The legacy :func:`encrypt_json_file` / :func:`decrypt_json_file` API is
    preserved for callers (``outreach.instagram_client`` and ``gui``). The
    decrypt function raises on failure (no plaintext fallback); a missing
    file still returns ``{}`` since "no data yet" is a soft state.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import sys
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


# ---------------------------------------------------------------------------
# Key file resolution — must be importable so tests can monkeypatch it.
# ---------------------------------------------------------------------------

def _resolve_key_file() -> Path:
    """Return the default on-disk key file path.

    Order:
      1. ``$AEGIS_FERNET_KEY_FILE`` (absolute or relative to CWD)
      2. ``<project_root>/data/.fernet_key``  (project root in dev,
         or sys.executable's parent when frozen)
      3. ``$XDG_DATA_HOME/aegisScout/.fernet_key`` or
         ``~/.local/share/aegisScout/.fernet_key``  (user-level)
    """
    env_path = os.environ.get("AEGIS_FERNET_KEY_FILE")
    if env_path:
        return Path(env_path)

    if getattr(sys, "frozen", False):
        project_root = Path(sys.executable).parent
    else:
        # .../src/aegisScout/utils/encryption.py  -> project root = parents[3]
        project_root = Path(__file__).resolve().parents[3]
    candidate = project_root / "data" / ".fernet_key"
    if candidate.parent.exists():
        return candidate

    # User-level fallback (XDG-aware)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "aegisScout" / ".fernet_key"


# Public so tests can override.
_KEY_FILE: Path = _resolve_key_file()


def _set_key_file(path: Path) -> None:
    """Override the key file location (used by tests)."""
    global _KEY_FILE
    _KEY_FILE = Path(path)


# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------

def _load_key() -> bytes:
    """Resolve the active Fernet key.

    Order: ``$AEGIS_FERNET_KEY`` -> ``$AEGIS_FERNET_KEY`` file -> create
    a new key file on disk (with 0o600 perms).
    """
    env_key = os.environ.get("AEGIS_FERNET_KEY", "").strip()
    if env_key:
        return env_key.encode("utf-8")

    path = Path(_KEY_FILE)
    if path.exists():
        try:
            key = path.read_bytes().strip()
        except OSError as e:
            raise ValueError(
                f"Cannot read Fernet key file at {path}: {e}"
            ) from e
        if not key:
            raise ValueError(
                f"Fernet key file at {path} is empty. Delete it and re-run "
                "or set AEGIS_FERNET_KEY in the environment."
            )
        # Validate format; surface a helpful error early.
        try:
            Fernet(key)
        except Exception as e:
            raise ValueError(
                f"Fernet key file at {path} is not a valid Fernet key "
                f"(generate one with `python -c \"from cryptography.fernet "
                f"import Fernet; print(Fernet.generate_key().decode())\"`): {e}"
            ) from e
        return key

    # Create a fresh key file.
    path.parent.mkdir(parents=True, exist_ok=True)
    new_key = Fernet.generate_key()
    # Write with restrictive perms BEFORE writing content.
    fd = os.open(
        str(path),
        flags=os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        mode=0o600,
    )
    try:
        os.write(fd, new_key)
    finally:
        os.close(fd)
    # On POSIX, the os.open mode is honored; on Windows the ACL is
    # inherited from the parent directory which we created with 0o700.
    if hasattr(os, "chmod"):
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    return new_key


def _get_fernet() -> Fernet:
    """Build a Fernet instance from the resolved key. Raises ValueError on
    any failure with a clear, non-cryptographic message."""
    try:
        return Fernet(_load_key())
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            "Cannot build Fernet cipher: invalid key or corrupted data. "
            f"Generate a new one with `python -c \"from cryptography.fernet "
            "import Fernet; print(Fernet.generate_key().decode())\"` and set "
            "AEGIS_FERNET_KEY in your environment."
        ) from e


# ---------------------------------------------------------------------------
# Bytes API
# ---------------------------------------------------------------------------

def encrypt_bytes(plaintext: bytes) -> bytes:
    """Encrypt ``plaintext`` with the active Fernet key. Returns raw bytes."""
    if not isinstance(plaintext, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"encrypt_bytes expects bytes, got {type(plaintext).__name__}"
        )
    return _get_fernet().encrypt(bytes(plaintext))


def decrypt_bytes(token: bytes) -> bytes:
    """Decrypt ``token`` with the active Fernet key.

    Raises ``ValueError("Cannot decrypt: invalid key or corrupted data")``
    on any decryption failure. NEVER returns raw plaintext.
    """
    if not isinstance(token, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"decrypt_bytes expects bytes, got {type(token).__name__}"
        )
    try:
        return _get_fernet().decrypt(bytes(token))
    except InvalidToken as e:
        raise ValueError(
            "Cannot decrypt: invalid key or corrupted data"
        ) from e


# ---------------------------------------------------------------------------
# String API (base64 for safe text storage)
# ---------------------------------------------------------------------------

def encrypt_string(plaintext: str) -> str:
    """Encrypt a string and return a urlsafe-base64 token (str).

    Suitable for storing in JSON columns, SQLite TEXT fields, or any
    text-only destination.
    """
    if not isinstance(plaintext, str):
        raise TypeError(
            f"encrypt_string expects str, got {type(plaintext).__name__}"
        )
    return base64.urlsafe_b64encode(encrypt_bytes(plaintext.encode("utf-8"))).decode("ascii")


def decrypt_string(token: str) -> str:
    """Decrypt a base64 token (str) back to the original UTF-8 string.

    Raises ``ValueError`` on any failure. NEVER returns the input verbatim.
    """
    if not isinstance(token, str):
        raise TypeError(
            f"decrypt_string expects str, got {type(token).__name__}"
        )
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
    except (binascii.Error, ValueError) as e:
        raise ValueError(
            "Cannot decrypt: invalid key or corrupted data"
        ) from e
    return decrypt_bytes(raw).decode("utf-8")


# ---------------------------------------------------------------------------
# JSON file API (preserved for existing callers, no plaintext fallback)
# ---------------------------------------------------------------------------

def encrypt_json_file(file_path: Path, data: dict) -> None:
    """Encrypt ``data`` (a JSON-serializable dict) and write to ``file_path``."""
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted = encrypt_bytes(raw)
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(encrypted)


def decrypt_json_file(file_path: Path) -> dict:
    """Read and decrypt a JSON file written by :func:`encrypt_json_file`.

    A *missing* file returns ``{}`` (no data yet). A *present but
    undecryptable* file raises ``ValueError`` — the original code's
    silent plaintext-fallback is gone.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {}
    encrypted = file_path.read_bytes()
    decrypted = decrypt_bytes(encrypted)  # raises on failure
    return json.loads(decrypted.decode("utf-8"))


__all__ = [
    "encrypt_bytes",
    "decrypt_bytes",
    "encrypt_string",
    "decrypt_string",
    "encrypt_json_file",
    "decrypt_json_file",
]

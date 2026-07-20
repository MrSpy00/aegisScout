"""
Tests for the encryption module.

TDD: these tests were written BEFORE the production fix. They define the
expected new API:

    encrypt_bytes(plaintext: bytes, key: bytes | None = None) -> bytes
    decrypt_bytes(token: bytes, key: bytes | None = None) -> bytes
    encrypt_string(plaintext: str, key: bytes | None = None) -> str   # base64
    decrypt_string(token: str, key: bytes | None = None) -> str

The module-level key is resolved from env AEGIS_FERNET_KEY or from
data/.fernet_key (auto-created with 0600 perms).

NEVER falls back to plaintext on decrypt failure.
"""
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken


def _key() -> bytes:
    return Fernet.generate_key()


# ---------------------------------------------------------------------------
# Bytes API
# ---------------------------------------------------------------------------

class TestEncryptDecryptBytes:
    """Round-trip tests for the raw-bytes API."""

    def test_roundtrip_random_bytes(self):
        from aegisScout.utils import encryption
        key = _key()
        plain = os.urandom(256)
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            token = encryption.encrypt_bytes(plain)
            assert token != plain
            recovered = encryption.decrypt_bytes(token)
        assert recovered == plain

    def test_roundtrip_unicode_bytes(self):
        from aegisScout.utils import encryption
        key = _key()
        plain = "Merhaba Dunya - Turkce: oyku".encode("utf-8")
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            recovered = encryption.decrypt_bytes(encryption.encrypt_bytes(plain))
        assert recovered == plain

    def test_roundtrip_empty_bytes(self):
        from aegisScout.utils import encryption
        key = _key()
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            recovered = encryption.decrypt_bytes(encryption.encrypt_bytes(b""))
        assert recovered == b""

    def test_wrong_key_raises_value_error(self):
        from aegisScout.utils import encryption
        k1 = _key()
        k2 = _key()
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": k1.decode()}):
            token = encryption.encrypt_bytes(b"secret")
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": k2.decode()}):
            with pytest.raises(ValueError, match="[Cc]annot decrypt"):
                encryption.decrypt_bytes(token)

    def test_corrupted_token_raises_value_error(self):
        from aegisScout.utils import encryption
        key = _key()
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            with pytest.raises(ValueError, match="[Cc]annot decrypt"):
                encryption.decrypt_bytes(b"not-a-valid-fernet-token")


# ---------------------------------------------------------------------------
# String API (base64, the only safe format for storage)
# ---------------------------------------------------------------------------

class TestEncryptDecryptString:
    """Round-trip tests for the base64 string API."""

    def test_roundtrip_returns_base64_string(self):
        from aegisScout.utils import encryption
        key = _key()
        plain = "instagram_session_blob"
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            token = encryption.encrypt_string(plain)
        # Returned type is str, not bytes
        assert isinstance(token, str)
        # It's valid base64
        import base64
        base64.urlsafe_b64decode(token)
        # And it round-trips
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            recovered = encryption.decrypt_string(token)
        assert recovered == plain

    def test_unicode_string_roundtrip(self):
        from aegisScout.utils import encryption
        key = _key()
        plain = "Oturum JSON: {\"u\": \"test\", \"i\": 42}"
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            recovered = encryption.decrypt_string(encryption.encrypt_string(plain))
        assert recovered == plain

    def test_decrypt_string_wrong_key_raises(self):
        from aegisScout.utils import encryption
        k1 = _key()
        k2 = _key()
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": k1.decode()}):
            token = encryption.encrypt_string("secret")
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": k2.decode()}):
            with pytest.raises(ValueError):
                encryption.decrypt_string(token)

    def test_decrypt_string_garbage_raises(self):
        from aegisScout.utils import encryption
        key = _key()
        with patch.dict(os.environ, {"AEGIS_FERNET_KEY": key.decode()}):
            with pytest.raises(ValueError):
                encryption.decrypt_string("not-base64-!!!-garbage")


# ---------------------------------------------------------------------------
# No plaintext fallback (the original security hole)
# ---------------------------------------------------------------------------

class TestNoPlaintextFallback:
    """The original bug was: on decrypt failure, the module fell back to
    treating the input as raw plaintext. This must NEVER happen."""

    def test_no_plaintext_fallback_on_decrypt_failure(self, tmp_path, monkeypatch):
        # The fix removed the exception-swallowing fallback. Force a bad
        # token and assert the module raises ValueError instead of returning
        # the input verbatim.
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())
        # A clear "this is plaintext" marker.
        sentinel = b"this-is-raw-plaintext-do-not-return-me"
        # Any token-looking bytes that are NOT valid fernet must raise.
        with pytest.raises(ValueError):
            encryption.decrypt_bytes(sentinel)

    def test_no_plaintext_fallback_on_string(self, monkeypatch):
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())
        with pytest.raises(ValueError):
            encryption.decrypt_string("not-a-valid-base64-fernet-token")

    def test_module_source_has_no_except_around_decrypt(self):
        """Static check: the module source must not contain a broad
        `except Exception` wrapping the Fernet.decrypt call. This is the
        regression guard for the original bug."""
        from aegisScout.utils import encryption
        import re
        src = Path(encryption.__file__).read_text(encoding="utf-8")
        # Look for any `except` line that contains `Exception` within ~3
        # lines of a `.decrypt(` call. This is approximate but sufficient.
        lines = src.splitlines()
        bad = []
        for i, line in enumerate(lines):
            if "except" in line and "Exception" in line:
                window = "\n".join(lines[max(0, i - 3): i + 1])
                if ".decrypt(" in window:
                    bad.append((i, line.strip()))
        assert bad == [], f"Found exception-swallowing near decrypt: {bad}"


# ---------------------------------------------------------------------------
# Key file fallback (data/.fernet_key, 0600 perms)
# ---------------------------------------------------------------------------

class TestKeyFileFallback:
    """If AEGIS_FERNET_KEY is unset, the module falls back to a key file at
    data/.fernet_key (auto-created on first use, 0600 perms on POSIX)."""

    def test_falls_back_to_key_file_when_env_unset(self, tmp_path, monkeypatch):
        from aegisScout.utils import encryption
        # Pre-create a key file
        key_file = tmp_path / "fernet.key"
        key_file.write_bytes(Fernet.generate_key())
        key_file.chmod(0o600)
        # Point the module at this file
        monkeypatch.setattr(encryption, "_KEY_FILE", key_file)
        monkeypatch.delenv("AEGIS_FERNET_KEY", raising=False)

        # The module-level loader should pick it up
        loaded = encryption._load_key()
        assert loaded == key_file.read_bytes()

    def test_creates_key_file_with_0600_when_missing(self, tmp_path, monkeypatch):
        from aegisScout.utils import encryption
        key_file = tmp_path / "subdir" / "fernet.key"  # parent doesn't exist
        monkeypatch.setattr(encryption, "_KEY_FILE", key_file)
        monkeypatch.delenv("AEGIS_FERNET_KEY", raising=False)

        # First call creates the file
        loaded = encryption._load_key()

        assert key_file.exists()
        assert len(loaded) == 44  # Fernet key is 32 bytes base64-encoded = 44 chars
        # Permissions — only meaningful on POSIX, but we always chmod
        if os.name == "posix":
            mode = stat.S_IMODE(key_file.stat().st_mode)
            assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"

    def test_env_key_takes_precedence_over_key_file(self, tmp_path, monkeypatch):
        from aegisScout.utils import encryption
        key_file = tmp_path / "fernet.key"
        key_file.write_bytes(b"file-key-do-not-use")
        monkeypatch.setattr(encryption, "_KEY_FILE", key_file)
        env_key = _key().decode()
        monkeypatch.setenv("AEGIS_FERNET_KEY", env_key)

        loaded = encryption._load_key()
        assert loaded == env_key.encode()

    def test_env_with_whitespace_is_stripped(self, monkeypatch):
        from aegisScout.utils import encryption
        key = _key().decode()
        monkeypatch.setenv("AEGIS_FERNET_KEY", "  " + key + "\n")
        loaded = encryption._load_key()
        assert loaded == key.encode()

    def test_missing_env_and_missing_file_auto_creates_key(self, tmp_path, monkeypatch):
        from aegisScout.utils import encryption
        key_file = tmp_path / "subdir" / "nope.key"
        monkeypatch.setattr(encryption, "_KEY_FILE", key_file)
        monkeypatch.delenv("AEGIS_FERNET_KEY", raising=False)

        loaded = encryption._load_key()

        assert key_file.exists()
        Fernet(loaded)
        assert encryption._load_key() == loaded


# ---------------------------------------------------------------------------
# Compatibility shim — the project still imports encrypt_json_file /
# decrypt_json_file from elsewhere. The new module must keep these working,
# but decrypt_json_file MUST raise on failure (no plaintext fallback).
# ---------------------------------------------------------------------------

class TestJsonFileApiCompatibility:
    def test_encrypt_decrypt_json_file_roundtrip(self, tmp_path, monkeypatch):
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())

        target = tmp_path / "subdir" / "session.json"
        payload = {"username": "u", "session_id": "abc"}
        encryption.encrypt_json_file(target, payload)
        assert target.exists()

        recovered = encryption.decrypt_json_file(target)
        assert recovered == payload

    def test_decrypt_json_file_raises_on_corruption(self, tmp_path, monkeypatch):
        """The original code silently returned {} on any failure — including
        on tampered files. The new code MUST raise instead."""
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())

        target = tmp_path / "session.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"this is not a valid fernet token")
        with pytest.raises(ValueError):
            encryption.decrypt_json_file(target)

    def test_decrypt_json_file_raises_on_plain_json(self, tmp_path, monkeypatch):
        """Original code fell back to reading the file as raw JSON when
        decryption failed — that fallback must be GONE."""
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())

        target = tmp_path / "session.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        # File is valid JSON, but NOT encrypted. The old code returned it.
        # The new code must refuse (it cannot know whether the file was
        # never-encrypted or had its key rotated).
        target.write_text('{"plain": true}', encoding="utf-8")
        with pytest.raises(ValueError):
            encryption.decrypt_json_file(target)

    def test_decrypt_json_file_missing_returns_empty_dict(self, tmp_path, monkeypatch):
        """A missing file is still a soft "no data yet" case — returns
        {} rather than raising. This is the only acceptable silent path."""
        from aegisScout.utils import encryption
        key = _key()
        monkeypatch.setenv("AEGIS_FERNET_KEY", key.decode())

        target = tmp_path / "never_created.json"
        assert encryption.decrypt_json_file(target) == {}

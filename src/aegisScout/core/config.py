"""
Pydantic-Settings configuration for aegisScout.

All values come from environment variables / ``.env`` file. The
singleton is exposed as ``settings`` and can be mutated in-process via
``get_settings()`` (read) / ``set_settings(**overrides)`` (write).

Mod-B (full Instagram automation) is ALWAYS default-dry-run.
The user must explicitly opt-in by running ``aegisScout config set-acknowledged``
which flips ``mod_b_acknowledged`` to True. The actual automation code
should refuse to run if ``mod_b_acknowledged`` is False.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# .env path resolution
# ---------------------------------------------------------------------------

def get_env_path() -> str:
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).parent / ".env")
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists() and cwd_env.is_file():
        return str(cwd_env)
    # .../src/aegisScout/core/config.py -> project root = parents[3]
    root_env = Path(__file__).resolve().parents[3] / ".env"
    return str(root_env)


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------

class AppSettings(BaseSettings):
    # --- LLM provider settings ---
    llm_primary_provider: str = "deepseek"
    llm_fallback_provider: Optional[str] = "anthropic"
    llm_timeout_seconds: int = 60
    # Backwards-compat alias: some callers/tests use `llm_timeout` directly.
    # Both names point at the same canonical value (the seconds-suffixed one).
    llm_timeout: int = 60
    deepseek_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    provider_primary: Optional[str] = None  # alias for llm_primary_provider
    provider_fallback: Optional[str] = None  # alias for llm_fallback_provider

    # --- Discovery provider settings ---
    discovery_primary_provider: str = "osm"
    google_places_api_key: Optional[str] = None
    opencage_api_key: Optional[str] = None
    google_custom_search_api_key: Optional[str] = None
    google_custom_search_cx: Optional[str] = None

    # --- Instagram credentials (Mod B only) ---
    instagram_username: Optional[str] = None
    instagram_password: Optional[str] = None
    instagram_session_encryption_key: Optional[str] = None

    # --- Notification channels ---
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    notify_email_smtp_host: Optional[str] = None
    notify_email_smtp_port: int = 587
    notify_email_smtp_user: Optional[str] = None
    notify_email_smtp_pass: Optional[str] = None
    notify_email_username: Optional[str] = None
    notify_email_password: Optional[str] = None
    notify_email_recipient: str = ""  # who receives the alerts
    notify_email_imap_host: Optional[str] = None
    notify_email_imap_port: int = 993
    notify_email_imap_username: Optional[str] = None
    notify_email_imap_password: Optional[str] = None

    # --- Proxy and Scraping APIs ---
    proxy_pool: Optional[str] = None
    scraper_api_key: Optional[str] = None
    zenrows_api_key: Optional[str] = None
    crawlbase_api_key: Optional[str] = None
    apify_api_key: Optional[str] = None

    # --- Other Third-Party Session Cookies ---
    linkedin_session_cookie: Optional[str] = None

    # --- Ollama model ---
    ollama_model: str = "llama3.2:3b"

    # --- General / runtime ---
    outreach_mode: str = "assisted"        # "assisted" | "full_auto"
    max_daily_outreach: int = 15
    email_warmup_active: bool = False

    # --- Mod-B safety defaults (always-on dry-run, require explicit ack) ---
    instagram_dry_run: bool = True
    mod_b_acknowledged: bool = False

    # --- Database override (empty = use default SQLite file in ./data) ---
    database_url: str = ""

    # --- Pydantic config ---
    model_config = SettingsConfigDict(
        env_file=get_env_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __setattr__(self, name: str, value) -> None:
        """
        Keep ``llm_timeout`` and ``llm_timeout_seconds`` in lockstep.
        Setting either name updates the other so monkeypatched tests and
        the canonical field never drift apart.
        """
        if name == "llm_timeout":
            super().__setattr__("llm_timeout_seconds", value)
            super().__setattr__(name, value)
            return
        if name == "llm_timeout_seconds":
            super().__setattr__("llm_timeout", value)
            super().__setattr__(name, value)
            return
        super().__setattr__(name, value)

    def get_encryption_key(self) -> bytes:
        """
        Return the configured Fernet encryption key as bytes.

        Backwards-compat: honours the legacy env var
        ``INSTAGRAM_SESSION_ENCRYPTION_KEY`` first (existing installations),
        then ``AEGIS_FERNET_KEY`` (new canonical name). Raises ``ValueError``
        with a clear message if neither is set or the value is invalid.
        """
        legacy = (self.instagram_session_encryption_key or "").strip()
        canonical = (os.environ.get("AEGIS_FERNET_KEY") or "").strip()
        key_str = canonical or legacy
        if not key_str:
            raise ValueError(
                "Fernet key is not configured. Either set AEGIS_FERNET_KEY "
                "or INSTAGRAM_SESSION_ENCRYPTION_KEY in your .env, or rely "
                "on the auto-created data/.fernet_key file. To generate a "
                "key manually:\n"
                "  python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
        try:
            Fernet(key_str.encode("utf-8"))
        except Exception as e:
            raise ValueError(
                "Fernet key is not a valid Fernet format. Generate one with "
                "`python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\"` and put it in "
                "your .env as AEGIS_FERNET_KEY."
            ) from e
        return key_str.encode("utf-8")


# ---------------------------------------------------------------------------
# Singleton + mutators
# ---------------------------------------------------------------------------

_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Return the cached settings singleton, creating it on first call."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def set_settings(**overrides) -> AppSettings:
    """Mutate the in-process settings singleton.

    Only the fields declared on :class:`AppSettings` are accepted; unknown
    keys raise ``ValueError`` (not silently dropped). The mutation is
    in-process only — it does NOT write to the ``.env`` file.
    """
    global _settings
    base = get_settings().model_dump()
    for key, value in overrides.items():
      if key not in base:
        raise ValueError(f"Unknown settings field: {key!r}")
      base[key] = value
    _settings = AppSettings(**base)
    return _settings


# Module-level singleton — also exposes a Settings alias for back-compat
# with code that imported `from aegisScout.core.config import settings`.
settings = get_settings()
Settings = AppSettings  # re-export under the original name

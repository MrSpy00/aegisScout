"""
SQLite engine + session factory for aegisScout.

Key design points (post-audit):

* PRAGMAs are applied on EVERY new connection via a SQLAlchemy
  ``connect`` event listener — not via a one-shot session that drops
  the settings as soon as the connection closes. This is the only
  way to guarantee foreign keys (and the rest of the perf pragmas)
  are on for every connection, including the ones opened by ``cli``
  scripts that bypass ``init_db()``.

* A ``make_engine(url=None)`` factory builds a fresh engine. ``url``
  defaults to ``$AEGIS_DATABASE_URL`` (env var), then
  ``./data/aegisScout.db`` (parent dirs created on demand).

* ``init_db(engine)`` runs ``SQLModel.metadata.create_all`` and applies
  the project-specific migrations that previously lived in the
  module-level ``init_db()``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine, text


DEFAULT_DB_FILENAME = "aegisScout.db"
DEFAULT_RELATIVE_DIR = "data"
DEFAULT_SESSION_COLUMN_DEF = "INTEGER REFERENCES user_sessions(id) DEFAULT 1"


# ---------------------------------------------------------------------------
# Path / URL resolution
# ---------------------------------------------------------------------------

def _default_url() -> str:
    """
    Build the default SQLite URL.

    Order:
      1. ``$AEGIS_DATABASE_URL``  (full URL such as
         ``sqlite:///path/to.db`` or ``postgresql+psycopg://...``)
      2. ``./data/aegisScout.db``  (dev / frozen-exe layout)
    """
    env_url = os.environ.get("AEGIS_DATABASE_URL", "").strip()
    if env_url:
        return env_url

    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        # .../src/aegisScout/core/database.py -> project root = parents[3]
        base = Path(__file__).resolve().parents[3]
    data_dir = base / DEFAULT_RELATIVE_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / DEFAULT_DB_FILENAME).resolve()}"


# Module-level attribute that mirrors the engine's effective URL. Tests
# monkeypatch this BEFORE importing/re-using the module-level engine to
# route the project at an in-memory or temp-file DB.
DATABASE_URL: str = _default_url()


# ---------------------------------------------------------------------------
# Connection-level PRAGMAs
# ---------------------------------------------------------------------------

def _register_sqlite_pragmas(engine) -> None:
    """Attach a ``connect`` listener that applies PRAGMAs to every new
    SQLite connection. Foreign keys MUST be set this way — they are
    per-connection, not per-database."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
        # Only SQLite supports PRAGMA. Skip silently for other dialects.
        try:
            is_sqlite = "sqlite" in type(dbapi_connection).__module__.lower()
        except Exception:
            is_sqlite = False
        if not is_sqlite:
            return

        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # SQLCipher support setup
            try:
                from aegisScout.utils.encryption import _load_key
                key_hex = _load_key().hex()
                cursor.execute(f"PRAGMA key = \"x'{key_hex}'\"")
            except Exception:
                pass
        except Exception as e:
            from aegisScout.utils.logger import get_logger
            get_logger("core.database").warning(
                f"Could not set SQLite pragmas: {e}"
            )
        finally:
            cursor.close()


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------

def make_engine(url: Optional[str] = None):
    """Create a fresh SQLAlchemy engine.

    Parameters
    ----------
    url:
        Optional override. If absent, falls back to
        ``$AEGIS_DATABASE_URL`` then ``./data/aegisScout.db``.
    """
    effective_url = (url or _default_url()).strip()
    if not effective_url:
        raise ValueError(
            "No database URL configured. Set AEGIS_DATABASE_URL or pass "
            "url=... to make_engine()."
        )

    connect_args: dict = {}
    if effective_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False, "timeout": 30}

    kwargs = {"pool_pre_ping": True}
    if not effective_url.endswith(":memory:"):
        kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_recycle": 3600,
        })

    engine = create_engine(
        effective_url,
        echo=False,
        connect_args=connect_args,
        **kwargs,
    )
    _register_sqlite_pragmas(engine)
    return engine


# Module-level engine for callers that import it directly (cli scripts,
# background workers). Created lazily so tests can override ``AEGIS_DATABASE_URL``
# before the first import-time access.
engine = make_engine()


def get_database_url() -> str:
    """Return the URL of the module-level engine (for tests + CLI introspection)."""
    global DATABASE_URL
    try:
        DATABASE_URL = str(engine.url)
    except Exception:
        pass
    return DATABASE_URL


# ---------------------------------------------------------------------------
# init_db / migrations
# ---------------------------------------------------------------------------

def init_db(engine_to_use=None) -> None:
    """
    Initialize the database:
      1. Apply WAL mode & performance pragmas (via the connect listener).
      2. Create all tables.
      3. Seed the default ``UserSession`` (id=1).
      4. Run incremental column-addition migrations.
    """
    if engine_to_use is None:
        engine_to_use = engine

    # Import models here so SQLModel.metadata knows about them.
    from aegisScout.core.models import (
        ActivityLog,
        Campaign,
        DiscoveryDraft,
        Lead,
        Message,
        ResearchNote,
        SearchPreset,
        UserSession,
        CrmLog,
        SmtpAccount,
    )
    from aegisScout.utils.logger import get_logger
    db_logger = get_logger("core.database")

    SQLModel.metadata.create_all(engine_to_use)

    with Session(engine_to_use) as session:
        # --- Seed default session ---
        try:
            cnt = session.exec(
                text("SELECT COUNT(*) FROM user_sessions WHERE id = 1")
            ).first()
            if not cnt or cnt[0] == 0:
                session.exec(
                    text(
                        "INSERT OR IGNORE INTO user_sessions (id, name, created_at) "
                        "VALUES (1, 'Varsayılan Oturum', CURRENT_TIMESTAMP)"
                    )
                )
                session.commit()
                db_logger.info("Default UserSession seeded successfully.")
        except Exception as e:
            db_logger.error(f"Failed to seed default UserSession: {e}")
            session.rollback()

        # --- Incremental migrations (column additions) ---
        _run_migrations(session, db_logger)


def _column_exists(session: Session, table: str, column: str) -> bool:
    try:
        rows = session.exec(text(f"PRAGMA table_info({table})")).all()
        return any(row[1] == column for row in rows)
    except Exception:
        return False


def _run_migrations(session: Session, db_logger) -> None:
    migrations = [
        ("leads", "campaign_id", "INTEGER REFERENCES campaigns(id)"),
        ("leads", "session_id", DEFAULT_SESSION_COLUMN_DEF),
        ("campaigns", "session_id", DEFAULT_SESSION_COLUMN_DEF),
        ("activity_log", "session_id", DEFAULT_SESSION_COLUMN_DEF),
        ("leads", "instagram_bio", "TEXT"),
        ("leads", "youtube_url", "TEXT"),
        ("leads", "linkedin_url", "TEXT"),
        ("leads", "tiktok_url", "TEXT"),
        ("leads", "facebook_url", "TEXT"),
        ("leads", "telegram_url", "TEXT"),
        ("leads", "twitter_url", "TEXT"),
        ("leads", "email", "TEXT"),
        ("leads", "kvkk_compliant", "BOOLEAN"),
        ("leads", "has_broken_links", "BOOLEAN"),
        ("leads", "broken_links_details", "TEXT"),
        ("leads", "page_speed_desktop", "INTEGER"),
        ("leads", "page_speed_mobile", "INTEGER"),
        ("leads", "technologies", "TEXT"),
        ("leads", "priority_score", "REAL"),
        ("leads", "priority_label", "TEXT"),
        ("messages", "smtp_account_id", "INTEGER REFERENCES smtp_accounts(id)"),
        ("messages", "message_type", "TEXT DEFAULT 'initial'"),
        ("campaigns", "followup_delay_1_days", "INTEGER DEFAULT 3"),
        ("campaigns", "followup_subject_1", "TEXT"),
        ("campaigns", "followup_body_1", "TEXT"),
        ("campaigns", "followup_delay_2_days", "INTEGER DEFAULT 7"),
        ("campaigns", "followup_subject_2", "TEXT"),
        ("campaigns", "followup_body_2", "TEXT"),
        ("leads", "screenshot_path", "TEXT"),
        ("leads", "visual_audit_notes", "TEXT"),
        ("leads", "outreach_hook", "TEXT"),
        ("leads", "email_verification_status", "TEXT"),
        ("leads", "email_verification_details", "TEXT"),
    ]

    for table, column, col_def in migrations:
        if not _column_exists(session, table, column):
            db_logger.info(f"Migration: adding '{column}' to '{table}'...")
            try:
                session.exec(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                )
                session.commit()
                db_logger.info(f"Migration OK: {table}.{column} added.")
            except Exception as e:
                db_logger.error(f"Migration failed ({table}.{column}): {e}")
                session.rollback()


def get_session():
    """Dependency-injection compatible session generator (for the existing
    module-level engine). Prefer ``make_engine`` + ``init_db`` + a
    per-test engine in new code."""
    with Session(engine) as session:
        yield session


__all__ = [
    "engine",
    "make_engine",
    "init_db",
    "get_session",
    "get_database_url",
    "DATABASE_URL",
    "DEFAULT_DB_FILENAME",
    "DEFAULT_RELATIVE_DIR",
]

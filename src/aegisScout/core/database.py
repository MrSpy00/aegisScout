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
from typing import Optional, Any

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
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")
            
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


def sqlite_retry_on_lock(max_retries: int = 5, delay: float = 0.2):
    """Decorator to retry DB operations if SQLite database is locked."""
    import time
    import functools
    import sqlite3

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (sqlite3.OperationalError, Exception) as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                    else:
                        raise
        return wrapper
    return decorator


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
    if effective_url.lower().startswith("sqlite"):
        connect_args = {"check_same_thread": False, "timeout": 30}

    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if ":memory:" in effective_url.lower():
        from sqlalchemy.pool import StaticPool
        kwargs["poolclass"] = StaticPool
    elif effective_url.lower().startswith("sqlite"):
        from sqlalchemy.pool import NullPool
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update({
            "pool_size": 30,
            "max_overflow": 60,
            "pool_recycle": 1800,
            "pool_timeout": 30,
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
            cnt = session.execute(
                text("SELECT COUNT(*) FROM user_sessions WHERE id = 1")
            ).first()
            if not cnt or cnt[0] == 0:
                session.execute(
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


def _table_exists(session: Session, table: str) -> bool:
    try:
        r = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table}
        ).first()
        return bool(r)
    except Exception:
        return False


def _column_exists(session: Session, table: str, column: str) -> bool:
    if not _table_exists(session, table):
        return True
    try:
        rows = session.execute(text(f"PRAGMA table_info('{table}')")).all()
        return any(row[1] == column for row in rows)
    except Exception:
        return False


def _run_migrations(session: Session, db_logger) -> None:
    from sqlalchemy import inspect
    engine_to_use = session.bind

    existing_columns: dict[str, set[str]] = {}
    try:
        if engine_to_use:
            inspector = inspect(engine_to_use)
            for table in inspector.get_table_names():
                existing_columns[table] = {c["name"] for c in inspector.get_columns(table)}
    except Exception as e:
        db_logger.warning(f"Could not inspect table columns: {e}")

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
        ("leads", "profile_image_url", "TEXT"),
        ("leads", "osint_data", "TEXT"),
        ("leads", "scan_depth", "TEXT DEFAULT 'medium'"),
        ("leads", "phone_carrier", "TEXT"),
        ("leads", "phone_type", "TEXT"),
        ("leads", "lat", "REAL"),
        ("leads", "lon", "REAL"),
        ("leads", "place_id", "TEXT"),
        ("leads", "reviews_json", "TEXT"),
    ]

    for table, column, col_def in migrations:
        cols_for_table = existing_columns.get(table)
        if cols_for_table is not None and column in cols_for_table:
            continue

        db_logger.info(f"Migration: adding '{column}' to '{table}'...")
        try:
            session.execute(
                text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
            )
            session.commit()
            if cols_for_table is not None:
                cols_for_table.add(column)
            db_logger.info(f"Migration OK: {table}.{column} added.")
        except Exception as e:
            err_str = str(e).lower()
            if "duplicate column" in err_str or "already exists" in err_str:
                session.rollback()
                if cols_for_table is not None:
                    cols_for_table.add(column)
            else:
                db_logger.error(f"Migration failed ({table}.{column}): {e}")
                session.rollback()

    # Create Compound Indexes for fast queries
    indexes = [
        ("idx_leads_status_score", "CREATE INDEX IF NOT EXISTS idx_leads_status_score ON leads (status, website_quality_score);"),
        ("idx_leads_created", "CREATE INDEX IF NOT EXISTS idx_leads_created ON leads (discovered_at);"),
        ("idx_leads_domain", "CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads (website_url);"),
        ("idx_leads_phone", "CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads (phone);"),
    ]
    for idx_name, idx_sql in indexes:
        try:
            session.execute(text(idx_sql))
            session.commit()
        except Exception as e:
            db_logger.warning(f"Failed to create index {idx_name}: {e}")
            session.rollback()


def deduplicate_leads(session: Session) -> int:
    """Intelligent lead deduplication based on domain/website, business name, and phone."""
    from aegisScout.core.models import Lead
    from sqlmodel import select

    leads = session.exec(select(Lead)).all()
    seen_domains: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    seen_phones: dict[str, int] = {}
    merged_count = 0

    for lead in leads:
        if not lead.id:
            continue
        url_val = getattr(lead, "website_url", None) or getattr(lead, "domain", None)
        domain_key = url_val.strip().lower() if url_val else None
        name_key = lead.business_name.strip().lower() if lead.business_name else None
        phone_key = lead.phone.strip() if lead.phone else None

        primary_id = None
        if domain_key and domain_key in seen_domains:
            primary_id = seen_domains[domain_key]
        elif name_key and name_key in seen_names:
            primary_id = seen_names[name_key]
        elif phone_key and phone_key in seen_phones:
            primary_id = seen_phones[phone_key]

        if primary_id and primary_id != lead.id:
            primary_lead = session.get(Lead, primary_id)
            if primary_lead:
                # Merge missing values into primary
                if not primary_lead.email and lead.email:
                    primary_lead.email = lead.email
                if not primary_lead.phone and lead.phone:
                    primary_lead.phone = lead.phone
                if not primary_lead.website_url and lead.website_url:
                    primary_lead.website_url = lead.website_url
                
                score_lead = getattr(lead, "score", 0) or 0
                score_primary = getattr(primary_lead, "score", 0) or 0
                if score_lead > score_primary:
                    primary_lead.score = score_lead
                session.delete(lead)
                merged_count += 1
                continue

        # Register primary keys
        if domain_key:
            seen_domains[domain_key] = lead.id
        if name_key:
            seen_names[name_key] = lead.id
        if phone_key:
            seen_phones[phone_key] = lead.id

    if merged_count > 0:
        session.commit()
    return merged_count


def get_session():
    """Dependency-injection compatible session generator (for the existing
    module-level engine). Prefer ``make_engine`` + ``init_db`` + a
    per-test engine in new code."""
    with Session(engine) as session:
        yield session


def increment_usage(
    provider: str,
    action: str,
    count: int = 1,
    estimated_cost_usd: float = 0.0,
) -> None:
    """Atomically increment API usage counter for today.

    Uses INSERT OR IGNORE + UPDATE to handle concurrent access safely.
    Silently swallows all errors — usage tracking must never break the main flow.
    """
    from datetime import date as _date
    try:
        today = _date.today().isoformat()
        with Session(engine) as session:
            # Try INSERT first (new row for today)
            session.exec(
                text(
                    "INSERT OR IGNORE INTO api_usage_daily (date, provider, action, count, estimated_cost_usd) "
                    "VALUES (:date, :provider, :action, 0, 0)"
                ),
                params={"date": today, "provider": provider, "action": action},
            )
            session.exec(
                text(
                    "UPDATE api_usage_daily "
                    "SET count = count + :count, estimated_cost_usd = estimated_cost_usd + :cost "
                    "WHERE date = :date AND provider = :provider AND action = :action"
                ),
                params={
                    "count": count,
                    "cost": estimated_cost_usd,
                    "date": today,
                    "provider": provider,
                    "action": action,
                },
            )
            session.commit()
    except Exception:
        pass  # Never let tracking errors propagate


def get_daily_usage(days: int = 7) -> dict:
    """Return API usage stats for the last N days (default 7).

    Returns a dict with:
        - ``today``: {provider: {action: {count, cost}}} for today
        - ``totals``: {action: count} aggregated across providers for today
        - ``history``: list of {date, total_count, total_cost} for the last N days
    """
    from datetime import date as _date, timedelta as _timedelta
    try:
        today = _date.today().isoformat()
        since = (_date.today() - _timedelta(days=days - 1)).isoformat()
        with Session(engine) as session:
            rows = session.exec(
                text(
                    "SELECT date, provider, action, count, estimated_cost_usd "
                    "FROM api_usage_daily WHERE date >= :since ORDER BY date DESC"
                ),
                params={"since": since},
            ).all()

        today_data: dict = {}
        totals: dict = {}
        history_map: dict = {}
        for row in rows:
            d, prov, act, cnt, cost = row
            if d == today:
                today_data.setdefault(prov, {})[act] = {
                    "count": cnt,
                    "cost": round(cost, 6),
                }
                totals[act] = totals.get(act, 0) + cnt
            history_map.setdefault(d, {"date": d, "total_count": 0, "total_cost": 0.0})
            history_map[d]["total_count"] += cnt
            history_map[d]["total_cost"] = round(history_map[d]["total_cost"] + cost, 6)

        history = sorted(history_map.values(), key=lambda x: x["date"])
        return {"today": today_data, "totals": totals, "history": history}
    except Exception as e:
        return {"today": {}, "totals": {}, "history": [], "error": str(e)}


__all__ = [
    "engine",
    "make_engine",
    "init_db",
    "get_session",
    "get_database_url",
    "sqlite_retry_on_lock",
    "deduplicate_leads",
    "increment_usage",
    "get_daily_usage",
    "DATABASE_URL",
    "DEFAULT_DB_FILENAME",
    "DEFAULT_RELATIVE_DIR",
]


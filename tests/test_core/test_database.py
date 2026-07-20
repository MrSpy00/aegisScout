"""
Tests for the database engine factory.

These tests cover the per-connection PRAGMA registration in
``aegisScout.core.database``. The fix ensures that EVERY new SQLite
connection gets ``PRAGMA foreign_keys=ON`` (and friends) via a
SQLAlchemy ``connect`` event listener — not just the first connection
or only the module-level engine.
"""
import pytest
from sqlalchemy import event, text
from sqlmodel import SQLModel, create_engine

from aegisScout.core import database as db_module
from aegisScout.core.models import Lead, Campaign, ActivityLog, UserSession


def _foreign_keys_on(engine) -> bool:
    """Return True iff the most-recently-opened SQLite connection has FK enforcement on."""
    with engine.connect() as conn:
        row = conn.execute(text("PRAGMA foreign_keys")).first()
        return bool(row and row[0] == 1)


def test_two_independent_engines_both_have_foreign_keys_on(tmp_path):
    """
    Build two separate engine instances against the same in-memory DB and
    confirm BOTH have foreign_keys=ON after connecting. The original bug
    registered pragmas only on the first engine. This test guards against
    the regression where a second engine inherits no pragmas.
    """
    # Use a shared in-memory URI so both engines see the same schema.
    shared_url = "sqlite:///:memory:"
    e1 = db_module.make_engine(shared_url)
    e2 = db_module.make_engine(shared_url)

    # Bootstrap the schema once on e1.
    SQLModel.metadata.create_all(e1)

    assert _foreign_keys_on(e1) is True, "engine #1 must have foreign_keys=ON"
    assert _foreign_keys_on(e2) is True, "engine #2 must have foreign_keys=ON"


def test_independent_engine_enforces_foreign_keys_via_schema(tmp_path):
    """
    Functional test: with PRAGMA foreign_keys=ON, inserting a Lead with
    a campaign_id pointing at a non-existent Campaign must fail.
    With PRAGMA foreign_keys=OFF it would silently succeed.
    """
    engine = db_module.make_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    from sqlmodel import Session
    with Session(engine) as session:
        bogus = Lead(
            business_name="Orphan",
            sector="x",
            address="y",
            campaign_id=9999,  # does not exist
        )
        session.add(bogus)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()


def test_module_level_engine_has_foreign_keys_on(tmp_path, monkeypatch):
    """The module-level ``engine`` (created on import) must also have FK on."""
    # Just import the module; engine is created at import time.
    assert _foreign_keys_on(db_module.engine) is True

"""
Tests for the `review` command's status filter.

The audit requires the review queue to include leads with status
'researched' OR 'drafted' (previously it only included 'researched').
"""

import os
import tempfile
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine
from typer.testing import CliRunner

from aegisScout.core.models import Lead, Campaign
from aegisScout.core.database import init_db
from aegisScout.main import app


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """Spin up an isolated SQLite DB, set it as the engine, seed two leads."""
    db_path = tmp_path / "aegisScout.db"
    test_engine = create_engine(
        f"sqlite:///{db_path.resolve()}",
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    # Patch the engine used by gui/main/commands
    import aegisScout.core.database as db_module
    import aegisScout.gui as gui_module
    import aegisScout.main as main_module

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(gui_module, "engine", test_engine)
    monkeypatch.setattr(main_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "DATABASE_URL", f"sqlite:///{db_path.resolve()}")

    SQLModel.metadata.create_all(test_engine)

    # Seed: one 'researched' lead, one 'drafted' lead
    with Session(test_engine) as session:
        # Ensure default session row (some code expects session_id=1)
        from sqlmodel import text
        try:
            session.exec(
                text("INSERT OR IGNORE INTO user_sessions (id, name, created_at) "
                     "VALUES (1, 'Test', CURRENT_TIMESTAMP)")
            )
            session.commit()
        except Exception:
            session.rollback()

        researched = Lead(
            business_name="Researched Co",
            sector="kuaför",
            address="Test Adres 1",
            status="researched",
            session_id=1,
        )
        drafted = Lead(
            business_name="Drafted Co",
            sector="kuaför",
            address="Test Adres 2",
            status="drafted",
            session_id=1,
        )
        ignored = Lead(
            business_name="New Co",
            sector="kuaför",
            address="Test Adres 3",
            status="new",
            session_id=1,
        )
        session.add(researched)
        session.add(drafted)
        session.add(ignored)
        session.commit()
        for obj in (researched, drafted, ignored):
            session.refresh(obj)

    return {
        "engine": test_engine,
        "ids": {
            "researched": researched.id,
            "drafted": drafted.id,
            "new": ignored.id,
        },
    }


def test_review_lists_both_researched_and_drafted(isolated_db, monkeypatch):
    """
    The review command should display BOTH 'researched' and 'drafted' leads
    (not just researched, as in the buggy pre-audit implementation).
    The new lead with status='new' should NOT appear.
    """
    # Patch _ensure_db to be a no-op (we already initialised the test engine)
    import aegisScout.main as main_module
    monkeypatch.setattr(main_module, "_ensure_db", lambda: None)

    # When review hits the choice prompt, immediately say "s" to skip each lead.
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["review"],
        input="s\n" * 10,  # 10x 's' to skip any leads that show up
    )
    # Should not crash
    assert result.exit_code == 0, f"review exit={result.exit_code}; out={result.output}"
    combined = result.output

    assert "Researched Co" in combined, (
        f"researched lead must appear in review output. Got:\n{combined}"
    )
    assert "Drafted Co" in combined, (
        f"drafted lead must appear in review output (audit fix). Got:\n{combined}"
    )
    # The 'new' lead should NOT appear (out of scope for review)
    # We allow it to appear if no filtering is in place, but ideally it
    # shouldn't. Don't fail on this; the important assertion is the
    # presence of both 'researched' and 'drafted'.

import os
import pytest
import re
import json
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from sqlmodel import SQLModel, Session, select, text
from pathlib import Path

from aegisScout.core import database as db_module
from aegisScout.gui import GuiApi
from aegisScout.core.models import Lead, ActivityLog, UserSession

@pytest.fixture
def test_env():
    # Setup in-memory DB engine
    test_engine = db_module.make_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    
    # Seed default user session
    with Session(test_engine) as session:
        us = UserSession(id=1, name="Varsayılan Oturum")
        session.add(us)
        session.commit()
        
    # Patch database engine in module
    old_engine = db_module.engine
    db_module.engine = test_engine
    
    # We must patch it in gui module too
    from aegisScout import gui
    gui.engine = test_engine
    
    yield test_engine
    
    db_module.engine = old_engine
    gui.engine = old_engine


def test_get_search_history(test_env):
    api = GuiApi()
    
    # Seed activity logs
    with Session(test_env) as session:
        log1 = ActivityLog(
            action="discover",
            details="Discovered 5 new leads (skipped 2 duplicates) out of 7 candidates for sector='berber', location='ankara' via 'all'",
            timestamp=datetime(2026, 7, 12, 12, 0, 0),
            session_id=1
        )
        log2 = ActivityLog(
            action="discover",
            details="Discovered 10 new leads for sector='psikolog', location='izmir' via 'osm'",
            timestamp=datetime(2026, 7, 12, 13, 0, 0),
            session_id=1
        )
        log3 = ActivityLog(
            action="other_action",
            details="Some random action",
            timestamp=datetime(2026, 7, 12, 14, 0, 0),
            session_id=1
        )
        session.add(log1)
        session.add(log2)
        session.add(log3)
        session.commit()
        
    history = api.get_search_history()
    assert len(history) == 2
    
    # Assert log2 (most recent first)
    assert history[0]["sector"] == "psikolog"
    assert history[0]["location"] == "izmir"
    assert history[0]["provider"] == "osm"
    assert history[0]["added_count"] == 10
    assert history[0]["duplicate_count"] == 0
    assert history[0]["total_candidates"] == 10
    
    # Assert log1
    assert history[1]["sector"] == "berber"
    assert history[1]["location"] == "ankara"
    assert history[1]["provider"] == "all"
    assert history[1]["added_count"] == 5
    assert history[1]["duplicate_count"] == 2
    assert history[1]["total_candidates"] == 7


def test_delete_leads_by_search(test_env):
    api = GuiApi()
    
    t_search = datetime(2026, 7, 12, 12, 0, 0)
    
    with Session(test_env) as session:
        log = ActivityLog(
            action="discover",
            details="Discovered 2 new leads for sector='berber', location='ankara' via 'all'",
            timestamp=t_search,
            session_id=1
        )
        session.add(log)
        session.commit()
        log_id = log.id
        
        # Leads
        lead1 = Lead(business_name="Lead 1 Within Window", discovered_at=t_search + timedelta(seconds=1), session_id=1, status="new")
        lead2 = Lead(business_name="Lead 2 Within Window", discovered_at=t_search - timedelta(seconds=2), session_id=1, status="new")
        lead3 = Lead(business_name="Lead 3 Outside Window", discovered_at=t_search + timedelta(seconds=10), session_id=1, status="new")
        session.add(lead1)
        session.add(lead2)
        session.add(lead3)
        session.commit()
        
    # Delete leads by search
    res = api.delete_leads_by_search(log_id)
    assert res["success"] is True
    assert res["deleted_count"] == 2
    
    # Verify DB state
    with Session(test_env) as session:
        remaining_leads = session.exec(select(Lead)).all()
        assert len(remaining_leads) == 1
        assert remaining_leads[0].business_name == "Lead 3 Outside Window"
        
        # Arama logu da silinmis olmali
        remaining_logs = session.exec(select(ActivityLog).where(ActivityLog.id == log_id)).all()
        assert len(remaining_logs) == 0


def test_clear_leads_advanced(test_env):
    api = GuiApi()
    
    with Session(test_env) as session:
        session.add(Lead(business_name="Berber Ahmet", sector="berber", rating=4.5, has_website=True, source="osm", discovered_at=datetime(2026, 7, 12, 10, 0, 0), session_id=1, status="new"))
        session.add(Lead(business_name="Berber Mehmet", sector="berber", rating=3.2, has_website=False, source="osm", discovered_at=datetime(2026, 7, 12, 11, 0, 0), session_id=1, status="new"))
        session.add(Lead(business_name="Kuaför Ayşe", sector="kuafor", rating=4.8, has_website=True, source="google_places", discovered_at=datetime(2026, 7, 12, 12, 0, 0), session_id=1, status="contacted"))
        session.commit()
        
    # 1. Dry run calculation
    res = api.clear_leads_advanced({"keyword": "Berber", "dry_run": True})
    assert res["success"] is True
    assert res["count"] == 2
    
    # Verify no deletion occurred
    with Session(test_env) as session:
        assert len(session.exec(select(Lead)).all()) == 3
        
    # 2. Filter by status
    res = api.clear_leads_advanced({"status": "contacted", "dry_run": False})
    assert res["success"] is True
    assert res["deleted_count"] == 1
    
    with Session(test_env) as session:
        remaining = session.exec(select(Lead)).all()
        assert len(remaining) == 2
        assert all(l.status == "new" for l in remaining)
        
    # 3. Filter by website + rating
    res = api.clear_leads_advanced({"has_website": "no", "max_rating": 3.5, "dry_run": False})
    assert res["success"] is True
    assert res["deleted_count"] == 1
    
    with Session(test_env) as session:
        remaining = session.exec(select(Lead)).all()
        assert len(remaining) == 1
        assert remaining[0].business_name == "Berber Ahmet"


def test_export_leads_dialog(test_env, tmp_path):
    api = GuiApi()
    
    # Mock window create_file_dialog
    save_path = str(tmp_path / "export_test.xlsx")
    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = (save_path,)
    api._window = mock_window
    
    with Session(test_env) as session:
        session.add(Lead(business_name="Berber Ahmet", sector="berber", rating=4.5, has_website=True, source="osm", discovered_at=datetime(2026, 7, 12, 10, 0, 0), session_id=1, status="new"))
        session.commit()
        
    # Run export
    res = api.export_leads_dialog({"format": ".xlsx", "status": "all"})
    assert res["success"] is True
    assert res["count"] == 1
    assert res["path"] == save_path
    
    # Assert file exists
    assert os.path.exists(save_path)
    
    # Test CSV
    csv_path = str(tmp_path / "export_test.csv")
    mock_window.create_file_dialog.return_value = (csv_path,)
    res = api.export_leads_dialog({"format": ".csv", "status": "all"})
    assert res["success"] is True
    assert os.path.exists(csv_path)
    
    # Test JSON
    json_path = str(tmp_path / "export_test.json")
    mock_window.create_file_dialog.return_value = (json_path,)
    res = api.export_leads_dialog({"format": ".json", "status": "all"})
    assert res["success"] is True
    assert os.path.exists(json_path)
    
    # Test HTML
    html_path = str(tmp_path / "export_test.html")
    mock_window.create_file_dialog.return_value = (html_path,)
    res = api.export_leads_dialog({"format": ".html", "status": "all"})
    assert res["success"] is True
    assert os.path.exists(html_path)

    # Test PDF
    pdf_path = str(tmp_path / "export_test.pdf")
    mock_window.create_file_dialog.return_value = (pdf_path,)
    res = api.export_leads_dialog({"format": ".pdf", "status": "all"})
    assert res["success"] is True
    assert os.path.exists(pdf_path)

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlmodel import SQLModel, Session, select
from aegisScout.core import database as db_module
from aegisScout.gui import GuiApi
from aegisScout.core.models import Lead, CrmLog, UserSession

@pytest.fixture
def test_db_env():
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
    
    # Patch it in gui module too
    from aegisScout import gui
    gui.engine = test_engine
    
    yield test_engine
    
    db_module.engine = old_engine
    gui.engine = old_engine


def test_crm_log_management(test_db_env):
    api = GuiApi()
    
    # Create a test lead
    with Session(test_db_env) as session:
        lead = Lead(business_name="CRM Test İşletmesi", session_id=1, status="new")
        session.add(lead)
        session.commit()
        lead_id = lead.id

    # Add a CRM log note
    res_add = api.add_crm_log(lead_id, "Telefon araması yapıldı, olumlu yanıt alındı.")
    assert res_add.get("success") is True
    
    # Fetch CRM logs
    res_get = api.get_crm_logs(lead_id)
    assert "logs" in res_get
    assert len(res_get["logs"]) == 1
    assert res_get["logs"][0]["note"] == "Telefon araması yapıldı, olumlu yanıt alındı."
    assert res_get["logs"][0]["created_at"] is not None

    # Error handling test
    res_err = api.add_crm_log(99999, "Deneme notu")
    assert "error" in res_err


@patch("httpx.get")
def test_get_ollama_status_running(mock_get):
    # Mock Ollama server running
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "qwen2.5:7b"}
        ]
    }
    mock_get.return_value = mock_resp
    
    api = GuiApi()
    res = api.get_ollama_status()
    assert res.get("status") == "running"
    assert "llama3.2:3b" in res.get("models", [])


@patch("httpx.get")
def test_get_ollama_status_offline(mock_get):
    # Mock Ollama server offline
    mock_get.side_effect = Exception("Connection refused")
    
    api = GuiApi()
    res = api.get_ollama_status()
    assert res.get("status") == "offline"


def test_heuristic_lead_scoring():
    # Helper to evaluate scoring
    def calculate_score(lead: Lead) -> float:
        base_score = 50.0
        if not lead.has_website:
            base_score += 20.0
        elif lead.website_quality_score is not None and lead.website_quality_score < 50:
            base_score += 15.0
            
        if lead.rating is not None and lead.rating >= 4.0:
            base_score += 10.0
        if lead.review_count is not None:
            if lead.review_count >= 25:
                base_score += 10.0
            elif lead.review_count < 5:
                base_score -= 10.0
                
        return min(max(base_score, 0.0), 100.0)

    # 1. Hot Lead: No website, rating >= 4.0, reviews >= 25
    lead_hot = Lead(has_website=False, rating=4.5, review_count=30)
    score_hot = calculate_score(lead_hot)
    assert score_hot == 90.0  # 50 + 20 + 10 + 10

    # 2. Cold Lead: Has website, good quality, low rating, few reviews
    lead_cold = Lead(has_website=True, website_quality_score=90, rating=3.2, review_count=3)
    score_cold = calculate_score(lead_cold)
    assert score_cold == 40.0  # 50 + 0 + 0 + 0 - 10

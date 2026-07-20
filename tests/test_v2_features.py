import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import SQLModel, Session
from datetime import datetime

from aegisScout.core import database as db_module
from aegisScout.core.models import Lead, UserSession, SmtpAccount
from aegisScout.utils.email_verifier import verify_email
from aegisScout.utils.encryption import encrypt_string
from aegisScout.outreach.warmup import run_p2p_warmup_cycle
from aegisScout.gui import GuiApi

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
        
    old_engine = db_module.engine
    db_module.engine = test_engine
    
    from aegisScout import gui
    old_gui_engine = gui.engine
    gui.engine = test_engine
    
    import aegisScout.core.waterfall
    old_waterfall_engine = aegisScout.core.waterfall.engine
    aegisScout.core.waterfall.engine = test_engine
    
    import aegisScout.outreach.warmup
    old_warmup_engine = aegisScout.outreach.warmup.engine
    aegisScout.outreach.warmup.engine = test_engine
    
    yield test_engine
    
    db_module.engine = old_engine
    gui.engine = old_gui_engine
    aegisScout.core.waterfall.engine = old_waterfall_engine
    aegisScout.outreach.warmup.engine = old_warmup_engine


# --- 1. Local Email Verifier Tests ---
def test_email_verifier_regex_and_disposable():
    # Test regex validation
    res = verify_email("invalid-email")
    assert res["status"] == "invalid"
    assert "format" in res["details"]
    
    res2 = verify_email("test@dispostable.com")
    assert res2["status"] == "invalid"
    assert "Geçici" in res2["details"]


@patch("dns.resolver.resolve")
@patch("socket.socket")
def test_email_verifier_dns_smtp(mock_socket_cls, mock_dns):
    # Mock DNS MX resolution
    mock_mx = MagicMock()
    mock_mx.exchange = "mail.gmail.com"
    mock_dns.return_value = [mock_mx]
    
    # Mock SMTP socket connection handshake
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = [
        b"220 mail.gmail.com ESMTP\r\n",
        b"250 mx.google.com\r\n",
        b"250 2.1.0 OK\r\n",
        b"250 2.1.5 OK\r\n"
    ]
    mock_socket_cls.return_value = mock_socket
    
    res = verify_email("test@gmail.com")
    assert res["status"] == "valid"
    assert "SMTP Doğrulama Başarılı" in res["details"]


# --- 2. Waterfall enrichment Cascade Tests ---
from aegisScout.core.waterfall import load_waterfall_config, save_waterfall_config, run_waterfall_enrichment

@pytest.mark.asyncio
@patch("aegisScout.discovery.web_scraper.WebScraper.audit_site")
@patch("aegisScout.core.waterfall.free_duckduckgo_search_emails")
@patch("aegisScout.core.waterfall.verify_email")
async def test_waterfall_orchestrator(mock_verify, mock_search, mock_audit, test_env):
    with Session(test_env) as session:
        lead = Lead(
            id=1,
            business_name="Test Business",
            website_url="https://testbusiness.com",
            status="new",
            session_id=1
        )
        session.add(lead)
        session.commit()

    config = load_waterfall_config()
    assert len(config) > 0
    assert any(step["step_id"] == "email_verify" for step in config)

    # Mock return values
    mock_audit.return_value = {
        "email": "test@testbusiness.com",
        "instagram_handle": "testbus",
        "phone": "123456789",
        "quality_score": 85
    }
    mock_search.return_value = ["test@testbusiness.com"]
    mock_verify.return_value = {"success": True, "status": "valid", "details": "Mock verification passed."}
    
    # Enable all steps
    for step in config:
        step["enabled"] = True
    save_waterfall_config(config)
    
    res = await run_waterfall_enrichment(1)
    assert res["success"] is True
    assert res["email"] == "test@testbusiness.com"
    assert res["verification_status"] == "valid"
    assert res["status"] == "researched"
    
    with Session(test_env) as session:
        updated_lead = session.get(Lead, 1)
        assert updated_lead.email == "test@testbusiness.com"
        assert updated_lead.email_verification_status == "valid"
        assert updated_lead.status == "researched"



# --- 3. P2P Email Warmup Tests ---
@pytest.mark.asyncio
@patch("smtplib.SMTP")
@patch("imaplib.IMAP4_SSL")
async def test_email_warmup_cycle(mock_imap, mock_smtp, test_env):
    # Seed two active SmtpAccounts
    with Session(test_env) as session:
        acc1 = SmtpAccount(
            id=1,
            name="Account A",
            smtp_host="smtp.a.com",
            smtp_port=587,
            smtp_user="a@a.com",
            smtp_pass=encrypt_string("password"),
            imap_host="imap.a.com",
            imap_port=993,
            imap_user="a@a.com",
            imap_pass=encrypt_string("password"),
            is_active=True
        )
        acc2 = SmtpAccount(
            id=2,
            name="Account B",
            smtp_host="smtp.b.com",
            smtp_port=587,
            smtp_user="b@b.com",
            smtp_pass=encrypt_string("password"),
            imap_host="imap.b.com",
            imap_port=993,
            imap_user="b@b.com",
            imap_pass=encrypt_string("password"),
            is_active=True
        )
        session.add(acc1)
        session.add(acc2)
        session.commit()

    # Mock SMTP object methods
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance
    
    # Mock IMAP object methods
    imap_instance = MagicMock()
    imap_instance.list.return_value = ("OK", [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Spam"'])
    imap_instance.select.return_value = ("OK", [b"1"])
    imap_instance.search.return_value = ("OK", [b"101 102"])
    imap_instance.fetch.return_value = ("OK", [
        (b"102 (RFC822 {100}", b"Subject: Warmup reply\nFrom: a@a.com\n\nHello from Account A")
    ])
    # warmup.py assigns imaplib.IMAP4_SSL() directly to variable (no `with`), so return_value = imap_instance
    mock_imap.return_value = imap_instance
    # Also set up __enter__ for safety if any code path uses `with`
    mock_imap.return_value.__enter__.return_value = imap_instance

    # Run warmup cycle
    res = await run_p2p_warmup_cycle()
    assert res["success"] is True
    assert "döngüsü tamamlandı" in res["details"]


# --- 4. GuiApi Integration Tests ---
def test_gui_api_integration(test_env):
    api = GuiApi()
    
    # Check default warmup toggle and stats
    status = api.get_warmup_status()
    assert status["active"] is False
    assert "sent" in status["stats"]
    
    # Toggle warmup
    toggle_res = api.toggle_warmup(True)
    assert toggle_res["success"] is True
    assert toggle_res["active"] is True
    
    # Verify email via GUI bridge
    with patch("aegisScout.utils.email_verifier.verify_email") as mock_verify:
        mock_verify.return_value = {"success": True, "status": "valid", "details": "Verified!"}
        res = api.verify_email_address("test@domain.com")
        assert res["success"] is True
        assert res["status"] == "valid"
        assert res["details"] == "Verified!"

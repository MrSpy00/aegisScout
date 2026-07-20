"""
Unit tests for aegisScout v3 roadmap features:
  - Zero-Cost Local Email Verifier
  - Multimodal Vision Audit
  - HTTP/SOCKS5 Proxy Pool Manager
  - WhatsApp & LinkedIn Assisted Outreach
"""

import pytest
from aegisScout.outreach.email_verifier import (
    is_valid_syntax,
    is_disposable,
    is_role_account,
    EmailVerifier
)
from aegisScout.ai.vision_audit import VisionAuditManager
from aegisScout.utils.proxy_pool import ProxyPoolManager
from aegisScout.outreach.assisted_mode import send_whatsapp_assisted, send_linkedin_assisted


def test_email_verifier_syntax():
    assert is_valid_syntax("user@example.com") is True
    assert is_valid_syntax("invalid-email-format") is False
    assert is_valid_syntax("") is False
    assert is_valid_syntax(None) is False


def test_email_verifier_disposable():
    assert is_disposable("test@10minutemail.com") is True
    assert is_disposable("test@gmail.com") is False


def test_email_verifier_role_account():
    assert is_role_account("info@company.com") is True
    assert is_role_account("john.doe@company.com") is False


def test_email_verifier_pipeline():
    verifier = EmailVerifier(check_smtp=False)
    
    # Disposable test
    res = verifier.verify("user@10minutemail.com")
    assert res["valid"] is False
    assert res["status"] == "disposable"

    # Syntax test
    res_syntax = verifier.verify("bad_email_format")
    assert res_syntax["valid"] is False
    assert res_syntax["status"] == "invalid_syntax"


@pytest.mark.asyncio
async def test_vision_audit_fallback():
    mgr = VisionAuditManager()
    res = await mgr.audit_url("example.com")
    assert "url" in res
    assert "issues" in res
    assert "hook_sentence" in res


def test_proxy_pool_rotation():
    pool = ProxyPoolManager()
    proxies = ["http://127.0.0.1:8080", "http://127.0.0.1:8081"]
    pool.set_proxies(proxies)

    p1 = pool.get_next_proxy()
    p2 = pool.get_next_proxy()
    p3 = pool.get_next_proxy()

    assert p1 == "http://127.0.0.1:8080"
    assert p2 == "http://127.0.0.1:8081"
    assert p3 == "http://127.0.0.1:8080"


def test_whatsapp_assisted():
    res = send_whatsapp_assisted("05321234567", "Merhaba test mesajı")
    assert res["success"] is True
    assert "wa.me/905321234567" in res["wa_url"]


def test_linkedin_assisted():
    res = send_linkedin_assisted("Acme Corp", "Test pitch", "https://linkedin.com/company/acme")
    assert res["success"] is True
    assert res["target_url"] == "https://linkedin.com/company/acme"

"""
Tests for Multi-Step AI Cadence Sequence Builder and Auto Responder.
"""
from aegisScout.outreach.cadence import AISequenceBuilder
from aegisScout.outreach.auto_responder import AIAutoResponder
from aegisScout.core.models import Lead


def test_ai_sequence_builder_and_variable_rendering():
    lead = Lead(
        id=1,
        business_name="TechCorp İstanbul",
        category="Yazılım",
        domain="techcorp.com.tr",
        score=92.5,
        outreach_hook="Sayfa yüklenme süresi 4.5s (yavaş)",
        city="İstanbul",
    )

    builder = AISequenceBuilder()
    steps = builder.build_lead_sequence(lead)

    assert len(steps) == 3
    assert steps[0]["step"] == 1
    assert "TechCorp" in steps[0]["subject"]
    assert "Sayfa yüklenme süresi 4.5s (yavaş)" in steps[0]["body"]
    assert "92" in steps[0]["body"]
    assert steps[1]["delay_days"] == 3
    assert steps[2]["delay_days"] == 7


def test_ai_auto_responder():
    lead = Lead(id=1, business_name="Innovate LLC")
    responder = AIAutoResponder()

    resp_interested = responder.generate_response(lead, "interested")
    assert resp_interested is not None
    assert "Innovate LLC" in resp_interested["subject"]
    assert "demo" in resp_interested["body"].lower()

    resp_optout = responder.generate_response(lead, "unsubscribe")
    assert resp_optout is None

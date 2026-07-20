import pytest
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from aegisScout.core.database import engine, init_db
from aegisScout.core.models import SmtpAccount, Message
from aegisScout.outreach.email_client import get_available_smtp_account


def test_smtp_rotation_and_limits():
    init_db()
    with Session(engine) as session:
        # Cleanup any existing accounts
        session.exec(select(SmtpAccount)).all()
        for a in session.exec(select(SmtpAccount)).all():
            session.delete(a)
        for m in session.exec(select(Message)).all():
            session.delete(m)
        session.commit()

        # Insert 2 active accounts
        acc1 = SmtpAccount(name="Acc 1", smtp_host="smtp.1.com", smtp_user="1@1.com", smtp_pass="pass", is_active=True, last_used_at=None)
        acc2 = SmtpAccount(name="Acc 2", smtp_host="smtp.2.com", smtp_user="2@2.com", smtp_pass="pass", is_active=True, last_used_at=None)
        session.add(acc1)
        session.add(acc2)
        session.commit()
        session.refresh(acc1)
        session.refresh(acc2)

        # 1. First rotation call should pick acc1 or acc2 (nulls first, stable sorting)
        selected1, err = get_available_smtp_account()
        assert selected1 is not None
        assert err is None
        
        # 2. Next call should pick the other account (since selected1's last_used_at was touched)
        selected2, err = get_available_smtp_account()
        assert selected2 is not None
        assert selected2.id != selected1.id

        # Insert a parent Lead to satisfy FOREIGN KEY constraint on messages
        from aegisScout.core.models import Lead
        lead = Lead(business_name="Test Business", has_website=True, is_active=True)
        session.add(lead)
        session.commit()
        session.refresh(lead)

        # 3. Simulate rate limit on acc1 by adding 5 sent messages in last hour
        for i in range(5):
            msg = Message(
                lead_id=lead.id,
                direction="outbound",
                channel="email",
                content="test content",
                status="sent",
                sent_at=datetime.utcnow() - timedelta(minutes=10),
                smtp_account_id=selected1.id
            )
            session.add(msg)
        session.commit()

        # Call rotation again: since selected1 reached the limit of 5, it must return selected2 (limit is <5)
        selected3, err = get_available_smtp_account()
        assert selected3.id == selected2.id

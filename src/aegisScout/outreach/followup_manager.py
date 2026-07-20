import asyncio
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from typing import Dict, Any

from aegisScout.core.database import engine
from aegisScout.core.models import Lead, Message, Campaign, ActivityLog
from aegisScout.outreach.email_client import send_cold_email
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.followup_manager")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def check_and_send_followups() -> dict:
    """
    Checks all campaigns for leads in 'contacted' status that require follow-ups,
    and sends the next scheduled follow-up email if the threshold has passed.
    """
    stats = {"emails_sent": 0, "errors": []}
    
    with Session(engine) as session:
        # Load campaigns that have follow-up templates configured
        campaigns = session.exec(select(Campaign)).all()
        
        for campaign in campaigns:
            # We check if there is at least one follow-up step configured
            has_step1 = bool(campaign.followup_subject_1 and campaign.followup_body_1)
            has_step2 = bool(campaign.followup_subject_2 and campaign.followup_body_2)
            
            if not has_step1 and not has_step2:
                continue
                
            # Find all leads in this campaign that have status 'contacted'
            leads = session.exec(
                select(Lead).where(
                    (Lead.campaign_id == campaign.id) &
                    (Lead.status == "contacted") &
                    (Lead.email != None)
                )
            ).all()
            
            for lead in leads:
                # Double check that the lead hasn't replied (no inbound messages)
                inbound_exists = session.exec(
                    select(Message).where(
                        (Message.lead_id == lead.id) &
                        (Message.direction == "inbound")
                    )
                ).first()
                if inbound_exists:
                    # Inbound exists, skip! (IMAP watcher should have updated status to replied, but safety first)
                    continue

                # Load all outbound email messages sent to this lead
                outbound_messages = session.exec(
                    select(Message).where(
                        (Message.lead_id == lead.id) &
                        (Message.direction == "outbound") &
                        (Message.channel == "email") &
                        (Message.status == "sent")
                    ).order_by(Message.sent_at.desc())
                ).all()

                if not outbound_messages:
                    # Has not received the initial email yet, skip
                    continue
                
                # Get the most recent outbound email
                last_msg = outbound_messages[0]
                if not last_msg.sent_at:
                    continue

                days_elapsed = (datetime.utcnow() - last_msg.sent_at).days

                # Step 1: Check if last message was Initial, and we need to send Follow-up 1
                if last_msg.message_type == "initial" and has_step1:
                    delay_days = campaign.followup_delay_1_days or 3
                    if days_elapsed >= delay_days:
                        logger.info(f"Sending Follow-up 1 to {lead.business_name} ({lead.email})...")
                        success, err, smtp_id = send_cold_email(
                            to_email=lead.email,
                            subject=campaign.followup_subject_1,
                            body=campaign.followup_body_1
                        )
                        if success:
                            new_msg = Message(
                                lead_id=lead.id,
                                direction="outbound",
                                channel="email",
                                content=campaign.followup_body_1,
                                status="sent",
                                sent_at=_utcnow(),
                                smtp_account_id=smtp_id,
                                message_type="followup_1"
                            )
                            session.add(new_msg)
                            session.add(ActivityLog(
                                action="followup_sent",
                                details=f"Follow-up 1 sent to {lead.business_name} ({lead.email})",
                                session_id=lead.session_id
                            ))
                            stats["emails_sent"] += 1
                        else:
                            stats["errors"].append(f"Follow-up 1 failed for {lead.business_name}: {err}")
                
                # Step 2: Check if last message was Follow-up 1, and we need to send Follow-up 2
                elif last_msg.message_type == "followup_1" and has_step2:
                    delay_days = campaign.followup_delay_2_days or 7
                    if days_elapsed >= delay_days:
                        logger.info(f"Sending Follow-up 2 to {lead.business_name} ({lead.email})...")
                        success, err, smtp_id = send_cold_email(
                            to_email=lead.email,
                            subject=campaign.followup_subject_2,
                            body=campaign.followup_body_2
                        )
                        if success:
                            new_msg = Message(
                                lead_id=lead.id,
                                direction="outbound",
                                channel="email",
                                content=campaign.followup_body_2,
                                status="sent",
                                sent_at=_utcnow(),
                                smtp_account_id=smtp_id,
                                message_type="followup_2"
                            )
                            session.add(new_msg)
                            session.add(ActivityLog(
                                action="followup_sent",
                                details=f"Follow-up 2 sent to {lead.business_name} ({lead.email})",
                                session_id=lead.session_id
                            ))
                            stats["emails_sent"] += 1
                        else:
                            stats["errors"].append(f"Follow-up 2 failed for {lead.business_name}: {err}")
            session.commit()
            
    return stats

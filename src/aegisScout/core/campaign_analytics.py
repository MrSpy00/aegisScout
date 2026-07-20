"""
Campaign Analytics Engine for aegisScout (N4).
Calculates outreach metrics: open rates, reply rates, lead funnel breakdown, and best send times.
"""
from typing import Dict, Any, List
from sqlmodel import Session, select, func
from aegisScout.core.database import engine
from aegisScout.core.models import Message, Lead, Campaign

def get_campaign_analytics(campaign_id: int) -> Dict[str, Any]:
    """Calculate aggregate statistics and funnel breakdown for a campaign."""
    with Session(engine) as session:
        messages = session.exec(select(Message).where(Message.campaign_id == campaign_id)).all()
        total_sent = len(messages)
        delivered = sum(1 for m in messages if m.status in ("sent", "delivered", "read"))
        replied = sum(1 for m in messages if m.reply_received or m.status == "replied")
        converted = sum(1 for m in messages if m.status == "converted")

        open_rate = (delivered / total_sent * 100.0) if total_sent > 0 else 0.0
        reply_rate = (replied / total_sent * 100.0) if total_sent > 0 else 0.0

        funnel = {
            "sent": total_sent,
            "delivered": delivered,
            "replied": replied,
            "converted": converted
        }

        # Best send time distribution (hour of day -> response count)
        hourly_stats: Dict[int, int] = {h: 0 for h in range(24)}
        for m in messages:
            if m.sent_at:
                hourly_stats[m.sent_at.hour] += 1

        best_hour = max(hourly_stats, key=hourly_stats.get) if total_sent > 0 else 10

    return {
        "campaign_id": campaign_id,
        "total_sent": total_sent,
        "open_rate_percent": round(open_rate, 1),
        "reply_rate_percent": round(reply_rate, 1),
        "lead_funnel": funnel,
        "best_send_hour": best_hour,
        "hourly_distribution": hourly_stats
    }

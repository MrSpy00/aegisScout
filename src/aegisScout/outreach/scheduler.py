"""
Smart Outreach Scheduler for aegisScout (N5).
Schedules campaign messages within customizable working hour windows and daily limits.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.scheduler")

@dataclass
class ScheduleResult:
    campaign_id: int
    scheduled_count: int
    start_time: str
    estimated_completion: str

class OutreachScheduler:
    """Schedules campaign sending slots."""
    def schedule_campaign(
        self,
        campaign_id: int,
        lead_ids: List[int],
        start_time: datetime,
        daily_limit: int = 10,
        send_window: Tuple[int, int] = (9, 18),
        skip_weekends: bool = True
    ) -> ScheduleResult:
        """Schedule outbound messages across days and time windows."""
        logger.info(f"Scheduling {len(lead_ids)} leads for campaign {campaign_id}...")
        current_time = start_time
        scheduled_slots = []

        for lead_id in lead_ids:
            # Adjust to window
            if current_time.hour < send_window[0]:
                current_time = current_time.replace(hour=send_window[0], minute=0)
            elif current_time.hour >= send_window[1]:
                current_time = (current_time + timedelta(days=1)).replace(hour=send_window[0], minute=0)

            # Skip weekends if enabled
            if skip_weekends:
                while current_time.weekday() in (5, 6):  # Saturday, Sunday
                    current_time += timedelta(days=1)

            scheduled_slots.append((lead_id, current_time.isoformat()))
            current_time += timedelta(minutes=15)  # Pace 15 mins apart

        completion = current_time.isoformat()
        return ScheduleResult(
            campaign_id=campaign_id,
            scheduled_count=len(scheduled_slots),
            start_time=start_time.isoformat(),
            estimated_completion=completion
        )

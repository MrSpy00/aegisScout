"""
Automated Scheduler & Alert Manager for aegisScout.
Runs periodic lead discovery tasks and emits desktop toast / Slack / Telegram notifications.
"""
import asyncio
from typing import Optional, Callable, Dict, Any, List
from aegisScout.core.models import Lead
from aegisScout.monitoring.notifier import Notifier
from aegisScout.utils.logger import get_logger

logger = get_logger("core.scheduler")


class AegisScheduler:
    """Schedules recurring discovery jobs and high-score lead alerts."""

    def __init__(self, interval_seconds: int = 3600):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.notifier = Notifier()

    def send_high_score_alert(self, lead: Lead, webhook_url: Optional[str] = None) -> None:
        """Send Desktop / Webhook alert for high-value discovered leads."""
        score_val = lead.priority_score or lead.website_quality_score or 0
        title = f"🎯 Yüksek Skorlu Lider Bulundu: {lead.business_name}"
        message = (
            f"Şirket: {lead.business_name}\n"
            f"Skor: {score_val}/100\n"
            f"E-posta: {lead.email or 'N/A'}\n"
            f"Telefon: {lead.phone or 'N/A'}"
        )
        # Send notifications
        asyncio.create_task(self.notifier.notify_all(title=title, text=message))

        # Send Webhook alert if configured
        if webhook_url:
            async def _post_webhook():
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(webhook_url, json={"event": "high_score_lead", "lead": lead.dict()})
                except Exception as e:
                    logger.warning(f"Webhook send failed: {e}")
            asyncio.create_task(_post_webhook())

    async def _run_loop(self, discovery_job: Callable[[], List[Lead]], min_alert_score: float = 80.0):
        """Internal worker loop executing scheduled jobs."""
        logger.info(f"Scheduler loop started with interval {self.interval_seconds}s.")
        while self.is_running:
            try:
                logger.info("Scheduler triggering periodic discovery job...")
                if asyncio.iscoroutinefunction(discovery_job):
                    leads = await discovery_job()
                else:
                    leads = await asyncio.to_thread(discovery_job)

                high_scoring = [l for l in (leads or []) if ((l.priority_score or l.website_quality_score or 0) >= min_alert_score)]
                for lead in high_scoring:
                    self.send_high_score_alert(lead)

            except Exception as e:
                logger.error(f"Scheduler execution error: {e}")

            await asyncio.sleep(self.interval_seconds)

    def start(self, discovery_job: Callable[[], List[Lead]], min_alert_score: float = 80.0):
        """Start the scheduler task."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop(discovery_job, min_alert_score))

    def stop(self):
        """Stop the scheduler task."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Scheduler stopped.")

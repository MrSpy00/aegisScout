import time
import random
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select, func
from aegisScout.core.toml_config import config_data
from aegisScout.utils.logger import get_logger

logger = get_logger("outreach.rate_limiter")


class RateLimiter:
    """
    Ensures safe pacing of Instagram actions to prevent anti-bot bans/lockouts.

    Enforces:
    - Minimum random delay between each action (sleep_random)
    - Hard daily limit: checks activity_log for today's send count (check_daily_limit)
    - Hard hourly limit: checks activity_log for this hour's send count (check_hourly_limit)
    """

    def __init__(self):
        # Load from config.toml with safe defaults
        rate_limits = config_data.get("rate_limits", {})
        self.min_delay: float = rate_limits.get("scrape_delay_min_seconds", 3)
        self.max_delay: float = rate_limits.get("scrape_delay_max_seconds", 8)
        self.daily_limit: int = rate_limits.get("instagram_actions_per_day", 15)
        self.hourly_limit: int = rate_limits.get("instagram_actions_per_hour", 5)

    # ------------------------------------------------------------------
    # Pacing helpers
    # ------------------------------------------------------------------

    def sleep_random(self) -> None:
        """Sleep a random amount between min_delay and max_delay seconds."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Pacing delay: sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def sleep_long(self, reason: str = "general pacing") -> None:
        """Sleep a longer random amount (30–90 s) for post-action cooldown."""
        delay = random.uniform(30, 90)
        logger.info(f"Long pacing delay for {reason}: sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    # ------------------------------------------------------------------
    # DB-backed limit enforcement
    # ------------------------------------------------------------------

    def _count_sends_since(self, since: datetime) -> int:
        """Count instagram_send actions in activity_log after `since`."""
        # Lazy import to avoid circular dependency at module load time
        from aegisScout.core.database import engine
        from aegisScout.core.models import ActivityLog
        with Session(engine) as session:
            count = session.exec(
                select(func.count(ActivityLog.id)).where(
                    ActivityLog.action == "instagram_send",
                    ActivityLog.timestamp >= since,
                )
            ).one()
        return count or 0

    def check_daily_limit(self) -> tuple[bool, int]:
        """
        Returns (can_send, remaining_today).
        `can_send` is False when today's send count >= daily_limit.
        """
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        try:
            count = self._count_sends_since(today_start)
        except Exception as e:
            logger.error(f"RateLimiter check_daily_limit DB query failed: {e}")
            return False, -1
        remaining = max(0, self.daily_limit - count)
        can_send = count < self.daily_limit
        if not can_send:
            logger.warning(
                f"Günlük Instagram gönderim limiti doldu ({count}/{self.daily_limit}). "
                f"Yeni mesaj gönderilemez."
            )
        return can_send, remaining

    def check_hourly_limit(self) -> tuple[bool, int]:
        """
        Returns (can_send, remaining_this_hour).
        `can_send` is False when this hour's send count >= hourly_limit.
        """
        hour_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        try:
            count = self._count_sends_since(hour_start)
        except Exception as e:
            logger.error(f"RateLimiter check_hourly_limit DB query failed: {e}")
            return False, -1
        remaining = max(0, self.hourly_limit - count)
        can_send = count < self.hourly_limit
        if not can_send:
            logger.warning(
                f"Saatlik Instagram gönderim limiti doldu ({count}/{self.hourly_limit}). "
                f"Bir saat sonra tekrar deneyin."
            )
        return can_send, remaining

    def can_send(self) -> tuple[bool, str]:
        """
        Master check: returns (True, "") if both daily and hourly limits allow a send.
        Returns (False, reason_message) otherwise.
        """
        daily_ok, daily_remaining = self.check_daily_limit()
        if daily_remaining == -1:
            return False, "Veritabanı hatası nedeniyle limit kontrolü yapılamadı (güvenli mod engellemesi)."
        if not daily_ok:
            return False, f"Günlük limit doldu (maks. {self.daily_limit}/gün)."

        hourly_ok, hourly_remaining = self.check_hourly_limit()
        if hourly_remaining == -1:
            return False, "Veritabanı hatası nedeniyle limit kontrolü yapılamadı (güvenli mod engellemesi)."
        if not hourly_ok:
            return False, f"Saatlik limit doldu (maks. {self.hourly_limit}/saat)."

        return True, ""

    def record_send(self, lead_name: str = "") -> None:
        """
        Record an instagram_send event in the activity_log table.
        Call this immediately after a successful DM send.
        """
        from aegisScout.core.database import engine
        from aegisScout.core.models import ActivityLog
        try:
            with Session(engine) as session:
                log = ActivityLog(
                    action="instagram_send",
                    details=f"Instagram DM gönderildi: {lead_name}" if lead_name else "Instagram DM gönderildi",
                )
                session.add(log)
                session.commit()
        except Exception as e:
            logger.error(f"RateLimiter: send kaydedilemedi: {e}")


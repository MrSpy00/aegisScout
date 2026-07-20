"""
Auto-Discovery Cron Manager for aegisScout (N11).
Schedules periodic discovery runs in the background.
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from aegisScout.cli.commands import discover_leads
from aegisScout.utils.logger import get_logger

logger = get_logger("core.cron_manager")

class CronJob:
    def __init__(self, job_id: str, sector: str, location: str, radius_km: float, interval_hours: int):
        self.job_id = job_id
        self.sector = sector
        self.location = location
        self.radius_km = radius_km
        self.interval_hours = interval_hours
        self.last_run: Optional[datetime] = None
        self.next_run: datetime = datetime.now() + timedelta(hours=interval_hours)
        self.is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "sector": self.sector,
            "location": self.location,
            "radius_km": self.radius_km,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "is_active": self.is_active
        }

class CronManager:
    _instance: Optional['CronManager'] = None

    @classmethod
    def get_instance(cls) -> 'CronManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}

    def add_job(self, sector: str, location: str, radius_km: float = 5.0, interval_hours: int = 24) -> CronJob:
        job_id = str(uuid.uuid4())[:8]
        job = CronJob(job_id=job_id, sector=sector, location=location, radius_km=radius_km, interval_hours=interval_hours)
        self.jobs[job_id] = job
        logger.info(f"Cron job added: {job_id} ({sector} in {location} every {interval_hours}h)")
        return job

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [job.to_dict() for job in self.jobs.values()]

    def run_now(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False
        logger.info(f"Triggering cron job {job_id} immediately...")
        try:
            asyncio.run(discover_leads(sector=job.sector, location=job.location, radius_km=int(job.radius_km), provider_name="all"))
            job.last_run = datetime.now()
            job.next_run = datetime.now() + timedelta(hours=job.interval_hours)
            return True
        except Exception as e:
            logger.error(f"Cron job execution failed: {e}")
            return False

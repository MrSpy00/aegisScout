"""
Bulk Discovery Engine for aegisScout (N3).
Executes parallel business discovery across multiple locations and sectors based on JSON target configs.
"""
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from aegisScout.cli.commands import discover_leads
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.bulk")

async def run_bulk_discovery(config_path: Path, max_parallel: int = 3) -> Dict[str, Any]:
    """
    Run parallel discovery tasks defined in bulk_targets.json.
    Config format:
    {
      "targets": [
        {"sector": "kuaför", "location": "Kadıköy", "radius": 3},
        {"sector": "kuaför", "location": "Beşiktaş", "radius": 3}
      ]
    }
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Bulk targets config not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    targets = data.get("targets", [])
    if not targets:
        return {"success": True, "total_leads": 0, "processed_targets": 0}

    logger.info(f"Starting bulk discovery for {len(targets)} targets with parallelism={max_parallel}...")
    semaphore = asyncio.Semaphore(max_parallel)

    async def _process_target(target: dict):
        async with semaphore:
            sector = target.get("sector", "")
            location = target.get("location", "")
            radius = float(target.get("radius", 5.0))
            provider = target.get("provider", "all")

            logger.info(f"Bulk discovery worker starting: {sector} in {location} ({radius}km)...")
            added_count, _, _ = await discover_leads(sector=sector, location=location, radius_km=int(radius), provider_name=provider)
            return {
                "sector": sector,
                "location": location,
                "count": added_count
            }

    tasks = [_process_target(t) for t in targets]
    completed = await asyncio.gather(*tasks, return_exceptions=True)

    total_leads = 0
    target_summary = []
    for res in completed:
        if isinstance(res, dict):
            total_leads += res.get("count", 0)
            target_summary.append(res)
        elif isinstance(res, Exception):
            logger.error(f"Bulk target failed: {res}")

    logger.info(f"Bulk discovery complete. Total leads found: {total_leads}")
    return {
        "success": True,
        "total_leads": total_leads,
        "processed_targets": len(target_summary),
        "details": target_summary
    }

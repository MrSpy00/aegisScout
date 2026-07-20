"""
Parallel Discovery Engine & Progressive Enrichment Orchestrator for aegisScout.
Runs multiple search providers concurrently using asyncio.gather and Semaphore,
yielding leads progressively to GUI & database.
"""
import asyncio
from typing import List, Callable, Optional, Dict, Any, AsyncGenerator
from aegisScout.core.models import Lead
from aegisScout.discovery.enrichers import enrichment_pool
from aegisScout.utils.logger import get_logger

logger = get_logger("discovery.orchestrator")


class DiscoveryOrchestrator:
    """Orchestrates parallel lead discovery across multiple search providers."""

    def __init__(self, max_concurrent_providers: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent_providers)

    async def execute_provider(
        self,
        provider_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> List[Lead]:
        """Execute single search provider with semaphore constraint."""
        async with self.semaphore:
            try:
                if asyncio.iscoroutinefunction(provider_fn):
                    results = await provider_fn(*args, **kwargs)
                else:
                    results = await asyncio.to_thread(provider_fn, *args, **kwargs)
                return results or []
            except Exception as e:
                logger.error(f"Provider execution failed for {provider_fn}: {e}")
                return []

    async def run_parallel_discovery(
        self,
        provider_tasks: List[Callable[[], Any]],
        on_lead_found_callback: Optional[Callable[[Lead], None]] = None,
    ) -> List[Lead]:
        """
        Execute multiple search provider functions in parallel.
        Progressively streams leads to callback as soon as they are found.
        """
        all_leads: List[Lead] = []
        seen_identifiers = set()

        async def worker(task_fn: Callable[[], Any]):
            results = await self.execute_provider(task_fn)
            for item in results:
                # Convert dict or Lead model if needed
                lead = item if isinstance(item, Lead) else Lead(**item) if isinstance(item, dict) else None
                if not lead:
                    continue
                
                identifier = (lead.domain or lead.business_name or lead.phone or "").strip().lower()
                if identifier and identifier in seen_identifiers:
                    continue
                if identifier:
                    seen_identifiers.add(identifier)

                all_leads.append(lead)
                if on_lead_found_callback:
                    try:
                        on_lead_found_callback(lead)
                    except Exception as cb_err:
                        logger.warning(f"Callback error on lead stream: {cb_err}")

        # Run all provider tasks concurrently
        await asyncio.gather(*(worker(task) for task in provider_tasks), return_exceptions=True)
        logger.info(f"Parallel discovery finished. Discovered total {len(all_leads)} unique leads.")
        return all_leads


orchestrator = DiscoveryOrchestrator()

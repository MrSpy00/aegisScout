"""
Tests for Discovery Orchestrator & Progressive Enrichment Pool.
"""
import pytest
from aegisScout.discovery.orchestrator import DiscoveryOrchestrator
from aegisScout.discovery.enrichers import SharedEnrichmentPool
from aegisScout.core.models import Lead


@pytest.mark.asyncio
async def test_parallel_discovery_orchestration():
    orchestrator = DiscoveryOrchestrator(max_concurrent_providers=2)

    def dummy_provider_1():
        return [Lead(id=101, business_name="Alpha Tech", domain="alphatech.io")]

    async def dummy_provider_2():
        return [
            Lead(id=102, business_name="Beta Solutions", domain="betasol.com"),
            Lead(id=103, business_name="Alpha Tech", domain="alphatech.io"), # duplicate
        ]

    streamed_leads = []
    def callback(lead):
        streamed_leads.append(lead)

    all_leads = await orchestrator.run_parallel_discovery(
        [dummy_provider_1, dummy_provider_2],
        on_lead_found_callback=callback
    )

    assert len(all_leads) == 2
    assert len(streamed_leads) == 2
    assert all_leads[0].business_name == "Alpha Tech"
    assert all_leads[1].business_name == "Beta Solutions"


@pytest.mark.asyncio
async def test_shared_enrichment_pool():
    pool = SharedEnrichmentPool()
    client = await pool.get_client()
    assert client is not None
    await pool.close()

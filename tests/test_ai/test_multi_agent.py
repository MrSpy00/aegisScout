import pytest
from unittest.mock import AsyncMock, patch
from aegisScout.ai.multi_agent import generate_multi_agent_draft


@pytest.mark.asyncio
async def test_generate_multi_agent_draft():
    mock_router = AsyncMock()
    mock_router.generate.side_effect = [
        "Technical Inspector Report: PageSpeed is low, viewport is missing.",
        "Outbound Draft: Merhaba, sitenizi inceledik ve yavas oldugunu gorduk.",
        '{"analysis": "Cleaned jargon", "opening_message": "Siteniz biraz yavaş çalışıyor, yardımcı olmak isteriz."}'
    ]
    
    with patch("aegisScout.ai.multi_agent.ProviderRouter", return_value=mock_router):
        res = await generate_multi_agent_draft(
            business_name="Dentist Istanbul",
            sector="Health",
            has_website=True,
            website_notes="Slow PageSpeed",
            instagram_bio="Dentist Clinic",
            review_highlights="Highly rated",
            opportunities="Low PageSpeed"
        )
        
        assert res["opening_message"] == "Siteniz biraz yavaş çalışıyor, yardımcı olmak isteriz."
        assert res["analysis"] == "Cleaned jargon"
        assert mock_router.generate.call_count == 3

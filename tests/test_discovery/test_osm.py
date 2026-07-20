import pytest
import respx
import httpx
from aegisScout.discovery.osm_provider import OSMDiscoveryProvider

@pytest.mark.asyncio
async def test_osm_discovery_geocoding():
    provider = OSMDiscoveryProvider()
    
    # Mock geocoding (Nominatim API) and Overpass API queries using respx
    with respx.mock:
        respx.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(
                200, 
                json=[{"lat": "40.9901", "lon": "29.0205"}]
            )
        )
        
        # Mock Overpass response
        overpass_mock_data = {
            "elements": [
                {
                    "type": "node",
                    "id": 12345,
                    "tags": {
                        "name": "Kadıköy Kuaför",
                        "contact:phone": "+90 216 123 45 67",
                        "contact:instagram": "kadikoykuafor",
                        "website": "http://kadikoykuafor.com"
                    }
                }
            ]
        }
        respx.post("https://overpass-api.de/api/interpreter").mock(
            return_value=httpx.Response(200, json=overpass_mock_data)
        )
        
        candidates = await provider.search("kuaför", "Kadıköy, İstanbul")
        
        assert len(candidates) == 1
        assert candidates[0].business_name == "Kadıköy Kuaför"
        assert candidates[0].phone == "+90 216 123 45 67"
        assert candidates[0].instagram_handle == "kadikoykuafor"
        assert candidates[0].website_url == "http://kadikoykuafor.com"
        assert candidates[0].source == "osm"

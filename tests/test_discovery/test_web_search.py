import pytest
import respx
import httpx
from aegisScout.discovery.web_search_provider import WebSearchDiscoveryProvider

@pytest.mark.asyncio
async def test_web_search_discovery():
    provider = WebSearchDiscoveryProvider()
    
    mock_html = """
    <html>
      <body>
        <div class="result">
          <h2 class="result__title">
            <a class="result__a" href="https://duckduckgo.com/l/?kh=-1&uddg=https%3A%2F%2Fwww.instagram.com%2Fkadikoykuafor%2F">Kadıköy Kuaför Salonu (@kadikoykuafor) • Instagram photos and videos</a>
          </h2>
          <a class="result__snippet" href="#">Güzellik salonumuzda saç tasarımı ve bakım hizmetleri. İletişim: +90 216 123 4567</a>
        </div>
        <div class="result">
          <h2 class="result__title">
            <a class="result__a" href="https://duckduckgo.com/l/?kh=-1&uddg=https%3A%2F%2Fwww.meliskuafor.com">Melis Kuaför - Kadıköy - Web Sitesi</a>
          </h2>
          <a class="result__snippet" href="#">Kadıköy kuaförleri arasında lider. Web sitemizden randevu alın.</a>
        </div>
      </body>
    </html>
    """
    
    with respx.mock:
        # Mock DuckDuckGo HTML search results
        respx.get(url__startswith="https://html.duckduckgo.com/html/").mock(
            return_value=httpx.Response(200, text=mock_html)
        )
        
        candidates = await provider.search("kuaför", "Kadıköy")
        
        assert len(candidates) >= 2
        
        # Verify Instagram candidate details
        insta_cand = next(c for c in candidates if c.instagram_handle == "kadikoykuafor")
        assert insta_cand.business_name == "Kadıköy Kuaför Salonu"
        assert insta_cand.instagram_url == "https://instagram.com/kadikoykuafor"
        assert insta_cand.phone == "+90 216 123 4567"
        assert insta_cand.source == "web_search"
        
        # Verify Web candidate details
        web_cand = next(c for c in candidates if c.website_url == "https://www.meliskuafor.com")
        assert web_cand.business_name == "Melis Kuaför - Kadıköy"
        assert web_cand.has_website is True
        assert web_cand.source == "web_search"

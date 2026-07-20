import pytest
import respx
import httpx
from aegisScout.discovery.web_scraper import WebScraper

@pytest.mark.asyncio
async def test_web_scraper_parser():
    scraper = WebScraper()
    
    # Mock network call to return custom HTML containing specific tags for parsing
    mock_html = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="Kariyer ve Güzellik Salonu">
        </head>
        <body>
            <a href="https://instagram.com/mrspy00_style">Instagram Link</a>
            <a href="tel:+905555555555">Phone Link</a>
        </body>
    </html>
    """
    
    with respx.mock:
        respx.get("https://dummyurl.com").mock(
            return_value=httpx.Response(200, text=mock_html)
        )
        
        instagram_handle, phone, quality_score, notes = await scraper.scrape_site("https://dummyurl.com")
        
    assert instagram_handle == "mrspy00_style"
    assert phone == "+905555555555"
    assert quality_score == 80 # viewport (30), ssl (30), description (20), content length <= 5000 (0)


@pytest.mark.asyncio
async def test_web_scraper_crawls_contact_subpage():
    scraper = WebScraper()
    
    homepage_html = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <a href="/contact">İletişim</a>
        </body>
    </html>
    """
    
    contact_html = """
    <html>
        <body>
            <a href="https://instagram.com/subpage_insta">Instagram Link</a>
        </body>
    </html>
    """
    
    with respx.mock:
        respx.get("https://dummyurl.com/contact").mock(
            return_value=httpx.Response(200, text=contact_html)
        )
        respx.get("https://dummyurl.com").mock(
            return_value=httpx.Response(200, text=homepage_html)
        )      
        instagram_handle, phone, quality_score, notes = await scraper.scrape_site("https://dummyurl.com")
        
    assert instagram_handle == "subpage_insta"
    assert "iletişim/hakkımızda sayfasından bulundu" in notes

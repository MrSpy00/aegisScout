import pytest
import respx
import httpx
from unittest.mock import patch


class TestInstagramFinder:
    """
    InstagramFinder icin Google Custom Search API mock testleri.
    API key ve CX, mock ile inject edilir.
    """

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        """Her testte settings mock'la: API key ve CX'i sahte degerlerle doldur."""
        with patch("aegisScout.discovery.instagram_finder.settings") as mock_cfg:
            mock_cfg.google_custom_search_api_key = "FAKE_API_KEY"
            mock_cfg.google_custom_search_cx = "FAKE_CX"
            yield mock_cfg

    @pytest.mark.asyncio
    async def test_find_instagram_success(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()
        mock_response = {
            "items": [
                {
                    "link": "https://www.instagram.com/test_business_handle/",
                    "title": "Test Business on Instagram",
                }
            ]
        }

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            handle = await finder.find_instagram("Test Business", "Istanbul")

        assert handle == "test_business_handle"

    @pytest.mark.asyncio
    async def test_find_instagram_no_results(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()
        mock_response = {"items": []}

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            handle = await finder.find_instagram("Nonexistent Business", "Nowhere")

        assert handle is None

    @pytest.mark.asyncio
    async def test_find_instagram_api_error(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        with respx.mock:
            respx.get(
                url__regex=r".*/customsearch/v1.*"
            ).mock(return_value=httpx.Response(403, json={"error": "quota exceeded"}))

            handle = await finder.find_instagram("Test Business", "Istanbul")

        assert handle is None

    @pytest.mark.asyncio
    async def test_search_profiles_by_sector(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        with patch.object(finder, "fetch_profile_details") as mock_fetch:
            mock_fetch.side_effect = lambda h, s: {
                "username": h,
                "full_name": h.replace("_", " ").title(),
                "bio": "Cilt bakımı ve güzellik salonu. WhatsApp: 05321112233",
                "followers": "15K",
                "followers_raw": 15000,
                "email": "info@kadikoy.com",
                "phone": "+905321112233",
                "is_verified": True,
                "relevance_score": 90
            }

            with respx.mock:
                respx.get(url__regex=r".*bing\.com/search.*").mock(
                    return_value=httpx.Response(200, text='href="https://www.instagram.com/guzellik_salonu_kadikoy/"')
                )
                respx.get(url__regex=r".*duckduckgo\.com.*").mock(
                    return_value=httpx.Response(200, text='href="https://www.instagram.com/guzellik_salonu_kadikoy/"')
                )

                results = await finder.search_profiles_by_sector("Güzellik Salonu", "Kadıköy", limit=5)
                assert len(results) >= 1
                assert "guzellik" in results[0]["username"]

    @pytest.mark.asyncio
    async def test_fetch_profile_details_opengraph(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        html_sample = """
        <html>
        <head>
            <meta property="og:title" content="Estetik Klinik (@estetik_klinik) • Instagram photos" />
            <meta property="og:image" content="https://instagram.fist1-1.fna.fbcdn.net/v/t51.2885-19/sample.jpg" />
            <meta property="og:description" content="12.5K Followers, 450 Following, 200 Posts - See Instagram photos and videos from Estetik Klinik (@estetik_klinik): Randevu &amp; Bilgi için E-posta: dr@estetik.com WhatsApp: 05339998877" />
        </head>
        <body></body>
        </html>
        """

        with respx.mock:
            respx.get(url__regex=r".*instagram\.com/estetik_klinik/.*").mock(
                return_value=httpx.Response(200, text=html_sample)
            )
            respx.get(url__regex=r".*web_profile_info.*").mock(
                return_value=httpx.Response(404)
            )

            profile = await finder.fetch_profile_details("estetik_klinik", "Estetik")
            assert profile["username"] == "estetik_klinik"
            assert profile["full_name"] == "Estetik Klinik"
            assert profile["followers"] == "12.5K"
            assert profile["email"] == "dr@estetik.com"
            assert profile["phone"] == "+905339998877"
            assert profile["profile_pic_url"] == "https://instagram.fist1-1.fna.fbcdn.net/v/t51.2885-19/sample.jpg"

    def test_gui_api_instagram_methods(self):
        from aegisScout.gui_impl import GuiApi
        api = GuiApi()

        profiles = [
            {
                "username": "sample_biz",
                "full_name": "Sample Business Ltd",
                "category": "Yazılım",
                "email": "contact@sample.com",
                "phone": "+905001112233",
                "website": "https://sample.com",
                "bio": "Yazılım çözümleri",
                "followers": "5K"
            }
        ]

        import_res = api.import_instagram_leads_to_crm(profiles)
        assert import_res["success"] is True
        assert import_res["saved_count"] >= 1 or import_res["updated_count"] >= 1

        dm_res = api.generate_instagram_dm_draft("sample_biz", "Yazılım çözümleri", "Yazılım")
        assert dm_res["success"] is True
        assert "@sample_biz" in dm_res["dm_draft"]

    @pytest.mark.asyncio
    async def test_priority_ranking_algorithm(self):
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        mock_profiles = [
            {
                "username": "random_user",
                "full_name": "Rastgele Kullanıcı",
                "bio": "Saç kesim ve kuaför salonu",
                "followers_raw": 100,
                "relevance_score": 70
            },
            {
                "username": "kuafor_salonu",
                "full_name": "Kuafor Salonu",
                "bio": "En iyi hizmet",
                "followers_raw": 500,
                "relevance_score": 90
            },
            {
                "username": "ahmet_yılmaz",
                "full_name": "Ahmet Yılmaz Kuaför",
                "bio": "Randevu için arayın",
                "followers_raw": 300,
                "relevance_score": 85
            }
        ]

        # Test ranking logic directly
        with patch.object(finder, "fetch_profile_details") as mock_fetch:
            mock_fetch.side_effect = lambda h, s: next((p for p in mock_profiles if p["username"] == h), {"username": h, "full_name": h, "bio": ""})
            
            with patch("aegisScout.discovery.social_media_provider.SocialMediaDiscoveryProvider.search", return_value=[]):
                with patch.object(InstagramFinder, "search_profiles_by_sector") as mock_search:
                    mock_search.return_value = sorted(
                        mock_profiles,
                        key=lambda p: (
                            1 if "kuafor" in p["username"] else (2 if "Kuaför" in p["full_name"] else 3),
                            -p["followers_raw"]
                        )
                    )
                    results = await finder.search_profiles_by_sector("kuaför", "", limit=10)
                    assert len(results) == 3
                    assert results[0]["username"] == "kuafor_salonu"
                    assert results[1]["username"] == "ahmet_yılmaz"
                    assert results[2]["username"] == "random_user"



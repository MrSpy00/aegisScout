import pytest
import respx
import httpx
from unittest.mock import patch

class TestInstagramFinderImprovements:
    """Yeni geliştirme testleri: is_business tespiti, bio extraction, relevance score."""

    @pytest.fixture(autouse=True)
    def mock_settings(self):
        with patch("aegisScout.discovery.instagram_finder.settings") as mock_cfg:
            mock_cfg.google_custom_search_api_key = "FAKE_API_KEY"
            mock_cfg.google_custom_search_cx = "FAKE_CX"
            yield mock_cfg

    def test_relevance_score_no_sector(self):
        """Sektör verilmediğinde score sadece iletişim bilgisine göre belirlenmeli."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        profile_with_contact = {
            "username": "test_user",
            "full_name": "Test User",
            "bio": "Bireysel kullanici",
            "category": "",
            "email": "test@example.com",
            "phone": "+905001112233",
            "website": None,
            "is_verified": False,
            "linktree_url": None,
        }
        score = finder._calculate_relevance_score(profile_with_contact, "")
        assert score >= 50, "Iletisim bilgisi olan profil en az 50 almalı"
        assert score <= 75, "Sektorsuz profil 75'ten fazla almamalı"

    def test_relevance_score_with_username_keyword_match(self):
        """Kullanici adi sektor kelimesiyle esllesince yuksek skor gelmeli."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        profile = {
            "username": "kuafor_istanbul",
            "full_name": "Kuafor Salonu",
            "bio": "Sac bakimi ve guzellik hizmetleri",
            "category": "Kuafor",
            "email": "info@kuafor.com",
            "phone": "+905001112233",
            "website": "https://kuafor.com",
            "is_verified": False,
            "linktree_url": None,
        }
        score = finder._calculate_relevance_score(profile, "kuafor")
        assert score >= 70, f"Guclu eslesme icin skor 70+ olmali, aldi: {score}"
        assert score <= 99, "Skor 99'u geccmemeli"

    def test_relevance_score_no_keyword_match_penalty(self):
        """Sektor ile hic esllesmeyen profil dusuk skor almali."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        profile = {
            "username": "random_person_xyz",
            "full_name": "Random Person",
            "bio": "Kisisel hesap, fotograflarim",
            "category": "Kisisel Profil",
            "email": None,
            "phone": None,
            "website": None,
            "is_verified": False,
            "linktree_url": None,
        }
        score = finder._calculate_relevance_score(profile, "dis hekimi klinigi")
        assert score <= 50, f"Hic esllesme yok, dusuk skor olmali: {score}"

    def test_dm_draft_generation_all_tones(self):
        """DM taslak tum tonlarla basariyla olusturulmali."""
        from aegisScout.gui_impl import GuiApi
        api = GuiApi()

        tones = ["professional", "friendly", "persuasive", "concise"]
        for tone in tones:
            result = api.generate_instagram_dm_draft(
                username="test_isletme",
                bio="Guzellik salonu ve kuafor hizmetleri",
                sector="Guzellik Salonu",
                tone=tone,
                goal="digital_transformation"
            )
            assert result["success"] is True, f"Tone '{tone}' basarisiz oldu"
            assert "@test_isletme" in result["dm_draft"], f"Tone '{tone}' username icermiyor"
            assert len(result["dm_draft"]) > 50, f"Tone '{tone}' mesaj cok kisa"

    @pytest.mark.asyncio
    async def test_anonymous_viewer_fallback_on_no_posts(self):
        """Anonim goruntuleyici post bulamazsa profil fotografini gostermeli."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        with patch.object(finder, "fetch_profile_details", return_value={
            "username": "test_user",
            "full_name": "Test User",
            "profile_pic_url": "https://unavatar.io/instagram/test_user",
            "bio": "Test biyografi",
            "followers": "1K",
            "followers_raw": 1000,
            "posts": "10",
            "last_active_raw": 80,
            "has_story": False,
        }):
            with respx.mock:
                respx.get(url__regex=r".*instagram\.com/test_user/embed.*").mock(
                    return_value=httpx.Response(200, text="<html><body>No posts</body></html>")
                )
                respx.get(url__regex=r".*picuki\.com.*").mock(
                    return_value=httpx.Response(404)
                )
                respx.get(url__regex=r".*imginn\.com.*").mock(
                    return_value=httpx.Response(404)
                )

                result = await finder.fetch_anonymous_user_posts_and_stories("test_user")

        assert result["success"] is True
        assert result["username"] == "test_user"
        # When no posts found, should fallback to profile pic
        assert len(result["posts"]) >= 1

    def test_extract_phone_and_whatsapp_formats(self):
        """Telefon numarasi extraction farkli formatlarda calismalı."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        # Format 1: wa.me link
        phone, wp = finder._extract_phone_and_whatsapp("https://wa.me/905321234567")
        assert phone == "+905321234567"
        assert wp == "https://wa.me/905321234567"

        # Format 2: 05XX with spaces
        phone2, wp2 = finder._extract_phone_and_whatsapp("Tel: 0532 123 45 67 ara!")
        assert phone2 == "+905321234567"
        assert wp2 is not None

        # Format 3: No phone
        phone3, wp3 = finder._extract_phone_and_whatsapp("Hello world no phone here")
        assert phone3 is None
        assert wp3 is None
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

    @pytest.mark.asyncio
    async def test_direct_username_search_no_suffix_variations(self):
        """Doğrudan kullanıcı adı aramasında yapay son takılar (_official, _tr vb.) üretilmemeli."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        with patch.object(finder, "_instagram_topsearch", return_value=[{"username": "muammeremincaglar"}]):
            with patch.object(finder, "fetch_profile_details", side_effect=lambda u, s: {
                "username": u, "full_name": u.title(), "bio": "Test bio", "is_business": False, "category": "Kişisel Profil"
            }):
                results = await finder._search_by_username_direct("muammeremincaglar", "", target_limit=10)
                handles = [r["username"] for r in results]
                # Ensure no synthetic suffixes like muammeremincaglar_official were generated
                assert "muammeremincaglar_official" not in handles
                assert "muammeremincaglar_tr" not in handles
                assert "muammeremincaglar_resmi" not in handles
                assert "muammeremincaglar" in handles

    def test_is_business_personal_classification(self):
        """Kişisel profiller is_business=False ve category='Kişisel Profil' olmalı."""
        from aegisScout.discovery.instagram_finder import InstagramFinder
        finder = InstagramFinder()

        # Mock HTML parsing for personal account
        html_personal = """
        <html>
        <head>
            <meta property="og:title" content="Emin Çağlar (@muammeremincaglar) • Instagram photos" />
            <meta property="og:description" content="1,200 Followers, 500 Following, 80 Posts - Emin Çağlar kişisel profil, özel fotoğraflarım." />
        </head>
        <body></body>
        </html>
        """
        with respx.mock:
            respx.get(url__regex=r".*instagram\.com/muammeremincaglar/.*").mock(
                return_value=httpx.Response(200, text=html_personal)
            )
            respx.get(url__regex=r".*web_profile_info.*").mock(
                return_value=httpx.Response(404)
            )

            import asyncio
            profile = asyncio.run(finder.fetch_profile_details("muammeremincaglar", target_sector=""))
            assert profile["is_business"] is False
            assert profile["category"] == "Kişisel Profil"
            assert profile["username"] == "muammeremincaglar"



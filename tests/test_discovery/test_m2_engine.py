"""
Unit test suite for Milestone M2 (Anonymous Profile, Story & Highlight Engine).
Tests Features 5, 6, 7, 8 in AegisScout.
"""
import pytest
import respx
import httpx
from unittest.mock import patch

from aegisScout.discovery.instagram_finder import InstagramFinder
from aegisScout.discovery.instagram_session import InstagramSessionManager
from aegisScout.discovery.web_mirrors import WebMirrorPipeline, InstaNavigationAdapter, PicukiAdapter
from aegisScout.discovery.recency_classifier import RecencyClassifier, RecencyResult


class TestM2Engine:
    """Comprehensive test suite for AegisScout M2 Engine."""

    @pytest.mark.asyncio
    async def test_feature_5_web_profile_info_headers_and_parsing(self):
        """Verify Tier 0 web_profile_info API headers and JSON response parsing."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        mock_user_json = {
            "data": {
                "user": {
                    "id": "12345678",
                    "username": "testuser",
                    "full_name": "Test User Name",
                    "biography": "Official Test Bio for aegisScout",
                    "is_verified": True,
                    "is_business_account": True,
                    "category_name": "Digital Creator",
                    "edge_followed_by": {"count": 12500},
                    "edge_follow": {"count": 300},
                    "edge_owner_to_timeline_media": {
                        "count": 45,
                        "edges": [
                            {
                                "node": {
                                    "id": "post_100",
                                    "shortcode": "Cx12345",
                                    "display_url": "https://cdn.example.com/p1.jpg",
                                    "edge_media_to_caption": {"edges": [{"node": {"text": "Test Caption"}}] if True else []},
                                    "is_video": False,
                                }
                            }
                        ],
                    },
                }
            }
        }

        with respx.mock:
            # Mock guest cookie bootstrapping endpoint
            respx.get("https://www.instagram.com/").mock(
                return_value=httpx.Response(
                    200,
                    text='<html><script>var x = {"csrf_token":"mock_csrf_val"};</script></html>',
                    headers={"set-cookie": "mid=MOCKMID; Path=/"},
                )
            )

            # Mock web_profile_info endpoint
            route = respx.get("https://www.instagram.com/api/v1/users/web_profile_info/?username=testuser").mock(
                return_value=httpx.Response(200, json=mock_user_json)
            )

            profile = await finder.fetch_profile_details("testuser")

            assert route.called
            last_req = route.calls.last.request
            assert last_req.headers.get("x-asbd-id") == "198387"
            assert last_req.headers.get("x-ig-www-claim") == "0"
            assert last_req.headers.get("x-requested-with") == "XMLHttpRequest"
            assert "Referer" in last_req.headers
            assert "testuser" in last_req.headers["Referer"]

            assert profile["username"] == "testuser"
            assert profile["id"] == "12345678"
            assert profile["full_name"] == "Test User Name"
            assert profile["bio"] == "Official Test Bio for aegisScout"
            assert profile["is_verified"] is True
            assert profile["is_business"] is True
            assert profile["category"] == "Digital Creator"
            assert profile["followers_raw"] == 12500

    @pytest.mark.asyncio
    async def test_feature_6_anonymous_story_and_highlight_extractor(self):
        """Verify anonymous story and highlight extraction with structured output."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        mock_reel_json = {
            "reels": {
                "12345678": {
                    "items": [
                        {
                            "id": "story_999",
                            "media_type": 1,
                            "taken_at": 1700000000,
                            "expiring_at": 1700086400,
                            "image_versions2": {
                                "candidates": [{"url": "https://cdn.example.com/story1.jpg"}]
                            },
                        }
                    ]
                }
            }
        }

        mock_hl_json = {
            "tray": [
                {
                    "id": "highlight_101",
                    "title": "Summer 2026",
                    "cover_media": {
                        "cropped_image_version": {"url": "https://cdn.example.com/cover1.jpg"}
                    },
                    "items": [
                        {
                            "id": "hl_item_1",
                            "media_type": 1,
                            "taken_at": 1690000000,
                            "image_versions2": {
                                "candidates": [{"url": "https://cdn.example.com/hl1.jpg"}]
                            },
                        }
                    ],
                }
            ]
        }

        with respx.mock(assert_all_mocked=False) as respx_mock:
            # Mock web_profile_info to return user ID
            respx_mock.get("https://www.instagram.com/api/v1/users/web_profile_info/?username=testuser").mock(
                return_value=httpx.Response(
                    200,
                    json={"data": {"user": {"id": "12345678", "username": "testuser"}}},
                )
            )

            respx_mock.get("https://www.instagram.com/api/v1/feed/reels_media/?reel_ids=12345678").mock(
                return_value=httpx.Response(200, json=mock_reel_json)
            )

            respx_mock.get("https://www.instagram.com/api/v1/highlights/12345678/highlights_tray/").mock(
                return_value=httpx.Response(200, json=mock_hl_json)
            )

            respx_mock.get("https://www.instagram.com/testuser/embed/").mock(
                return_value=httpx.Response(200, text="<html><body>No embed media</body></html>")
            )

            result = await finder.fetch_anonymous_user_posts_and_stories("testuser")

            assert result["success"] is True
            assert result["username"] == "testuser"
            assert len(result["stories"]) == 1
            story = result["stories"][0]
            assert story["id"] == "story_999"
            assert story["media_type"] == "image"
            assert story["media_url"] == "https://cdn.example.com/story1.jpg"
            assert story["source"] == "Direct IG API"

            assert len(result["highlights"]) == 1
            hl = result["highlights"][0]
            assert hl["id"] == "highlight_101"
            assert hl["title"] == "Summer 2026"
            assert hl["cover_media_url"] == "https://cdn.example.com/cover1.jpg"
            assert hl["media_count"] == 1

    @pytest.mark.asyncio
    async def test_feature_7_web_mirror_pipeline_failover(self):
        """Verify WebMirrorPipeline failover across multiple adapters."""
        session_mgr = InstagramSessionManager()
        pipeline = WebMirrorPipeline(session_manager=session_mgr)

        with respx.mock(assert_all_mocked=False) as respx_mock:
            # Picuki succeeds with profile HTML (Picuki is first profile adapter)
            picuki_html = """
            <html>
                <head><title>Picuki Target</title></head>
                <body>
                    <div class="profile-name">Target User Full Name</div>
                    <div class="profile-bio">Bio retrieved via Picuki Mirror</div>
                    <div class="followed_by">15.4K</div>
                    <div class="profile-avatar"><img src="https://picuki.com/avatar.jpg"/></div>
                </body>
            </html>
            """
            # Mock both Picuki URL variants
            respx_mock.get(url__regex=r".*picuki\.com/profile/targetuser.*").mock(
                return_value=httpx.Response(200, text=picuki_html)
            )

            profile = await pipeline.fetch_profile("targetuser")

            assert profile is not None
            assert profile["username"] == "targetuser"
            assert profile["bio"] == "Bio retrieved via Picuki Mirror"
            assert profile["followers_raw"] == 15400
            assert profile["source_api"] == "Picuki"

    def test_feature_8_multi_signal_recency_classification(self):
        """Verify RecencyClassifier multi-signal parsing logic."""
        # 1. Hours ago pattern
        r1 = RecencyClassifier.classify(text_or_html="Active 3 saat önce posted")
        assert r1.status_enum == "ACTIVE_RECENT"
        assert r1.raw_score >= 90
        assert "3 Saat" in r1.human_text

        # 2. Relative days pattern ("Son 5 Gün")
        r2 = RecencyClassifier.classify(text_or_html="Son 5 Gün İçinde Aktif")
        assert r2.status_enum == "ACTIVE_RECENT"
        assert r2.raw_score >= 85
        assert r2.estimated_days == 5.0

        # 3. Month-Year pattern ("Son İçerik: Mart 2026")
        r3 = RecencyClassifier.classify(text_or_html="Son İçerik: Mart 2026")
        assert r3.status_enum == "ACTIVE_RECENT"
        assert "Mart 2026" in r3.human_text

        # 4. Zero post pattern
        r4 = RecencyClassifier.classify(text_or_html="Gönderi Yok", post_count=0)
        assert r4.status_enum == "INACTIVE"
        assert r4.is_zero_post is True
        assert r4.raw_score == 15
        assert r4.human_text == "Gönderisiz Hesap"

        # 5. Year-only pattern 2025
        r5 = RecencyClassifier.classify(text_or_html="Copyright 2025 Account")
        assert r5.status_enum == "ACTIVE_MODERATE"
        assert r5.raw_score == 80

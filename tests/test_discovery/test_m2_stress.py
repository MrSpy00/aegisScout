"""
Empirical Stress Test Suite for Milestone M2 (Anonymous Profile, Story & Highlight Engine).
Created by Challenger M2 to stress-test edge cases, adversarial inputs, malformed HTML,
corrupted payloads, invalid dates, zero-post profiles, and network errors.
"""
import pytest
import respx
import httpx
import re
from datetime import datetime, timezone

from aegisScout.discovery.instagram_finder import InstagramFinder
from aegisScout.discovery.instagram_session import InstagramSessionManager
from aegisScout.discovery.web_mirrors import (
    WebMirrorPipeline,
    InstaNavigationAdapter,
    PicukiAdapter,
    ImginnAdapter,
    DumporAdapter,
    GreatfonAdapter,
)
from aegisScout.discovery.recency_classifier import RecencyClassifier, RecencyResult


def mock_guest_cookies(respx_mock):
    """Helper to mock Instagram guest cookie bootstrapping."""
    respx_mock.get("https://www.instagram.com/").mock(
        return_value=httpx.Response(
            200,
            text='<html><script>var x = {"csrf_token":"mock_csrf"};</script></html>',
            headers={"set-cookie": "mid=MOCKMID; Path=/"},
        )
    )


class TestM2StressAndResilience:
    """Stress tests for M2 component resilience."""

    # =========================================================================
    # 1. Malformed Mirror HTML & Missing DOM Elements
    # =========================================================================

    @pytest.mark.asyncio
    async def test_instanavigation_malformed_html_and_missing_attributes(self):
        """Test InstaNavigationAdapter with malformed HTML, empty tags, missing src/content."""
        session_mgr = InstagramSessionManager()
        adapter = InstaNavigationAdapter(session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            # 1. Empty body / short response
            respx_mock.route(url__regex=r".*instanavigation\.com.*shortuser.*").mock(
                side_effect=lambda req: httpx.Response(200, text="<html><body>Short</body></html>")
            )
            res_short = await adapter.fetch_profile("shortuser")
            assert res_short is None

            # 2. Malformed HTML with meta tag missing content attribute & img inside div container
            malformed_html = """
            <html>
                <head>
                    <meta property="og:title">
                    <meta property="og:description" content="10.5K Followers, 100 Following, 50 Posts">
                </head>
                <body>
                    <img class="profile-avatar" /> <!-- No src attribute -->
                    <div class="story-item"><img /></div> <!-- No src or data-src inside img -->
                    <div class="story-item"><img src="https://cdn.example.com/valid.jpg" class="video"/></div>
                    <div class="highlight-item">
                        <span class="title"></span> <!-- Empty title -->
                        <img></img> <!-- No src -->
                    </div>
                </body>
            </html>
            """
            respx_mock.route(url__regex=r".*instanavigation\.com.*malformeduser.*").mock(
                side_effect=lambda req: httpx.Response(200, text=malformed_html * 5)
            )

            prof = await adapter.fetch_profile("malformeduser")
            assert prof is not None
            assert prof["username"] == "malformeduser"
            assert prof["followers_raw"] == 10500
            assert prof["profile_pic_url"] is None

            # CHALLENGE: fetch_stories when story-item is a div container around img
            stories = await adapter.fetch_stories("malformeduser")
            # If implementation properly extracts src from child img or handles container, stories should be extracted.
            assert stories is not None, "BUG: InstaNavigationAdapter.fetch_stories returned None when story-item is a div containing img"
            assert len(stories) == 1
            assert stories[0]["media_type"] == "video"
            assert stories[0]["media_url"] == "https://cdn.example.com/valid.jpg"

    @pytest.mark.asyncio
    async def test_picuki_malformed_html(self):
        """Test PicukiAdapter with missing profile elements or garbage text.
        Updated: PicukiAdapter now returns None when profile HTML has no meaningful data
        (no bio, no followers, name same as username) — this is the correct behavior.
        """
        session_mgr = InstagramSessionManager()
        adapter = PicukiAdapter(session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            garbage_html = "<html><body><div>Random Content Without Profile Tags</div></body></html>" * 20
            respx_mock.route(url__regex=r".*picuki\.com/profile/garbageuser.*").mock(
                side_effect=lambda req: httpx.Response(200, text=garbage_html)
            )

            prof = await adapter.fetch_profile("garbageuser")
            # Improved behavior: None returned when no meaningful profile data found
            # This prevents garbage data from polluting the results
            assert prof is None

    @pytest.mark.asyncio
    async def test_imginn_malformed_stories(self):
        """Test ImginnAdapter story parsing with missing or invalid image sources."""
        session_mgr = InstagramSessionManager()
        adapter = ImginnAdapter(session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            # HTML with img tags having short/invalid src
            html = """
            <html>
                <body>
                    <div class="items">
                        <img src="short.jpg" />
                        <img data-src="https://cdn.example.com/story_valid_image.jpg" />
                    </div>
                </body>
            </html>
            """
            # Adapter tries: /stories/, /story/, imginn.org/stories/ — mock all patterns
            respx_mock.route(url__regex=r".*imginn\.(com|org).*(stories|story)/testuser.*").mock(
                side_effect=lambda req: httpx.Response(200, text=html)
            )

            stories = await adapter.fetch_stories("testuser")
            assert stories is not None
            assert len(stories) == 1
            assert stories[0]["media_url"] == "https://cdn.example.com/story_valid_image.jpg"

    @pytest.mark.asyncio
    async def test_pipeline_total_mirror_failure(self):
        """Test WebMirrorPipeline when all mirrors fail or timeout."""
        session_mgr = InstagramSessionManager()
        pipeline = WebMirrorPipeline(session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            respx_mock.route(url__regex=r".*").mock(side_effect=httpx.ConnectTimeout("Down"))

            prof = await pipeline.fetch_profile("downuser")
            assert prof is None

            stories = await pipeline.fetch_stories("downuser")
            assert stories == []

            highlights = await pipeline.fetch_highlights("downuser")
            assert highlights == []

    # =========================================================================
    # 2. Corrupted / Empty / Null Story & Highlight API Payloads
    # =========================================================================

    @pytest.mark.asyncio
    async def test_corrupted_direct_story_api_payloads(self):
        """Test fetch_user_stories against empty, null, or weirdly structured JSON responses."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            # Case A: reels media returns empty dict {}
            respx_mock.route(url__startswith="https://www.instagram.com/api/v1/feed/reels_media/?reel_ids=111").mock(
                side_effect=lambda req: httpx.Response(200, json={})
            )
            # Mock all mirror/story URLs to return 404 (so stories == [])
            respx_mock.route(url__regex=r".*(instanavigation|imginn|storiesig|instafinsta|story).*user111.*").mock(
                side_effect=lambda req: httpx.Response(404, text="Not Found")
            )

            s1 = await finder.fetch_user_stories("user111", user_id="111")
            assert s1 == []

            # Case B: reels media returns items with missing video_versions/candidates
            corrupted_reels = {
                "reels": {
                    "222": {
                        "items": [
                            {"id": "s1", "media_type": 2},  # Video but no video_versions
                            {"id": "s2", "media_type": 1, "image_versions2": {}},  # Image but no candidates
                            {"id": "s3", "media_type": 1, "image_versions2": {"candidates": [{"url": "http://ok.com/img.jpg"}]}},
                        ]
                    }
                }
            }
            respx_mock.route(url__startswith="https://www.instagram.com/api/v1/feed/reels_media/?reel_ids=222").mock(
                side_effect=lambda req: httpx.Response(200, json=corrupted_reels)
            )

            s2 = await finder.fetch_user_stories("user222", user_id="222")
            assert len(s2) == 1
            assert s2[0]["id"] == "s3"
            assert s2[0]["media_url"] == "http://ok.com/img.jpg"

    @pytest.mark.asyncio
    async def test_corrupted_direct_highlight_api_payloads(self):
        """Test fetch_user_highlights against null cover_media and items with missing fields."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            # Notice cover_media is None in JSON (null in JSON)
            corrupted_hl = {
                "tray": [
                    {
                        "id": "hl_corrupt",
                        "title": "Broken Highlight",
                        "cover_media": None,
                        "items": [
                            {"id": "i1", "media_type": 1, "image_versions2": None}
                        ]
                    },
                    {
                        "id": "hl_valid",
                        "title": "Good Highlight",
                        "cover_media": {"cropped_image_version": {"url": "http://ok.com/cover.jpg"}},
                        "items": [
                            {"id": "i2", "media_type": 1, "image_versions2": {"candidates": [{"url": "http://ok.com/h.jpg"}]}}
                        ]
                    }
                ]
            }
            respx_mock.route(url__startswith="https://www.instagram.com/api/v1/highlights/333/highlights_tray/").mock(
                side_effect=lambda req: httpx.Response(200, json=corrupted_hl)
            )

            hl = await finder.fetch_user_highlights("user333", user_id="333")
            # Should handle exception on first corrupt tray gracefully or process valid ones
            assert isinstance(hl, list)

    # =========================================================================
    # 3. RecencyClassifier Edge Cases & Invalid Dates
    # =========================================================================

    def test_recency_classifier_invalid_and_edge_inputs(self):
        """Test RecencyClassifier under extreme/invalid date strings and timestamps."""
        # 1. Invalid / Out-of-bounds days in Month-Year format ("35 Mart 2026")
        r_invalid_day = RecencyClassifier.classify(text_or_html="Son İçerik: 35 Mart 2026")
        assert r_invalid_day.status_enum in ["ACTIVE_RECENT", "UNKNOWN", "ACTIVE_MODERATE"]

        # 2. Future timestamp (now + 100,000 seconds)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        r_future = RecencyClassifier.classify(latest_timestamp=now_ts + 100000)
        assert r_future.status_enum == "ACTIVE_RECENT"
        assert r_future.estimated_days == 0.0

        # 3. Negative / 0 timestamp
        r_neg = RecencyClassifier.classify(latest_timestamp=-500)
        assert r_neg.status_enum == "UNKNOWN"

        # 4. English month parsing with uppercase ("15 DECEMBER 2025")
        r_eng_month = RecencyClassifier.classify(text_or_html="Posted on 15 DECEMBER 2025")
        assert r_eng_month.status_enum == "ACTIVE_MODERATE"
        assert "December 2025" in r_eng_month.human_text

        # 5. Overly large relative hours / days
        r_huge_hours = RecencyClassifier.classify(text_or_html="Active 5000 saat önce")
        assert r_huge_hours.status_enum == "ACTIVE_RECENT"
        assert r_huge_hours.human_text == "Son 5000 Saat İçinde Aktif"

        # 6. Ambiguous year strings (e.g. "Founded in 2024")
        r_year = RecencyClassifier.classify(text_or_html="Established company since 2024")
        assert r_year.status_enum == "INACTIVE"
        assert "2024" in r_year.human_text

    # =========================================================================
    # 4. Zero-Post Profiles & Tier 0 Recency Contract
    # =========================================================================

    @pytest.mark.asyncio
    async def test_tier0_profile_recency_and_zero_post_contract(self):
        """Test profile detail fetching via Tier 0 JSON API for presence of recency_status & is_zero_post."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        mock_zero_user_json = {
            "data": {
                "user": {
                    "id": "999000",
                    "username": "zeropostuser",
                    "full_name": "Zero Post User",
                    "biography": "Empty account with 0 posts yet",
                    "is_verified": False,
                    "is_business_account": False,
                    "edge_followed_by": {"count": 10},
                    "edge_follow": {"count": 50},
                    "edge_owner_to_timeline_media": {
                        "count": 0,
                        "edges": []
                    }
                }
            }
        }

        with respx.mock:
            mock_guest_cookies(respx)
            respx.get("https://www.instagram.com/api/v1/users/web_profile_info/?username=zeropostuser").mock(
                return_value=httpx.Response(200, json=mock_zero_user_json)
            )

            profile = await finder.fetch_profile_details("zeropostuser")
            assert profile["username"] == "zeropostuser"
            assert profile["posts"] == "0"
            
            # CHALLENGE: Contract check for Feature 8 on Tier 0 API
            assert "is_zero_post" in profile, "BUG: fetch_profile_details missing 'is_zero_post' on Tier 0 web_profile_info path"
            assert "recency_status" in profile, "BUG: fetch_profile_details missing 'recency_status' on Tier 0 web_profile_info path"
            assert profile["is_zero_post"] is True
            assert profile["recency_status"] == "INACTIVE"

    # =========================================================================
    # 5. Network Errors & Retry Resilience
    # =========================================================================

    @pytest.mark.asyncio
    async def test_network_errors_and_http_status_failures(self):
        """Test system stability under HTTP status errors and connection timeouts."""
        session_mgr = InstagramSessionManager()
        finder = InstagramFinder(session_manager=session_mgr)

        with respx.mock(assert_all_called=False, assert_all_mocked=False) as respx_mock:
            mock_guest_cookies(respx_mock)
            respx_mock.route(url__regex=r".*web_profile_info.*erruser.*").mock(
                side_effect=lambda req: httpx.Response(404, text="Not Found")
            )
            respx_mock.route(url__regex=r".*instagram\.com/erruser/").mock(
                side_effect=lambda req: httpx.Response(500, text="Server Error")
            )
            respx_mock.route(url__regex=r".*instagram\.com/erruser/embed.*").mock(
                side_effect=lambda req: httpx.Response(503, text="Service Unavailable")
            )
            # Mock all mirror profiles to 500/404
            respx_mock.route(url__regex=r".*picuki\.com.*erruser.*").mock(
                side_effect=lambda req: httpx.Response(500, text="Internal Error")
            )
            respx_mock.route(url__regex=r".*imginn\.com/erruser.*").mock(
                side_effect=lambda req: httpx.Response(404, text="Not Found")
            )
            respx_mock.route(url__regex=r".*instanavigation\.com.*erruser.*").mock(
                side_effect=httpx.ReadTimeout("Read Timeout")
            )
            respx_mock.route(url__regex=r".*dumpor\.com.*erruser.*").mock(
                side_effect=lambda req: httpx.Response(404, text="Not Found")
            )
            respx_mock.route(url__regex=r".*greatfon\.com.*erruser.*").mock(
                side_effect=lambda req: httpx.Response(404, text="Not Found")
            )

            profile = await finder.fetch_profile_details("erruser")
            assert profile["username"] == "erruser"
            assert profile["followers"] == "N/A"

            anon_res = await finder.fetch_anonymous_user_posts_and_stories("erruser")
            assert anon_res["success"] is True
            assert anon_res["username"] == "erruser"
            assert len(anon_res["posts"]) == 1

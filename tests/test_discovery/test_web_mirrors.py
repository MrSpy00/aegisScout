"""
Unit tests for WebMirrorPipeline and all mirror adapters.
Tests run in mock mode — no real HTTP calls.
"""
from __future__ import annotations

import pytest
import respx
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from aegisScout.discovery.instagram_session import InstagramSessionManager
from aegisScout.discovery.web_mirrors import (
    WebMirrorPipeline,
    StoriesIgAdapter,
    PicukiAdapter,
    ImginnAdapter,
    InstaNavigationAdapter,
    InstaFinstaAdapter,
    DumporAdapter,
    GreatfonAdapter,
)


@pytest.fixture
def session_manager():
    """Create a real InstagramSessionManager with minimal config."""
    sm = InstagramSessionManager()
    return sm


@pytest.fixture
def pipeline(session_manager):
    return WebMirrorPipeline(session_manager)


class TestStoriesIgAdapter:
    """Tests for StoriesIG story viewer adapter."""

    @pytest.mark.asyncio
    async def test_fetch_stories_success(self, session_manager):
        """Should parse story images from valid storiesig HTML."""
        adapter = StoriesIgAdapter(session_manager)
        html = """
        <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>cristiano - StoriesIG</title>
        </head>
        <body>
          <div class="stories-container">
            <div class="story-item">
              <img src="https://cdninstagram.com/v/story1.jpg" alt="story 1" />
            </div>
            <div class="story-item">
              <img src="https://cdninstagram.com/v/story2.jpg" alt="story 2" />
            </div>
          </div>
          <footer>Powered by StoriesIG - Anonymous Instagram Viewer</footer>
        </body>
        </html>
        """
        with respx.mock:
            # Adapter tries multiple URLs — mock all variants
            respx.get(url__regex=r".*storiesig\.info.*cristiano.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            respx.get(url__regex=r".*storiesig\.app.*cristiano.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            respx.get(url__regex=r".*storiesig\.com.*cristiano.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_stories("cristiano")

        assert result is not None
        assert len(result) >= 1
        assert all("media_url" in s for s in result)
        assert all(s["media_type"] == "image" for s in result)
        assert all(s["source"] == "StoriesIG" for s in result)

    @pytest.mark.asyncio
    async def test_fetch_stories_empty_page(self, session_manager):
        """Should return None on empty/invalid page."""
        adapter = StoriesIgAdapter(session_manager)
        with respx.mock:
            respx.get(url__regex=r".*storiesig.*").mock(
                return_value=httpx.Response(200, text="<html><body></body></html>")
            )
            result = await adapter.fetch_stories("nonexistent_user_xyz")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_stories_http_error(self, session_manager):
        """Should return None on HTTP errors."""
        adapter = StoriesIgAdapter(session_manager)
        with respx.mock:
            respx.get(url__regex=r".*storiesig.*").mock(
                return_value=httpx.Response(404)
            )
            result = await adapter.fetch_stories("test_user")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_profile_returns_none(self, session_manager):
        """StoriesIg doesn't expose profile stats — should return None."""
        adapter = StoriesIgAdapter(session_manager)
        result = await adapter.fetch_profile("any_user")
        assert result is None


class TestPicukiAdapter:
    """Tests for Picuki profile adapter."""

    @pytest.mark.asyncio
    async def test_fetch_profile_success(self, session_manager):
        """Should extract profile data from Picuki HTML."""
        adapter = PicukiAdapter(session_manager)
        html = """
        <html>
        <head>
          <meta property="og:title" content="Test Business Profile" />
          <meta property="og:description" content="12.5K Followers, 450 Following, 200 Posts" />
        </head>
        <body>
          <h1 class="profile-name-top h1">Test Business</h1>
          <div class="profile-description">Güzellik salonu hizmetleri</div>
          <img class="avatar" src="https://cdninstagram.com/profile.jpg" />
        </body>
        </html>
        """
        with respx.mock:
            respx.get(url__regex=r".*picuki\.com.*test_business.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_profile("test_business")

        assert result is not None
        assert result["username"] == "test_business"
        assert result["source_api"] == "Picuki"

    @pytest.mark.asyncio
    async def test_fetch_profile_404(self, session_manager):
        """Should return None on 404."""
        adapter = PicukiAdapter(session_manager)
        with respx.mock:
            respx.get(url__regex=r".*picuki\.com.*").mock(
                return_value=httpx.Response(404)
            )
            result = await adapter.fetch_profile("nonexistent_user")

        assert result is None


class TestImginnAdapter:
    """Tests for Imginn adapter."""

    @pytest.mark.asyncio
    async def test_fetch_stories_imginn(self, session_manager):
        """Should extract stories from Imginn story page."""
        adapter = ImginnAdapter(session_manager)
        html = """
        <html><body>
          <div class="story-item">
            <img src="https://scontent.cdninstagram.com/story1_img.jpg" />
          </div>
        </body></html>
        """
        with respx.mock:
            respx.get(url__regex=r".*imginn\.(com|org).*stories.*test_user.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_stories("test_user")

        assert result is not None
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_fetch_profile_imginn(self, session_manager):
        """Should extract profile from Imginn."""
        adapter = ImginnAdapter(session_manager)
        # full_name must differ from username; HTML must be > 400 bytes
        html = """
        <html>
        <head><title>test_user - Imginn Anonymous Instagram Viewer</title></head>
        <body>
          <div class="user-name">Imginn Test Profile Name</div>
          <div class="user-bio">Test bio text from imginn</div>
          <div class="posts-list">
            <div class="post-item"><img src="https://cdn.test/post1.jpg" /></div>
          </div>
          <div class="user-stats">
            <span class="count">1234 followers</span>
          </div>
        </body>
        </html>
        """
        with respx.mock:
            respx.get(url__regex=r".*imginn\.com/test_user.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_profile("test_user")

        assert result is not None
        assert result["username"] == "test_user"
        assert result["bio"] == "Test bio text from imginn"


class TestInstaNavigationAdapter:
    """Tests for InstaNavigation adapter."""

    @pytest.mark.asyncio
    async def test_fetch_profile_via_og_tags(self, session_manager):
        """Should extract profile from InstaNavigation og: meta tags."""
        adapter = InstaNavigationAdapter(session_manager)
        html = """
        <html>
        <head>
          <meta property="og:title" content="Kuafor Salonu - InstaNavigation" />
          <meta property="og:description" content="25.3K Followers, 120 Following, 300 Posts" />
          <meta property="og:image" content="https://cdninstagram.com/profile_pic.jpg" />
          <meta name="description" content="Anonymous Instagram viewer for Kuafor Salonu" />
        </head>
        <body>
          <div class="profile-container">
            <h1>Kuafor Salonu</h1>
            <p class="bio">En iyi kuafor hizmetleri istanbul'da</p>
          </div>
        </body>
        </html>
        """
        with respx.mock:
            # Adapter tries two URL patterns
            respx.get(url__regex=r".*instanavigation\.com.*kuafor_salonu.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_profile("kuafor_salonu")

        assert result is not None
        assert result["username"] == "kuafor_salonu"
        assert result["profile_pic_url"] == "https://cdninstagram.com/profile_pic.jpg"

    @pytest.mark.asyncio
    async def test_fetch_stories_with_swiper_slides(self, session_manager):
        """Should extract stories from Swiper-style story containers."""
        adapter = InstaNavigationAdapter(session_manager)
        html = """
        <html><body>
          <div class="swiper-slide">
            <img src="https://cdn.example.com/story_slide1.jpg" />
          </div>
          <div class="swiper-slide">
            <img src="https://cdn.example.com/story_slide2.jpg" />
          </div>
        </body></html>
        """
        with respx.mock:
            respx.get(url__regex=r".*instanavigation\.com.*").mock(
                return_value=httpx.Response(200, text=html)
            )
            result = await adapter.fetch_stories("test_user")

        assert result is not None
        assert len(result) >= 1


class TestWebMirrorPipeline:
    """Integration tests for the full mirror pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_fetch_stories_first_adapter_wins(self, pipeline):
        """Pipeline should return first adapter's stories and stop."""
        expected_stories = [
            {"id": "s1", "media_type": "image", "media_url": "https://cdn.test/s1.jpg",
             "thumbnail_url": "https://cdn.test/s1.jpg", "taken_at": 0, "taken_at_iso": "", "source": "StoriesIG"}
        ]
        with patch.object(pipeline.story_adapters[0], "fetch_stories", return_value=expected_stories):
            with patch.object(pipeline.story_adapters[1], "fetch_stories") as mock_second:
                result = await pipeline.fetch_stories("cristiano")
                # Second adapter should NOT be called once first succeeds
                mock_second.assert_not_called()

        assert result == expected_stories

    @pytest.mark.asyncio
    async def test_pipeline_fetch_stories_fallback_on_empty(self, pipeline):
        """Pipeline should fall through to next adapter when first returns empty."""
        second_stories = [
            {"id": "s2", "media_type": "image", "media_url": "https://cdn.test/s2.jpg",
             "thumbnail_url": "https://cdn.test/s2.jpg", "taken_at": 0, "taken_at_iso": "", "source": "Imginn"}
        ]
        with patch.object(pipeline.story_adapters[0], "fetch_stories", return_value=None):
            with patch.object(pipeline.story_adapters[1], "fetch_stories", return_value=second_stories):
                result = await pipeline.fetch_stories("test_user")

        assert result == second_stories

    @pytest.mark.asyncio
    async def test_pipeline_fetch_stories_all_fail_returns_empty(self, pipeline):
        """Pipeline should return [] when all adapters fail."""
        for adapter in pipeline.story_adapters:
            adapter.fetch_stories = AsyncMock(return_value=None)

        result = await pipeline.fetch_stories("test_user")
        assert result == []

    @pytest.mark.asyncio
    async def test_pipeline_fetch_profile_returns_best(self, pipeline):
        """Pipeline should return first profile with meaningful data."""
        valid_profile = {
            "username": "test_biz",
            "full_name": "Test Business",
            "bio": "Güzellik salonu",
            "followers_raw": 5000,
            "followers": "5K",
            "source_api": "Picuki",
        }
        with patch.object(pipeline.profile_adapters[0], "fetch_profile", return_value=valid_profile):
            result = await pipeline.fetch_profile("test_biz")

        assert result is not None
        assert result["followers_raw"] == 5000

    @pytest.mark.asyncio
    async def test_pipeline_adapter_exception_does_not_crash(self, pipeline):
        """Adapter raising an exception should be silently skipped."""
        for adapter in pipeline.story_adapters:
            adapter.fetch_stories = AsyncMock(side_effect=Exception("connection timeout"))

        # Should not raise
        result = await pipeline.fetch_stories("test_user")
        assert result == []

    def test_pipeline_has_all_expected_adapters(self, pipeline):
        """Pipeline should include all expected adapter types."""
        adapter_names = {a.name for a in pipeline.adapters}
        expected_names = {"StoriesIG", "Picuki", "Imginn", "InstaNavigation", "InstaFinsta", "Dumpor", "Greatfon"}
        assert expected_names.issubset(adapter_names), \
            f"Missing adapters: {expected_names - adapter_names}"

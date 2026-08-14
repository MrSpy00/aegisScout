# Handoff Report: Milestone M2 (Anonymous Profile, Story & Highlight Engine)

## 1. Observation

1. **Created `src/aegisScout/discovery/web_mirrors.py`**:
   - Implemented `WebMirrorAdapter` abstract base class defining `name`, `fetch_profile`, `fetch_stories`, and `fetch_highlights`.
   - Implemented 5 concrete adapters: `InstaNavigationAdapter`, `PicukiAdapter`, `ImginnAdapter`, `DumporAdapter`, `GreatfonAdapter`.
   - Implemented `WebMirrorPipeline` to manage sequential fallback across adapters for profile, story, and highlight extraction.

2. **Created `src/aegisScout/discovery/recency_classifier.py`**:
   - Implemented `RecencyResult` dataclass (`status_enum`, `human_text`, `raw_score`, `estimated_days`, `last_post_timestamp`, `is_zero_post`).
   - Implemented `RecencyClassifier.classify()` supporting:
     - Explicit Unix timestamp delta calculations.
     - Zero-post indicators (`post_count == 0` or regex matches `"gönderi yok"`, `"0 posts"`, etc.).
     - Relative hours ("3 saat önce", "5 hours ago", "3h").
     - Relative days ("Son 5 Gün", "2 gün önce", "5d").
     - Relative weeks ("2 hafta önce", "3 weeks ago").
     - Month-year dates ("Son İçerik: Mart 2026", "Ocak 2025") with Turkish/English month lookup and year matching.
     - Exact year signals (2026 -> `ACTIVE_RECENT`, 2025 -> `ACTIVE_MODERATE`, 2024 -> `INACTIVE`).

3. **Refactored `src/aegisScout/discovery/instagram_finder.py`**:
   - **Feature 5**: Updated Tier 0 `web_profile_info` JSON API request in `fetch_profile_details`. Added guest cookie pre-fetching (`await self.session_manager.get_guest_cookies()`), injected required headers (`x-asbd-id: "198387"`, `x-ig-www-claim: "0"`, `x-requested-with: "XMLHttpRequest"`, `x-csrftoken`, `Referer`), and stored numeric user ID in `default_data["id"]`.
   - **Feature 6**: Implemented `fetch_user_stories` and `fetch_user_highlights` returning structured `StoryMediaItem` and `HighlightTrayItem` dicts with fallback to `WebMirrorPipeline`. Refactored `fetch_anonymous_user_posts_and_stories` to include `stories` and `highlights` arrays.
   - **Feature 7**: Wired `WebMirrorPipeline` in `_fetch_via_web_mirrors` and `InstagramFinder.__init__`.
   - **Feature 8**: Integrated `RecencyClassifier` into `fetch_profile_details` to set `last_active`, `last_active_raw`, `recency_status`, and `is_zero_post`.

4. **Created test suite `tests/test_discovery/test_m2_engine.py`**:
   - Implemented unit tests covering Features 5, 6, 7, and 8.
   - Executed full test suite:
     ```pwsh
     pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v
     ```
   - Result: `28 passed, 0 failed` in 23.43s.

---

## 2. Logic Chain

1. **Direct Guest API Headers (Feature 5)**:
   Pre-fetching guest cookies (`mid`, `ig_did`, `csrftoken`) and including headers (`x-asbd-id`, `x-ig-www-claim`, `x-requested-with`, `x-csrftoken`, `Referer`) makes guest `web_profile_info` requests closely mirror genuine browser traffic, avoiding HTTP 403 Forbidden responses.

2. **Story & Highlight Extractor with Mirror Fallback (Feature 6)**:
   `fetch_user_stories` and `fetch_user_highlights` attempt direct Instagram REST/GraphQL endpoints first when `user_id` is available, and fall back to `WebMirrorPipeline` if direct endpoints fail. This guarantees high reliability for media extraction without requiring logged-in credentials.

3. **Modular Public Web Mirror Pipeline (Feature 7)**:
   Abstracting mirror scraping into `WebMirrorAdapter` instances inside `WebMirrorPipeline` allows clean failover between InstaNavigation, Picuki, Imginn, Dumpor, and Greatfon without cluttering `instagram_finder.py`.

4. **Multi-Signal Recency Classifier (Feature 8)**:
   Standardizing activity scoring in `RecencyClassifier` provides uniform status enums (`ACTIVE_RECENT`, `ACTIVE_MODERATE`, `INACTIVE`, `UNKNOWN`), human-readable descriptions, estimated days, and numeric scores across all profile discovery layers.

---

## 3. Caveats

- **Third-Party Mirror Availability**: Third-party public mirrors (InstaNavigation, Picuki, Imginn, Dumpor, Greatfon) occasionally change DOM layouts or add anti-bot challenges. `WebMirrorPipeline` handles individual adapter failures gracefully by falling back to subsequent mirrors in the pipeline.
- **Instagram Guest Rate Limits**: Guest API calls may encounter temporary IP rate limits (HTTP 429). `InstagramSessionManager` retry logic and proxy rotation mitigate this.

---

## 4. Conclusion

Milestone M2 (Anonymous Profile, Story & Highlight Engine) has been fully implemented and verified. All 4 features (Features 5, 6, 7, and 8) are complete and tested with a 100% pass rate across all 28 unit test cases.

---

## 5. Verification Method

To verify the implementation:

1. **Run the full discovery test suite**:
   ```pwsh
   pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v
   ```
2. **Inspect modified and newly created files**:
   - `src/aegisScout/discovery/web_mirrors.py`
   - `src/aegisScout/discovery/recency_classifier.py`
   - `src/aegisScout/discovery/instagram_finder.py`
   - `tests/test_discovery/test_m2_engine.py`

3. **Invalidation Conditions**:
   - Any test failure in `test_m2_engine.py`.
   - `fetch_profile_details` missing `x-asbd-id` or `x-csrftoken` headers.
   - `fetch_anonymous_user_posts_and_stories` failing to return `stories` and `highlights` keys.
   - `RecencyClassifier` failing on relative Turkish/English recency strings.

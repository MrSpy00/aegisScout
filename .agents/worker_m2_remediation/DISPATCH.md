## 2026-08-06T16:26:36Z
Fix all 4 findings raised by Reviewer 2 in `x:\Projects\ActiveProjects\aegisScout\.agents\reviewer_m2_2\handoff.md`:

1. [Major] Finding 1 (RecencyClassifier Bypassed on Tier 0 JSON API):
   In `src/aegisScout/discovery/instagram_finder.py` (`fetch_profile_details`), move `RecencyClassifier.classify()` OUTSIDE `if fetched_html:` so it runs unconditionally for profiles fetched via Tier 0 `web_profile_info` JSON API as well as HTML tiers.
   Pass `text_or_html=fetched_html or default_data.get("bio", "")` and `post_count=_parse_count(default_data.get("posts", "0"))`. Ensure output dictionary always contains `last_active`, `last_active_raw`, `recency_status`, and `is_zero_post`.

2. [Major] Finding 2 (InstaNavigation Story Container Selector Mismatch):
   In `src/aegisScout/discovery/web_mirrors.py` (`InstaNavigationAdapter.fetch_stories`), update story item CSS selector to `.story-item img, .stories-list img, .story-box img` or inspect `item.find("img")` if `item.name != "img"` to properly extract `src` attributes when story images are wrapped in container `<div>` tags.

3. [Minor] Finding 3 (TypeError in RecencyClassifier on None Input):
   In `src/aegisScout/discovery/recency_classifier.py` (`RecencyClassifier.classify`), sanitize entry point: `text_or_html = str(text_or_html or "")`.

4. [Minor] Finding 4 (Deprecated MOCK_ROUTES in test_m2_stress.py):
   In `tests/test_discovery/test_m2_stress.py`, replace deprecated `respx.patterns.MOCK_ROUTES` with `respx.get(re.compile(r".*"))`.

Run full pytest verification across all test suites:
`pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py tests/test_discovery/test_m2_stress.py -v`

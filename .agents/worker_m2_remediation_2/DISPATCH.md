# DISPATCH — 2026-08-06T19:51:00Z

## Mission
Remediate the 4 findings identified by Reviewer 2 in Milestone M2 (Anonymous Profile, Story & Highlight Engine) for `aegisScout`.

## Path References
- Original User Request: `x:\Projects\ActiveProjects\aegisScout\.agents\ORIGINAL_REQUEST.md`
- Project Plan: `x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator\PROJECT.md`
- Reviewer 2 Report: `x:\Projects\ActiveProjects\aegisScout\.agents\reviewer_m2_2\handoff.md`

## Required Remediation Tasks
1. **Fix Finding 1: `RecencyClassifier` Bypassed When Tier 0 JSON API Succeeds**
   - Location: `src/aegisScout/discovery/instagram_finder.py` (around lines 886-984)
   - Issue: `RecencyClassifier.classify()` call is nested inside `if fetched_html:`. When Tier 0 `web_profile_info` succeeds, `fetched_html` remains `""` because Tier 0 returns JSON.
   - Fix: Move `RecencyClassifier.classify()` call outside `if fetched_html:`, passing `text_or_html=fetched_html or default_data.get("bio", "")` and `post_count=_parse_count(default_data.get("posts", "0"))` or extracting posts properly so `recency_status` and `is_zero_post` are populated.

2. **Fix Finding 2: `InstaNavigationAdapter` Container Selector Story Parsing Error**
   - Location: `src/aegisScout/discovery/web_mirrors.py` (around line 103)
   - Issue: `InstaNavigationAdapter.fetch_stories()` uses `.story-item, .stories-list img, .story-box img`. When story images are inside `<div class="story-item"><img .../></div>`, `soup.select` matches the `<div>` tag, causing `item.get("src")` to return `None`.
   - Fix: Update selector to `.story-item img, .stories-list img, .story-box img` or inspect `item.find("img")` if `item.name != "img"`.

3. **Fix Finding 3: `TypeError` in `RecencyClassifier` when `text_or_html=None`**
   - Location: `src/aegisScout/discovery/recency_classifier.py` (around line 90)
   - Issue: Passing `None` to `RecencyClassifier.classify()` raises `TypeError` in `re.search`.
   - Fix: Sanitize parameter: `text_or_html = str(text_or_html or "")`.

4. **Fix Finding 4: Deprecated `respx.patterns.MOCK_ROUTES` in `test_m2_stress.py`**
   - Location: `tests/test_discovery/test_m2_stress.py` (around line 135)
   - Issue: `respx.patterns.MOCK_ROUTES` was removed in `respx >= 0.23.1`, causing `AttributeError`.
   - Fix: Replace `respx.patterns.MOCK_ROUTES` with `respx.get(re.compile(r".*"))` or equivalent respx pattern.

## Mandatory Rules
- Run unit test suite: `pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v`
- Run stress test suite: `pytest tests/test_discovery/test_m2_stress.py -v`
- DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
- Document all changes and test outputs in `handoff.md` inside your working directory (`x:\Projects\ActiveProjects\aegisScout\.agents\worker_m2_remediation_2\`).

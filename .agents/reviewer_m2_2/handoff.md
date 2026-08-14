# Review & Critic Handoff Report: Milestone M2 (Anonymous Profile, Story & Highlight Engine)

**Reviewer Instance**: `reviewer_m2_2`  
**Verdict**: `REQUEST_CHANGES`  
**Overall Risk Assessment**: `HIGH`  

---

## 1. Observation

1. **Test Execution Results**:
   - Primary unit test suite execution:
     ```pwsh
     pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v
     ```
     Result: **28 passed, 0 failed** in 29.91s.
   - Empirical stress test suite execution:
     ```pwsh
     pytest tests/test_discovery/test_m2_stress.py -v
     ```
     Result: **6 passed, 3 failed**. Failures revealed integration gaps and DOM parsing deficiencies.

2. **Source Code Inspection Findings**:
   - **`src/aegisScout/discovery/instagram_finder.py` (lines 886-984)**:
     `RecencyClassifier.classify()` invocation is nested inside `if fetched_html:`. When Tier 0 `web_profile_info` JSON API succeeds, `fetched_html` remains `""` because Tier 0 returns JSON rather than HTML, causing HTML fetching tiers 1-4 to be skipped. Consequently, `RecencyClassifier.classify()` is **never executed** for profiles fetched via the primary JSON API. The output dictionary lacks `recency_status` and `is_zero_post`, and `last_active` is hardcoded to `"🟢 Aktif Profil (Gönderileri Mevcut)"` instead of dynamically calculated.
   - **`src/aegisScout/discovery/web_mirrors.py` (line 103)**:
     `InstaNavigationAdapter.fetch_stories()` uses CSS selector `.story-item, .stories-list img, .story-box img`. When InstaNavigation wraps story images in `<div class="story-item"><img src="..." /></div>`, `soup.select` returns the `<div class="story-item">` container. Attempting `item.get("src")` on a `<div>` tag yields `None`, causing story extraction from InstaNavigation to return no stories.
   - **`src/aegisScout/discovery/recency_classifier.py` (line 90)**:
     `RecencyClassifier.classify()` accepts `text_or_html: str = ""`. However, if `text_or_html` is explicitly passed as `None`, `re.search(pat, text_or_html, re.I)` raises `TypeError: expected string or bytes-like object`.
   - **`tests/test_discovery/test_m2_stress.py` (line 135)**:
     Uses `respx.patterns.MOCK_ROUTES` which does not exist in `respx >= 0.23.1`, causing `AttributeError`.

3. **Integrity Violation Assessment**:
   - Checked for hardcoded test results, facade implementations, and self-certifying shortcuts.
   - No intentional integrity violations or cheating detected in Worker M2's code. The implementation is genuine, but contains critical integration logic gaps.

---

## 2. Logic Chain

1. **Bypassed Recency Classification**:
   - Observation: In `fetch_profile_details()`, `recency_res = RecencyClassifier.classify(...)` is called at line 976 inside `if fetched_html:`.
   - Step 1: Tier 0 (`web_profile_info`) retrieves JSON data (biography, edge_owner_to_timeline_media, etc.) and updates `default_data`.
   - Step 2: Tiers 1-4 inspect `if fetched_html or default_data.get("posts_preview"): break`, skipping HTML network calls. `fetched_html` remains `""`.
   - Step 3: `if fetched_html:` evaluates to `False`. Lines 976-983 do not execute.
   - Conclusion: Profiles fetched via Tier 0 (the primary endpoint) miss `recency_status` and `is_zero_post` keys, and `last_active` is not scored by `RecencyClassifier`.

2. **DOM Element Selector Mismatch in Mirror Adapter**:
   - Observation: `soup.select(".story-item, .stories-list img, .story-box img")` matches `<div class="story-item">`.
   - Step 1: `item.get("src")` is called on the `<div>` tag. HTML `<div>` tags do not have `src` attributes.
   - Step 2: `src` evaluates to `None`, filter `if src and ("cdn" in src...)` skips the item.
   - Conclusion: `fetch_stories()` fails to parse story media from InstaNavigation when HTML structure wraps images inside `.story-item` containers.

---

## 3. Findings & Challenge Summary

### Major Findings (Must Fix)

#### [Major] Finding 1: `RecencyClassifier` Bypassed When Tier 0 JSON API Succeeds
- **What**: `RecencyClassifier.classify()` is not called when `web_profile_info` succeeds because it is nested inside `if fetched_html:`.
- **Where**: `src/aegisScout/discovery/instagram_finder.py`, lines 886-984.
- **Why**: `web_profile_info` returns JSON without setting `fetched_html`. As a result, returned profile dictionaries omit `recency_status` and `is_zero_post`, and `last_active` is not dynamically classified.
- **Suggestion**: Move `RecencyClassifier.classify()` call outside `if fetched_html:`, passing `text_or_html=fetched_html or default_data.get("bio", "")` and `post_count=_parse_count(default_data.get("posts", "0"))`.

#### [Major] Finding 2: `InstaNavigationAdapter` Container Selector Story Parsing Error
- **What**: `InstaNavigationAdapter.fetch_stories()` fails when story items are wrapped in `<div class="story-item">`.
- **Where**: `src/aegisScout/discovery/web_mirrors.py`, line 103.
- **Why**: Selector picks up `<div>` tags instead of inner `<img>` elements, leading to `src = None`.
- **Suggestion**: Change selector to `.story-item img, .stories-list img, .story-box img` or check `item.find("img")` if `item.name != "img"`.

### Minor Findings (Should Fix)

#### [Minor] Finding 3: `TypeError` in `RecencyClassifier` when `text_or_html=None`
- **What**: Passing `None` to `RecencyClassifier.classify()` raises `TypeError`.
- **Where**: `src/aegisScout/discovery/recency_classifier.py`, line 90.
- **Why**: `re.search` requires a string argument.
- **Suggestion**: Sanitize at entry point: `text_or_html = str(text_or_html or "")`.

#### [Minor] Finding 4: Deprecated `respx.patterns.MOCK_ROUTES` in `test_m2_stress.py`
- **What**: `test_pipeline_total_mirror_failure` fails with `AttributeError`.
- **Where**: `tests/test_discovery/test_m2_stress.py`, line 135.
- **Why**: `respx.patterns.MOCK_ROUTES` is removed in recent `respx` versions.
- **Suggestion**: Replace with `respx.get(re.compile(r".*"))`.

---

## 4. Caveats

- The 28 standard unit tests in `test_m2_engine.py`, `test_instagram_finder.py`, and `test_instagram_session.py` pass 100%. The issues were uncovered through deeper structural code analysis and empirical stress testing (`test_m2_stress.py`).
- Fixes for Findings 1 and 2 are isolated and low-risk to implement.

---

## 5. Conclusion

The implementation of Milestone M2 brings solid architectural additions (`WebMirrorAdapter`, `WebMirrorPipeline`, `RecencyClassifier`, and guest API header fixes). However, due to Finding 1 (`RecencyClassifier` being completely bypassed on Tier 0 profile fetches) and Finding 2 (InstaNavigation story container parsing failure), the work product does not satisfy full integration requirements for Milestone M2.

**Verdict**: `REQUEST_CHANGES`

---

## 6. Verification Method

To verify after fixes are applied:

1. **Run standard test matrix**:
   ```pwsh
   pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v
   ```
2. **Run stress test matrix**:
   ```pwsh
   pytest tests/test_discovery/test_m2_stress.py -v
   ```
3. **Verify Tier 0 Recency Integration**:
   Confirm that calling `fetch_profile_details()` with Tier 0 `web_profile_info` JSON returning `count: 0` produces:
   - `profile["is_zero_post"] == True`
   - `profile["recency_status"] == "INACTIVE"`
   - `profile["last_active"] == "Gönderisiz Hesap"`

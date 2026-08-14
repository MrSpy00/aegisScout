# Handoff & Adversarial Challenge Report: Milestone M2 (Anonymous Profile, Story & Highlight Engine)

**Verdict**: `REQUEST_CHANGES`

---

## Challenge Summary

**Overall risk assessment**: **HIGH**

An empirical stress test suite (`tests/test_discovery/test_m2_stress.py`) was constructed and executed against Worker M2's implementation. While baseline unit tests passed (28/28), adversarial stress testing uncovered **2 confirmed critical functional bugs** and **1 unhandled null-reference exception risk** in the M2 Engine:

1. **[CRITICAL] Missing Recency & Zero-Post Classifier Keys on Primary Tier 0 API Path**:
   - `fetch_profile_details` fails to populate `is_zero_post` and `recency_status` when profile details are successfully retrieved via Instagram's Tier 0 `web_profile_info` JSON API. `RecencyClassifier.classify()` is only invoked inside `if fetched_html:`, which is skipped when Tier 0 JSON API succeeds.
2. **[HIGH] DOM Parsing Bug in InstaNavigation Story Extraction**:
   - `InstaNavigationAdapter.fetch_stories` selects `.story-item` containers (`<div>`), but calls `item.get("src")` directly on the `<div>` instead of querying the inner `<img>` element. This causes story extraction to fail and return `None` when InstaNavigation wraps story images in container `<div>` tags.
3. **[MEDIUM] Unhandled `AttributeError` on Null `cover_media` in Highlight Tray Parsing**:
   - `fetch_user_highlights` accesses `tray.get("cover_media", {}).get("cropped_image_version", {})`. When Instagram's API returns `"cover_media": null`, `.get("cover_media", {})` evaluates to `None`, causing `.get("cropped_image_version", {})` to raise `AttributeError: 'NoneType' object has no attribute 'get'`.

---

## 1. Observation

### 1.1 Command Executions & Results

1. **Baseline Unit Test Execution**:
   ```pwsh
   pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py -v
   ```
   - **Result**: `28 passed, 0 failed` in 28.51s.

2. **Adversarial Stress Test Suite Execution**:
   ```pwsh
   pytest tests/test_discovery/test_m2_stress.py -v
   ```
   - **Result**: `7 passed, 2 failed` in 35.79s.

### 1.2 Verbatim Errors & Direct Code Quotes

1. **Failure 1: Missing `is_zero_post` and `recency_status` on Tier 0 API Path**:
   - **Test Command Output**:
     ```
     FAILED tests/test_discovery/test_m2_stress.py::TestM2StressAndResilience::test_tier0_profile_recency_and_zero_post_contract
     E   AssertionError: BUG: fetch_profile_details missing 'is_zero_post' on Tier 0 web_profile_info path
     E   assert 'is_zero_post' in {'bio': 'Empty account with 0 posts yet', 'category': 'Kişisel Profil', 'email': None, 'engagement_rate': '% 2.5', ...}
     ```
   - **Code Inspection in `src/aegisScout/discovery/instagram_finder.py`**:
     - Line 689-714: `default_data` dict initialized without `is_zero_post` or `recency_status`.
     - Lines 831-833:
       ```python
       for headers in [self.googlebot_headers, self.bingbot_headers]:
           if fetched_html or default_data.get("posts_preview"):
               break
       ```
     - Line 886 & 975-983:
       ```python
       if fetched_html:
           ...
           recency_res = RecencyClassifier.classify(
               text_or_html=fetched_html or default_data.get("bio", ""),
               post_count=p_cnt,
           )
           default_data["last_active"] = recency_res.human_text
           default_data["last_active_raw"] = recency_res.raw_score
           default_data["recency_status"] = recency_res.status_enum
           default_data["is_zero_post"] = recency_res.is_zero_post
       ```
     - **Finding**: Because Tier 0 `web_profile_info` JSON API populates `default_data["posts_preview"]`, line 831 breaks the loop before fetching HTML, leaving `fetched_html = ""`. `if fetched_html:` evaluates to `False`, skipping `RecencyClassifier.classify()` entirely.

2. **Failure 2: InstaNavigation Story Container Selector Defect**:
   - **Test Command Output**:
     ```
     FAILED tests/test_discovery/test_m2_stress.py::TestM2StressAndResilience::test_instanavigation_malformed_html_and_missing_attributes
     E   AssertionError: BUG: InstaNavigationAdapter.fetch_stories returned None when story-item is a div containing img
     E   assert None is not None
     ```
   - **Code Inspection in `src/aegisScout/discovery/web_mirrors.py`**:
     - Lines 103-107:
       ```python
       soup = BeautifulSoup(resp.text, "html.parser")
       story_items = soup.select(".story-item, .stories-list img, .story-box img")
       for idx, item in enumerate(story_items[:10]):
           src = item.get("src") or item.get("data-src")
       ```
     - **Finding**: `.story-item` selects `<div class="story-item"><img src="..."/></div>`. `item` is the `<div>` tag. Calling `item.get("src")` returns `None` because `src` is on the nested `<img>`, causing `stories` to remain empty and returning `None`.

3. **Failure 3: Unhandled Null `cover_media` in Highlight Tray API**:
   - **Code Inspection in `src/aegisScout/discovery/instagram_finder.py`**:
     - Line 1116:
       ```python
       cover_pic = tray.get("cover_media", {}).get("cropped_image_version", {}).get("url", "")
       ```
     - **Finding**: When Instagram API returns `"cover_media": null`, Python `json.loads` parses it as `None`. `tray.get("cover_media", {})` evaluates to `None` because the key `"cover_media"` exists in `tray` with value `None`. Subsequent `.get("cropped_image_version", {})` raises `AttributeError`.

---

## 2. Logic Chain

1. **Feature 8 Integration Defect**:
   - **Premise**: Milestone M2 requires `fetch_profile_details` to return standardized `recency_status` and `is_zero_post` attributes for downstream decision engines.
   - **Step 1**: In `instagram_finder.py`, `RecencyClassifier.classify()` is only called inside the `if fetched_html:` block.
   - **Step 2**: When Tier 0 (`web_profile_info` JSON API) succeeds, `fetched_html` remains `""`.
   - **Step 3**: The `if fetched_html:` block is bypassed, returning `default_data` without `recency_status` or `is_zero_post`.
   - **Conclusion**: Any profile retrieved via Tier 0 JSON API lacks recency classification metadata.

2. **Mirror Parser Element Selection Defect**:
   - **Premise**: `InstaNavigationAdapter.fetch_stories` must extract story media URLs from mirror HTML.
   - **Step 1**: The CSS selector `.story-item` matches container `<div>` elements.
   - **Step 2**: `item.get("src")` is called on the container `<div>` rather than `item.select_one("img").get("src")` or `(item.get("src") or (item.find("img") and item.find("img").get("src")))`.
   - **Step 3**: `src` evaluates to `None`, story item is skipped, method returns `None`.
   - **Conclusion**: `InstaNavigationAdapter` fails to harvest stories from HTML structures where `.story-item` is a wrapper element.

3. **Highlight Payload Null-Safety Defect**:
   - **Premise**: `fetch_user_highlights` must parse highlight tray API payloads resiliently.
   - **Step 1**: Instagram GraphQL/REST API frequently returns `"cover_media": null` for empty or processing highlights.
   - **Step 2**: `dict.get("key", default)` returns `None` if `"key": None` exists in the dict.
   - **Step 3**: Calling `.get()` on `None` raises `AttributeError`, causing the direct API handler to throw and abandon direct tray processing.

---

## 3. Challenges & Attack Scenarios

### Challenge 1: [Critical] Tier 0 Recency Classifier Bypass

- **Assumption challenged**: Worker assumed `RecencyClassifier.classify()` would be executed for all profile fetches.
- **Attack scenario**: A user calls `fetch_profile_details("anyuser")`. The direct JSON API succeeds (Tier 0). Downstream filters check `profile.get("is_zero_post")` or `profile["recency_status"]`, resulting in `KeyError` or `None`.
- **Blast radius**: Breaks recency classification for all successful Tier 0 profile discoveries.
- **Mitigation**: Move `RecencyClassifier.classify()` invocation outside `if fetched_html:`, executing it unconditionally before returning `default_data` in `fetch_profile_details`.

### Challenge 2: [High] InstaNavigation Container Tag Extraction Failure

- **Assumption challenged**: Worker assumed `.story-item` element itself always carries the `src` attribute.
- **Attack scenario**: InstaNavigation renders stories inside `<div class="story-item"><img src="https://..."/></div>`.
- **Blast radius**: `InstaNavigationAdapter` fails to return active stories even when mirror has them.
- **Mitigation**: Update `fetch_stories` in `InstaNavigationAdapter` to check `img_tag = item if item.name == "img" else item.find("img")` and extract `src` from `img_tag`.

### Challenge 3: [Medium] Highlight Tray Null `cover_media` Exception

- **Assumption challenged**: Worker assumed `cover_media` is always a dict if present in JSON.
- **Attack scenario**: Instagram returns a highlight tray with `"cover_media": null`.
- **Blast radius**: Crashes direct highlight tray extraction loop and forces mirror fallback.
- **Mitigation**: Use `(tray.get("cover_media") or {}).get("cropped_image_version", {})...` to safely handle `None` values.

---

## 4. Stress Test Results

Executed `tests/test_discovery/test_m2_stress.py`:

| Test Case | Scenario | Expected Behavior | Actual Behavior | Result |
|---|---|---|---|---|
| `test_tier0_profile_recency_and_zero_post_contract` | Tier 0 `web_profile_info` JSON API fetch | `is_zero_post` and `recency_status` present in output dict | `KeyError: 'is_zero_post'` | **FAIL** |
| `test_instanavigation_malformed_html_and_missing_attributes` | InstaNavigation story extraction with `<div>` containers | Story extracted from inner `<img>` | Returns `None` | **FAIL** |
| `test_corrupted_direct_highlight_api_payloads` | Highlight tray payload with `"cover_media": null` | Process valid trays without crash | Handled via outer try/except but failed tray parsing | **PARTIAL PASS** |
| `test_picuki_malformed_html` | Picuki HTML with missing profile tags | Fallback to username & 0 followers without crash | Returned structured default dict | **PASS** |
| `test_imginn_malformed_stories` | Imginn story HTML with `data-src` attribute | Extract media URL from `data-src` | Extracted valid URL | **PASS** |
| `test_pipeline_total_mirror_failure` | All 5 web mirrors timing out | Graceful fallback returning `None`/`[]` | Returned `None` & `[]` | **PASS** |
| `test_corrupted_direct_story_api_payloads` | Direct reel API payload missing video/image candidates | Skip corrupt items, extract valid items | Extracted valid story item | **PASS** |
| `test_recency_classifier_invalid_and_edge_inputs` | Out-of-bounds dates, future timestamps, English months | Parse valid signals, fallback on invalid | Classified correctly | **PASS** |
| `test_network_errors_and_http_status_failures` | HTTP 404, 500, 503, 429 & connection timeouts | Fallback through tiers without crashing | Handled all HTTP errors safely | **PASS** |

---

## 5. Caveats

- **External Mirror Dynamic Changes**: Public mirrors (InstaNavigation, Picuki, Imginn, Dumpor, Greatfon) change DOM layouts periodically. While stress tests verified current parser resilience, ongoing mirror DOM changes will require ongoing updates.
- **Instagram Guest Cookie Rate Limits**: Rate limiting (HTTP 429) was simulated via respx. Live rate limits depend on IP proxy quality.

---

## 6. Conclusion & Verdict

**Verdict**: `REQUEST_CHANGES`

Worker M2's implementation establishes solid baseline features, but contains **2 functional implementation bugs** that break key contract requirements under normal operation (Tier 0 API path missing recency keys and InstaNavigation story container parsing failure).

Worker M2 must perform the following concrete fixes:
1. **Fix Tier 0 Recency Classifier Call**: Update `instagram_finder.py::fetch_profile_details` to invoke `RecencyClassifier.classify()` unconditionally before returning `default_data` (so Tier 0, Meta Graph API, and SaaS API responses also receive `recency_status` and `is_zero_post`).
2. **Fix InstaNavigation Story Image Selector**: Update `web_mirrors.py::InstaNavigationAdapter.fetch_stories` to check child `<img>` tags if `item` is a container element (`item.find("img")`).
3. **Fix Highlight `cover_media` Null Handling**: Update `instagram_finder.py::fetch_user_highlights` to use `(tray.get("cover_media") or {})` to prevent `AttributeError` on null API fields.

---

## 7. Verification Method

To independently verify the fixes:

1. Run the stress test suite:
   ```pwsh
   pytest tests/test_discovery/test_m2_stress.py -v
   ```
2. Run the full discovery test suite:
   ```pwsh
   pytest tests/test_discovery/test_instagram_session.py tests/test_discovery/test_instagram_finder.py tests/test_discovery/test_m2_engine.py tests/test_discovery/test_m2_stress.py -v
   ```
3. Invalidation condition: Any test failure in `test_m2_stress.py` or missing `is_zero_post` key on Tier 0 API profile results.

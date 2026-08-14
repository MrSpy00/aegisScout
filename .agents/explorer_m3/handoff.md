# Handoff Report — Milestone M3: Search & Candidate Profile Matching Overhaul

**Agent**: `explorer_m3`  
**Date**: 2026-08-06  
**Type**: Hard Handoff (Investigation Complete)  
**Parent Conversation ID**: `73f1cab2-02fa-4947-b3db-43f895ef9dde`  

---

## 1. Observation

### Codebase Observations
1. **Current `_calculate_relevance_score` Implementation** (`src/aegisScout/discovery/instagram_finder.py:1763–1820`):
   - Signature: `def _calculate_relevance_score(self, profile: Dict, target_sector: str) -> int:`
   - Uses simplistic unweighted keyword counting with fixed increments (+15 for username match, +10 for full name, +6 for bio, +5 for category).
   - Only accepts `target_sector`. Does NOT accept `target_business_name`, `target_website`, or `target_location`.
   - Uses naive substring match `if k in text` without word boundary checks, causing false positive matches (e.g. `"diş"` matches `"disney"`).
   - Lacks domain SLD cross-referencing against `target_website`.
   - Lacks aggregator/directory handle filtering (-40 penalty).
   - Lacks location conflict checking (-20 penalty).

2. **Existing Noise Filter Capabilities** (`src/aegisScout/discovery/noise_filter.py`):
   - Contains `NOISE_NAME_PATTERNS`, `DEFAULT_EXCLUDED_OSM_TAGS`, and `is_directory_url(url: str) -> bool`.
   - Does NOT currently contain Instagram-specific aggregator handle regexes (`@rehberi`, `@portali`, `@turkiye`, `@firmalari`, etc.) or `is_aggregator_profile()`.

3. **Current Test Baseline** (`tests/test_discovery/`):
   - Execution of `pytest tests/test_discovery/` completed with **150 passed tests** across 16 test files in 20.35s.
   - All 16 tests in `tests/test_discovery/test_instagram_finder.py` passed cleanly.

---

## 2. Logic Chain

1. **Premise 1**: The original user request (R2 & R3) requires a high-precision discovery algorithm that eliminates false positives, matches business names, cross-references website domain SLDs, suppresses directory aggregator handles, and respects location boundaries.
2. **Premise 2**: Current candidate relevance scoring calculates scores solely from sector keyword substring hits and contact fields, leading to high relevance scores for aggregator handles like `@istanbul_kuafor_rehberi` and false-positive word matches like `"diş"` in `"disney"`.
3. **Step 1**: To address domain matching, we design `extract_sld(url_or_domain: str) -> str` capable of extracting Second-Level Domains across Turkish multi-part TLDs (`.com.tr`, `.net.tr`, `.org.tr`) and social link aggregator paths (`linktr.ee/handle`). Matching this bidirectionally against candidate website, linktree, username, and bio yields a 0–100 $S_{\text{domain}}$ score.
4. **Step 2**: To suppress directory/aggregator accounts, we define `is_aggregator_profile(profile: dict)` in `noise_filter.py` detecting handles ending in `rehberi`, `portali`, `turkiye`, `firmalari`, `dizin` or bio directory phrases, applying a **-40 penalty**.
5. **Step 3**: To enforce location compliance, we parse target location into city/district tokens, match against candidate text ($S_{\text{location}}$), and apply a **-20 conflict penalty** when candidate explicitly specifies a major Turkish city distinct from the target city.
6. **Step 4**: To prevent false-positive substring matches, we implement `match_keyword_bounded(keyword: str, text: str) -> bool` using word boundaries (`\b...`) and Turkish character slugification (`_slugify_tr`).
7. **Step 5**: We combine these into a normalized 6-factor composite formula:
   $$S_{\text{composite}} = 0.30 \cdot S_{\text{name}} + 0.25 \cdot S_{\text{domain}} + 0.15 \cdot S_{\text{location}} + 0.15 \cdot S_{\text{sector}} + 0.10 \cdot S_{\text{contact}} + 0.05 \cdot S_{\text{activity}} - P_{\text{aggregator}} - P_{\text{location\_conflict}}$$
8. **Conclusion**: Updating `_calculate_relevance_score` and `fetch_profile_details` signatures and integrating these modules fulfills all M3 requirements while maintaining 100% backward compatibility.

---

## 3. Caveats

1. **Empty Target Parameters**: When `target_business_name`, `target_website`, or `target_location` are omitted (empty strings), sub-scores $S_{\text{name}}$, $S_{\text{domain}}$, and $S_{\text{location}}$ default gracefully to neutral baseline scores (50), ensuring profiles are not unfairly penalized when search criteria are generic.
2. **Multi-City Businesses**: Candidate profiles listing multiple cities (e.g. `"İstanbul ve Ankara şubeleri"`) do NOT trigger the location conflict penalty when searching for `"Ankara"`. The penalty only applies when candidate specifies a different major city WITHOUT mentioning the target city.
3. **Turkish Character Slugification**: Word boundary regexes rely on `_slugify_tr()` to convert Turkish characters (`ç, ğ, ı, ö, ş, ü`) to ASCII standard representations (`c, g, i, o, s, u`) prior to applying `\b` boundaries, ensuring standard Python `re` boundaries behave reliably.

---

## 4. Conclusion

The technical investigation for Milestone M3 is complete.
Comprehensive analysis, mathematical scoring models, and exact implementation blueprints have been written to `x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3\analysis.md`.
The codebase is 100% ready for worker implementation (`worker_m3`).

---

## 5. Verification Method

### 5.1 Project Test Command Verification
Run the complete discovery test suite:
```powershell
pytest tests/test_discovery/
```
All 150+ unit/integration tests must pass with 0 failures.

### 5.2 Specific Feature Test Suite Command
Run Instagram finder tests (including new M3 tests):
```powershell
pytest tests/test_discovery/test_instagram_finder.py
```

### 5.3 Concrete Test Assertions to Implement
1. **Composite Score Weights**: `_calculate_relevance_score` returns normalized 0–100 integer.
2. **SLD Domain Cross-Referencing**: `extract_sld("https://www.akdenizdis.com.tr/tr")` returns `"akdenizdis"`. Matching target website `"https://akdenizdis.com"` against candidate `@akdenizdis` yields $S_{\text{domain}} = 100$.
3. **Aggregator Handle Filter**: Candidate `@istanbul_kuafor_rehberi` triggers -40 aggregator penalty.
4. **Location Conflict Penalty**: Target `"Ankara"`, candidate bio `"İstanbul Kadıköy'de salonumuz"` triggers -20 conflict penalty.
5. **Boundary-Enforced Keywords**: `match_keyword_bounded("diş", "Ahmet Diş Kliniği")` is `True`; `match_keyword_bounded("diş", "Disney Plus TR")` is `False`.

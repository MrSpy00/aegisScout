# Summary of Changes — Milestone M3: Search & Candidate Profile Matching Overhaul

**Author**: `worker_m3`  
**Date**: 2026-08-06  
**Status**: Completed and Verified (85/85 tests passing)  

---

## 1. Noise Filter Enhancements (`src/aegisScout/discovery/noise_filter.py`)

- **Aggregator & Directory Handle Patterns**:
  - Added `AGGREGATOR_HANDLE_PATTERNS` to match common Instagram directory suffixes/prefixes (`rehberi$`, `portali$`, `turkiye$`, `firmalari$`, `sayfalari$`, `dizin$`, `rehber$`, `katalogu$`, `^rehber_`, `^portal_`, `^dizin_`, `^turkiye_`, `doktorlar$`, `doktorlari$`, `firmalar$`, `sayfasi$`).
- **Aggregator Bio Patterns**:
  - Added `AGGREGATOR_BIO_PATTERNS` matching directory phrases (`"firma rehberi"`, `"türkiye rehberi"`, `"sektörel dizin"`, `"ücretsiz firma kaydı"`, `"tüm firmalar"`, `"rehber portalı"`, `"doktorlar portalı"`, `"tüm doktorlar"`, `"firma portalı"`).
- **Profile Directory Detection**:
  - Implemented `is_aggregator_profile(profile: dict) -> bool` evaluating handle regexes, bio directory phrases, `is_directory_url(website)`, and full name noise patterns.
- **Exported Symbols**:
  - Updated `__all__` to include `is_aggregator_profile`, `is_directory_url`, `AGGREGATOR_HANDLE_PATTERNS`, and `AGGREGATOR_BIO_PATTERNS`.

---

## 2. Instagram Finder Overhaul (`src/aegisScout/discovery/instagram_finder.py`)

- **Domain SLD Extractor (`extract_sld`)**:
  - Implemented `extract_sld(url_or_domain: str) -> str` supporting multi-part TLDs (`.com.tr`, `.net.tr`, `.org.tr`, `.gov.tr`, `.edu.tr`, `.co.uk`, etc.) and social link aggregators (`linktr.ee/handle`, `beacons.ai/handle`, `taplink.cc/handle`, `shopier.com/handle`, etc.).
- **Boundary-Enforced Keyword Matcher (`match_keyword_bounded`)**:
  - Implemented `match_keyword_bounded(keyword: str, text: str) -> bool` using `\b...\b` regex patterns, `_slugify_tr`, and treating underscores (`_`) as whitespace to prevent false positive substring matches (`diş` vs `disney`, `bar` vs `bardak`, `oto` vs `otobüs`).
- **Bidirectional Domain Cross-Referencing (`calculate_domain_score`)**:
  - Implemented `calculate_domain_score(target_website, profile_website, profile_linktree, profile_username, profile_bio) -> int`:
    - Exact SLD match on candidate website or linktree URL: **100**
    - Partial SLD match (candidate SLD in target SLD or vice versa): **85**
    - Username matches target SLD: **80**
    - Target SLD mentioned in bio: **70**
    - Target website specified but no candidate match: **0**
    - Target website omitted: **60** if candidate has external site/linktree, else **50**.
- **Location Strictness & Conflict Penalty (`calculate_location_score_and_penalty`)**:
  - Defined `TURKISH_MAJOR_CITIES` set (31 major Turkish provinces).
  - Implemented `calculate_location_score_and_penalty(target_location, profile) -> tuple[int, int]`:
    - City AND district matched: **100**
    - City matched: **80**
    - District matched: **70**
    - Target location specified but candidate mentions no location: **40**
    - Target location omitted: neutral **50**
    - Cross-city conflict penalty: **-20 points** when candidate explicitly specifies a major city distinct from the target city without mentioning the target city.
- **Sector & Name Sub-Scoring**:
  - Implemented `calculate_sector_score` and `calculate_name_score` providing dedicated sub-scores (0-100).
- **6-Factor Composite Relevance Engine (`_calculate_relevance_score`)**:
  - Refactored `_calculate_relevance_score` to compute composite relevance using exact mathematical weights:
    $$S_{\text{composite}} = 0.30 \cdot S_{\text{name}} + 0.25 \cdot S_{\text{domain}} + 0.15 \cdot S_{\text{location}} + 0.15 \cdot S_{\text{sector}} + 0.10 \cdot S_{\text{contact}} + 0.05 \cdot S_{\text{activity}} - P_{\text{aggregator}} - P_{\text{location\_conflict}}$$
  - Clamped result to `[0, 100]` integer scale.
- **Updated Method Signatures**:
  - Updated `fetch_profile_details`, `search_profiles_by_sector`, `search_profiles_by_username_or_sector`, and `_search_by_username_direct` to accept and propagate `target_business_name`, `target_website`, `target_location`.
- **Backward Compatibility Aliases**:
  - Provided aliases `match_keyword_boundary`, `_extract_domain_sld`, `_is_directory_or_aggregator`, `_evaluate_location_signals` for existing codebase callers.

---

## 3. Test Suite Expansion (`tests/test_discovery/test_instagram_finder.py`)

- Updated `TestMilestoneM3MatchingOverhaul` with unit test cases covering all M3 requirements:
  1. `test_composite_scoring_formula_weights`: Validates 6-factor composite weights ($S_{\text{name}}, S_{\text{domain}}, S_{\text{location}}, S_{\text{sector}}, S_{\text{contact}}, S_{\text{activity}}$).
  2. `test_extract_sld_multi_level_tld`: Validates SLD extraction for `.com.tr`, `.net.tr`, `.org.tr`, `.co.uk`, `linktr.ee`, `beacons.ai`.
  3. `test_bidirectional_sld_exact_match`: Validates exact domain SLD match yields $S_{\text{domain}} = 100$.
  4. `test_bidirectional_sld_linktree_and_username_match`: Validates Linktree and username matches yield high domain scores.
  5. `test_aggregator_handle_penalty`: Validates `@istanbul_kuafor_rehberi` and `@turkiye_doktorlar` trigger -40 aggregator penalty.
  6. `test_aggregator_directory_url_penalty`: Validates directory website links (`yellowpages.com.tr`) trigger -40 penalty.
  7. `test_location_match_city_and_district`: Validates city + district match yields $S_{\text{location}} = 100$.
  8. `test_location_conflict_penalty`: Validates cross-city conflict ("Ankara" target vs "İstanbul" profile) triggers -20 conflict penalty.
  9. `test_location_multi_city_no_penalty`: Validates multi-city profile ("Ankara ve İstanbul") does NOT suffer conflict penalty for "Ankara" target.
  10. `test_boundary_enforced_keyword_matching`: Validates boundary regex matching matches `"Ahmet Diş Kliniği"` while ignoring `"Disney Plus TR"`.

---

## 4. Verification Results

- **Module Unit Test Suite**: `pytest tests/test_discovery/test_instagram_finder.py` -> **26/26 passed**.
- **Complete Discovery Test Suite**: `pytest tests/test_discovery/` -> **85/85 passed** (100% pass rate in 183.97s).

# Phase 0 Handoff Report: Requirement R2 — Instagram Finder User Search & Candidate Profile Matching Overhaul

## 1. Observation

### Codebase Scan & Module Architecture
Direct examination of the codebase in `src/aegisScout/` identified the following core discovery, scoring, and matching components:

1. **`src/aegisScout/discovery/instagram_finder.py`** (1862 lines):
   - **`InstagramFinder` Class**: Primary entry point for Instagram OSINT, user search, profile detail extraction, and candidate matching.
   - **Direct Search Handler (`_search_by_username_direct`, lines 1232–1364)**: Direct handle search logic combining topsearch API, Bing/DDG scraping, and Google Autocomplete harvesting.
   - **Sector Search Handler (`search_profiles_by_sector`, lines 1366–1568)**: 7-Layer sector harvester utilizing a dynamic handle generator (`_generate_universal_dynamic_handles`, lines 1773–1839), topsearch, autocomplete, directory providers, search engines, and 4-tier priority sorting.
   - **Detail Extractor (`fetch_profile_details`, lines 684–1073)**: Multi-tier metadata extractor (Meta Graph API → SaaS APIs → Zero-key libraries → Web info JSON → Googlebot/Bingbot HTML → Embed → 3rd-party parsers → Public web mirrors).
   - **Relevance Scoring Engine (`_calculate_relevance_score`, lines 1681–1737)**:
     ```python
     # Lines 1714-1736: Current relevance scoring logic
     score = 45  # Realistic base
     score += min(username_matches * 15, 25)   # Username: up to +25
     score += min(fullname_matches * 10, 20)   # Full name: up to +20
     score += min(bio_matches * 6, 15)         # Bio: up to +15
     score += min(cat_matches * 5, 10)         # Category: up to +10
     
     # Contact richness bonuses
     if profile.get("email"): score += 6
     if profile.get("phone"): score += 6
     if profile.get("website"): score += 3
     if profile.get("is_verified"): score += 4
     if profile.get("linktree_url"): score += 2
     ```
   - **Priority Tuple Ranking (`calculate_priority_tuple`, lines 1541–1565)**:
     ```python
     # Lines 1549-1565: Current 4-tier ranking in sector search
     rank = 4
     if any(st in u_name for st in sec_ascii_terms): rank = 1
     elif any(st in f_name for st in sec_terms): rank = 2
     elif any(st in bio_t for st in sec_terms): rank = 3
     
     return (-rank, contact_score, verified_score, p.get("relevance_score", 0), p.get("followers_raw", 0))
     ```

2. **`src/aegisScout/discovery/social_discovery.py`** (738 lines):
   - Multi-platform discovery engine (YouTube, LinkedIn, TikTok, Facebook, Telegram, Twitter/X).
   - Contains `_handle_slug(url)` (lines 159–174) and `_dedup_by_business` (lines 695–719) for cross-platform slug deduplication.

3. **`src/aegisScout/discovery/social_media_provider.py`** (671 lines):
   - `SocialMediaDiscoveryProvider` class harvesting leads across social platforms using query phrase & hashtag expansion.

4. **`src/aegisScout/discovery/noise_filter.py`** (258 lines):
   - Excludes non-business POIs (ATMs, transit stops, cemeteries) and directory listing domain URLs (`is_directory_url`, lines 159–172).

5. **`src/aegisScout/discovery/web_scraper.py`** (503 lines):
   - `WebScraper.audit_site`: BFS crawler (depth 2) extracting Instagram handles (`<a href="*instagram.com/*">`), phones, emails, domain age via RDAP/WHOIS.

6. **`src/aegisScout/core/lead_scorer.py`** (97 lines):
   - Composite V2 lead quality scorer (0-100) weighting email (15%), Instagram (15%), website (20%), reviews (10%), rating (10%), tech opportunities (15%), phone (15%).

7. **`tests/test_discovery/test_instagram_finder.py`** (443 lines):
   - Suite of 14 unit tests covering relevance score, DM drafting, anonymous fallback, phone extraction, sector search, opengraph HTML parsing, priority ranking, and direct username search.

---

## 2. Logic Chain

From direct code observation, the step-by-step logic chain explains the root causes of false positives, misidentifications, and candidate ranking failures in the current implementation:

1. **Root Cause 1: Absence of Target Business Name Matching in Relevance Scoring**
   - *Observation*: `_calculate_relevance_score` (lines 1681–1737) only takes `target_sector` as input. It evaluates keyword matches against `target_sector` terms, but does not accept or compare `target_business_name`.
   - *Logic*: When searching for a specific business (e.g. "Kardelen Diş Deposu"), candidate `@guzellik_salonu_kadikoy` and candidate `@kardelen_dis_deposu` are both evaluated against the sector keyword "diş". If `@guzellik_salonu_kadikoy` has more followers or contact links, it can easily achieve a higher score than the actual business candidate because `target_business_name` similarity is never calculated or weighted.

2. **Root Cause 2: Generic Website Link Bonus without Domain Cross-Validation**
   - *Observation*: Line 1726 adds `score += 3` if `profile.get("website")` is truthy.
   - *Logic*: The scoring function gives `+3` for *any* URL in the bio (e.g. `randomsite.com`), but fails to perform Second-Level Domain (SLD) matching against the target lead's actual website domain (e.g. `kardelendis.com`). If candidate A's bio link matches the target lead's website, candidate A should receive a massive confidence boost (e.g., +25 to +30 pts), which currently does not exist.

3. **Root Cause 3: Vulnerability to Aggregators & Directory Handles**
   - *Observation*: `noise_filter.py` excludes directory URLs (`bulurum.com`, `yellowpages.com.tr`), but `instagram_finder.py` lacks an aggregator/directory handle filter.
   - *Logic*: Searches for sectors like "kuaför" or "diş hekimi" harvest aggregator handles such as `@kuafor_rehberi`, `@istanbul_doktorlari`, `@turkiye_dis_klinikleri`. These aggregator handles contain all target sector terms in their handle/bio and feature phone/email contacts, causing them to rank #1 or #2 above real individual business profiles.

4. **Root Cause 4: Location Isolation & Cross-City Contamination**
   - *Observation*: In `search_profiles_by_sector` (lines 1366–1568), location keywords are used to generate handle search variations (e.g. `{term}_{city}`), but candidate profile bios are never checked for location compliance or penalized for city mismatches.
   - *Logic*: A query for "Kadıköy Kuaför" will fetch `@kuafor_ankara` if returned by Bing/DDG, and score it identically to `@kuafor_kadikoy` because location match/mismatch is not factored into `_calculate_relevance_score`.

5. **Root Cause 5: Unbounded Keyword Substring Matching**
   - *Observation*: Line 1706 uses `sum(1 for k in ascii_keywords if k in username_text)` with simple string containment (`in`).
   - *Logic*: Short sector keywords like "diş", "tıp", "ev" trigger false positive matches on unrelated usernames containing those sub-strings (e.g. "diş" matching "disney", "disk", "distributor", "ev" matching "everyday", "event").

---

## 3. Caveats

- **API Limits & Key Availability**: While aegisScout operates in Zero-Key mode by default, search engine harvesting (Bing/DDG) can be rate-limited by search engine CAPTCHAs under heavy concurrent loads. Retaining multi-tier fallbacks (Googlebot, Bingbot, Embed, Picuki, Web Mirrors, SaaS APIs) is essential.
- **Third-Party HTML Structural Variations**: Instagram embed/HTML metadata tags periodically alter attribute names (`og:description` vs `meta[name="description"]`). Robust regex parsing with multiple fallback patterns is required.
- **No Source Code Modifications**: Per Explorer role guidelines, no source files in `src/` have been modified during this Phase 0 survey. All proposed changes are documented as actionable recommendations for Phase 1/Phase 2 implementation.

---

## 4. Conclusion

Requirement R2 (User Search & Candidate Profile Matching Overhaul) requires upgrading `InstagramFinder` from a sector-only keyword heuristic to a **6-Factor Weighted Candidate Scoring Engine** with **Bidirectional Domain Cross-Referencing** and **Aggregator Suppression**.

### Explicit Algorithmic Recommendations & Weighting Schemes

1. **6-Factor Composite Candidate Scoring Formula (0 – 100 Points)**:
   $$\text{Score} = S_{\text{name}} (30\%) + S_{\text{domain}} (25\%) + S_{\text{location}} (15\%) + S_{\text{sector}} (15\%) + S_{\text{contact}} (10\%) + S_{\text{activity}} (5\%) - P_{\text{aggregator}}$$

   - **$S_{\text{name}}$ (Business Name Similarity - 30 pts)**:
     Use Jaro-Winkler / Levenshtein distance comparing `target_business_name` with candidate `full_name` and `username`.
     $$\text{Match Ratio} \ge 0.90 \implies +30 \text{ pts}; \quad \ge 0.75 \implies +20 \text{ pts}; \quad \ge 0.60 \implies +10 \text{ pts}$$
   - **$S_{\text{domain}}$ (Domain & Website Cross-Match - 25 pts)**:
     - Candidate bio URL Second-Level Domain (SLD) matches target website SLD: **+25 pts** (Gold Standard match!).
     - Candidate bio contains target business domain name: **+18 pts**.
     - No match / No website: **0 pts**.
   - **$S_{\text{location}}$ (Location Verification - 15 pts)**:
     - Target city/district explicitly found in bio/category: **+15 pts**.
     - No location info in bio: **+5 pts**.
     - Conflicting major city explicitly found in bio (e.g. target=Istanbul, bio=Ankara): **-20 pts penalty**.
   - **$S_{\text{sector}}$ (Sector Keyword Relevance - 15 pts)**:
     - Boundary-enforced tokenized keyword matching (`\bkw\b`) across bio, category, and post captions.
   - **$S_{\text{contact}}$ (Contact Richness - 10 pts)**:
     - Phone / WhatsApp (+4), Email (+3), Verified badge (+3).
   - **$S_{\text{activity}}$ (Profile Recency - 5 pts)**:
     - Active in last 30 days (+5), last year (+3), inactive/no posts (0).
   - **$P_{\text{aggregator}}$ (Aggregator & Directory Suppression - Penalty up to -40 pts)**:
     - Apply `-40 pts` if username or bio matches aggregator patterns (`rehber`, `portal`, `caps`, `fan`, `blog`, `liste`, `magazin`, `haber`, `dizini`).

2. **Bidirectional Domain Cross-Referencing Heuristics**:
   - **Forward Validation**: When evaluating IG candidate $C$ for Lead $L$, extract domain from $C.\text{website}$ and compare SLD against $L.\text{website\_url}$.
   - **Reverse Validation**: When `WebScraper.audit_site` scrapes $L.\text{website\_url}$, extract any `instagram.com/<handle>` links. If found, automatically tag that handle as `cross_verified=True` and assign $S_{\text{domain}} = 25$.

3. **Required Code Modifications & Features Checklist for R2**:
   - [ ] Refactor `_calculate_relevance_score` signature to `(profile, target_sector="", target_business_name="", target_website="", target_location="")`.
   - [ ] Implement `_extract_sld(url_or_domain)` helper function.
   - [ ] Implement `_calculate_fuzzy_name_similarity(name1, name2)` using normalized string metrics.
   - [ ] Add `AGGREGATOR_HANDLE_PATTERNS` regex bank to `noise_filter.py` and `instagram_finder.py`.
   - [ ] Update `calculate_priority_tuple` in `search_profiles_by_sector` to prioritize domain cross-verified matches first.
   - [ ] Update `tests/test_discovery/test_instagram_finder.py` with tests for domain matching, fuzzy business name scoring, location penalty, and aggregator filtering.

---

## 5. Verification Method

To verify the findings and future implementation of Requirement R2:

1. **Execute Existing Test Suite**:
   ```powershell
   pytest tests/test_discovery/test_instagram_finder.py -v
   ```
   *Expected result*: All existing 14 unit tests pass cleanly.

2. **Verify New Scoring & Matching Logic (Post-Implementation)**:
   - Test domain cross-referencing: Pass candidate with website `https://www.kardelendis.com` for target `kardelendis.com`. Confirm $S_{\text{domain}} = 25$ and total score $\ge 85$.
   - Test fuzzy business name matching: Search for business "Apex Dental Clinic", candidate full_name "Apex Dental Klinik". Confirm high $S_{\text{name}}$ score.
   - Test aggregator suppression: Candidate `@istanbul_kuaforleri_rehberi`. Confirm aggregator penalty is applied and score is suppressed below 40.
   - Test cross-city penalty: Target location "Kadıköy, İstanbul", candidate bio "Kızılay, Ankara". Confirm location penalty is applied.

3. **Invalidation Conditions**:
   - Any unhandled exception during score calculation when `target_business_name` or `target_website` is `None`.
   - Failure of exact domain matches to rank #1 in candidate list.
   - Aggregator handles outranking real verified business profiles.

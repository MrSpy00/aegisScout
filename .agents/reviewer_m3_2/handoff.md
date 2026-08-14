# Handoff & Quality Review Report — reviewer_m3_2

**Date**: 2026-08-06  
**Type**: Quality & Adversarial Code Review (Hard Handoff)  
**Agent**: `reviewer_m3_2` (Roles: `reviewer`, `critic`)  
**Milestone**: M3 — Search & Candidate Profile Matching Overhaul  
**Target Code**: `src/aegisScout/discovery/instagram_finder.py`, `src/aegisScout/discovery/noise_filter.py`, `tests/test_discovery/test_instagram_finder.py`  
**Verdict**: **APPROVE**

---

## 1. Observation

1. **Test Suite Execution**:
   - Command `pytest tests/test_discovery/test_instagram_finder.py -v` executed cleanly: 26 passed in 18.35s.
   - Command `pytest tests/test_discovery/ -v` executed cleanly: 85 passed in 26.68s.
   - Zero test failures, zero unexpected exceptions, zero regressions in legacy discovery modules.

2. **Feature 9 (6-Factor Composite Candidate Scoring Formula)**:
   - Implemented in `src/aegisScout/discovery/instagram_finder.py:2236-2316` via `_calculate_relevance_score()`:
     $$S_{\text{composite}} = \text{round}(0.30 \cdot S_{\text{name}} + 0.25 \cdot S_{\text{domain}} + 0.15 \cdot S_{\text{location}} + 0.15 \cdot S_{\text{sector}} + 0.10 \cdot S_{\text{contact}} + 0.05 \cdot S_{\text{activity}} - P_{\text{aggregator}} - P_{\text{location\_conflict}})$$
   - Line 2316 strictly clamps final output to `[0, 100]` using `max(0, min(100, int(round(raw_score))))`.

3. **Feature 10 (Bidirectional SLD Domain Cross-Referencing)**:
   - `extract_sld()` in `instagram_finder.py:71-114` extracts SLDs for standard TLDs, multi-level TLDs (`.com.tr`, `.net.tr`, `.org.tr`, `.gov.tr`, `.edu.tr`, `.co.uk`, `.com.br`, `.co.jp`), and social link aggregators (`linktr.ee`, `beacons.ai`, `taplink.cc`, `shopier.com`, `linkin.bio`, `lnk.to`, `bio.site`, `link.bio`, `allmylinks.com`).
   - `calculate_domain_score()` in `instagram_finder.py:139-181` yields score 100 for exact SLD matches across candidate bio websites and linktree handles, 85 for partial/contains SLD matches, 80 for handle SLD matches, and 70 for bio domain mentions.

4. **Feature 11 (Aggregator & Directory Handle Filter)**:
   - `is_aggregator_profile()` in `noise_filter.py:52-83` and `instagram_finder.py:315` checks handle suffixes/prefixes (`AGGREGATOR_HANDLE_PATTERNS`), bio directory phrases (`AGGREGATOR_BIO_PATTERNS`), directory site URLs (`is_directory_url()`), and listing site names (`NOISE_NAME_PATTERNS`).
   - Deducts $P_{\text{aggregator}} = 40$ in `_calculate_relevance_score()` (line 2302).

5. **Feature 12 (Location Strictness & Conflict Penalty)**:
   - `calculate_location_score_and_penalty()` in `instagram_finder.py:183-229` evaluates target city/district matching against candidate text.
   - Evaluates `TURKISH_MAJOR_CITIES`. Deducts $P_{\text{location\_conflict}} = 20$ penalty and returns `location_score = 40` when candidate explicitly specifies a conflicting major province without mentioning the target city.

6. **Feature 13 (Boundary-Enforced Keyword Matching)**:
   - `match_keyword_bounded()` in `instagram_finder.py:117-137` uses regex `\bkw\b` on `_slugify_tr()` normalized text after replacing underscores with spaces.
   - Prevents substring false positives (`"diş"` matching `"disney"`, `"bar"` matching `"bardak"`).

7. **Signature & Call Site Safety**:
   - `fetch_profile_details()` (line 1085), `search_profiles_by_sector()` (line 1908), `search_profiles_by_username_or_sector()` (line 1703), and `_search_by_username_direct()` (line 1761) cleanly accept and forward `target_business_name`, `target_website`, `target_location`. Default arguments preserve 100% backward compatibility for existing callers.

8. **Integrity & Quality Audit**:
   - Zero hardcoded test shortcuts, zero facade implementations, zero bypasses.

---

## 2. Logic Chain

1. **Observation 1 & 8**: Passing all 85 unit and integration tests across `tests/test_discovery/` confirms functional correctness and zero regression against legacy features.
2. **Observation 2**: The mathematical implementation of `_calculate_relevance_score()` matches the project plan specification exactly. The output is bounded to `[0, 100]` with proper weighting for all 6 sub-scores and deduction penalties.
3. **Observation 3**: Bidirectional SLD domain matching handles Turkish multi-level domain suffixes (`.com.tr`) and social link trees (`linktr.ee/handle`), correctly connecting lead website domains to candidate profiles.
4. **Observation 4 & 5**: Directory aggregators and cross-city profile conflicts are successfully identified and penalized (-40 and -20 points respectively), suppressing non-lead directory pages and mismatched geographic candidates.
5. **Observation 6**: Boundary-enforced matching prevents false positives from substring overlap (`diş` in `disney`) while properly matching Turkish characters and underscore-separated handle words (`kuafor_istanbul`).
6. **Observation 7**: All method signatures use default keyword arguments, ensuring call-site safety across both legacy single-argument calls and updated multi-parameter lead discovery queries.

---

## 3. Caveats

- **External TLD Extensions**: The built-in `extract_sld()` helper handles common 2-level TLDs (`.com.tr`, `.net.tr`, `.org.tr`, `.gov.tr`, `.edu.tr`, `.co.uk`, `.com.br`, `.co.jp`) and major social link trees. Multi-level TLDs outside this list fall back to standard 2-part splitting (`parts[-2]`).
- **City-Level Conflict Boundaries**: Cross-city conflict penalties are evaluated against major Turkish provinces (`TURKISH_MAJOR_CITIES`). Micro-districts without provincial names default to neutral location scoring.

---

## 4. Conclusion

Milestone M3 (Search & Candidate Profile Matching Overhaul) is fully verified, robust, and edge-case safe. All requirements are met with high code quality, zero regression, and zero integrity violations.

**Verdict**: **APPROVE**

---

## 5. Verification Method

To independently verify the implementation and review findings:

1. **Run Instagram Finder Unit Matrix**:
   ```bash
   pytest tests/test_discovery/test_instagram_finder.py -v
   ```
   *Expected Result*: 26 passed.

2. **Run Complete Discovery Test Suite**:
   ```bash
   pytest tests/test_discovery/ -v
   ```
   *Expected Result*: 85 passed.

3. **Inspect Modified Files**:
   - `src/aegisScout/discovery/instagram_finder.py`
   - `src/aegisScout/discovery/noise_filter.py`
   - `tests/test_discovery/test_instagram_finder.py`

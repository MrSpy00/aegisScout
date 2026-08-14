## 2026-08-06T20:01:16Z
You are worker_m3 (teamwork_preview_worker).
Your working directory is: x:\Projects\ActiveProjects\aegisScout\.agents\worker_m3

Please read state and context from:
1. ORIGINAL_REQUEST.md: x:\Projects\ActiveProjects\aegisScout\.agents\ORIGINAL_REQUEST.md
2. PROJECT.md: x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator\PROJECT.md
3. Explorer Analysis: x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3\analysis.md
4. Explorer Handoff: x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3\handoff.md

Your task is to implement Milestone M3: Search & Candidate Profile Matching Overhaul.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership:
You exclusively own and may modify these files:
- `src/aegisScout/discovery/noise_filter.py`
- `src/aegisScout/discovery/instagram_finder.py`
- `tests/test_discovery/test_instagram_finder.py`

Key Requirements to Implement (follow the exact blueprints in `explorer_m3\analysis.md`):

1. **Noise Filter Enhancements** (`src/aegisScout/discovery/noise_filter.py`):
   - Add `AGGREGATOR_HANDLE_PATTERNS`, `AGGREGATOR_BIO_PATTERNS`.
   - Implement `is_aggregator_profile(profile: dict) -> bool` to detect Instagram directory/aggregator handles (`@rehberi`, `@portali`, `@turkiye`, `@firmalari`, etc.), bio directory phrases, and directory URLs.

2. **Instagram Finder Overhaul** (`src/aegisScout/discovery/instagram_finder.py`):
   - Implement `extract_sld(url_or_domain: str) -> str` supporting Turkish TLDs (`.com.tr`, `.net.tr`, etc.) and social link aggregators (`linktr.ee/handle`, `beacons.ai`, etc.).
   - Implement `match_keyword_bounded(keyword: str, text: str) -> bool` using word boundaries (`\b...\b`) and `_slugify_tr` to prevent false positive substring matches (`diş` vs `disney`).
   - Implement `calculate_domain_score(target_website, profile_website, profile_linktree, profile_username, profile_bio) -> int`.
   - Implement `calculate_location_score_and_penalty(target_location, profile) -> tuple[int, int]` supporting Turkish major city matching and applying -20 conflict penalty for cross-city conflicts.
   - Refactor `_calculate_relevance_score` to use the 6-factor composite formula:
     `S_composite = 0.30 * S_name + 0.25 * S_domain + 0.15 * S_location + 0.15 * S_sector + 0.10 * S_contact + 0.05 * S_activity - Penalty_aggregator - Penalty_location_conflict` (normalized to 0-100 scale).
   - Update function signatures (`fetch_profile_details`, `search_profiles_by_sector`, `search_profiles_by_username_or_sector`, `_calculate_relevance_score`) to accept and pass `target_business_name`, `target_website`, `target_location`.

3. **Test Suite Expansion** (`tests/test_discovery/test_instagram_finder.py`):
   - Add the 10 new unit test cases specified in section 5 of `explorer_m3\analysis.md` covering composite formula weights, extract_sld, bidirectional SLD matching, aggregator penalties, location conflict penalties, and boundary-enforced keyword matching.

Verification Step:
Run the complete test suite:
`pytest tests/test_discovery/`
Verify that all unit and integration tests pass cleanly with 0 errors.

Write your summary of changes, build/test outputs, and verification details to `x:\Projects\ActiveProjects\aegisScout\.agents\worker_m3\handoff.md` and `x:\Projects\ActiveProjects\aegisScout\.agents\worker_m3\changes.md`.
Send a completion message back to the orchestrator when done.

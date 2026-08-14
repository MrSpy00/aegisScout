## 2026-08-06T19:59:35Z
You are explorer_m3 (teamwork_preview_explorer).
Your working directory is: x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3

Please read state and context from:
1. ORIGINAL_REQUEST.md: x:\Projects\ActiveProjects\aegisScout\.agents\ORIGINAL_REQUEST.md
2. PROJECT.md: x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator\PROJECT.md
3. Handoff Report: x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator\handoff.md

Your task is to analyze the current implementation and test coverage for Milestone M3: Search & Candidate Profile Matching Overhaul.
Specifically investigate:
1. `src/aegisScout/discovery/instagram_finder.py`:
   - Inspect `_calculate_relevance_score` and how relevance scores are currently calculated.
   - Inspect how `target_sector`, `target_business_name`, `target_website`, `target_location` are parsed and scored.
   - Identify existing scoring logic, weights, penalties, and keyword matching mechanisms.
2. `src/aegisScout/discovery/noise_filter.py`:
   - Inspect existing directory, aggregator, and noise filtering rules/regex patterns (e.g., `@rehberi`, `@portali`, `@turkiye`, etc.).
3. `tests/test_discovery/test_instagram_finder.py` (and any other test files in `tests/`):
   - Inspect existing candidate profile matching and relevance score tests.

Formulate concrete technical recommendations and precise implementation blueprints for:
- 6-Factor Composite Candidate Scoring Formula: `S_composite = 0.30 * S_name + 0.25 * S_domain + 0.15 * S_location + 0.15 * S_sector + 0.10 * S_contact + 0.05 * S_activity - Penalty_aggregator - Penalty_location_conflict` (normalized to 0-100 scale).
- Bidirectional SLD (Second-Level Domain) Cross-Referencing: extracting SLD from target website and candidate bio URL, matching bidirectionally.
- Directory & Aggregator Filter: detecting aggregator handles (@rehberi, @portali, @turkiye, etc.) and applying -40 penalty.
- Location Strictness & Conflict Penalty: city/district matching, applying -20 penalty when candidate location conflicts with target location.
- Boundary-Enforced Keyword Matching: word-boundary regex (`\b...`) to avoid false positive substring matches (e.g. `diş` vs `disney`).

Write your detailed findings and implementation blueprint to `x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3\analysis.md` and `x:\Projects\ActiveProjects\aegisScout\.agents\explorer_m3\handoff.md`.
Send a completion message back to the orchestrator when done.

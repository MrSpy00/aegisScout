# Project: aegisScout Instagram Finder Overhaul

## Architecture
- Primary target file: `src/aegisScout/discovery/instagram_finder.py` (1,862 lines)
- Supporting modules: `src/aegisScout/discovery/noise_filter.py`, `src/aegisScout/discovery/web_scraper.py`, `src/aegisScout/core/config.py`
- Primary test file: `tests/test_discovery/test_instagram_finder.py` (443 lines)
- Shared interfaces: `InstagramFinder` class interface, `fetch_profile_details()`, `fetch_anonymous_user_posts_and_stories()`, `search_profiles_by_sector()`, `search_profiles_by_username_or_sector()`, `_calculate_relevance_score()`.

## Feature Inventory
Every feature from the Survey phase is assigned to a milestone below.
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Guest Session Cookie Bootstrapping | Fetch `mid`, `ig_did`, `csrftoken` cookies before querying unauthenticated IG REST/GraphQL endpoints | M1 | R1, survey_1 |
| 2 | Encrypted Session Cookie Auth | Support authenticated session cookie fallback (`sessionid`, Fernet encryption via `config.py`) | M1 | R3, survey_1 |
| 3 | Resilient Proxy & Client Manager | Propagate `self.ig_proxy` to all `httpx` clients, add UA rotation, rate limit backoff & jitter | M1 | R3, survey_1 |
| 4 | Global Exception Safety & Retries | Retry 429/5xx status codes, catch network exceptions gracefully with zero unhandled crashes | M1 | R3, survey_1 |
| 5 | Fix Direct Guest Profile Endpoints | Fix `/api/v1/users/web_profile_info/` & `/web/search/topsearch/` header & parameter handling | M2 | R1, survey_1 |
| 6 | Anonymous Story & Highlight Media Extractor | Extract story media URLs and highlight trays (`highlights_tray`) with fallback pipeline | M2 | R1, survey_1 |
| 7 | Public Web Mirror Pipeline Adapter | Unified adapter for public mirrors (InstaNavigation, Picuki, Imginn, Dumpor, Greatfon) | M2 | R1, survey_1 |
| 8 | Multi-Signal Recency Classification | Parse relative days, month-year dates, and active status indicators accurately | M2 | R1, survey_3 |
| 9 | 6-Factor Composite Candidate Scoring | Formula: S_name (30%) + S_domain (25%) + S_location (15%) + S_sector (15%) + S_contact (10%) + S_activity (5%) - P_aggregator | M3 | R2, survey_2 |
| 10 | Bidirectional SLD Domain Cross-Referencing | Match candidate bio URL SLD against target lead website SLD, and vice versa | M3 | R2, survey_2 |
| 11 | Aggregator & Directory Handle Filter | Suppress directory/aggregator accounts (@rehberi, @portali, @turkiye) with -40 penalty | M3 | R2, survey_2 |
| 12 | Location Strictness & Conflict Penalty | Verify city/district compliance and apply -20 penalty for cross-city conflicts | M3 | R2, survey_2 |
| 13 | Boundary-Enforced Keyword Matching | Tokenized regex matching (`\bkw\b`) to eliminate false positive substrings (diş/disney) | M3 | R2, survey_2 |
| 14 | Automated Unit Test Suite Matrix | 14-test matrix expansion in `test_instagram_finder.py` achieving >85% coverage | M4 | R4, survey_3 |
| 15 | Verification & Smoke Test Pass | Clean run of `smoke_test.py` and `smoke_test_commands.py` with exit code 0 | M4 | R4, survey_3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Session & Anti-Blocking Resilience Infra | Cookie bootstrapper, session auth, proxy propagation, resilient HTTP client | none | DONE |
| M2 | Anonymous Profile, Story & Highlight Engine | Guest API fixes, story/highlight media extractor, mirror adapters, recency parser | M1 | DONE |
| M3 | Search & Candidate Profile Matching Overhaul | 6-factor composite score, domain SLD matching, aggregator filter, location penalty | M1, M2 | DONE |
| M4 | Test Suite Expansion & E2E Verification | 14-test unit matrix, >85% coverage, smoke test execution | M1, M2, M3 | IN_PROGRESS |

## Interface Contracts
### `InstagramSessionManager` ↔ `InstagramFinder`
- `get_guest_cookies()` -> `dict[str, str]`: returns bootstrapped guest cookies (`mid`, `ig_did`, `csrftoken`).
- `get_authenticated_session()` -> `httpx.AsyncClient | None`: returns client authenticated via decrypted `sessionid` if configured.
- `get_resilient_client(headers, proxy, timeout)` -> `httpx.AsyncClient`: configures proxy, UA rotation, and backoff retries.

### `_calculate_relevance_score` Refactored Signature
- `_calculate_relevance_score(profile: dict, target_sector: str = "", target_business_name: str = "", target_website: str = "", target_location: str = "") -> int`
- Returns composite score 0-100.

## Code Layout
- `src/aegisScout/discovery/instagram_finder.py`: Main Instagram OSINT and finder engine.
- `src/aegisScout/discovery/noise_filter.py`: Directory and aggregator regex filtering.
- `src/aegisScout/discovery/web_scraper.py`: Website scraping and reverse IG handle extraction.
- `tests/test_discovery/test_instagram_finder.py`: Primary test suite.

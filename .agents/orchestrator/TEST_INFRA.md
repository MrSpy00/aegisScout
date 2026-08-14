# E2E Test Infra: aegisScout Instagram Finder

## Test Philosophy
- Opaque-box, requirement-driven test suite.
- Comprehensive unit and integration coverage for anonymous profile/story viewing, profile search & matching algorithms, anti-blocking resilience, and root verification scripts.

## Feature Inventory & Test Mapping
| # | Feature | Requirement | Tier 1 (Unit) | Tier 2 (Edge/Boundary) | Tier 3 (Cross-Module) | Tier 4 (Integration/Smoke) |
|---|---------|-------------|:-------------:|:---------------------:|:--------------------:|:--------------------------:|
| 1 | Guest Cookie Bootstrapping | R1, R3 | 2 | 2 | 1 | 1 |
| 2 | Session Cookie Auth & Encryption | R3 | 2 | 2 | 1 | 1 |
| 3 | Resilient Proxy & Retry Client | R3 | 2 | 2 | 1 | 1 |
| 4 | Direct Profile API Parsing | R1 | 2 | 2 | 1 | 1 |
| 5 | Story & Highlight Media Extraction | R1 | 2 | 2 | 1 | 1 |
| 6 | Public Web Mirror Pipeline | R1 | 2 | 2 | 1 | 1 |
| 7 | Multi-Signal Recency Classification | R1 | 2 | 2 | 1 | 1 |
| 8 | 6-Factor Composite Candidate Scoring | R2 | 3 | 3 | 1 | 1 |
| 9 | Bidirectional SLD Domain Matching | R2 | 2 | 2 | 1 | 1 |
| 10 | Aggregator & Directory Handle Filter | R2 | 2 | 2 | 1 | 1 |
| 11 | Location Conflict Penalty | R2 | 2 | 2 | 1 | 1 |
| 12 | Network Failure & Exception Safety | R1, R3 | 2 | 2 | 1 | 1 |
| 13 | Dynamic Handle Generation & Autocomplete | R2 | 2 | 2 | 1 | 1 |
| 14 | Root Smoke Test Execution | R4 | 1 | 1 | 1 | 2 |

## Test Architecture
- Test Runner: `pytest` with `pytest-cov`, `pytest-asyncio`, `respx`
- Command: `pytest --cov=aegisScout.discovery.instagram_finder --cov-report=term-missing tests/test_discovery/test_instagram_finder.py`
- Root Smoke Scripts: `python smoke_test.py` and `python smoke_test_commands.py`

## Coverage Thresholds
- Unit test pass rate: 100% (all existing 16 tests + 14 new tests = 30 total tests)
- `instagram_finder.py` Statement Coverage: >= 85%
- Smoke test execution exit code: 0

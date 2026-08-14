## 2026-08-06T19:05:28Z

You are the Project Orchestrator for aegisScout.
Your working directory is x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator.
Original user request file: x:\Projects\ActiveProjects\aegisScout\.agents\ORIGINAL_REQUEST.md.

Mission:
Audit, fix, and overhaul the Instagram Finder system (`instagram_finder.py` and related discovery modules) in `aegisScout`.
Key tasks:
1. R1: Fix anonymous profile, story & highlight viewing (endpoints, headers, rate limiting, public web mirror fallbacks).
2. R2: Overhaul user search & candidate profile matching logic (scoring, domain cross-referencing, title/bio/location/website/post relevance).
3. R3: Enhance anti-blocking resilience & session handling (session cookie fallback, request retries, User-Agent rotation, proxy support, graceful error handling).
4. R4: Create/update automated tests in `tests/test_instagram_finder.py` and run verification scripts (`smoke_test.py` or similar).

Please initialize your BRIEFING.md and plan.md in x:\Projects\ActiveProjects\aegisScout\.agents\orchestrator, update progress.md regularly, execute/delegate all implementation and testing subtasks, and report completion when all criteria are met.

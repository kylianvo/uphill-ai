# SDD ledger — plan: docs/superpowers/plans/2026-10-13-race-history-review.md

Execution: native, approved by user on 2026-10-13; Impeccable UI extensions preserve incumbent system.
Tasks: 1 pending; 2 pending; 3 pending; 4 pending.
Pre-flight A1 -> A2: metadata is additive; selection retained. A2 -> A3/A4: road_prs shape and legacy aliases consistent. A1 -> A3/A4: optional clears require JSON null. B1 -> B2: course_context contract consistent. B2 -> B3/B4: detail and coach scopes consistent.

Ruling: batch visual inspection after both phases, with one correction round, to follow the user-invoked Impeccable verification ceiling — functional tasks can be committed but stay pending visual evidence; cost if wrong: UI defects discovered later in the same implementation.

Ruling: complete backend review tasks before final UI verification while A3/A4 await the single visual batch — all consumed backend Phase A contracts already pass; cost if wrong: UI work must adapt before final acceptance.

Ruling: repair four existing test-only TypeScript errors that block the frontend build (location restoration, unsupported role option, async test narrowing) — no runtime changes; cost if wrong: three existing tests need correction.
Task 1: complete (commits 6ebc414..0103ea1, tests: python3 .superpowers/run_backend.py -m pytest tests/unit/test_race_review.py tests/unit/test_race_matcher.py -q → 35 passed in 9.40s)
Task 2: complete (commits cb504c6..0103ea1, tests: python3 .superpowers/run_backend.py -m pytest tests/unit/test_race_review.py tests/integration/test_race_review.py -q → 17 passed, 5 warnings in 155.42s (0:02:35))

Ruling: run the UphillAI-E2E scheme directly after the scoped preview seed because e2e.sh hardcodes port 8000 and the shared DB — use owned API 8014 and isolated DB; cost if wrong: launch setup must be maintained explicitly.

User amendment: remove Trail/Road race-list filters; retain one chronological confirmed list and discipline labels. No change to PB eligibility.

Ruling: capture native UI on a fresh, task-owned iOS 26.5 simulator after repeated iOS 27 tab accessibility failures and screen-surface timeout — keep iOS 27 model-test evidence separately; cost if wrong: iOS 27 UI behavior needs a separate manual check.

Ruling: bootstrap race UI tests with an authenticated local API token in a DEBUG-only, local-HTTP-only in-memory store — normal session restore still validates it with /auth/me, and Release ignores the hook; cost if wrong: one extra developer-only app-entry helper must be removed or corrected. Guard tests observed RED before implementation.

Handoff 2026-10-13: user requested Claude continuation. See docs/handoffs/2026-10-13-race-history-claude.md. Web 514 units / 6 E2Es / tsc / build pass. Native latest review and retry cases pass; confirmation/Me PB assertions pass before manual form time-field failure at E2E line 123. UI commits/visual inspection/final reviews remain outstanding. Work stopped for handoff; no production deployment.

Resume 2026-10-13: user chose Pause Claude; Codex continues. Suspended verified Claude Race History process 98618 (SIGSTOP), preserving its state. Concurrent simulator runs caused signal-kill failures; do not resume that process while native tests run. Docker engine restarted from hung stopped state; only the existing local preview Postgres container started. Backend targeted verification: 68 passed, 5 inherited warnings. Detector: [] on five changed web targets. Initial screenshot batch inspected.

Manual-entry RED reproduced in Claude-owned run with the current instrumented test: finish field not found, keyboard persisted after scrolling to lower rankings. Applied existing SignInView scroll-dismiss behavior to the manual Form; GREEN verification pending.

Ruling: start the single fresh whole-change code review while native verification is pending — surfaces code/contract gaps in time for one consolidated fix pass, and review includes untracked implementation rather than only commits; cost if wrong: late implementation edits need author verification against the review focus. Reviewer is fresh gpt-6-astra, read-only.

Task 3: complete (native detail/review UI; E2E testRaceReviewStates, testReviewRetryKeepsRecordedResult, testLongNameAndEditionWarnings passed in 4/4 run; different-edition and unknown-edition + Dynamic Type long-name screenshots captured).
Task 4: complete (web detail dialog; review E2E 4/4, 514 unit tests, tsc, build passed earlier; detector clean).
Ruling: Release build compiled with CODE_SIGNING_ALLOWED=NO and binary scanned — no UITEST_SESSION_TOKEN/UPHILL_LOCAL_API_PORT strings present (.superpowers/native-release-build.log); cost if wrong: DEBUG hook leaks into Release.
Ruling: web captures left as-is after inspection (VI manual-edit shows a grey note field, likely focus/hover artifact) — one correction round was spent on the native error text; cost if wrong: minor visual noise in evidence.

## Review fix pass (single pass after 79d2e23)
- Backend payload tolerance (non-dict distances/climate/results, list payload), historical_field key whitelist, string avg_temp_c range: fixed in 1fd434c.
- edition_year deliberately unchanged: stays "unknown" until the course is curated with an edition year.
- Web items 4-10 (dialog centring, pbItem border, input focus, localized error copy, legacy HM/FM chips removed, discipline/source labels, formatNumber/formatKm, pace rounding): fixed in 014bd7f.
- Native items 11-15 (labels, app-language number locale, courseId reset, pending-VBM date strip, badge grid text styles, pace rounding): fixed in the ios commit following 014bd7f. Skipped within 15: monospaced kept on distance labels (lines 55, 111) by instruction.
- Item 16: no native coach athlete view lists races; not built. Known gap recorded in the expansion spec.
- No new screenshots taken (user instruction); E2E not run.

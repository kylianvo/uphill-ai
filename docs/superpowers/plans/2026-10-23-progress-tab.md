# Progress Tab (v1: data, endpoint, iOS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the iOS Progress tab (Training + Health) on top of a backend endpoint that returns only the cards that have enough data. That needs three new pieces of COROS data first: sleep, HRV/sleep history and long-run heart-rate drift.

**Architecture:** The COROS adapter gains a sleep source, chunked history fetches and a per-activity lap call. Results go into existing tables (`daily_metrics`, `activities`) plus a few new columns. One pure module, `services/progress_cards.py`, decides which cards qualify and builds their series; `GET /api/progress` serves it. The iOS app renders whatever comes back, so neither client can show an empty card.

**Tech Stack:** FastAPI + SQLAlchemy Core `text()` (no ORM), Alembic, pytest; SwiftUI + Swift Charts, XcodeGen, `Localizable.xcstrings`.

**Spec:** `docs/superpowers/specs/2026-10-23-progress-tab-design.md` (research: `docs/research/2026-10-23-training-health-literature-review.md`)

**Out of this plan (own plans later):** spec Phase 4, Coach (Coach's read model text, "Ask Coach about this", week-review extension, Langfuse process); spec Phase 5, web tab.

## Global Constraints

- **Never render an empty chart.** A card is returned only once it meets its threshold. iOS renders exactly what the endpoint returns.
- Card thresholds: Consistency ≥ 2 completed plan weeks · Volume ≥ 3 weeks with sessions · Aerobic speed when `fitness_tracking.refresh` returns a status · Durability ≥ 3 qualifying long runs · Load ≥ 28 days of load · Sleep ≥ 7 nights · Resting HR ≥ 7 days · HRV ≥ 14 nights from one source.
- Default window 28 days. Long run = ≥ 90 min (5400 s). Hard workouts excluded from drift: matched workout `type` in `aerobic_speed._HARD_WORKOUTS`.
- One source per metric: reuse `db._pick_readiness_provider` (newest provider wins, COROS on a tie). Every card carries `source`.
- Interpretations are **keys plus numbers** (e.g. `{"key": "rhr.below", "delta": 2}`), never sentences. iOS localizes EN/VI. Wording never says "risk", "injury", or names a sleep stage.
- No brand scores as values: COROS sleep score, Recovery % and VO2max are not shown.
- Schema changes go in both `db.py:init_db()` (idempotent `ALTER ... IF NOT EXISTS`) and one hand-written Alembic migration (`db-migration` skill).
- iOS: emerald (`Tokens.swift` accent) is the only accent colour; system grouped backgrounds; SF Pro with `.fontDesign(.rounded)` values; Dynamic Type; every chart has an `AXChartDescriptor`; no glass, no video inside the tab.
- VI copy follows the `uphill-ai-vietnamese-copy` skill. Tab label "Progress" / "Tiến độ".
- Backend tests: `cd backend && pytest tests/unit -q`. iOS tests: `ios-native/scripts/test.sh` (regenerates the XcodeGen project first).

## Review Focus

1. **A COROS user who connected years ago but synced little:** history must fill on the next manual sync (`POST /coros/sync` already allows up to 365 days). The 90-day cap must apply to sleep and HRV, not just to RHR. Test: Task 3 `test_long_window_fetches_hrv_in_7_day_chunks`.
2. **Two providers (COROS + Apple Health) with different HRV methods:** the HRV card must use one provider only and name it. Test: Task 6 `test_hrv_uses_single_provider`.
3. **Nights or days with gaps ("No data", nap-only nights):** they must not count as nights and must not draw as zero. Tests: Task 1 `test_nap_only_day_counts_naps_only`, Task 6 `test_sleep_ignores_missing_nights`.
4. **Long runs with a pause or treadmill section:** too few 1 km laps or zero HR laps must give no drift rather than a wild number. Test: Task 4 `test_drift_none_when_laps_missing_hr`.
5. **No device and no plan:** the endpoint must return empty `cards` with flags, never an error. The tab still shows the connect card and the create-plan card. Test: Task 7 `test_progress_for_brand_new_user`.

---

### Task 1: Parse COROS sleep overview and the HRV normal range

**Files:**
- Modify: `backend/services/providers/coros_parsers.py` (new `parse_sleep_overview`; extend `parse_sleep_hrv`)
- Test: `backend/tests/unit/test_coros_parsers.py`

**Interfaces:**
- Produces: `parse_sleep_overview(text: str) -> dict[date, dict]`, each value `{"sleep_minutes": int, "sleep_start": time | None, "sleep_end": time | None}`. `parse_sleep_hrv` values gain `"hrv_range_low": float | None, "hrv_range_high": float | None`.

- [ ] **Step 1: Write failing tests** using verbatim samples from the real account (spec research, section 3):
  - `test_sleep_overview_current_format`: the `2026-10-22` block (`Daily Sleep: 6h 58min (incl. naps)`, window `00:48 - 07:51`) gives `sleep_minutes == 418`, `sleep_start == time(0, 48)`, `sleep_end == time(7, 51)`.
  - `test_sleep_overview_old_format_without_daily_sleep`: the `2026-07-03` block (`Main Sleep: 5h 19min`, no `Daily Sleep` line) gives `319`.
  - `test_nap_only_day_counts_naps_only`: the `2026-10-21` block (`Sleep Score: -1`, `Daily Sleep: 3h 27min`, no main window) gives `207` with `sleep_start is None`.
  - `test_sleep_overview_missing_header_raises`: text without `Sleep Overview` raises `CorosParseError`.
  - `test_sleep_hrv_captures_normal_range`: `Normal Range: 51 - 75 ms` gives `hrv_range_low == 51.0`, `hrv_range_high == 75.0`.
- [ ] **Step 2: Run** `pytest tests/unit/test_coros_parsers.py -q`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement.** Follow the existing style: `_clean_text`, the header guard, `_drop_lines` for "header but no rows". `sleep_minutes` is `Daily Sleep` when present, else `Main Sleep (asleep)`, else `Main Sleep`. Use `parse_duration` for "7h 57min" only if it supports that format; otherwise add a small `_hm_minutes`. `sleep_start`/`sleep_end` come from `Main Sleep Window` as local wall-clock times.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `feat(coros): parse sleep overview and HRV normal range`

### Task 2: Schema: sleep window, HRV range, drift

**Files:**
- Modify: `backend/db.py` (`init_db` ALTERs; `upsert_daily_metric`; `upsert_activity`; `get_activities_for_pace` SELECT adds `a.hr_drift_pct`)
- Modify: `backend/services/providers/base.py` (`CanonicalDailyMetric` + `CanonicalActivity` fields)
- Create: `backend/alembic/versions/<rev>_progress_tab_columns.py` (`down_revision` = output of `alembic heads`; if there are two heads, make it a merge revision listing both)
- Test: `backend/tests/unit/test_recovery_metrics.py` or the nearest existing `upsert_daily_metric` test

**Interfaces:**
- Produces columns: `daily_metrics.sleep_start TIME`, `daily_metrics.sleep_end TIME`, `daily_metrics.hrv_range_low REAL`, `daily_metrics.hrv_range_high REAL`, `activities.hr_drift_pct REAL`, `activities.hr_drift_checked BOOLEAN NOT NULL DEFAULT FALSE`.
- Produces dataclass fields: `CanonicalDailyMetric.sleep_start: time | None = None`, `.sleep_end`, `.hrv_range_low`, `.hrv_range_high`; `CanonicalActivity.hr_drift_pct: float | None = None`.
- Produces `db.get_activities_needing_drift(user_id: int, provider: str, since: datetime, min_seconds: int = 5400, limit: int = 10) -> list[dict]` (keys `id`, `external_id`, `activity_type`, `workout_type`), selecting `hr_drift_checked = FALSE` non-duplicates, newest first. And `db.set_activity_hr_drift(activity_id: int, pct: float | None) -> None`, which sets `hr_drift_pct` and `hr_drift_checked = TRUE`.

- [ ] **Step 1: Write failing tests.** `upsert_daily_metric` round-trips the four new fields (COALESCE on conflict like its siblings), and `upsert_activity` writes `hr_drift_pct` (set `hr_drift_checked = TRUE` when it is not None). Follow the existing DB test pattern; integration tests TRUNCATE, so run them only against a scratch DB.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** the ALTERs, the migration (upgrade adds, downgrade drops), the dataclass fields, the SQL and the two helpers.
- [ ] **Step 4: Run** `pytest tests/unit -q`. Expected: PASS. Then `alembic upgrade head` on the local dev DB succeeds.
- [ ] **Step 5: Commit** `feat(db): columns for sleep window, HRV range and long-run drift`

### Task 3: Adapter: sleep source and history chunks

**Files:**
- Modify: `backend/services/providers/coros.py` (`fetch_daily_metrics`)
- Modify: `backend/services/coros_sync.py:105` (`min(days, 30)` → `min(days, METRICS_HISTORY_DAYS)`, `METRICS_HISTORY_DAYS = 90`)
- Test: `backend/tests/unit/test_coros_adapter.py`, `backend/tests/unit/test_coros_sync.py`

**Interfaces:**
- Consumes: Task 1 parsers, Task 2 dataclass fields.
- Produces: `CorosAdapter.fetch_daily_metrics(days: int = 7, today: date | None = None)`. It now merges four sources (resting HR, sleep HRV, training load, sleep overview) and raises `CorosDailyMetricsUnavailableError` only when **all four** fail.

- [ ] **Step 1: Write failing tests** with `StubMcp`:
  - `test_sleep_fills_sleep_minutes_and_window`: a `querySleepOverview` response lands on the matching date's metric.
  - `test_long_window_fetches_hrv_in_7_day_chunks`: `days=30` makes 5 `querySleepHrv` calls with explicit `startDate`/`endDate` covering `today-29 … today` without overlap; `querySleepOverview` uses chunks of at most 30 days.
  - `test_short_window_keeps_single_recent_days_call`: `days=7` makes one `querySleepHrv` call with `days=7` (current behaviour).
  - `test_all_four_sources_failing_raises` and `test_three_failing_still_returns_the_fourth`.
  - In `test_coros_sync.py`: `persist(..., days=365)` calls `fetch_daily_metrics(days=90)`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.** Each chunked source still goes through the existing `source(...)` guard: one failed chunk drops only that chunk, and a source counts as failed only if every chunk failed. Run chunks with the same `asyncio.gather`, behind a `Semaphore(DETAIL_CONCURRENCY)`.
- [ ] **Step 4: Run** `pytest tests/unit/test_coros_adapter.py tests/unit/test_coros_sync.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(coros): sync sleep and 90 days of HRV/sleep history`

### Task 4: Long-run heart-rate drift

**Files:**
- Create: `backend/services/hr_drift.py`
- Modify: `backend/services/providers/coros.py` (new `fetch_hr_drift`)
- Modify: `backend/services/coros_sync.py` (`persist` calls `update_hr_drift` after activities are stored)
- Test: `backend/tests/unit/test_hr_drift.py`, `backend/tests/unit/test_coros_sync.py`

**Interfaces:**
- Produces: `hr_drift.drift_pct(lap_json: str) -> float | None`. `CorosAdapter.fetch_hr_drift(label_id: str, sport_type: int) -> float | None` calls `queryActivityLapData` and returns `drift_pct`; it returns None on `McpError` or invalid JSON. `coros_sync.update_hr_drift(user_id: int, adapter, today: date | None = None) -> int` (rows checked).
- Consumes: Task 2 `get_activities_needing_drift`, `set_activity_hr_drift`; sport type from the reverse of `SPORT_TYPE_NAMES`.

- [ ] **Step 1: Write failing tests:**
  - `test_drift_matches_real_trail_run`: a fixture built from the 25.6 km run (1 km group, `lapDistance == 100000`, the 26 laps from the research note) gives `1.6`.
  - `test_drift_none_with_fewer_than_10_full_laps`.
  - `test_drift_none_when_laps_missing_hr`: any full lap with `avgHr == 0` or `adjustedPace == 0` gives None.
  - `test_drift_keys_on_field_name_not_label`: the same data with English labels gives the same result.
  - `test_update_hr_drift_marks_checked_and_skips_hard_workouts`: an activity matched to an `interval` workout is marked checked with `None` and no MCP call is made.
- [ ] **Step 2: Run** `pytest tests/unit/test_hr_drift.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `drift_pct`.** Take the lap group whose `lapDistance == 100000`, keep full laps (`distance == lapDistance`), require ≥ 10, split by count into halves (first half gets the shorter side), compute efficiency per half as mean(1000 / adjustedPace) / mean(avgHr), and return `round((eff1 / eff2 - 1) * 100, 1)`. `update_hr_drift` looks back 90 days, 10 activities per sync.
- [ ] **Step 4: Run** `pytest tests/unit -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(progress): long-run heart-rate drift from COROS laps`

### Task 5: Card rules: Training section

**Files:**
- Create: `backend/services/progress_cards.py`
- Test: `backend/tests/unit/test_progress_cards.py`

**Interfaces:**
- Produces (pure; no DB access in these functions):
  - `@dataclass(frozen=True) class Card: key: str; value: float | None; unit: str | None; series: list[dict]; band: tuple[float, float] | None; note: dict; as_of: date | None; source: str | None`
  - `@dataclass(frozen=True) class Pending: key: str; needs: int; have: int`
  - `consistency(workouts: list[dict], current_week: int) -> Card | Pending`: weeks `< current_week`, non-`Rest`; done = `is_completed == 1` or `matched_activity_id`; `series = [{"week", "done", "planned"}]` (last 8); `note = {"key": "consistency", "pct": int, "top_missed_reason": str | None}`.
  - `volume(workouts: list[dict], activities: list[dict], plan_monday: date, current_week: int) -> Card | Pending`: per week `{"week", "km", "km_planned", "climb_m", "climb_planned"}`.
  - `durability(activities: list[dict]) -> Card | Pending`: rows with `hr_drift_pct` not None, `duration_seconds >= 5400`, `workout_type` not in `_HARD_WORKOUTS`; `value` = median of the last 3; `note.key` = `"durability"`.
  - `training_load(metrics: list[dict]) -> Card | Pending`: 28 days of `training_load_short/long`; `note.key` is `"load.above"` (latest ratio > 1.3), `"load.below"` (< 0.8) or `"load.within"`.
  - `aerobic_speed_card(checkpoints: list[dict], path: dict | None) -> Card | Pending`: Pending when `path is None`.
- Threshold constants at the top, named as in Global Constraints.
- `Card.key` values, used verbatim by Task 7 and iOS: `consistency`, `volume`, `durability`, `load`, `aerobic_speed` (Training); `coach_read`, `sleep`, `resting_hr`, `hrv` (Health); `goal` is a marker built in Task 7. `Pending.key` uses the same strings.

- [ ] **Step 1: Write failing tests**, one pair per card at the threshold: `test_<card>_pending_below_threshold` (returns `Pending` with the right `needs`/`have`) and `test_<card>_card_at_threshold` (returns `Card` with the expected `value`/`note`). Add `test_consistency_counts_watch_matched_as_done` and `test_durability_excludes_hard_workouts`.
- [ ] **Step 2: Run** `pytest tests/unit/test_progress_cards.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the five functions.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(progress): training card rules`

### Task 6: Card rules: Health section

**Files:**
- Modify: `backend/services/progress_cards.py`
- Test: `backend/tests/unit/test_progress_cards.py`

**Interfaces:**
- Produces:
  - `usual_range(values: list[float], floor: float) -> tuple[float, float, float]` gives `(low, mid, high)`: mid = median, half-width = `max(floor, 1.4826 * MAD)`.
  - All three metric functions take `window_days: int = 28` (Task 7 passes 28 or 90). `series` spans the window; thresholds and the 7-day "current" value don't change.
  - `sleep(metrics: list[dict], today: date, window_days: int = 28) -> Card | Pending`: floor 30 min; value = 7-night mean; `note.key` ∈ `sleep.below|within|above`; `series` includes `sleep_start`/`sleep_end` when present.
  - `resting_hr(metrics, today, window_days=28) -> Card | Pending`: floor 2 bpm; `note = {"key": "rhr.below|within|above", "delta": int}`.
  - `hrv(metrics, today, window_days=28) -> Card | Pending`: band = the latest `hrv_range_low/high` when present (COROS), else `usual_range(floor=3)` over the window (Apple Health); `note.key` ∈ `hrv.below|within|above`.
  - `health_summary(cards: list[Card]) -> Card | None`: the rule-based Coach's read (`key = "coach_read"`); `note = {"key": "health.all_usual" | "health.off", "contributors": [card keys not in "within"]}`. None when no health card qualified.
- Every function receives rows for **one provider** (the caller filters). Days with the metric None are not counted.

- [ ] **Step 1: Write failing tests:** threshold pairs for sleep (7), resting HR (7) and HRV (14); `test_sleep_ignores_missing_nights` (6 real nights + 3 None gives Pending); `test_hrv_prefers_coros_range`; `test_hrv_apple_uses_usual_range`; `test_usual_range_floor_applies`; `test_summary_names_off_contributors`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(progress): health card rules`

### Task 7: `GET /api/progress`

**Files:**
- Create: `backend/routers/progress.py` (`router = APIRouter()`, `get_current_user` as in `routers/integrations.py`)
- Modify: `backend/main.py:153-155` (`app.include_router(progress_router, prefix="/api")`)
- Modify: `backend/db.py` (new `get_daily_metrics(user_id: int, since: date) -> list[dict]`, all providers)
- Modify: `backend/services/progress_cards.py` (new `build(user: dict, section: str, today: date | None = None) -> dict`)
- Test: `backend/tests/unit/test_progress_route.py` (monkeypatch `db`, as in `test_coros_sync_route.py`)

**Interfaces:**
- Consumes: Tasks 5–6; `db.get_active_plan`, `db.get_plan_workouts_with_match`, `db.get_activities_for_pace`, `db.get_fitness_checkpoints`, `fitness_tracking.refresh`, `aerobic_speed.plan_monday`, `db._pick_readiness_provider`, `db.list_active_connections`/connection status for `connected`.
- `build(user, section, today=None, days=28)`. Query `?section=training|health&days=28|90`; any other value is 422. `days` only affects Health series and the Load series.
- Produces the response:
```json
{"section": "health", "connected": true, "has_plan": true, "plan_id": 12,
 "cards": [{"key": "sleep", "value": 431.0, "unit": "min", "series": [...], "band": [400, 460],
            "note": {"key": "sleep.within"}, "as_of": "2026-10-22", "source": "coros"}],
 "pending": [{"key": "hrv", "needs": 14, "have": 9}]}
```
  Training order: `goal` (only `{"key": "goal"}` when `has_plan`; iOS renders the existing goal row), `aerobic_speed`, `consistency`, `volume`, `durability`, `load`. Health order: `coach_read`, `sleep`, `resting_hr`, `hrv`. `connected` is true when the user has an active COROS connection or any `apple_health` daily metric or activity in the last 30 days.

- [ ] **Step 1: Write failing tests:** `test_progress_for_brand_new_user` (no plan, no metrics: `cards == []`, `connected is False`, `has_plan is False`, 200); `test_health_cards_from_single_provider`; `test_days_90_widens_series` and `test_days_other_value_is_422`; `test_training_order_and_goal_marker`; `test_bad_section_is_422`; `test_requires_auth`.
- [ ] **Step 2: Run** `pytest tests/unit/test_progress_route.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** `build` (DB reads, then the pure card functions) and the route.
- [ ] **Step 4: Run** `pytest tests/unit -q`. Expected: PASS. Then hit `curl -H "Authorization: Bearer <local token>" "localhost:8000/api/progress?section=health"` against the local stack after a COROS sync: the JSON has cards and no empty series.
- [ ] **Step 5: Commit** `feat(progress): GET /api/progress`

### Task 8: iOS models, service and view model

**Files:**
- Create: `ios-native/UphillAI/Core/Progress/ProgressModels.swift`, `ios-native/UphillAI/Core/Progress/ProgressService.swift`, `ios-native/UphillAI/Features/Progress/ProgressViewModel.swift`
- Test: `ios-native/UphillAITests/Progress/ProgressDecodingTests.swift`, `ios-native/UphillAITests/Progress/ProgressViewModelTests.swift`

**Interfaces:**
- Produces: `struct ProgressResponse: Decodable { section: String; connected: Bool; hasPlan: Bool; planId: Int?; cards: [ProgressCard]; pending: [ProgressPending] }` (snake_case is converted by `JSONCoding`). `ProgressCard` has `key: String`, `value: Double?`, `unit: String?`, `series: [[String: JSONValue]]` (existing `Core/Models/JSONValue.swift`), `band: [Double]?`, `note: [String: JSONValue]`, `asOf: String?` and `source: String?`. `ProgressPending` has `key`, `needs: Int` and `have: Int`. Plus `protocol ProgressServicing: Sendable { func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse }` with `enum ProgressSection: String { case training, health }`, implemented over `client.send(.get("/api/progress", query:))` the way `PlanService.journey` does. And `@Observable @MainActor final class ProgressViewModel` with `section`, `days` (28 | 90), `state: LoadState` (same cases as `PlanViewModel.LoadState`: `loading, empty, loaded, failed(String)`), `response: ProgressResponse?` and `func load() async`.

- [ ] **Step 1: Write failing tests:** decode a JSON fixture recorded from the local backend (README's DTO-recording script) for each section; the view model `load()` with a stub service sets `.loaded`; a thrown error sets `.failed`; switching `section` reloads.
- [ ] **Step 2: Run** `ios-native/scripts/test.sh`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(ios): progress models, service and view model`

### Task 9: iOS Progress tab UI

**Files:**
- Create: `ios-native/UphillAI/Features/Progress/ProgressView.swift` (NavigationStack, large title, segmented Picker, card list, pending line, connect and create-plan cards), `ProgressCardView.swift` (shared anatomy: SF Symbol + name in emerald, as-of date, rounded value + unit, compact chart slot, one note line), `ProgressCharts.swift` (one small Swift Chart per card key with a band `RectangleMark` at low emerald opacity and an `AXChartDescriptor`), `ProgressDetailView.swift` (a 4W / 3M segmented switch that re-requests with `days` 28/90, a larger chart with axes, and a "what this means" paragraph per card key in `Localizable.xcstrings`), `ProgressNoteText.swift` (maps `note.key` + numbers to a `LocalizedStringResource`)
- Modify: `ios-native/UphillAI/App/RootView.swift:80-110` (`Tab.progress`, `SwiftUI.Tab("Progress", systemImage: "chart.line.uptrend.xyaxis", ...)` between Plan and Coach)
- Modify: `ios-native/UphillAI/Resources/Localizable.xcstrings` (EN + VI for every note key, card names, pending lines, connect/create-plan cards, tab label "Tiến độ")
- The connect card opens the existing `Features/Integrations/ConnectedAccountsView`; the create-plan card switches to the Plan tab (its existing create flow).
- Reuse: `GoalPathRow` for the `goal` card (fed by `PlanService.goal(planID:)`), `CardModifier`, `Tokens.swift`
- Test: `ios-native/UphillAITests/Progress/ProgressScreenshots.swift` (the existing screenshot-test pattern, e.g. `PlanAuditScreenshots.swift`)

**Interfaces:**
- Consumes: Task 8.

- [ ] **Step 1: Write the screenshot tests** for five fixture states: COROS user (all cards), Apple Health only (no load or durability), no device (Health = connect card only), no plan (Training = create-plan card), brand-new (welcome cards). Each in light and dark, plus one at Dynamic Type accessibility XL.
- [ ] **Step 2: Run** `ios-native/scripts/test.sh`. Expected: FAIL (views missing).
- [ ] **Step 3: Implement** the views. Assert in code that the card list renders only `response.cards`. There is no placeholder branch.
- [ ] **Step 4: Run.** Expected: PASS. Inspect each screenshot: no empty chart, emerald is the only accent, VI strings fit at XL.
- [ ] **Step 5: Run the app** on the simulator against the local backend with a synced COROS account (`ui-screenshot-evidence` skill). Capture Training and Health and attach them to the PR.
- [ ] **Step 6: Commit** `feat(ios): Progress tab`

---

## Done when

- `pytest tests/unit -q` and `ios-native/scripts/test.sh` pass.
- The real COROS account shows Sleep, Resting HR, HRV, Load, Durability (after its runs sync) and Aerobic speed, with no empty card.
- Screenshots for the five states in light and dark are attached to the PR.
- Prod deploy notes: the Alembic revision, and one manual COROS sync per athlete to fill history (or let the next scheduled sync do it).

# Athletes Tab Coach Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the iOS Athletes tab into a coach workbench. It covers three things:
- a triage screen: filters, overview, highlights, an inbox sorted by urgency with one-line takeaways, and an On-track table
- per-week plan review
- building and publishing a plan

The runner's own Plan tab, plus a coach card, serves as the detail view.

**Architecture:**
- **Backend:** a pure rule module (`services/coach_signals.py`) turns batched per-athlete facts into signals. `get_roster_overview_data` gathers those facts in a few roster-wide queries and adds new fields to the existing response (additive only). Three small endpoints handle the plan type, review and publish.
- **iOS:**
  - Filtering, aggregation and sectioning live in a pure `RosterTriage` type.
  - A new `AthletesView` replaces `CoachDashboardView`.
  - `CoachFocusCard` slots into the existing `PlanView`.

**Tech Stack:** FastAPI + SQLAlchemy Core `text()` on PostgreSQL, Alembic, pytest. SwiftUI (iOS 26+), Swift Testing, xcodegen, Swift Charts.

**Spec:** `docs/superpowers/specs/2026-10-23-athletes-tab-coach-workbench-design.md`

## Global Constraints

- The overview response is **additive only**: every existing key and type stays, because the web tab reads it.
- Every schema change goes in **both** `backend/db.py:init_db()` (idempotent `ADD COLUMN IF NOT EXISTS`) and a hand-written Alembic migration (`db-migration` skill).
- There is no LLM call anywhere in triage. Every signal comes from a deterministic rule.
- All copy is EN + VI in `ios-native/UphillAI/Resources/Localizable.xcstrings` (`uphill-ai-vietnamese-copy` skill).
- **UI:** Apple design, native patterns first (`List` sections, `Menu`, swipe actions, `.searchable`, SF Symbols, Dynamic Type, system materials). Minimalist style: warm monochrome, one status accent, flat cards, no gradients or heavy shadows. Build with the `impeccable` and `taste-skill:minimalist-ui` skills. Reuse `UH.*` tokens.
- **Backend:** `ponytail`. Make the smallest complete change and reuse existing helpers (`plan_lint`, `workout_calendar.workout_date`, `compute_current_week`, `week_range_for_block`, `approve_plan`).
- Coach endpoints use `require_athlete_access` or `require_coach`, as the existing `/api/coaching/...` routes do.
- Signal thresholds, copied exactly from the spec:
  - overload: >130% of planned minutes, with planned ≥ 60 min
  - no sync: ≥5 days
  - missed many: ≥3 in 7 days
  - adherence: <0.6, or a drop of ≥20 points over 14 days
  - HRV low: ≥2 of the last 3 days
  - hard easy days: ≥2 in 7 days
  - race soon: ≤14 days
  - next week due: ≤7 days
- **Review is per week:** `generated_block` = the block of the highest generated `week_number`, and a block is `settings.WEEKS_PER_BLOCK` weeks (currently 1).
- Before calling UI done, capture screenshot evidence (`ui-screenshot-evidence` skill, via `Phase6CoachScreenshots`).
- Tests:
  - Backend integration tests truncate the DB, so run them **only** against a scratch database (default `uphill_ai_test` on :5433).
  - iOS: `ios-native/scripts/test.sh`.

## Review Focus

1. **A runner with no plan, no workouts, no watch and no Apple Health** must not crash the overview. All data rules stay silent. A Coached runner shows `needs_plan`; a Review runner with no plan lands in On track with the meta "No plan" (owned by Task 4 and Task 5).
2. **Building a plan for an athlete must never change the coach's own session user or profile.** `PlanSetupViewModel` calls `session.setUser` (owned by Task 10).
3. **The old overview contract must still hold:** `athletes[].adherence_pct`, `action_items`, `phase_alerts`, `race_readiness` and the rest keep their keys and types, because the web tab depends on them (owned by Task 5).
4. **Every runner appears exactly once.** A runner with any `act_now` signal is never in the On-track table, whatever the filters (owned by Task 7).
5. **Filters that match nobody** show "No runners match", never "Nothing needs you today". The stats show "—", never NaN or a divide-by-zero (owned by Task 7).

---

## Phase 1: Bug fixes (PR 1)

### Task 1: Approvals no longer double-count drafts

**Files:**
- Modify: `backend/db.py`, the `pending_rows` query in `get_roster_overview_data` (~line 2741)
- Test: `backend/tests/integration/test_coach_overview.py`

- [ ] **Step 1: Write the failing test** `test_pending_approvals_exclude_draft_plans_keep_active_rest`
  - Setup: a coach with one athlete.
    - The athlete has a **draft** plan with 3 workouts, `approved_at` NULL, including one `type='Rest'`.
    - The athlete has an **active** plan where one workout was set to rest by the coach (`approved_at` NULL, `type='Rest'`).
  - Assert:
    - `len(ov["action_items"]["draft_plans"]) == 1`
    - `[p["plan_id"] for p in ov["action_items"]["pending_workout_approvals"]] == [active_plan_id]`
- [ ] **Step 2: Run it**
  - Run: `cd backend && pytest tests/integration/test_coach_overview.py::test_pending_approvals_exclude_draft_plans_keep_active_rest -v`
  - Expected: FAIL (4 pending items).
- [ ] **Step 3: Fix the query.** Add `AND p.plan_status <> 'draft'` to the `pending_rows` SQL.
- [ ] **Step 4: Run the whole `test_coach_overview.py` file.** Expected: PASS.
- [ ] **Step 5: Commit**: `fix(coach): a draft plan is one action item, not one per workout`

### Task 2: iOS coach-tab bug fixes

**Files:**
- Modify: `ios-native/UphillAI/Core/Generation/GenerationService.swift:31-33`
- Modify: `ios-native/UphillAI/Features/Coaching/CoachDashboardView.swift`
- Test: `ios-native/UphillAITests/Phase6/CoachCoachingTests.swift`

**Interfaces:**
- Produces: `GenerationService.generatePlan` posts to `"\(prefix)/generate-plan"`. For a coach that is `/api/coaching/athletes/{id}/generate-plan`; for a user's own plan it is `/api/coach/generate-plan`.
- Produces: `CoachedAthleteRow.init(fromOverview athlete: CoachOverviewAthlete)`, with `id = 0`, `athleteEmail = ""` and `athleteName = athlete.name`.

- [ ] **Step 1: Write the failing test** `testScopedGeneratePlanHitsCoachingRoute`.
  - Register a `StubURLProtocol` that records request paths, call `GenerationService(client:).scoped(toAthlete: 7).generatePlan(body)`, and expect `"/api/coaching/athletes/7/generate-plan"`.
  - The unscoped call still expects `"/api/coach/generate-plan"`.
- [ ] **Step 2: Run it.** `ios-native/scripts/test.sh -only-testing:UphillAITests/CoachCoachingTests`. Expected: FAIL.
- [ ] **Step 3: Use `prefix` in `generatePlan`.** Run the tests again. Expected: PASS.
- [ ] **Step 4: Fix the remaining bugs in `CoachDashboardView`.** This view is replaced in Task 8, so keep each fix minimal:
  - **#1 refresh:**
    - `loadData(force: Bool = false)`. The toolbar button passes `force: true`.
    - The early return applies only when `!force`.
  - **#4 dead taps:**
    - Replace each `roster.first(where:)` lookup with a helper `athleteRef(_ id: Int, _ name: String) -> CoachedAthleteRow`. It returns the roster row, or else `CoachedAthleteRow(fromOverview:)`.
    - Show a load-failure `Text` with a Retry button instead of `print`.
  - **#5:** `navigationTitle("Athletes")`.
  - **#7:** remove `fetchMyInvites` and `pendingInvites` from this view.
  - **#2:** the race card's callback filters to the race entry's athlete ids, using a new `@State var raceAthleteIds: Set<Int>?`, instead of setting `rosterSearch`.
- [ ] **Step 5: Write the test** `testOverviewAthleteFallsBackToRowWhenRosterMissing`, which asserts `CoachedAthleteRow(fromOverview:)` keeps `athleteId` and the display name. Run it. Expected: PASS.
- [ ] **Step 6: Commit**: `fix(ios-coach): refresh, dead taps, scoped plan generation, title`

---

## Phase 2: Triage screen (PR 2)

### Task 3: Schema for plan type and per-week review, plus the plan-type endpoint

**Files:**
- Modify: `backend/db.py` (`init_db` ALTERs; `get_roster_for_coach` selects `plan_type`; new `set_coach_athlete_plan_type`)
- Create: `backend/alembic/versions/<rev>_coach_plan_type_and_review.py`. Its `down_revision` = the output of `alembic heads` at the time.
- Modify: `backend/main.py`: add a `PATCH /api/coaching/roster/{link_id}` route next to `remove_from_roster`
- Test: `backend/tests/integration/test_coach_plan_type.py`

**Interfaces:**
- Produces, columns:
  - `coach_athletes.plan_type TEXT NOT NULL DEFAULT 'review'`
  - `plans.coach_reviewed_block INTEGER`
  - `plans.coach_reviewed_at TIMESTAMPTZ`
  - `plans.coach_reviewed_by INTEGER REFERENCES users(id)`
- Produces: `db.set_coach_athlete_plan_type(link_id: int, coach_id: int, plan_type: str) -> dict | None`
- Produces: the roster row JSON gains `"plan_type"`.

- [ ] **Step 1: Write the failing tests:**
  - `test_new_link_defaults_to_review`: the roster row has `plan_type == "review"`.
  - `test_coach_sets_plan_type`: a PATCH with `{"plan_type":"coached"}` returns 200, and the roster then shows `"coached"`.
  - `test_patch_rejects_unknown_type`: `"vip"` returns 422.
  - `test_patch_other_coaches_link_404`.
- [ ] **Step 2: Run them.** `pytest tests/integration/test_coach_plan_type.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement:**
  - In `init_db`, `ADD COLUMN IF NOT EXISTS` for all four columns.
  - The migration adds the same columns, with a `downgrade` that drops them.
  - The request model `plan_type: Literal["review","coached"]`.
  - The route uses `require_coach` and returns 404 when the db helper returns None.
- [ ] **Step 4: Run the tests and check the migration.**
  - `pytest tests/integration/test_coach_plan_type.py -v` → PASS.
  - `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` runs cleanly on the scratch DB.
- [ ] **Step 5: Commit**: `feat(coach): plan type per athlete and per-week review columns`

### Task 4: Signal rules

**Files:**
- Create: `backend/services/coach_signals.py`
- Modify: `backend/services/plan_lint.py`: rename `_is_long` → `is_long` and `_is_quality` → `is_quality`, and update their callers in that file
- Test: `backend/tests/unit/test_coach_signals.py`

**Interfaces:**
- Produces:
```python
@dataclass(frozen=True)
class Signal:
    code: str          # see table below
    severity: str      # "act_now" | "review_build" | "check_in" | "highlight"
    params: dict[str, Any]

@dataclass
class AthleteFacts:
    plan_type: str                      # "review" | "coached"
    plan: dict[str, Any] | None         # active plan row (id, race_name, race_date, start_date, total_weeks, created_by_user_id, user_id, coach_reviewed_block, created_at)
    draft_plan_id: int | None
    workouts: list[dict[str, Any]]      # active plan workouts, each with a computed "date": date
    pending_active_count: int           # pending workouts on the active plan
    last_activity_at: datetime | None
    hrv_last3: list[str | None]         # newest provider, newest first
    new_result: dict[str, Any] | None   # race_results row added in the last 7 days
    today: date

def signals_for(f: AthleteFacts) -> list[Signal]          # most severe first; ties keep table order
def status_of(signals: list[Signal]) -> str              # "act_now" | "review_build" | "check_in" | "on_track"
def week_stats(workouts: list[dict], week: int) -> dict  # {sessions_planned, sessions_done, key_planned, key_done, minutes_planned, minutes_done}; rest excluded
```
- Signal codes and `params`:

  | Code | Params |
  |---|---|
  | `reported_pain`, `reported_sick` | `{day}` |
  | `missed_many` | `{count}` |
  | `overload` | `{done_min, planned_min}` |
  | `plan_to_review` | `{week, waiting_hours|None}` |
  | `needs_plan` | `{}` |
  | `draft_unpublished` | `{}` |
  | `next_block_due` | `{days}` |
  | `changes_to_approve` | `{count}` |
  | `no_sync` | `{days}` |
  | `missed_key` | `{title, day}` |
  | `adherence_drop` | `{from_pct, to_pct}` |
  | `hrv_low` | `{days}` |
  | `hard_easy_days` | `{count}` |
  | `race_soon` | `{race, days}` |
  | `phase_start` | `{phase, when: "this_week"|"next_week"}` |
  | `longest_long_run` | `{minutes}` |
  | `block_done` | `{phase}` |
  | `new_result` | `{race, finish_time_sec}` |

  - "Key" = `plan_lint.is_long(w) or plan_lint.is_quality(w)`. "Easy" = neither of those, and not rest.
  - `plan_to_review` fires when `plan.created_by_user_id == plan.user_id` and `generated_block > (coach_reviewed_block or 0)`.
  - `waiting_hours` is set only when `generated_block == 1`.

- [ ] **Step 1: Write the failing tests.** Write one test per code, each with a fixed `today` and the minimal facts that trigger it, plus one negative test per code just under its threshold. Required cases:
  - `test_pain_in_last_7_days_is_act_now` and `test_pain_8_days_ago_is_silent`
  - `test_overload_131_pct` and `test_overload_ignored_when_planned_under_60_min`
  - `test_plan_to_review_week_2_after_week_1_reviewed` (`coach_reviewed_block=1`, workouts up to week 2 → `params["week"] == 2`, `waiting_hours is None`)
  - `test_coach_created_plan_never_to_review`
  - `test_no_sync_when_no_activity_since_plan_start`
  - `test_no_watch_data_keeps_data_rules_silent` (Review Focus 1)
  - `test_coached_without_plan_needs_plan`
  - `test_review_without_plan_is_on_track`
  - `test_status_prefers_act_now_over_highlight`
- [ ] **Step 2: Run them.** `cd backend && pytest tests/unit/test_coach_signals.py -v`. Expected: FAIL (the module is missing).
- [ ] **Step 3: Implement `coach_signals.py`.** Use plain functions, one per rule, and a module-level ordered list of the rules.
- [ ] **Step 4: Run the tests again, plus the existing `pytest tests/unit/test_plan_lint*.py`** to cover the rename. Expected: PASS.
- [ ] **Step 5: Commit**: `feat(coach): deterministic coach signal rules`

### Task 5: Overview gains the new per-athlete fields

**Files:**
- Modify: `backend/db.py`, `get_roster_overview_data`
- Test: `backend/tests/integration/test_coach_overview.py`

**Interfaces:**
- Consumes: `coach_signals.AthleteFacts`, `signals_for`, `status_of`, `week_stats` (Task 4); `services.workout_calendar.workout_date(start_monday, week_number, day_of_week)`.
- Produces, added to each `athletes[]` entry:
  - `plan_type`, `phase`, `race_date`, `days_to_race`
  - `week`, `prev_weeks` (3 entries, newest first), `load_4w_minutes` (4 entries, oldest first)
  - `adherence_14d`, `last_sync_at` (ISO string)
  - `signals` (`[{code, severity, params}]`), `status`
  - `mix_minutes`: `{easy, long, quality}`, completed minutes in the current week
  - `recovery`: `{hrv_status, resting_hr, sleep_avg_7d_min}`, or null when there are no `daily_metrics` rows
- Produces, top level: `generated_at`.

- [ ] **Step 1: Write the failing tests:**
  - `test_overview_keeps_legacy_keys`: assert the full set of legacy top-level keys and legacy athlete keys is still present, with the same types (Review Focus 3).
  - `test_overview_athlete_signals_pain`: a workout missed with `missed_reason='pain'` yesterday → `status == "act_now"` and `signals[0]["code"] == "reported_pain"`.
  - `test_overview_athlete_without_plan_has_null_week`: `week is None`, `signals == []` for Review, `[needs_plan]` for Coached (Review Focus 1).
  - `test_overview_query_count_constant`: overview queries for 1 athlete and for 10 athletes. Count statements with a SQLAlchemy `before_cursor_execute` listener; the counts must be equal.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement the roster-wide batched queries.** Each is one query for all athlete ids:
  - Extend the existing athlete query with `ca.plan_type`, `p.created_by_user_id`, `p.coach_reviewed_block`, `p.created_at`.
  - Draft plan ids per athlete.
  - Extend the workouts query with `type, title, rpe, missed_reason, target_zone, approved_at`.
  - `MAX(start_time)` from `activities` grouped by `user_id`.
  - `daily_metrics` for the last 7 days: newest provider per user, choosing COROS on a tie (matching readiness). The last 3 days feed `hrv_last3`; the newest row gives `resting_hr`; all 7 days give `sleep_avg_7d_min`.
  - `race_results` with `created_at >= NOW() - 7 days`.
  - Then build `AthleteFacts` per athlete and attach the new fields. Leave the existing computation untouched.
- [ ] **Step 4: Run the tests.** `pytest tests/integration/test_coach_overview.py -v`. Expected: PASS.
- [ ] **Step 5: Commit**: `feat(coach): overview carries per-athlete week stats and signals`

### Task 6: iOS models, service and fixtures

**Files:**
- Modify: `ios-native/UphillAI/Core/Coaching/CoachOverviewModel.swift`, `CoachRosterModel.swift`, `CoachingService.swift`
- Modify (re-record): `ios-native/UphillAITests/Fixtures/coaching_*.json` via `ios-native/scripts/record_fixtures.sh` with a seeded local roster that covers every status
- Test: `ios-native/UphillAITests/Phase6/CoachCoachingTests.swift`

**Interfaces:**
- Produces:
  - `CoachSignal { code: String, severity: CoachSeverity, params: [String: JSONValue] }`, where `CoachSeverity` is `actNow | reviewBuild | checkIn | highlight`. Reuse the app's existing `JSONValue` type if there is one; otherwise add a minimal `Codable` enum (string/number/null) in this file.
  - `CoachWeekStats { sessionsPlanned, sessionsDone, keyPlanned, keyDone, minutesPlanned, minutesDone: Int }`
  - New optional fields on `CoachOverviewAthlete`: `planType: String?`, `phase: String?`, `raceDate: String?`, `daysToRace: Int?`, `week: CoachWeekStats?`, `prevWeeks: [CoachWeekStats]?`, `load4wMinutes: [Double]?`, `adherence14d: Double?`, `lastSyncAt: String?`, `signals: [CoachSignal]?`, `status: String?`, `mixMinutes: CoachMix?` (easy/long/quality: Double), `recovery: CoachRecovery?` (hrvStatus: String?, restingHr: Int?, sleepAvg7dMin: Int?)
  - `CoachedAthleteRow.planType: String?`
  - `CoachingServicing.setPlanType(linkId: Int, planType: String) async throws -> CoachedAthleteRow`
- [ ] **Step 1: Re-record the fixtures** with a seeded roster of 6 athletes: one act_now (pain), one plan_to_review, one needs_plan (Coached), one no_sync, one race_soon, one on_track.
- [ ] **Step 2: Write the failing test** `testOverviewDecodesSignals`: the decoded fixture has 6 athletes, and the first act_now athlete's `signals?.first?.code == "reported_pain"`.
- [ ] **Step 3: Add the fields and the service method.** Optionals keep older fixtures decoding. Run the tests. Expected: PASS.
- [ ] **Step 4: Commit**: `feat(ios-coach): decode coach signals and plan type`

### Task 7: `RosterTriage`: filters, sections, stats, sentences

**Files:**
- Create: `ios-native/UphillAI/Core/Coaching/RosterTriage.swift`
- Create: `ios-native/UphillAI/Core/Coaching/CoachSignalText.swift`
- Test: `ios-native/UphillAITests/Phase6/RosterTriageTests.swift`

**Interfaces:**
- Consumes: Task 6 models.
- Produces:
```swift
struct RosterFilter: Equatable { var planType: String?; var race: String?; var level: String?; var phase: String? }
enum TriageSection: CaseIterable { case actNow, reviewBuild, checkIn, onTrack }
struct RosterTriage {
    init(athletes: [CoachOverviewAthlete], filter: RosterFilter, weekOffset: Int)   // weekOffset 0...3 (0 = current)
    var visible: [CoachOverviewAthlete] { get }
    func athletes(in: TriageSection) -> [CoachOverviewAthlete]       // each athlete in exactly one section
    var highlights: [(athlete: CoachOverviewAthlete, signal: CoachSignal)] { get }
    var sessionsDonePct: Double? { get }    // nil when nothing planned → UI shows "—"
    var keyDonePct: Double? { get }
    var volumePct: Double? { get }
    func groups(by: GroupKey) -> [(label: String, count: Int, donePct: Double?)]   // GroupKey: race | level | planType
    var mix: (easy: Double, long: Double, quality: Double)? { get }  // nil without the needed data; see note
    var counts: (all: Int, review: Int, coached: Int) { get }        // unfiltered, for chip labels
}
enum CoachSignalText { static func sentence(_ s: CoachSignal, lang: String) -> String }
enum CoachAction { case adaptWeek, reviewPlan, buildPlan, openDraft, buildNextWeek, reviewChanges, note }
extension CoachOverviewAthlete { var primaryAction: CoachAction? }   // mapping from the spec table
```
- `mix` sums each visible athlete's `mixMinutes` (Task 5), and is nil when there are none.
- [ ] **Step 1: Write the failing tests:**
  - `testEveryAthleteInExactlyOneSection`: the union across sections equals `visible`, with no duplicates (Review Focus 4).
  - `testActNowAthleteNeverOnTrack`, including under each filter.
  - `testFilterToNobodyGivesNilStats`: an empty `visible`, with all three pct values nil (Review Focus 5).
  - `testWeekOffsetUsesPrevWeeks`: offset 2 reads `prevWeeks[1]`.
  - `testGroupsByPlanType`.
  - `testSentenceEnVi`: one assertion per signal code, for both `lang: "en"` and `lang: "vi"`. The strings come from `Localizable.xcstrings`.
  - `testPrimaryActionMapping`: the spec table, row by row.
- [ ] **Step 2: Run them.** `ios-native/scripts/test.sh -only-testing:UphillAITests/RosterTriageTests`. Expected: FAIL.
- [ ] **Step 3: Implement both files and add the strings to `Localizable.xcstrings`.** Run the VI copy past the `uphill-ai-vietnamese-copy` skill.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit**: `feat(ios-coach): roster triage model and signal sentences`

### Task 8: `AthletesView` replaces `CoachDashboardView`

**Files:**
- Create: `ios-native/UphillAI/Features/Coaching/AthletesView.swift` (screen)
- Create: `ios-native/UphillAI/Features/Coaching/AthleteTriageRow.swift` (inbox card)
- Create: `ios-native/UphillAI/Features/Coaching/RosterOverviewCard.swift` (stats, week stepper, group-by, mix)
- Create: `ios-native/UphillAI/Features/Coaching/InviteAthleteSheet.swift` (the ＋ sheet)
- Modify: `ios-native/UphillAI/App/RootView.swift:84-90`: the Athletes tab shows `AthletesView`
- Delete: `CoachDashboardView.swift` and `CoachChartsView.swift`. First check no other caller remains: `grep -rn "CoachDashboardView\|AdherenceTrendChartView\|MissedByDayChartView\|WorkoutTypeMixChartView\|RaceBreakdownCardView" ios-native/`.
- Modify: `ios-native/UphillAITests/Phase6/Phase6CoachScreenshots.swift`

**Interfaces:**
- Consumes: `RosterTriage`, `CoachSignalText`, `primaryAction` (Task 7); `app.coachingService.setPlanType` (Task 6); `app.enterAthleteView(athlete:)` and `onSelectTab?(1)` (existing).
- Produces: `AthletesView(app: AppModel, onSelectTab: ((Int) -> Void)?, initialOverview: CoachOverview? = nil, initialRoster: [CoachedAthleteRow]? = nil)`.
- Produces: `AppModel.pendingCoachAction: CoachAction?`. It is set when a row's button is tapped, just before `enterAthleteView`, and consumed by Task 11.

- [ ] **Step 1: Invoke the `impeccable` and `taste-skill:minimalist-ui` skills** with the approved mockup (`.superpowers/brainstorm/*/content/athletes-layout-v2.html`) and the Apple-design constraint, and settle the visual details. The structure is fixed by the spec: filters → This week → Highlights → 🔴/🔵/🟠 sections → On-track table → Invited row.
- [ ] **Step 2: Build the screen** as a `List` with `.insetGrouped` sections:
  - The filter chips sit in the top section. Race, Level and Phase are `Menu`s.
  - Swipe actions on rows: the primary action and Note.
  - `.refreshable` triggers a forced load.
  - `.searchable` searches by name.
  - The On-track section is a compact table (name, week + phase, `adherence14d`, a Swift Charts sparkline of `load4wMinutes`) with a sort `Menu`: name / race date / done %.
  - Each row's button sets `pendingCoachAction`, then calls `enterAthleteView` and `onSelectTab?(1)`.
  - Tapping a highlight opens that runner.
  - The ＋ toolbar button opens the invite sheet.
  - The ⋯ menu on a row holds: switch plan type (with optimistic update and revert on error), race history (the existing `RaceHistoryPanel` route), and remove (the existing confirmation dialog).
  - Empty states: "Nothing needs you today" only when `visible` is non-empty and the 🔴/🔵/🟠 sections are all empty; "No runners match" when `visible` is empty.
- [ ] **Step 3: Update the screenshot tests.** Render `AthletesView` from the new fixtures: top, scrolled to the inbox, filtered to Coached, the no-match empty state, dark mode, and VI. Run `TEST_RUNNER_SCREENSHOT_DIR=$PWD/docs/screenshots/athletes-workbench ios-native/scripts/test.sh -only-testing:UphillAITests/Phase6CoachScreenshots`.
- [ ] **Step 4: Inspect every PNG.** Fix truncation of the VI strings, Dynamic Type at XXXL, and contrast. Re-run until they're clean.
- [ ] **Step 5: Run the full suite** with `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** with the screenshots: `feat(ios-coach): Athletes triage screen`

---

## Phase 3: Runner detail and actions (PR 3)

### Task 9: Review and publish endpoints; a coach-built week counts as reviewed

**Files:**
- Modify: `backend/main.py`: add routes next to `/api/coaching/athletes/{athlete_id}/plans/draft` (~line 1673), and change `_generate_next_block_for_athlete` (~line 2461)
- Modify: `backend/db.py`: `mark_plan_reviewed`, `publish_plan`, `generated_block`
- Test: `backend/tests/integration/test_coach_review_publish.py`

**Interfaces:**
- Produces:
  - `db.generated_block(plan_id: int) -> int`. It returns the block of `MAX(week_number)`, using `week_range_for_block`'s formula, or 0 when there are no workouts.
  - `db.mark_plan_reviewed(plan_id: int, athlete_id: int, coach_id: int) -> dict | None`. It sets `coach_reviewed_block = generated_block(plan_id)` plus `_at`/`_by`, and returns None if the plan isn't this athlete's.
  - `db.publish_plan(plan_id: int, athlete_id: int, coach_id: int) -> dict | None`. In one transaction it sets `approved_at = NOW()` on every pending workout and calls `approve_plan` when the plan is a draft. It returns `{"plan_id", "plan_status", "approved_count"}`.
  - `GET /api/coaching/athletes/{id}/plans/{plan_id}/review` → `{generated_block, reviewed_block, reviewed_at, reviewed_by, issues: [{code, week, message}], feasibility, levers}`. `issues` comes from `plan_lint.lint_weeks` over the stored workouts, and `feasibility`/`levers` from `goal_feasibility.assess`. Copy the inputs from how `goal_service.py:~289` already calls `assess` on a stored plan.
  - `POST .../review` with body `{note: str | None}` → the `mark_plan_reviewed` result. When there's a note it calls the existing `db.create_coach_note(...)` with `target_type="plan"`, `target_id=plan_id`.
  - `POST .../publish` → the `publish_plan` result.
  - In `_generate_next_block_for_athlete`: when `job_owner_user_id != athlete_id` (a coach ran it), call `mark_plan_reviewed` after the workouts are saved.
- [ ] **Step 1: Write the failing tests:**
  - `test_review_marks_current_week_and_is_idempotent`: two POSTs give the same `coach_reviewed_block`.
  - `test_new_week_reopens_review`: after inserting week-2 workouts, `generated_block == 2 > reviewed_block`.
  - `test_publish_draft_activates_and_approves_all`.
  - `test_publish_active_approves_pending_rest_edit`.
  - `test_review_other_athletes_plan_404`.
  - `test_coach_next_block_counts_as_reviewed`. Call the db/save path the job uses directly, not the LLM.
- [ ] **Step 2: Run them.** `pytest tests/integration/test_coach_review_publish.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** Run again. Expected: PASS.
- [ ] **Step 4: Commit**: `feat(coach): per-week plan review and one-tap publish`

### Task 10: The coach can build a plan for an athlete and see drafts

**Files:**
- Modify: `ios-native/UphillAI/App/AppModel.swift`, `makeSetup` (~line 173)
- Modify: `ios-native/UphillAI/Features/Onboarding/PlanSetupViewModel.swift`: the `session.setUser` calls (~line 335 and the plan-submit path)
- Modify: `ios-native/UphillAI/Core/Plan/PlanService.swift:134`: when scoped, fall back to the draft plan
- Test: `ios-native/UphillAITests/Phase6/CoachBuildPlanTests.swift`

**Interfaces:**
- Produces: `AppModel.makeSetup(mode: .newPlan, athlete: User?)`.
  - With an athlete, it uses `generationService.scoped(toAthlete: athlete.id)` and `user: athlete`.
  - It passes `updatesSession: false` to `PlanSetupViewModel`, a new `init` parameter that defaults to `true`; when false, `session.setUser` is never called.
- Produces: the scoped `PlanService.activePlan()` returns the active plan, or else the draft from `"\(coachPrefix)/plans/draft"`. `Plan.planStatus` is `"draft"` in that case.
- [ ] **Step 1: Write the failing tests:**
  - `testCoachSetupNeverTouchesCoachSession`: run setup submit with stubbed generation for athlete 7. Afterwards the `session.user` id is still the coach's, and the request path is `/api/coaching/athletes/7/generate-plan` (Review Focus 2).
  - `testScopedActivePlanFallsBackToDraft`: the stub returns `{active:false}` for active-plan and a draft snapshot for `plans/draft`, so the snapshot's `planStatus == "draft"`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement.** Run again. Expected: PASS.
- [ ] **Step 4: Commit**: `feat(ios-coach): build a plan for an athlete; show coach drafts`

### Task 11: `CoachFocusCard` in the Plan tab

**Files:**
- Create: `ios-native/UphillAI/Features/Coaching/CoachFocusCard.swift`
- Create: `ios-native/UphillAI/Core/Coaching/PlanReviewModels.swift` (`PlanReview`, `PlanReviewIssue`, `PublishResult`), plus service methods in `CoachingService.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanView.swift`: insert directly after `raceGoalHeader` (~line 207); the build sheet reuses the `overlay = .setup(...)` route via a new `onBuildPlanForAthlete` closure from `RootView`
- Modify: `ios-native/UphillAI/App/RootView.swift:94-101`: pass `onBuildPlanForAthlete: { overlay = .setup(app.makeSetup(mode: .newPlan, athlete: app.coachedAthleteProfile)) }`
- Test: `ios-native/UphillAITests/Phase6/CoachFocusCardTests.swift`; screenshots in `Phase6CoachScreenshots.swift`

**Interfaces:**
- Consumes:
  - `CoachSignalText`, `primaryAction` (Task 7)
  - `AppModel.pendingCoachAction` (Task 8)
  - the review/publish endpoints (Task 9)
  - `makeSetup(athlete:)` (Task 10)
  - the existing `AdaptWeekSheet` (via `showAdapt`), `generateNextBlock` (scoped), `CoachedAthleteProfileView` and `addNote`
- Produces:
  - `CoachingServicing.planReview(athleteId:planId:) -> PlanReview`
  - `markReviewed(athleteId:planId:note:) -> PlanReview`
  - `publish(athleteId:planId:) -> PublishResult`
  - `CoachFocusCard(athlete: CoachOverviewAthlete, plan: Plan?, review: PlanReview?, latestNote: CoachNote?, onAction: (CoachAction) -> Void)`
  - The card gets the athlete's overview entry from `app.coachDashboard?.overview` by `actingAsAthlete.athleteId`.
  - The recovery figures come from the overview entry's `recovery` (Task 5). The row is hidden when `recovery` is null.
- [ ] **Step 1: Write the failing tests:**
  - `testCardActionsFollowSituation`: act_now shows Adapt; plan_to_review shows Mark reviewed and lists the issues in EN/VI via one sentence per `code` with a fallback to `message`; a draft shows Publish; needs_plan shows Build plan.
  - `testPendingActionConsumedOnce`: `pendingCoachAction = .adaptWeek` opens the adapt sheet once and is then cleared.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Build the card** with the `impeccable` and `taste-skill:minimalist-ui` skills, styled to match `CoachReviewCard` (the same card shell and caps labels), with the border tinted by status. Show it only while `app.actingAsAthlete != nil`.
  - **Mark reviewed** opens a short note field; on success it refreshes the overview cache.
  - **Publish** shows a confirmation dialog with the count, then reloads the plan.
  - A **⋯ menu** in the card header offers the plan-type switch, race history and remove.
- [ ] **Step 4: Add screenshots:** Minh (act_now), Huy (plan_to_review with issues), a draft with Publish, needs_plan; plus dark mode and VI. Inspect each PNG and fix what's wrong.
- [ ] **Step 5: Run the full suite** with `ios-native/scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** with the screenshots: `feat(ios-coach): coach card on the runner's plan`

### Task 12: End-to-end check

- [ ] **Step 1:** Run the backend tests: `cd backend && pytest tests/unit -q && pytest tests/integration -q`, with the scratch DB only.
- [ ] **Step 2:** Run the iOS tests: `ios-native/scripts/test.sh`.
- [ ] **Step 3:** On the local stack (`docker compose up -d`), sign in as the seeded coach in the simulator, go through Athletes → a runner → Mark reviewed / Publish / Adapt, and take screenshots of each step.
- [ ] **Step 4:** Run the `code-reviewer` agent over the branch diff, and `security-reviewer` over the new coach routes.

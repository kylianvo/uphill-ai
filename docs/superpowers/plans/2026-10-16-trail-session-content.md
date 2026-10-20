# Trail Session Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mountain-day sessions show believable time, km, D+, zone and trail pace from one formula, sized for the trip; sprint/interval structure shows on web and iOS; coach zone edits keep the plan's pace source.

**Architecture:** Two small pure modules (`services/trail_pace.py` for the formula, `services/training_mountains.py` for the curated mountain list) are wired into `PlanGenerator.post_process_workouts`, which already recomputes pace/distance/elevation for every generated workout. Two new plan columns hold the athlete's mountain choice and minimum; one new workout column holds the mountain mode (mountain/chill/skip). UI changes are thin: a mountain picker beside the existing `mountain_days` field and card labels.

**Tech Stack:** FastAPI + SQLAlchemy Core (`text()`), Alembic, pytest; Next.js 16 + vitest; SwiftUI + Swift Testing (xcodegen project).

**Spec:** `docs/superpowers/specs/2026-10-16-trail-session-content-design.md`

## Approved amendments during implementation

- Task 4 uses `--service scheduler`; the CLI has no `plan` service.
- Without a configured mountain minimum (Dalat/Sapa by default), keep generated duration capped at 300 and omit the prompt's minimum-time clause.
- Add HCMC's Núi Châu Thới (`chau_thoi`, 28 m D+/km, long runs allowed, 180-minute default); the catalog now has seven mountains.
- Task 4's three snapshot volume checks use a separate flat-equivalent metric while workout distances remain actual trail km. Golden fixtures start on a fixed Monday. The ME cutoff decision explicitly overrides the short-block instruction. Keep ME expectations unchanged.
- Task 5 persists the original climb rate in nullable `workouts.mountain_climb_rate` so skip → mountain/chill restores the original estimate without requiring a selected mountain. Update both schema definitions.
- Task 6 uses the shared `coros_workouts.py` mapper; `coros_push.py` delegates payload construction there.
- Push completed tasks as work progresses, as requested, rather than waiting until Task 12.
- Final review: ordinary coach edits without an explicit km + D+ pair retain climb rate and recalculate from duration/zone; an explicit pair takes priority (user approved).
- Final iOS verification uses a locally ad-hoc-signed simulator build and `test-without-building` so the existing Keychain test has its required entitlements (user approved); source/tests are unchanged for signing.
- Task 11 distinguishes omitted mountain fields from explicit null: "Other / none" clears the mountain, and Dalat/Sapa clears an old minimum (user approved). Both client creation flows and schedule request bodies must carry these fields.

## Global Constraints

- Branch: `claude/quangtranultra-plan-review-1a3cd3` (PR #142, held). Keep its iOS parser fix and its treadmill flat-pace fix.
- Trail formula: `trail_pace = flat_zone_pace × (1 + 0.012 × climb_rate)`, `km = minutes / trail_pace`, `D+ = km × climb_rate`. Constant `0.012`.
- Mountain data (m D+ per km): Núi Dinh 60, Núi Châu Thới 28 (user addition), Núi Chứa Chan 85, Núi Bà Đen 176 (repeats only), Núi Hàm Lợn 45, Dalat trails 47, Sapa trails 56.
- Mountain minimum: 180 min for HCMC and Hanoi mountains, none for Dalat/Sapa; editable per plan.
- Applies only to `Easy` and `Long Run`. Tempo/Interval keep zone paces. Treadmill settings always use the flat pace.
- Schema changes in both `backend/db.py:init_db()` and a hand-written Alembic migration (down_revision `c8e2a4f6d9b1`); follow `.claude/skills/db-migration/SKILL.md`.
- Prompt changes follow `.claude/skills/llm-change-process/SKILL.md` (Langfuse version, golden eval, staging → production label); checklist goes in the PR body.
- Any Vietnamese copy follows the `uphill-ai-vietnamese-copy` skill. UI changes need a local screenshot (`ui-screenshot-evidence`).
- Plan 108's rows are not touched.

## Review Focus

1. Athlete with mountain days but no mountain chosen and a race with no course D+ (Quang's plan 108 today) — must still get a trail pace, not road pace. *(Spec deviation, my call: last fallback is the AI's own elevation ÷ flat km as the climb rate, instead of the spec's "today's behaviour" which is road pace.)* Test in Task 3.
2. Home mountain is Bà Đen (repeats only) — a long run must use the area default (Núi Dinh 60), never 176. Test in Task 2.
3. Coach-set km + D+ session — a later week rebuild or adapt must not recompute it. Test in Task 6.
4. Hill sprint session on a mountain day — reps show without a pace; the Easy part gets the trail pace. Tests in Tasks 8 and 10.
5. Vietnamese step text with "thả lỏng" inside a recovery — stays in Main Set on web as on iOS. Test in Task 9.

---

### Task 1: Trail pace formula (replaces PR #142's km-effort rule)

**Files:**
- Create: `backend/services/trail_pace.py`
- Modify: `backend/services/plan_generator.py` (delete `CLIMB_ADJUSTED_TYPES`, `METERS_CLIMB_PER_EFFORT_KM`, `CLIMB_MIN_DISTANCE_FACTOR`, `adjust_pace_for_climbing`, and the block that calls it in `post_process_workouts`; keep `flat_pace` passed to `resolve_treadmill_settings`)
- Test: `backend/tests/unit/test_trail_pace.py`; delete `TestAdjustPaceForClimbing` from `backend/tests/unit/test_plan_generator_helpers.py`

**Interfaces:**
- Produces:
  - `TRAIL_CLIMB_FACTOR = 0.012`
  - `trail_pace_range(flat_pace: str, climb_rate: float) -> str` — `"4:54 - 4:30 /km"` → slowed range in the same format.
  - `trail_session(flat_pace: str, minutes: float, climb_rate: float) -> tuple[str, float, float]` — `(pace_str, distance_km, elevation_gain_m)`, km and D+ rounded to 0.1 / whole metres; km from the range midpoint.
  - `trail_minutes(flat_pace: str, distance_km: float, elevation_gain_m: float) -> float` — inverse, for coach km + D+ mode.

- [x] **Step 1: Write failing tests**

```python
def test_quang_example_flat_5_00_at_50_m_per_km_is_8_00():
    # a single pace stays a single pace
    assert trail_pace_range("5:00 /km", 50) == "8:00 /km"

def test_nui_dinh_3_5h_for_quang():
    pace, km, dplus = trail_session("4:54 - 4:30 /km", 210, 60)
    assert pace == "8:26 - 7:44 /km"
    assert 25.0 <= km <= 26.5
    assert dplus == round(km * 60)

def test_zero_climb_is_flat():
    assert trail_session("5:00 - 4:30 /km", 60, 0)[0] == "5:00 - 4:30 /km"

def test_minutes_round_trips_session():
    pace, km, dplus = trail_session("4:54 - 4:30 /km", 210, 60)
    assert abs(trail_minutes("4:54 - 4:30 /km", km, dplus) - 210) < 2
```

(4:54 × 1.72 = 8:26, 4:30 × 1.72 = 7:44; midpoint 8:05 → 210 / 8.08 ≈ 26.0 km.)

- [x] **Step 2: Run** `cd backend && .venv/bin/pytest tests/unit/test_trail_pace.py -q` — expected FAIL (module missing).
- [x] **Step 3: Implement** using `PlanGenerator.parse_pace_range` / `decimal_to_pace_str`. Remove the PR #142 climb code and its tests.
- [x] **Step 4: Run** `.venv/bin/pytest tests/unit -q` — expected all pass.
- [x] **Step 5: Commit** `feat: trail pace formula from Quang's flat→trail rule`

### Task 2: Training mountains list

**Files:**
- Create: `backend/services/training_mountains.py`
- Test: `backend/tests/unit/test_training_mountains.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Mountain: key: str; area: str; name_en: str; name_vi: str; climb_rate: float; repeats_only: bool; default_min_minutes: int | None`
  - `MOUNTAINS: dict[str, Mountain]` with keys `nui_dinh`, `chau_thoi`, `chua_chan`, `ba_den`, `ham_lon`, `dalat`, `sapa`; areas `hcmc`, `hanoi`, `dalat`, `sapa`.
  - `long_run_climb_rate(key: str | None) -> float | None` — repeats-only mountains return their area's default long-run mountain rate; unknown/None → None.
  - `default_min_minutes(key: str | None) -> int | None` — 180 for hcmc/hanoi, None otherwise.

- [x] **Step 1: Tests:** `long_run_climb_rate("nui_dinh") == 60`; `long_run_climb_rate("ba_den") == 60`; `long_run_climb_rate("ham_lon") == 45`; `long_run_climb_rate(None) is None`; `default_min_minutes("ham_lon") == 180`; `default_min_minutes("sapa") is None`.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement** with the Global Constraints values; one comment line naming the sources (spec B1).
- [x] **Step 4: Run** — PASS.
- [x] **Step 5: Commit** `feat: curated training mountains`

### Task 3: Plan columns + mountain-day wiring in post-processing

**Files:**
- Modify: `backend/db.py` (plans table: `training_mountain TEXT`, `mountain_min_minutes INTEGER`; workouts table: `mountain_mode TEXT` — values `mountain|chill|skip|indoor|NULL`; idempotent ALTERs in `init_db()`)
- Create: `backend/alembic/versions/<rev>_trail_mountain_fields.py` (down_revision `c8e2a4f6d9b1`)
- Modify: `backend/main.py` request models that carry `mountain_days` (lines ~246, 318, 342, 495) and the persist/return sites (~1290, 1320, 2148, 2180, 2490, 2505, 2734) to carry `training_mountain` and `mountain_min_minutes`
- Modify: `backend/services/training_venues.py` — `Venues.training_mountain: str | None`, `Venues.mountain_min_minutes: int | None`, read in `from_race_info`; `Venues.is_mountain_day(day: str) -> bool`
- Modify: `backend/services/plan_generator.py` `post_process_workouts`
- Test: `backend/tests/unit/test_plan_generator_helpers.py` (new class `TestMountainDaySessions`), `backend/tests/unit/test_training_venues.py`

**Interfaces:**
- Consumes: `trail_session` (Task 1), `long_run_climb_rate`, `default_min_minutes` (Task 2).
- Produces: `PlanGenerator.resolve_climb_rate(venues: Venues, course_elevation_gain_m: float | None, course_distance_km: float | None, ai_elevation_m: float | None, flat_distance_km: float) -> float | None` — order: mountain rate → course D+/km → AI elevation ÷ flat km (Review Focus 1) → None.

Rules in `post_process_workouts` for `type in ("Easy", "Long Run")` and trail terrain:
- climb rate from `resolve_climb_rate`; if not None → `target_pace, distance_km, elevation_gain_m = trail_session(flat_pace, dur, rate)` and `grade_percent = elevation_gain_m / (distance_km * 10)`; AI elevation is ignored when a mountain or course rate exists.
- `Long Run` on `venues.is_mountain_day(day)` with `mountain_mode` not set by Task 5 → `dur = min(max(dur, min_minutes), 300)` (300 = the HCMC bus window ceiling, my call) where `min_minutes = venues.mountain_min_minutes or default_min_minutes(venues.training_mountain)`; set `mountain_mode = "mountain"`.
- Treadmill still gets `flat_pace`.

- [x] **Step 1: Tests:** (a) Núi Dinh Long Run 130 min on Saturday mountain day → `duration_minutes == 180`, pace slowed ×1.72, D+ ≈ km × 60; (b) no mountain, course D+ None, AI elevation 850 on 130 min → pace is a trail pace (slower than flat); (c) Saturday not a mountain day → duration unchanged; (d) treadmill speed for a mountain-day Long Run equals the speed computed from the flat pace; (e) migration round-trip per db-migration skill.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement** schema (both places), API fields, `Venues` fields, `resolve_climb_rate`, post-process rules.
- [x] **Step 4: Run** `.venv/bin/pytest tests/unit -q` and `.venv/bin/alembic upgrade head` against a scratch DB (never the integration-test DB in use) — PASS.
- [x] **Step 5: Commit** `feat: mountain-day sessions sized from training mountain`

### Task 4: Prompt rule for mountain days (LLM change process)

**Files:**
- Modify: `backend/services/training_venues.py` `prompt_block` — add one MOUNTAIN DAY rule line: Long Run on mountain days lasts at least `{min} min` at `{mountain name}` (~`{rate}` m D+/km); recovery week / Taper → keep the time at Zone 1, mostly power-hiking; Race Week or beginner tier → a short road/treadmill session instead.
- Test: `backend/tests/unit/test_training_venues.py`

**Interfaces:**
- Consumes: `Venues.training_mountain`, `MOUNTAINS`, `default_min_minutes`.

- [x] **Step 1: Test** that `prompt_block` for Núi Dinh + Saturday mountain day contains `"180 min"`, `"Núi Dinh"`, `"60 m D+/km"`, `"Zone 1"`; and contains none of them when `training_mountain` is None.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** unit tests — PASS; then run the llm-change-process checklist: `python scripts/golden_eval.py capture --service scheduler` on main, `compare --service scheduler` on this branch; push the Langfuse prompt version only if the plan prompt template itself changed (the rule is injected via the existing `equipment_terrain_rule` variable).
- [x] **Step 5: Commit** `feat: mountain-day rule in plan prompt`

### Task 5: Chill / skip by phase, indoor fallback, athlete switch

**Files:**
- Modify: `backend/services/plan_generator.py` `post_process_workouts`
- Modify: `backend/main.py` — new `PATCH /api/workouts/{workout_id}/mountain-mode` body `{"mode": "mountain" | "chill" | "skip" | "indoor"}`, owner or coach only (same auth check as the existing workout update route)
- Modify: `backend/db.py` — `update_workout_mountain_mode(workout_id: int, fields: dict) -> None` (parameterized `text()`)
- Test: `backend/tests/unit/test_plan_generator_helpers.py`, `backend/tests/unit/test_mountain_mode_route.py`

**Interfaces:**
- Produces: `PlanGenerator.apply_mountain_mode(wo: dict, mode: str, venues: Venues, est_zones: dict, flat_pace: str) -> dict`
  - `mountain`: Task 3 sizing.
  - `chill`: duration = mountain minimum, `target_zone = "Zone 1"`, Zone 1 HR range, trail pace from Zone 1 flat pace.
  - `skip`: 60 min (my call) Zone 2 city session, flat pace, `elevation_gain_m = 0`, `grade_percent = 0`.
  - `indoor`: 120 min. If `venues.use_treadmill`: incline = `min(mountain grade %, venues.treadmill_incline_cap)` (mountain grade % = `long_run_climb_rate / 10`), speed from the flat Zone 2 pace via `TrainingRules.calculate_treadmill_settings`, `distance_km = speed × 2`, `elevation_gain_m = distance_km × incline × 10`. Else if `venues.stair_access`: stairs climbing session, Zone 2, no pace, `elevation_gain_m = 0`. Else same as `skip`. Athlete-only mode (never chosen by the phase rule).
- Phase decision in post-process for mountain-day Long Runs: phase `Recovery` or `Taper` → `chill`; phase `Race Week` or tier `beginner` → `skip`; else `mountain`.

- [x] **Step 1: Tests:** Taper week → `mountain_mode == "chill"`, `target_zone == "Zone 1"`, 180 min; Race Week → `skip`, 0 elevation, flat pace; beginner tier Build week → `skip`; route switches chill→skip and leaves other workouts in the week unchanged; `indoor` with treadmill (max 15%) on Núi Dinh → 120 min, incline 6%, distance = speed × 2, D+ = km × 6 × 10; `indoor` with no treadmill but stairs → stairs session; with neither → equals `skip`.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** — PASS.
- [x] **Step 5: Commit** `feat: chill/skip mountain mode by phase with athlete switch`

### Task 6: Coach km + D+ mode

**Files:**
- Modify: `backend/main.py` `CoachWorkoutUpdateRequest` and its handler (around line 1687): when `distance_km` and `elevation_gain_m` are both set on an Easy/Long Run trail session, compute `duration_minutes = trail_minutes(flat_zone_pace, km, dplus)`, keep the coach's km and D+, set `source = "coach"` (check the value the handler already writes and reuse it).
- Modify: `backend/services/plan_generator.py` / `backend/services/week_rebuild.py` — rows with the coach source are never recomputed (they are history to the rebuild already if `_is_history`; verify and add the check where post-processing would touch them).
- Modify: `backend/services/coros_workouts.py` — a coach-set trail session pushes a distance target; others keep time.
- Test: `backend/tests/unit/test_coach_trail_mode.py`

**Interfaces:**
- Consumes: `trail_minutes` (Task 1).

- [x] **Step 1: Tests:** coach sets 26 km / 1500 m for Quang's zones → duration ≈ 210 min, km and D+ unchanged after a week rebuild draft is applied; COROS section built with a distance target for that workout.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** — PASS.
- [x] **Step 5: Commit** `feat: coach sets trail sessions by km + D+`

### Task 7: Coach zone edit uses the plan's pace source (gap A1)

**Files:**
- Modify: `backend/main.py:584` `_resolve_zone_pace_and_hr` — use `PlanGenerator.resolve_pace_zones({**athlete, "aet_hr": aet_hr, "ant_hr": ant_hr}, athlete.get("goal_type"))` like `_generate_single_workout`.
- Test: `backend/tests/unit/test_coach_zone_edit.py`

- [x] **Step 1: Test:** athlete with threshold 3:55, AeT 134, AnT 163 and default Zone 2 fields 6:30/5:45 → Zone 2 edit returns the same pace as `resolve_pace_zones(...)["zone2_pace"]` (≈ 4:54 - 4:30), not 6:30 - 5:45.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** — PASS.
- [x] **Step 5: Commit** `fix: coach zone edits use the plan's pace zones`

### Task 8: Rep fields parsed from the description (gap A3)

**Files:**
- Create: `backend/services/rep_parser.py`
- Modify: `backend/services/plan_generator.py` `resolve_interval_summary` — when AI fields are invalid, fall back to `parse_rep_block(description_process)`; allow any run type (not Rest/Strength/ME).
- Test: `backend/tests/unit/test_rep_parser.py`

**Interfaces:**
- Produces: `parse_rep_block(text: str) -> tuple[int, float, str] | None` — unit in `s|m|min|km`; returns None when the text has zero or more than one distinct rep block.

- [x] **Step 1: Tests** (real prod strings): `"8 x 12s hill sprints"` → `(8, 12, "s")`; `"6 reps of 10s maximum-effort"` → `(6, 10, "s")`; `"9 x 12-second maximum effort"` → `(9, 12, "s")`; `"3 x 10 min at threshold"` → `(3, 10, "min")`; `"5 x 400m"` → `(5, 400, "m")`; `"4 x 1.5 km"` → `(4, 1.5, "km")`; `"3 x 5 phút"` → `(3, 5, "min")`; `"8 x 10s Hill Sprints dốc >20%"` → `(8, 10, "s")`; `"4x10 mỗi chân"` → None; two different blocks → None.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** `.venv/bin/pytest tests/unit -q` — PASS.
- [x] **Step 5: Commit** `feat: derive rep fields from session text`

### Task 9: Web — Vietnamese step cues, rep chip, trail card labels

**Files:**
- Modify: `frontend/src/utils/workoutDescription.ts` `parseExecutionSteps` — warm-up also on leading `khởi động`; cool-down also on leading `thả lỏng` / `hạ nhiệt` (lead-of-step only).
- Modify: `frontend/src/components/WorkoutCard.tsx` — rep chip for any type with rep fields; no pace after reps when zone is Zone 5 or title has a hill-sprint/strides keyword; trail sessions (elevation > 0) label pace as trail pace and show est. km and est. D+ beside duration and zone.
- Modify: `frontend/src/app/translations.ts` — new keys `trailPace`, `estElevation` (VI via the Vietnamese copy skill).
- Test: `frontend/src/utils/workoutDescription.test.ts`, `frontend/src/components/WorkoutCard.test.tsx`

- [x] **Step 1: Tests:** Quang's Process string → main steps include the Hill Sprints step, cool-down starts with "Hạ nhiệt"; Easy workout with `interval_reps 8, value 10, unit s` renders chip `8x10s`; trail Long Run renders the trail-pace label and D+.
- [x] **Step 2: Run** `cd frontend && npx vitest run src/utils/workoutDescription.test.ts src/components/WorkoutCard.test.tsx` — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** vitest, `npm run lint`, `npx tsc --noEmit` — PASS; screenshot the card locally per `ui-screenshot-evidence`.
- [x] **Step 5: Commit** `feat(web): trail card labels, rep chip, Vietnamese step cues`

### Task 10: iOS — rep detection, values, trail card labels

**Files:**
- Modify: `ios-native/UphillAI/Core/Plan/WorkoutStepParser.swift` — `detectReps` scans every main step and matches seconds (`s`, `-second`, `giây`), minutes (`min`, `phút`), distance (`m`, `km`) and `N reps of Ns`; rep values formatted without truncation (match web `fmtRepValue`); no pace after reps for Zone 5 / hill-sprint / strides.
- Modify: the workout detail view that renders duration/distance/pace chips (find via `PACE (/KM)` label) — trail sessions label pace as trail pace and show est. D+.
- Test: `ios-native/UphillAITests/Plan/WorkoutStepParserTests.swift`

- [x] **Step 1: Tests:** Quang's session → main target `"8 × 10 s"` with no pace; `intervalRepValue 0.4, unit km` → `"5 × 0.4 km"`; `"3 x 5 phút"` detected; existing 13 tests still pass.
- [x] **Step 2: Run** `cd ios-native && xcodegen generate && xcodebuild test -project UphillAI.xcodeproj -scheme UphillAI -destination 'id=C61BEDF9-6807-47A8-8225-34A09EE1CF81' -only-testing:UphillAITests/WorkoutStepParserTests CODE_SIGNING_ALLOWED=NO` — FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** — `** TEST SUCCEEDED **`; simulator screenshot of the detail screen.
- [x] **Step 5: Commit** `feat(ios): rep detection for seconds/distance/VI, trail card labels`

### Task 11: Mountain picker (web + iOS)

**Files:**
- Modify: `frontend/src/components/TrainingVenueFields.tsx`, `frontend/src/types/index.ts`, `frontend/src/hooks/usePlanner.ts`, `frontend/src/components/ScheduleFieldsEditor.tsx` — select from `MOUNTAINS` keys (names + D+/km), "Other / none", and a minimum-minutes number field defaulting from the mountain.
- Modify: `ios-native/UphillAI/Features/Plan/TrainingVenueSection.swift`, `ios-native/UphillAI/Core/Plan/ScheduleDraft.swift`, `ios-native/UphillAI/Core/Plan/PlanSetupDraft.swift`, plan model — same two fields, sent only when changed (same pattern as `mountainDays`).
- Modify: `backend/main.py` — `GET /api/training-mountains` returns `MOUNTAINS` (key, area, names, climb_rate, repeats_only, default_min_minutes) so both clients read one list.
- Test: `frontend/src/components/TrainingVenueFields.test.tsx` (create if absent), iOS `ScheduleDraft` test, backend route test.

- [x] **Step 1: Tests:** web select saves `training_mountain: "nui_dinh"`, min field shows 180; iOS draft diff includes `trainingMountain` only when changed; route returns 7 mountains.
- [x] **Step 2: Run** — FAIL.
- [x] **Step 3: Implement.** Mountain names in VI via the Vietnamese copy skill.
- [x] **Step 4: Run** all three suites — PASS; screenshots on web and simulator.
- [x] **Step 5: Commit** `feat: training mountain picker in schedule preferences`

### Task 12: Finish the branch

- [x] **Step 1:** `cd backend && .venv/bin/pytest tests/unit -q`; `cd frontend && npx vitest run && npm run lint`; iOS full `UphillAITests` — all pass.
- [x] **Step 2:** Update PR #142 title/body: scope is now the full design; include the llm-change-process checklist, screenshots, and "plan 108 rows untouched".
- [x] **Step 3:** Push. Deploy and TestFlight are separate, user-approved steps.


Final verification (2026-10-17): backend 1,413 tests passed; frontend 530 passed, lint 0 errors (127 existing warnings), TypeScript passed; iOS 505 tests in 77 suites passed. iOS used the approved local ad-hoc `build-for-testing CODE_SIGNING_ALLOWED=YES CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY=-`, then full `test-without-building ... CODE_SIGNING_ALLOWED=NO`, because the unsigned build lacks simulator Keychain entitlements. No signing source/test changes were committed.

The fresh whole-branch review's three P2 findings are closed with RED→GREEN regressions: normal coach edits preserve trail calculations, Easy rep fields survive ordinary edits, and aerobic trail pace remains visible separately from sprint reps. Screenshots are in `docs/evidence/trail-session-content/`; PR #142 contains the LLM checklist, test results, complete deviation list and plan/spec rulings. Synthetic UI rows were removed from the scratch DB. Plan 108 rows untouched; no merge, deploy, TestFlight release or production prompt promotion.

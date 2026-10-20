# Goal-Reliable Plans, Part 1: Demands, Feasibility, Scorecard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each generated plan carry the goal's physical demands, an honest feasibility verdict, and a CI scorecard that backs the "reliable" claim. No schema change.

**Architecture:** Three pure modules (`goal_demands`, `goal_feasibility`, new lint codes in `plan_lint`) sit beside the existing `race_readiness` / `plan_adequacy`. The generator receives a short demand block instead of the one-line goal. `goal_service` returns the verdict with the plan goal and the Goal pill shows it. A script runs a fixed scenario matrix and a unit test pins its thresholds.

**Tech Stack:** Python 3.11 (FastAPI backend, pytest), Next.js/TypeScript frontend (vitest), existing `PacingCalculator`, `RaceEstimator.synthesize_course`, `athlete_tier.TierProfile`.

**Spec:** `docs/superpowers/specs/2026-10-20-goal-reliable-plans-design.md` (sections 1, 2, 3, 6). Tracking and the A gate (sections 4, 5) are Part 2, which needs a table.

**Precondition:** PR #154 (the combined stack) is merged to `main`. Branch every task from `main` after that. If it is not merged, stop and ask.

## Vietnamese runner cases (#142), owner note 2026-10-20

Most of our athletes train on flat city ground and reach hills only on set mountain days (`plans.mountain_days`, `training_mountain`, `mountain_min_minutes`; catalog `services/training_mountains.py`: Châu Thới 28, Núi Dinh 60, Chứa Chan 85, Bà Đen 176 repeats-only → 60, Hàm Lợn 45, Dalat 47, Sapa 56 m D+/km). Mountain Long Runs have a minimum (180 min HCMC/Hanoi; the owner kept it after illness/pain). Modes: mountain / chill / skip (60 min) / indoor (120 min). Consequences, all ruled here:
- `Demands` gains `venue_climb_rate: float | None` (from `long_run_climb_rate(training_mountain)`); `compute(..., venue_climb_rate=None)`.
- `LONG_RUN_GRADIENT` judges the plan's long runs against `min(required climb rate, venue rate)` and reads `mountain_climb_rate` when present. A venue that cannot reach 60% of the required rate is not a plan defect: it is a feasibility lever (`steeper_venue`), verdict at most `stretch`.
- Feasibility: `mountain_min_minutes` forces the long run to at least that many minutes; if `min / long_run_share_cap` exceeds the week's capacity, add lever `fewer_mountain_minimum` and mark `unsupported` only when the race needs it and capacity cannot hold it. Skip/indoor sessions count at their set durations.
- Flat-only athletes (no `training_mountain`, no `local_hills`): required climbing is met by treadmill incline or stairs; lever `mountain_access` when the course steepness exceeds 25 m D+/km.
- Vietnamese copy for every new string.

## Global Constraints

- Python 3.11 only: no same-quote nested f-strings. Before every push, `ast.parse` all backend files in `python:3.11-slim`.
- Raw SQL only, no ORM. This part adds no tables or columns.
- Bilingual: every new user-facing string has EN and VI in the same commit, following the `uphill-ai-vietnamese-copy` skill (keep `Pace`, `Long Run`, `Zone 2`, `D+` in English; never use `thể tích`; max 3 words on chips).
- Frontend changes need a real screenshot of the running UI before being called done (`ui-screenshot-evidence` skill).
- Lint caps stay as in `plan_lint.py`: `MAX_SESSION_MIN = 300`; tier weekday and long-run share caps come from `athlete_tier.TierProfile`.
- Book benchmarks stay as in `race_readiness.RACE_CLASSES` (50K peak 80–88 km, 100K 120–130, 100 miles 145–160); do not duplicate them.
- Flags default on, tests off: new behavior is gated by `PLAN_DEMANDS_ENABLED` (config.py, default `true`; `tests/conftest.py` sets it false, like `PLAN_LINT_ENABLED`).
- Prompt wording changes require the golden scheduler eval before and after: `python scripts/golden_eval.py capture|compare --service scheduler`.
- Integration tests TRUNCATE the DB: run them only against a scratch Postgres.

## Review Focus

- Race with no target time (finish goal): demands must fall back to the cutoff-safe pace, not divide by zero.
- No course elevation or distance: no demand block, no verdict (returns `None`), generation unchanged.
- Athlete with no stored Zone 2 pace: tier default pace; the verdict's confidence says "estimated".
- Days per week unset: capacity assumes the tier default days, not 7.
- Weeks to race fewer than the minimum needed to reach the floor: verdict `unsupported` with a "more weeks" lever, not an exception.
- Goal already below current fitness (athlete is faster than B needs): no improvement required, verdict `supported`.
- Scorecard must never call Gemini (CI cost): recorded responses or the rule-based path only.

---

## File Structure

- Create `backend/services/goal_demands.py`: pure; goal + course -> `Demands`.
- Create `backend/services/goal_feasibility.py`: pure; `Demands` + athlete capacity -> `Feasibility`.
- Modify `backend/services/plan_lint.py`: three new codes; `Prefs` gains an optional `demands`.
- Modify `backend/services/plan_generator.py` (~815, ~1156, ~1198): build demands once, pass to prompt, lint and fallback.
- Modify `backend/services/goal_service.py` (`plan_goal`, `with_plan_support`): attach `feasibility`.
- Modify `backend/config.py`, `backend/tests/conftest.py`, `CLAUDE.md`: the flag.
- Modify `frontend/src/lib/goalAssessment.ts`, `frontend/src/components/GoalPill.tsx`: show the verdict, EN/VI.
- Create `backend/scripts/plan_reliability.py` and `backend/tests/unit/test_plan_reliability.py`.
- Tests: `backend/tests/unit/test_goal_demands.py`, `test_goal_feasibility.py`, additions to `test_plan_lint.py`.

---

### Task 1: Goal demands

**Files:**
- Create: `backend/services/goal_demands.py`
- Test: `backend/tests/unit/test_goal_demands.py`

**Interfaces:**
- Consumes: `PacingCalculator.solve_base_pace(checkpoints, target_time_mins) -> float` (flat min/km), `RaceEstimator.synthesize_course(distance_km, elevation_gain_m) -> list[dict]`, `race_readiness.race_class(distance_km) -> tuple[str, float, float, float]` (label, avg km, peak lo, peak hi).
- Produces:
  - `@dataclass(frozen=True) class Demands` with fields: `target_time_min: float`, `source: str` (`"target" | "cutoff_safe" | "estimated"`), `required_flat_pace_min_km: float`, `climb_rate_m_per_h: float`, `steepness_m_per_km: float`, `time_on_feet_min: float`, `longest_session_min: float`, `peak_week_km_lo: float`, `peak_week_km_hi: float`, `race_class: str`.
  - `def compute(distance_km: float | None, gain_m: float | None, target_time_h: float | None, cutoff_h: float | None, checkpoints: list[dict[str, Any]] | None = None) -> Demands | None`.
  - `def prompt_block(d: Demands, lang: str) -> str` (3–5 short lines for the generator).

- [ ] **Step 1: Write the failing tests** in `test_goal_demands.py`:
  - `test_vht_100k_target_demands`: `compute(104.2, 5533, 14.67, 29)` has `source == "target"`, `race_class == "100K"`, `steepness_m_per_km` within 0.1 of 53.1, `climb_rate_m_per_h` within 1% of `5533 / 14.67`, `time_on_feet_min == 14.67 * 60`.
  - `test_longest_session_is_capped`: `longest_session_min <= 300` for the 100K case.
  - `test_finish_goal_uses_cutoff_safe_time`: `compute(56.4, 2946, None, 12)` has `source == "cutoff_safe"` and `target_time_min == 12 * 60 * 0.85` (the 85% rule already used in `plan_generator` ~1150).
  - `test_no_course_returns_none`: `compute(None, 2946, 14, 29) is None` and `compute(104.2, None, 14, 29)` is not None with `climb_rate_m_per_h == 0`.
  - `test_pace_matches_solver`: required pace equals `PacingCalculator.solve_base_pace(synthesize_course(...), target_min)`.
- [ ] **Step 2: Run to verify they fail.** Run: `cd backend && python3 -m pytest tests/unit/test_goal_demands.py -q`. Expected: FAIL, module not found.
- [ ] **Step 3: Implement `compute` and `prompt_block`** in `goal_demands.py`. `longest_session_min = min(300, 0.40 * time_on_feet_min)` (call this out as a named constant `LONGEST_SESSION_SHARE = 0.40`, my call; the book gives 4–5 h as the upper bound). Time source order: `target_time_h` if given, else `cutoff_h * 0.85`, else `None` result.
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(goal): derive the goal's physical demands`.

### Task 2: Feasibility verdict

**Files:**
- Create: `backend/services/goal_feasibility.py`
- Test: `backend/tests/unit/test_goal_feasibility.py`

**Interfaces:**
- Consumes: `goal_demands.Demands`; `athlete_tier.TierProfile` (`weekday_minutes: tuple[int,int]`, `long_run_share_cap: float`); `race_readiness.max_reachable(v, steps, builds_so_far, max_prog) -> float`.
- Produces:
  - `def week_capacity_minutes(profile: TierProfile, days_per_week: int | None) -> float`: `(n-1)*weekday_max + min(300, cap/(1-cap)*(n-1)*weekday_max)`; `n` defaults to 5 when `None` (my call).
  - `@dataclass(frozen=True) class Feasibility`: `verdict: str` (`"supported" | "stretch" | "unsupported"`), `capacity_h: float`, `needed_h: float`, `weeks_needed: int | None`, `levers: tuple[str, ...]` (codes: `more_days`, `more_weeks`, `shorter_race`, `finish_only`), `confidence: str` (`"measured" | "estimated"`).
  - `def assess(demands: Demands | None, profile: TierProfile, days_per_week: int | None, flat_pace_min_km: float, current_weekly_km: float, weeks_to_race: float | None, pace_is_estimated: bool) -> Feasibility | None`.

- [ ] **Step 1: Write the failing tests**:
  - `test_capacity_matches_tier_caps`: recreational (weekday max 75, share 0.33): `week_capacity_minutes(p, 3)` within 2 min of 222 (3.7 h); 4 days within 2 of 336; 6 days within 2 of 558.
  - `test_three_day_100k_is_unsupported`: 100K demands, 3 days -> `verdict == "unsupported"`, `"more_days" in levers`.
  - `test_six_day_100k_is_supported_with_runway`: 6 days, 26 weeks, current 60 km -> `supported`.
  - `test_not_enough_weeks_is_unsupported_with_more_weeks_lever`: 6 days, 4 weeks, current 30 km -> `unsupported`, `"more_weeks" in levers`, `weeks_needed > 4`.
  - `test_stretch_when_only_capacity_binds_slightly`: needed within 10% above capacity -> `stretch`.
  - `test_none_inputs`: `assess(None, ...) is None`.
  - `test_estimated_pace_marks_confidence`: `pace_is_estimated=True` -> `confidence == "estimated"`.
- [ ] **Step 2: Run to verify they fail.** Expected: FAIL, module not found.
- [ ] **Step 3: Implement.** `needed_h = demands.peak_week_km_lo * flat_pace_min_km / 60` (flat-equivalent km times flat pace). Verdict: `unsupported` if `needed_h > capacity_h * 1.10` or the peak is unreachable in `weeks_to_race` via `max_reachable` at the tier's weekly progression; `stretch` if `needed_h > capacity_h` or reachability slack under 1 week; else `supported`. Constants `STRETCH_MARGIN = 0.10` named at module top.
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Commit** `feat(goal): feasibility verdict from weekly capacity and runway`.

### Task 3: Specificity lint codes

**Files:**
- Modify: `backend/services/plan_lint.py` (`Prefs`, `lint_weeks`)
- Test: `backend/tests/unit/test_plan_lint.py`

**Interfaces:**
- Consumes: `goal_demands.Demands`.
- Produces: `Prefs.demands: Demands | None = None`; `lint_weeks` emits `LONG_RUN_GRADIENT`, `TIME_ON_FEET`, `SPECIFICITY_LATE` (plan-level, attached to the last build week) only when `prefs.demands` is set.

- [ ] **Step 1: Write the failing tests** (build workouts with the existing helper in the file):
  - `test_time_on_feet_flags_short_longest_session`: 100K demands, longest session in the plan 120 min -> issue `TIME_ON_FEET`; plan whose Peak-phase long run is `demands.longest_session_min` -> no issue.
  - `test_long_run_gradient_flags_flat_long_runs`: trail 100K with every long run `elevation_gain_m` 0 -> `LONG_RUN_GRADIENT`; long runs carrying at least 60% of `steepness_m_per_km` over their duration -> none.
  - `test_specificity_late`: no Zone 3/4 or hill work in the last 4 build weeks -> `SPECIFICITY_LATE`.
  - `test_no_demands_no_new_codes`: `Prefs()` -> none of the three.
- [ ] **Step 2: Run to verify they fail.** Expected: FAIL.
- [ ] **Step 3: Implement** in `plan_lint.py`: `TIME_ON_FEET` compares the maximum session minutes in Peak/Build weeks to `0.90 * demands.longest_session_min` (constant `TIME_ON_FEET_SHARE = 0.90`); `LONG_RUN_GRADIENT` compares each Long Run's `elevation_gain_m / (duration/60)` to `0.60 * demands.climb_rate_m_per_h` in the last half of the build (`GRADIENT_SHARE = 0.60`); `SPECIFICITY_LATE` checks the final four non-taper weeks for any hard or hill session. All three are warnings that feed the existing corrective retry; they never block.
- [ ] **Step 4: Run** `python3 -m pytest tests/unit/test_plan_lint.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(lint): specificity checks against the goal's demands`.

### Task 4: Goal-shaped generation

**Files:**
- Modify: `backend/services/plan_generator.py` (~815–823 pace, ~1156–1162 goal sentence, `_lint_issues`, rule-based builder)
- Modify: `backend/config.py`, `backend/tests/conftest.py`, `CLAUDE.md`
- Test: `backend/tests/unit/test_plan_generator_helpers.py`

**Interfaces:**
- Consumes: `goal_demands.compute / prompt_block`; `plan_lint.Prefs(demands=...)`.
- Produces: `settings.PLAN_DEMANDS_ENABLED: bool`; the generation prompt contains `prompt_block(...)` in place of `Goal: Finish in XhYY.` when demands exist; `Prefs` passed to lint carries `demands`; the fallback sets its Peak-phase long-run target to `demands.longest_session_min` (still within tier caps via `week_layout`) and puts the required climbing rate on trail long runs.

- [ ] **Step 1: Write the failing tests**:
  - `test_prompt_contains_demand_block`: capture the prompt (the existing tests stub the Gemini call; reuse that stub) for the VHT 100K; assert it contains the required climb rate and the longest-session minutes and no longer contains the bare `Goal: Finish in`.
  - `test_flag_off_keeps_old_sentence`: `PLAN_DEMANDS_ENABLED=False` -> old text.
  - `test_fallback_peak_long_run_reaches_target`: rule-based 100K for a 6-day sub_elite athlete -> longest session in Peak is at least `0.90 * demands.longest_session_min` and no hard lint codes (reuse `HARD_RULES` from the doctrine test).
  - `test_fallback_trail_long_run_has_gradient`: trail long runs in the last half of the build carry gain.
- [ ] **Step 2: Run to verify they fail.** Expected: FAIL.
- [ ] **Step 3: Implement.** Compute `demands` once in `generate_plan_workouts` (inputs from `race_info`: distance, gain, `target_time_hours`, `cutoff_hours`); keep the existing Zone 4 race-pace behavior untouched. Add the flag in `config.py` next to `PLAN_LINT_ENABLED` and document it in `CLAUDE.md`. This changes prompt text: run the golden scheduler eval before and after (`capture` on `main`, `compare` after) and note the diff in the PR; if the `plan_generation` Langfuse template renders the goal from a variable, bump the template version on staging first, otherwise no template change.
- [ ] **Step 4: Run** `python3 -m pytest tests/unit -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(plan): shape generation by the goal's demands`.

### Task 5: Verdict in the API and the Goal pill

**Files:**
- Modify: `backend/services/goal_service.py` (`plan_goal`, `with_plan_support`), `backend/main.py` only if the payload is built there
- Modify: `frontend/src/lib/goalAssessment.ts`, `frontend/src/components/GoalPill.tsx`
- Test: `backend/tests/integration/test_goal_assessment_api.py` (extend), `frontend/src/lib/goalAssessment.test.ts`

**Interfaces:**
- Consumes: `goal_feasibility.assess`; plan fields `days_per_week`, `target_time_hours`, race distance/gain, `start_date`.
- Produces: `plan_goal(plan)` response gains `feasibility: {verdict, capacity_h, needed_h, weeks_needed, levers, confidence} | null`; frontend `feasibilityNotice(feasibility, lang): string | null` returning one short sentence (EN/VI), `null` for `supported`.

- [ ] **Step 1: Write the failing tests**: integration — a plan with 3 days/week and a 100K race returns `feasibility.verdict == "unsupported"` with `more_days` in levers; a 6-day plan returns `supported`; a plan without distance returns `feasibility == null`. Frontend — `feasibilityNotice` returns EN and VI strings for `unsupported` and `stretch`, `null` for `supported`, and no VI string contains `thể tích`.
- [ ] **Step 2: Run to verify they fail.** Backend integration against the scratch DB; `cd frontend && npx vitest run src/lib/goalAssessment.test.ts`. Expected: FAIL.
- [ ] **Step 3: Implement** the payload and the pill notice under the existing plan-support notice (same placement and style). VI copy follows the copy skill; EN: "3 days a week can hold about 3.7 h; this race needs about 11 h." with the first lever appended.
- [ ] **Step 4: Run** the new tests, `npx tsc --noEmit`, `npm run lint`. Expected: PASS.
- [ ] **Step 5: Screenshot** the pill in `unsupported` and `supported` states per the `ui-screenshot-evidence` skill and attach to the PR.
- [ ] **Step 6: Commit** `feat(goal): show feasibility on the plan goal`.

### Task 6: Reliability scorecard

**Files:**
- Create: `backend/scripts/plan_reliability.py`, `backend/tests/unit/test_plan_reliability.py`
- Modify: `CLAUDE.md` (one line)

**Interfaces:**
- Consumes: `PlanGenerator.generate_plan_workouts(..., api_key=None)` (rule-based path, no network), `plan_lint.lint_weeks`, `race_readiness.assess_week`, `goal_demands.compute`, `goal_feasibility.assess`.
- Produces: `SCENARIOS: list[Scenario]` (4 athlete profiles × 50K/100K × goal in `{A, B, finish}` plus: injury-return, 3-day athlete, 4-week runway), `run(scenario) -> Result`, `main() -> int` (exit code 1 on any failure), report as a table.

- [ ] **Step 1: Write the failing test** `test_scorecard_passes`: runs every scenario and asserts, per scenario: no hard-rule lint codes; peak-phase `TIME_ON_FEET` and `LONG_RUN_GRADIENT` absent whenever the verdict is not `unsupported`; verdict `unsupported` for every 3-day 100K scenario and `supported` for the 6-day, 26-week 100K scenario; goals ordered A < B < C when assessed. Also `test_scorecard_never_calls_gemini`: monkeypatch the Gemini client to raise and assert the run still passes.
- [ ] **Step 2: Run to verify it fails.** Expected: FAIL, module not found.
- [ ] **Step 3: Implement** the script and scenarios; the unit test imports `plan_reliability.run`. Capacity-bound weekend back-to-back codes are tolerated exactly as in `TestRuleBasedFallbackFollowsDoctrine`.
- [ ] **Step 4: Run** `python3 -m pytest tests/unit -q` and `python3 scripts/plan_reliability.py`. Expected: all pass, table printed, exit 0.
- [ ] **Step 5: Run the full verification**: unit + integration on the scratch DB, 3.11 parse check, golden scheduler compare. Expected: green.
- [ ] **Step 6: Commit** `test(plan): reliability scorecard over a fixed scenario matrix`.

---

## After Part 1 (not in this plan)

Deploy by the user-run script; then throwaway plans on prod with the real model: retry hit-rate, demand-block adherence, coach review of one 50K and one 100K. Only after that and after Part 2 (aerobic-speed tracking, A gate) may we say "reliable to reach the goal".

## Self-review

- Spec coverage: section 1 -> Task 1; section 2 -> Tasks 3–4; section 3 -> Tasks 2 and 5; section 6 -> Task 6; sections 4–5 are deliberately Part 2.
- Names checked across tasks: `Demands`, `compute`, `prompt_block`, `Feasibility`, `assess`, `week_capacity_minutes`, `Prefs.demands`, `PLAN_DEMANDS_ENABLED` are used identically everywhere.
- Constants invented here (my calls, to be tuned): `LONGEST_SESSION_SHARE = 0.40`, `STRETCH_MARGIN = 0.10`, `TIME_ON_FEET_SHARE = 0.90`, `GRADIENT_SHARE = 0.60`, default 5 days.

# Beginner Milestones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `start_running` plans get a First 5K / First 10K target, an optional event, and a fixed milestone ladder. The ladder ticks automatically from completed workouts and synced runs, or by hand. It shows in iOS and web onboarding and in the plan view, and the plan prompt, week brief and Coach Uphill all know about it.

**Architecture:** The ladder and all achievement logic live in one pure module, `backend/services/beginner_milestones.py`. A thin `refresh_milestones(user_id)` re-evaluates the whole active plan from DB state after any event that can earn credit, so every hook is the same one-line call and the result is idempotent. The plan JSON carries a `beginner_milestones` object, and the clients render it. The LLM only receives milestone facts as context. It never decides achievement.

**Tech Stack:** FastAPI + SQLAlchemy Core `text()` + Alembic (backend), Next.js 16 + vitest (web), SwiftUI + XcodeGen + XCTest (iOS).

**Spec:** `docs/superpowers/specs/2026-10-20-beginner-milestones-design.md`

## Global Constraints

- Every schema change goes in BOTH `db.py:init_db()` (idempotent `CREATE`/`ALTER … IF NOT EXISTS`) and one Alembic migration with `down_revision = "a9d4c7e1f2b6"` (single head after the 2026-10-21 rebase; re-check with `alembic heads` before writing). Follow the `db-migration` skill.
- The ladder keys, kinds, thresholds and stages are exactly the spec table: `first_session`, `jog_5`, `jog_10`, `jog_20`, `jog_30`, `first_5k` (stage A, where 5K ends), then `jog_45`, `jog_60`, `first_10k` (stage B, where 10K ends).
- `typical_weeks`: first_session [1,1], jog_5 [3,5], jog_10 [4,6], jog_20 [5,8], jog_30 [7,10], first_5k [9,12], jog_45 [13,17], jog_60 [16,21], first_10k [18,24]. Shown as "usually around week X–Y", never compared to the current week.
- `source` ∈ `auto | manual | baseline | revoked`. A revoked row has `achieved_at = NULL`, and detection never overwrites any existing row.
- `max_continuous_jog_min` only ever goes up (`db.set_max_continuous_jog_min`). Nothing in this plan lowers it.
- Default plan length with no event: 5K = 12 weeks, 10K = 22 weeks. Minimum length with an event: 5K = 9 weeks, 10K = 17 weeks, before the baseline reduction. The too-soon warning is soft and never blocks.
- The server sends milestone keys only. Clients own the en/vi labels. All vi copy goes through the `uphill-ai-vietnamese-copy` skill.
- Plans with `milestone_target IS NULL` (legacy and non-beginner plans) behave exactly as today: `beginner_milestones` is `null` and no milestone UI renders.
- Milestone hooks must never break the request they ride on. Each hook call is wrapped so an exception is logged and swallowed.
- Prompt and context changes (Tasks 7–8) follow `.claude/skills/llm-change-process/SKILL.md`, and the PR description carries its checklist.
- UI tasks need a real screenshot as evidence (`ui-screenshot-evidence` skill for web, a simulator screenshot for iOS).
- Integration tests TRUNCATE tables, so run them only against a scratch DB.

## Review Focus

1. **Activities from before the plan started.** A 6 km run synced from 12 weeks of history must not tick `first_5k` on day one. Only activities with `start_time ≥ plan start_date` count. Test: `test_evaluate_ignores_activities_before_plan_start` (Task 2).
2. **Undo survives the next sync.** Revoke `jog_10`, run `refresh_milestones` again with the same completed workout, and it stays revoked. Tests: `test_evaluate_skips_revoked_rows` (Task 2), `test_delete_then_refresh_stays_revoked` (Task 4).
3. **Legacy beginner plans with no target.** Today's `start_running` plans have `milestone_target NULL`. `refresh_milestones` is a no-op for them and the plan response has `beginner_milestones: null`. Test: `test_refresh_noop_without_target` (Task 3). Web and iOS render the old header (Tasks 10 and 13).
4. **A watch-less athlete.** Jog and session milestones still tick from a hand-ticked workout. Test: `test_log_workout_complete_ticks_jog_milestone` (Task 3).
5. **The hook failing mid-sync.** A DB error in the milestone refresh must not fail the COROS or Apple Health sync response. Test: `test_apple_health_sync_survives_milestone_error` (Task 3).

## Changes since the 2026-10-21 rebase

Nine PRs (#149–#163) landed after this plan was first written. They change the plan as follows:

- **Plan journey already has "milestones".** `services/plan_journey.py` (`GET /api/plans/{id}/journey`, iOS `JourneyStrip`) computes *calendar* milestones (`long_run_3h`, `first_recovery_week`, `peak_week`, `taper_start`, `race_week`) that count as done once their week has passed. Beginner milestones are earned, not scheduled, so they stay a separate concept. To avoid two meanings of one word on the wire, the plan payload key is **`beginner_milestones`**, never `milestones`. On iOS, `JourneyStrip`'s trailing "next milestone · week N" label shows the beginner next milestone instead when the plan has one (Task 13), so the screen never shows two competing "next" lines.
- **The weekly coach message (`services/coach_nudge.py`) already celebrates milestones.** `facts_for` builds `milestones_just_done`. `tone_for` picks `encourage` when that list is non-empty. `fallback_text` reads labels from `_MILESTONE`, and `grounded()` checks every number in the message against the facts. Beginner milestones reached in the last 7 days join that list (Task 8), which gives a grounded celebration on the plan screen with no new prompt.
- **`plan_lint` already checks long-run growth** (`LONG_RUN_JUMP`, `MAX_LONG_RUN_GROWTH = 0.25`, `MIN_LONG_RUN_STEP_MIN = 20`). The stage B prompt clause (Task 7) cites the same limit instead of inventing a "+10 min/week" rule, and needs no new lint.
- **The web has no journey or coach-message UI.** The web `MilestonePath` (Task 10) reads `plan.beginner_milestones` from the active-plan payload, as planned.
- **Line numbers** throughout this plan were refreshed against `fa0de6b`. The Alembic head is now `a9d4c7e1f2b6`.

---

## PR 1 — Backend

### Task 1: Schema and DB helpers

**Files:**
- Modify: `backend/db.py`: `init_db()` (plans `ALTER`s + new table), `create_plan` (two new kwargs), new helpers next to `set_max_continuous_jog_min` (`db.py:2191`)
- Create: `backend/alembic/versions/<rev>_add_beginner_milestones.py`
- Test: `backend/tests/integration/test_milestones_db.py` (scratch DB only)

**Interfaces:**
- Produces:
  - `create_plan(..., milestone_target: str | None = None, has_target_event: bool = False) -> int`
  - `get_plan_milestone_rows(plan_id: int) -> list[dict]`: keys `milestone_key, achieved_at, source, activity_id, workout_id`
  - `insert_milestone_if_absent(plan_id: int, key: str, source: str, achieved_at: datetime | None, activity_id: int | None = None, workout_id: int | None = None) -> bool`: `ON CONFLICT DO NOTHING`, returns True when it inserted
  - `set_milestone_manual(plan_id: int, key: str) -> None`: upsert to `source='manual'`, `achieved_at=NOW()`
  - `revoke_milestone(plan_id: int, key: str) -> None`: upsert to `source='revoked'`, `achieved_at=NULL`
  - `set_plan_milestone_target(plan_id: int, target: str, total_weeks: int | None) -> None`
  - `get_completed_run_workouts(plan_id: int) -> list[dict]`: `is_completed = 1`, with `id, week_number, type, duration_minutes, interval_reps, interval_rep_value, interval_rep_unit, walk_interval_value`
  - `get_run_activities_since(user_id: int, since: date) -> list[dict]`: `activity_type IN bundler.RUN_TYPES` and `start_time ≥ since`, with `id, start_time, distance_km, duration_seconds`

- [ ] **Step 1: Write failing integration tests.** `test_insert_milestone_if_absent_is_idempotent`: the second insert returns False and leaves one row. `test_revoke_then_insert_if_absent_keeps_revoked`. `test_set_manual_replaces_revoked`. `test_create_plan_persists_target_and_event_flag`. `test_get_run_activities_since_filters_type_and_date`: a `strength` activity and an activity dated the day before `since` are both excluded.
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && DATABASE_URL=<scratch> pytest tests/integration/test_milestones_db.py -v`. Expect them to fail with an ImportError or a missing column.
- [ ] **Step 3: Implement.**
  - Add `plans.milestone_target TEXT` and `plans.has_target_event BOOLEAN NOT NULL DEFAULT FALSE`.
  - Add the table `plan_milestones(plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE, milestone_key TEXT NOT NULL, achieved_at TIMESTAMPTZ, source TEXT NOT NULL, activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL, workout_id INTEGER REFERENCES workouts(id) ON DELETE SET NULL, created_at TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(plan_id, milestone_key))`.
  - Write the same in the Alembic migration, with a `downgrade()` that drops both columns and the table.
  - Import `RUN_TYPES` from `services.matching.bundler` rather than copying the set.
- [ ] **Step 4: Run the tests again and run `cd backend && alembic upgrade head` against the scratch DB.** Expect all PASS, and the upgrade to finish without errors.
- [ ] **Step 5: Commit** with the message `feat(db): plan_milestones table and plan milestone_target/has_target_event`.

### Task 2: Pure ladder module

**Files:**
- Create: `backend/services/beginner_milestones.py`
- Test: `backend/tests/unit/test_beginner_milestones.py`

**Interfaces:**
- Produces:
  - `Milestone` (frozen dataclass): `key: str, kind: Literal["sessions","jog_min","distance_km"], threshold: float, stage: Literal["A","B"], typical_weeks: tuple[int,int]`
  - `LADDER: tuple[Milestone, ...]`, in the spec order
  - `ladder_for(target: Literal["5k","10k"]) -> tuple[Milestone, ...]`: 5k gives the first six, 10k gives all nine
  - `baseline_keys(target, current_jog_min: int | None) -> list[str]`: jog milestones with `threshold ≤ current_jog_min`
  - `jog_credit_minutes(workout: dict) -> float | None`: returns None for non-run workouts (`coros_workouts.workout_kind(w) != "run"`). With `walk_interval_value` set, it returns `interval_rep_value` (minutes; convert when `interval_rep_unit` is seconds). Otherwise it returns `duration_minutes`.
  - `evaluate(target, plan_start: date, completed_workouts: list[dict], run_activities: list[dict], existing_keys: set[str]) -> list[NewAchievement]`
  - `NewAchievement` (dataclass): `key, achieved_at: datetime, workout_id: int | None, activity_id: int | None`. It is never emitted for a key in `existing_keys`, whatever that row's source. Jog milestones use the earliest completed workout whose credit is ≥ threshold. Distance milestones use the earliest activity with `distance_km ≥ threshold` and `start_time.date() ≥ plan_start`. `first_session` uses the earliest completed run workout.
  - `default_weeks(target) -> int`: 12 or 22
  - `minimum_weeks(target, current_jog_min: int | None) -> int`: `max(3, base - (first_open.typical_weeks[0] - 1))`, where base is 9 or 17 and `first_open` is the first ladder item not in `baseline_keys`
  - `serialize(target, has_event: bool, rows: list[dict]) -> dict`: the spec's API shape, with `next_key` = the first ladder key that has no achieved row (revoked counts as open) and `achieved_at` as ISO strings

- [ ] **Step 1: Write failing tests.**

```python
def test_ladder_for_5k_ends_at_first_5k():
    assert [m.key for m in ladder_for("5k")][-1] == "first_5k" and len(ladder_for("5k")) == 6

def test_ladder_for_10k_has_nine_ending_first_10k():
    assert [m.key for m in ladder_for("10k")][-1] == "first_10k" and len(ladder_for("10k")) == 9

def test_baseline_keys_at_10_min():
    assert baseline_keys("5k", 10) == ["jog_5", "jog_10"]

def test_baseline_keys_none_or_zero():
    assert baseline_keys("5k", None) == [] and baseline_keys("5k", 0) == []

def test_jog_credit_run_walk_uses_rep_value():
    assert jog_credit_minutes({"type": "Walk/Run", "duration_minutes": 30, "interval_rep_value": 4, "interval_rep_unit": "min", "walk_interval_value": 1}) == 4

def test_jog_credit_continuous_uses_duration():
    assert jog_credit_minutes({"type": "Easy Run", "duration_minutes": 20, "walk_interval_value": None}) == 20

def test_jog_credit_non_run_is_none():
    assert jog_credit_minutes({"type": "Strength", "duration_minutes": 30}) is None
```

  Also add these tests:
  - `test_evaluate_continuous_20_ticks_jog_5_10_20_and_first_session`
  - `test_evaluate_ignores_activities_before_plan_start` (Review Focus 1)
  - `test_evaluate_5_2km_activity_ticks_first_5k`
  - `test_evaluate_skips_revoked_rows` (Review Focus 2): `existing_keys={"jog_10"}`, so no `jog_10` is emitted
  - `test_evaluate_5k_target_never_emits_stage_b`
  - `test_minimum_weeks_10k_with_jog_30_baseline == 9`
  - `test_minimum_weeks_5k_no_baseline == 9`
  - `test_serialize_next_key_skips_achieved_and_treats_revoked_as_open`
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && pytest tests/unit/test_beginner_milestones.py -v`. Expect them to fail with an ImportError.
- [ ] **Step 3: Implement the module.** No DB imports are allowed in it.
- [ ] **Step 4: Run them again.** Expect all PASS.
- [ ] **Step 5: Commit** with the message `feat: beginner milestone ladder and evaluation`.

### Task 3: Refresh service and hooks

**Files:**
- Modify: `backend/services/beginner_milestones.py`: add a `refresh_milestones` impure wrapper at the bottom, with a lazy `import db`
- Modify: `backend/main.py:3182` (`log_workout`, after a successful update with `request.is_completed == 1`)
- Modify: `backend/routers/integrations.py:977,984` (manual match), `:748` (Apple Health sync, once after the loop)
- Modify: `backend/services/coros_sync.py:113` (once after the upsert loop), `backend/services/matching/runner.py:223` (once at the end of `match_user` if any workout was marked complete)
- Test: `backend/tests/unit/test_milestone_refresh.py`, plus additions to `backend/tests/unit/test_apple_health_route.py`

**Interfaces:**
- Consumes: the Task 1 db helpers and the Task 2 `evaluate`
- Produces: `refresh_milestones(user_id: int) -> list[str]`. It returns the newly achieved keys. It is a no-op returning `[]` when the active plan is missing, its `goal_type != "start_running"`, or its `milestone_target` is None. For each new achievement it calls `db.insert_milestone_if_absent(..., source="auto")`. For each new jog achievement it calls `db.set_max_continuous_jog_min(user_id, int(threshold))`.
- Produces: `safe_refresh_milestones(user_id: int) -> None`, which wraps `refresh_milestones` in `try/except Exception` and logs at warning. Every hook calls this, never `refresh_milestones` directly.

- [ ] **Step 1: Write failing tests** with an in-memory fake `db` via monkeypatch, in the style of `test_apple_health_route.py`.
  - `test_refresh_noop_without_target` (Review Focus 3)
  - `test_refresh_inserts_auto_rows_and_raises_jog_ceiling`
  - `test_log_workout_complete_ticks_jog_milestone` (Review Focus 4): use TestClient on `PATCH /api/coach/workouts/log` with `is_completed: 1`, and assert `safe_refresh_milestones` was called with the user id
  - `test_log_workout_uncomplete_does_not_refresh`
  - `test_apple_health_sync_survives_milestone_error` (Review Focus 5): `refresh_milestones` raises, and the sync still returns 200
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && pytest tests/unit/test_milestone_refresh.py tests/unit/test_apple_health_route.py -v`. Expect them to FAIL.
- [ ] **Step 3: Implement `refresh_milestones` and `safe_refresh_milestones`, and add the five one-line hook calls.**
- [ ] **Step 4: Run the tests again, then the full unit suite.** Run `cd backend && pytest tests/unit -q`. Expect everything to PASS with no regressions.
- [ ] **Step 5: Commit** with the message `feat: refresh beginner milestones on workout completion and activity sync`.

### Task 4: Plan API: read, manual tick and undo, upgrade

**Files:**
- Modify: `backend/main.py`:
  - add `plan["beginner_milestones"]` in the three active-plan responses (`:1626`, `:2107`, `:3081`) through one helper
  - add the new routes next to `delete_plan_endpoint` (`:2452`)
- Test: `backend/tests/unit/test_milestone_routes.py`

**Interfaces:**
- Produces:
  - `_attach_milestones(plan: dict) -> dict`: sets `plan["beginner_milestones"] = serialize(...)`, or None when there is no target
  - `POST /api/plans/{plan_id}/milestones/{key}`: returns `{"beginner_milestones": {...}}`. It returns 404 when the plan isn't the caller's (`plan["user_id"] != user["id"]`) and 400 when the key isn't in `ladder_for(target)`.
  - `DELETE /api/plans/{plan_id}/milestones/{key}`: same responses, and calls `revoke_milestone`
  - `PATCH /api/plans/{plan_id}/milestone-target`, body `{"target": "10k", "clear_event": false}`:
    - It only allows `5k → 10k`; anything else is a 400.
    - `clear_event: true` sets `has_target_event = false`.
    - When there is no event afterwards, `total_weeks` is set to `max(current total_weeks, default_weeks("10k"))`. With an event, `total_weeks` is left unchanged.
    - Clients ask "keep your event or clear it?" before sending when `has_event` is true.
    - It returns `{"plan": plan}`.

- [ ] **Step 1: Write failing tests.**
  - `test_active_plan_includes_milestones_for_target_plan`
  - `test_active_plan_milestones_null_for_legacy_plan`
  - `test_post_milestone_marks_manual`
  - `test_post_unknown_key_400`: `first_10k` on a 5k plan
  - `test_other_users_plan_404`
  - `test_delete_then_refresh_stays_revoked` (Review Focus 2)
  - `test_patch_target_5k_to_10k_extends_weeks`
  - `test_patch_target_10k_to_5k_400`
  - `test_patch_target_clear_event_extends_weeks`
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && pytest tests/unit/test_milestone_routes.py -v`. Expect them to FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them again.** Expect all PASS.
- [ ] **Step 5: Commit** with the message `feat(api): plan milestones in active-plan, manual tick/undo, 5K→10K upgrade`.

### Task 5: Plan creation with target, current jog and event

**Files:**
- Modify: `backend/main.py`:
  - `OnboardingRequest` (`:449`) and `PlanGenerateRequest` (`:230`) gain `milestone_target: Literal["5k","10k"] | None = None`, `current_jog_min: int | None = Field(None, ge=0, le=120)`, `event_name: str | None = None` and `event_date: date | None = None`
  - the `complete_onboarding` start_running branch (`:1274`, plan names `:1411`, `_default_weeks` `:1419`) and the `_generate_plan_for_athlete` non-race branch (`:2154-2164`)
- Test: additions to `backend/tests/unit/test_onboarding_helpers.py`, plus a new `backend/tests/unit/test_beginner_plan_create.py`

**Interfaces:**
- Consumes: `default_weeks`, `baseline_keys` and `db.insert_milestone_if_absent(source="baseline", achieved_at=now)`
- Produces the behaviour when `goal_type == "start_running"` and `milestone_target` is set:
  - **With an event:**
    - `race_name = event_name or "First 5K"/"First 10K"`, and `race_date = event_date`.
    - `total_weeks` comes from the existing date math, with no `+2`.
    - Set `has_target_event = True`.
  - **Without an event:**
    - `total_weeks = default_weeks(target)`.
    - `race_name = "First 5K"/"First 10K"`, and `race_date` is the synthetic end date (as today).
  - **In both cases:**
    - Store the target.
    - Call `db.set_max_continuous_jog_min(user_id, current_jog_min)` when it is given.
    - Insert the baseline rows.
  - An `event_date` in the past is a 400.
  - Check that `goal_demands`, `goal_feasibility` and `plan_adequacy` (added in #154/#156) skip `start_running` plans even with `has_target_event`. They key off race goals, so a beginner event must not get a race feasibility verdict. Add `test_beginner_event_plan_gets_no_race_feasibility`.
  - A too-soon `event_date` is accepted. The response carries `"warning": {"code": "event_too_soon", "minimum_weeks": n}`.

- [ ] **Step 1: Write failing tests.**
  - `test_start_running_10k_no_event_is_22_weeks_named_first_10k`
  - `test_start_running_with_event_uses_event_date_and_flag`
  - `test_current_jog_10_seeds_baseline_jog_5_jog_10`
  - `test_event_too_soon_returns_warning_not_error`
  - `test_event_in_past_400`
  - `test_start_running_without_target_unchanged`: the legacy path keeps its 12 weeks, "My Running Journey", and no target
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && pytest tests/unit/test_beginner_plan_create.py tests/unit/test_onboarding_helpers.py -v`. Expect them to FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them again, then `pytest tests/unit -q`.** Expect everything to PASS.
- [ ] **Step 5: Commit** with the message `feat(api): start_running plans take milestone target, current jog and optional event`.

### Task 6: PR 1 wrap-up

- [ ] Update the CLAUDE.md "Architecture" section with a short **Beginner milestones** paragraph (module, table, hooks, spec link).
- [ ] Run `cd backend && ruff check . && ruff format --check . && pytest tests/unit -q`. Expect a clean run.
- [ ] Open the PR against `main`, with an end-to-end check on a scratch local stack (`docker compose up -d`):
  1. Create a 10K plan with `current_jog_min=3`.
  2. Tick a continuous 10-minute workout, and confirm `jog_5` and `jog_10` tick and the ceiling becomes 10.
  3. Insert a 5.2 km run activity, and confirm `first_5k` ticks.

---

## PR 2 — LLM context (stacked on PR 1; follow llm-change-process)

### Task 7: Plan prompt goal text and stage B rules

**Files:**
- Modify: `backend/services/plan_generator.py:2739` (the `start_running` `goal_description`), and the `build_rules_block` call site
- Modify: `backend/services/plan_rules.py`: `build_rules_block(..., milestones: dict | None = None)` passes into `_beginner_rules(profile, max_continuous_jog_min, milestones=None)`
- Test: `backend/tests/unit/test_plan_rules_beginner_milestones.py`

**Interfaces:**
- Consumes: the plan's `beginner_milestones` dict (Task 4 shape), passed through `race_info["beginner_milestones"]`
- Produces:
  - `goal_description`, when there is a target: `"Goal: First 5K"` (or 10K), then `" — event '{name}' on {date}"` when there is an event, then `". Next milestone: {key label}, usually around week {lo}-{hi}. Walk breaks are part of the plan."`. When there is an event, append `" Make the event week light, with the event as its last session; run/walk is fine on the day. No taper block."`. Use English labels from a `MILESTONE_PROMPT_LABELS` dict in `beginner_milestones.py`.
  - A rules **stage B clause**. It appears only when the target is 10k and `jog_30` is achieved:
    - Run/walk is finished.
    - Schedule one long run a week that grows against the longest run of the past 30 days, within `plan_lint.MAX_LONG_RUN_GROWTH` (import the constant; don't restate the number).
    - All sessions stay Zone 1–2, with no intensity.
  - Without stage B, the existing text is byte-identical.

- [ ] **Step 1: Write failing tests.**
  - `test_rules_without_milestones_unchanged`: compare against the current output for a fixed profile
  - `test_rules_stage_b_only_after_jog_30_on_10k`
  - `test_goal_description_names_target_next_and_event`
- [ ] **Step 2: Run them and confirm they fail.** Run `cd backend && pytest tests/unit/test_plan_rules_beginner_milestones.py -v`.
- [ ] **Step 3: Implement.** Check whether `goal_description` and the rules block are compiled into a Langfuse template variable. If the `plan_generation` template text itself changes, version it per the skill. If only variable content changes, note that in the PR checklist.
- [ ] **Step 4: Run the tests, then the golden set.** Run `cd backend && python scripts/golden_eval.py compare --service plan` (check the service name with `--help`). Expect no regression on non-beginner cases. Beginner cases should change only by the added text.
- [ ] **Step 5: Commit** with the message `feat(llm): plan prompt knows beginner target, next milestone and stage B`.

### Task 8: Week brief fact and Coach Uphill context

**Files:**
- Modify: `backend/main.py:2610` (`brief_decision_log`), and the matching decision log in `backend/services/week_rebuild.py`
- Modify: `backend/services/coach_context.py` (`build_chat_context`): add a `"beginner_milestones"` key
- Modify: `backend/services/coach_nudge.py`: `facts_for` appends beginner keys achieved (not baseline, not revoked) in the last 7 days to `milestones_just_done` as `{"key": k, "week": week - 1}`. Add an en/vi label per ladder key to `_MILESTONE`.
- Modify: the coach-nudge route in `backend/main.py` (`:4440-4465`): pass the plan's milestone rows into `facts_for` through a new keyword `beginner_rows: list[dict] | None = None`
- Test: additions to `backend/tests/unit/test_week_brief.py` and `backend/tests/unit/test_chat_context.py`

**Interfaces:**
- Produces:
  - `beginner_milestones.brief_fact(milestones: dict | None, max_jog_min: int | None) -> str | None`. It returns, for example, `"Milestone: next = 20 min unbroken jog (usually wk 5-8); best so far = 12 min; 3 of 6 reached"`, or None without a target.
  - The chat context gains `"beginner_milestones": {"target", "reached": [keys], "next_key", "event": {"name","date"} | None}`, or None.

- [ ] **Step 1: Write failing tests:** `test_brief_fact_none_without_target`, `test_brief_fact_text`, `test_decision_log_includes_milestone_fact`, `test_chat_context_includes_milestones`. In `backend/tests/unit/test_coach_nudge.py` : `test_facts_include_beginner_milestone_reached_this_week`, `test_baseline_and_revoked_not_in_just_done`, `test_fallback_text_names_first_5k_en_vi`, and `test_grounded_accepts_milestone_numbers` ("20 min" is allowed because the threshold is in the facts).
- [ ] **Step 2: Run them and confirm they fail.**
- [ ] **Step 3: Implement.** If the coach system prompt needs a line about using the block, version `coach_chat` in Langfuse and run its golden eval.
- [ ] **Step 4: Run** `cd backend && pytest tests/unit -q` and the relevant `golden_eval.py compare`. Expect them to PASS.
- [ ] **Step 5: Commit** with the message `feat(llm): week brief, coach chat and coach message carry milestone progress`. Then open PR 2 with the llm-change-process checklist.

---

## PR 3 — Web (stacked on PR 1; can run in parallel with PR 4)

### Task 9: Types, labels and hook calls

**Files:**
- Create: `frontend/src/lib/beginnerMilestones.ts`
- Modify: the plan type in `frontend/src/contexts/AppContext.tsx` (add `milestone_target?`, `has_target_event?`, `beginner_milestones?`), and `frontend/src/hooks/usePlanner.ts`
- Test: `frontend/src/lib/beginnerMilestones.test.ts`

**Interfaces:**
- Produces:
  - `type PlanMilestones = { target: "5k"|"10k"; has_event: boolean; items: MilestoneItem[]; next_key: string|null }`
  - `milestoneLabel(key, lang: "en"|"vi"): string`
  - `minimumWeeks(target, currentJogMin)`: the same formula as the backend, plus a comment pointing to `beginner_milestones.minimum_weeks`
  - `usePlanner`: `markMilestone(planId, key)`, `undoMilestone(planId, key)` and `upgradeTarget(planId)`. Each updates the active plan's `beginner_milestones` from the response.

- [ ] **Step 1:** Write failing tests: `labels exist for every key in en and vi`, `minimumWeeks("10k", 30) === 9`, `minimumWeeks("5k", 0) === 9`.
- [ ] **Step 2:** Run `cd frontend && npx vitest run src/lib/beginnerMilestones.test.ts`. Expect it to FAIL.
- [ ] **Step 3:** Implement. Write the vi labels with the Vietnamese copy skill.
- [ ] **Step 4:** Run it again. Expect PASS.
- [ ] **Step 5:** Commit with the message `feat(web): milestone types, labels, planner hook calls`.

### Task 10: MilestonePath in the plan view

**Files:**
- Create: `frontend/src/components/MilestonePath.tsx`, `MilestonePath.module.css`, `MilestonePath.test.tsx`
- Modify: `frontend/src/views/PlannerView.tsx` (`:1551` carousel `goalPill` slot, and the `:1677` "Block ends" header), `frontend/src/hooks/usePlanner.ts:455` and `frontend/src/app/app/page.tsx:2050` (plan labels)

**Interfaces:**
- Produces: `<MilestonePath milestones lang onMark onUndo onUpgrade />`, rendered only when `plan.beginner_milestones` is non-null. The header reads `"First 5K · {reached} of {total} milestones"`, plus `" · {n} weeks to {event}"` when there is an event. The plan label reads `"First 5K plan"`.

- [ ] **Step 1:** Write failing tests:
  - `renders achieved checkmarks and highlights next_key with "usually around week X–Y"`
  - `"I did it" asks to confirm, then calls onMark(next_key)`
  - `undo on an achieved row calls onUndo`
  - `first_5k achieved on a 5k target shows "Next: First 10K" which calls onUpgrade`
  - `newly achieved key (not in localStorage seen set) shows celebration once`
- [ ] **Step 2:** Run `cd frontend && npx vitest run src/components/MilestonePath.test.tsx`. Expect it to FAIL.
- [ ] **Step 3:** Implement. Reuse the `PlanSummaryCarousel` card styling. Keep the seen-set in localStorage under `uphill.milestonesSeen.{planId}`, wrapped in try/catch.
- [ ] **Step 4:** Run it, then `npm run lint`. Expect PASS. Then run the app locally, take screenshots of the path card, the confirm dialog, the celebration and the legacy plan (no card), and attach them to the PR.
- [ ] **Step 5:** Commit with the message `feat(web): milestone path card, celebration, 5K→10K upgrade`.

### Task 11: Web onboarding and planner fields

**Files:**
- Modify: `frontend/src/views/OnboardingWizard.tsx` (the `fitness_start` step `:1146`, for `start_running`), and `frontend/src/views/PlannerView.tsx` (the start-running block `:1256`: replace the "Duration (weeks)" select)

**Interfaces:**
- Produces: request bodies carrying `milestone_target`, `current_jog_min` (choices 0/3/10/20), `event_name` and `event_date`. An inline warning shows when the weeks to `event_date` are fewer than `minimumWeeks`. The "Your path" preview list reuses `MilestonePath` in a read-only mode (a `readOnly` prop).

- [ ] **Step 1:** Write failing tests in `OnboardingWizard` and `PlannerView` test files, or new ones beside them:
  - `start_running shows target, jog and event fields`
  - `submits milestone_target and current_jog_min`
  - `event 4 weeks out shows too-soon warning and still submits`
- [ ] **Step 2:** Run `npx vitest run` on those files. Expect it to FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run the tests, then take screenshots of the 5K flow, the 10K flow and the event warning. Then open PR 3.
- [ ] **Step 5:** Commit with the message `feat(web): onboarding and planner capture beginner target and event`.

---

## PR 4 — iOS (stacked on PR 1; can run in parallel with PR 3)

### Task 12: Models, service and onboarding steps

**Files:**
- Modify: `ios-native/UphillAI/Core/Models/Plan.swift`: add optional `milestoneTarget: String?`, `hasTargetEvent: Bool?` and `beginnerMilestones: PlanMilestones?`
- Create: `ios-native/UphillAI/Core/Plan/PlanMilestones.swift`: `PlanMilestones`, `MilestoneItem`, `MilestoneLabels.label(_ key: String) -> String` via `L(...)`, and `minimumWeeks(target:currentJogMin:)`
- Modify: `ios-native/UphillAI/Core/Plan/PlanService.swift`: `markMilestone(planID:key:)`, `undoMilestone(planID:key:)` and `upgradeTarget(planID:)`, each returning `PlanMilestones` or `Plan`
- Modify: `ios-native/UphillAI/Core/Plan/PlanSetupDraft.swift`: in `SetupStep.steps(for:)`, `.startRunning` gets steps `.beginnerTarget`, `.currentJog` and `.event`. The draft adds fields `milestoneTarget`, `currentJogMin` and `eventName/eventDate/hasEvent`. `OnboardingBody` and `PlanBody` encode them. Per-step validation requires the target.
- Modify: `ios-native/UphillAI/Features/Onboarding/SetupSteps.swift`: the three new step views, plus a "Your path" section in `SetupReviewStep`
- Fixtures: `ios-native/UphillAITests/Fixtures/active_plan_milestones.json`
- Test: `ios-native/UphillAITests/Models/PlanDecodingTests.swift`, plus a new `ios-native/UphillAITests/Onboarding/BeginnerSetupTests.swift`

- [ ] **Step 1:** Write failing tests:
  - `testDecodesMilestones`
  - `testLegacyPlanDecodesWithNilMilestones` (uses the existing `active_plan.json`)
  - `testStartRunningStepsIncludeTargetJogEvent`
  - `testPlanBodyEncodesMilestoneTargetAndJog`
  - `testMinimumWeeks10kJog30Is9`
- [ ] **Step 2:** Run `ios-native/scripts/test.sh`. Expect the new tests to FAIL.
- [ ] **Step 3:** Implement, using the `UH` tokens and the existing goal-tile style. The jog options are "Not yet" = 0, "1–5 min" = 3, "About 10 min" = 10 and "20+ min" = 20. Put the vi strings in `Localizable.xcstrings` via the Vietnamese copy skill.
- [ ] **Step 4:** Run `ios-native/scripts/test.sh` again. Expect PASS. Then take simulator screenshots of the target, jog, event (with the warning) and review "Your path" screens, in en and vi.
- [ ] **Step 5:** Commit with the message `feat(ios): beginner target, current jog and event in plan setup`.

### Task 13: MilestonePathCard, header and celebration

**Files:**
- Create: `ios-native/UphillAI/Features/Plan/MilestonePathCard.swift`, `ios-native/UphillAI/Features/Plan/MilestoneCelebrationSheet.swift`
- Modify:
  - `ios-native/UphillAI/Features/Plan/SummaryCarousel.swift`: show `MilestonePathCard` in place of `raceCard` (`:344`) when `plan.beginnerMilestones != nil`
  - `ios-native/UphillAI/Features/Plan/PlanView.swift`: `raceGoalHeader` (`:540`) shows the milestone line, and the celebration `.sheet` lives here
  - `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`: add `milestoneHeaderText`, `newlyAchievedKey` (diffed against a `UserDefaults` seen-set keyed `milestonesSeen.\(planID)`), `mark(_:)`, `undo(_:)` and `upgrade()`
  - `ios-native/UphillAI/Features/Plan/JourneyStrip.swift`: take an optional `beginnerNext: String?` (the localized label plus "usually wk X–Y") that replaces the trailing `nextMilestone` text when it is set
- Test: `ios-native/UphillAITests/Plan/MilestonePathTests.swift`

**Interfaces:**
- Consumes: Task 12 models and service methods
- Produces: the header `"First 5K · 3 of 6 milestones"` (+ `" · N weeks to {event}"`). The card shows the ladder, the next row with "usually around week X–Y", and an "I did it" button behind a confirmation dialog. Tapping the card opens the full list with swipe-to-undo. The celebration sheet uses `.sensoryFeedback(.success)`, shows a teaser for the next milestone, a certificate-style variant for `first_5k`/`first_10k`, and a "Next: First 10K" button when the target is 5k and `first_5k` is reached.

- [ ] **Step 1:** Write failing tests:
  - `testHeaderTextCountsReachedOfTotal`
  - `testNewlyAchievedKeyIgnoresBaselineAndSeen`
  - `testMarkUpdatesMilestonesFromResponse`
  - `testLegacyPlanHasNoMilestoneHeader`
  - `testJourneyStripShowsBeginnerNextInsteadOfCalendarMilestone`
- [ ] **Step 2:** Run `ios-native/scripts/test.sh`. Expect it to FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `ios-native/scripts/test.sh`. Expect PASS. Then do a simulator walkthrough against a local backend: onboarding → plan card → "I did it" → celebration → "Next: First 10K". Take screenshots in en and vi and attach them to PR 4.
- [ ] **Step 5:** Commit with the message `feat(ios): milestone path card, header and celebration`. Then open PR 4. The TestFlight build follows the native release process, with build number `YYYYMMDDNN`.

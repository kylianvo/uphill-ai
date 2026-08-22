# Coach Dashboard Dynamic Window + Expanded Insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed 2-week insights window with a coach-selectable `days` param (7/14/30/90), and add five new roster-wide insights: adherence trend, missed-by-day pattern, RPE distribution, race readiness, roster totals, and a most-consistent-athletes callout.

**Architecture:** `get_roster_overview_data` gains a `days` parameter that generalizes the existing hardcoded window into `window_weeks`. A roster-wide flat list of in-window workouts (`roster_window_wos`), accumulated during the same per-athlete loop that already exists, feeds the new roster-wide insights; a separate query against `block_reviews` (which has a real `created_at` timestamp, unlike `workouts`) feeds RPE distribution. The frontend adds a window-selector dropdown and new insight cards to the existing Overview tab.

**Tech Stack:** FastAPI + SQLAlchemy Core (`text()`), no ORM, on the backend; Next.js/React on the frontend; pytest against live Postgres, Vitest for frontend.

**Spec:** [docs/superpowers/specs/2026-08-22-coach-dashboard-insights-design.md](../specs/2026-08-22-coach-dashboard-insights-design.md)

**Depends on:** the Coach Dashboard Overview base feature (already implemented and merged on this branch) and, if executed after it, the Runner Levels plan (`2026-08-22-coach-dashboard-runner-levels.md`) — this plan does not require it, but if both have landed, Task 1's rename below applies on top of whatever `athletes[]` shape that plan left (it doesn't touch `runner_level`/`needs_attention`, so no conflict either way).

## Global Constraints

- No new database tables. `block_reviews` (`backend/db.py:302`) already has a real `created_at TIMESTAMPTZ` — used directly for the RPE insight's window filter, unlike every other window-scoped calculation here, which stays on the existing week-number approximation.
- `days` query param on `GET /api/coaching/overview`, default `14`. Converted internally via `window_weeks = max(1, math.ceil(days / 7))`. No validation beyond the `max(1, ...)` floor — any positive `days` value just widens or narrows the window.
- **Field rename**: `adherence_pct_14d` becomes `adherence_pct` everywhere (backend response, backend tests, frontend type, frontend usages) — the old name would misdescribe the window once it's adjustable. This is a same-branch rename, not a deprecation; there is no external consumer of this brand-new endpoint to keep compatible.
- Race-readiness buckets: `on_track` = `adherence_pct >= 0.8`, `at_risk` = `0.5 <= adherence_pct < 0.8`, `behind` = `adherence_pct < 0.5`. Athletes with `adherence_pct === null` are excluded from all three.
- Most-consistent: top 3 by `adherence_pct`, ties broken alphabetically by name, `null`-adherence athletes excluded, fewer than 3 eligible athletes returns fewer than 3 entries (no padding).
- Bilingual UI copy (en/vi) required for every new user-facing string, matching the existing `lang === "en" ? "..." : "..."` pattern.

---

## File Structure

- **Modify** `backend/db.py` — parameterize the window, rename the field, add the five new insight computations to `get_roster_overview_data`.
- **Modify** `backend/main.py` — `days` query param on the endpoint.
- **Modify** `backend/tests/integration/test_coach_overview.py` — window parameterization tests, rename fixups, and coverage for all five new insights.
- **Modify** `frontend/src/hooks/useCoachOverview.ts` — `days` param on `fetchOverview`, renamed field, five new response fields typed.
- **Modify** `frontend/src/views/CoachDashboardView.tsx` — window-selector dropdown and new insight cards (adherence trend, missed-by-day, RPE, race readiness, roster totals, most consistent).
- **Create** `frontend/src/components/AdherenceTrendChart.tsx` (+ test) — sparkline, following `WorkoutTypeMixChart`'s hand-rolled styling.
- **Create** `frontend/src/components/MissedByDayChart.tsx` (+ test) — bar row, zero-filled Mon–Sun.

---

### Task 1: Backend — parameterize the window, rename `adherence_pct_14d`

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/main.py`
- Modify: `backend/tests/integration/test_coach_overview.py`
- Modify: `frontend/src/hooks/useCoachOverview.ts`
- Modify: `frontend/src/views/CoachDashboardView.tsx`

**Interfaces:**
- Produces: `get_roster_overview_data(coach_id: int, days: int = 14) -> dict[str, Any]` — same shape as before, `adherence_pct_14d` renamed to `adherence_pct` on every athlete entry, window now driven by `days` instead of hardcoded.
- Produces: `GET /api/coaching/overview?days=<int>` (default 14).
- Produces: a roster-wide `roster_window_wos: list[dict]` variable inside `get_roster_overview_data` (accumulated during the existing per-athlete loop) — later tasks in this plan consume it directly; it is not part of the JSON response itself.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/integration/test_coach_overview.py`, inside `TestGetRosterOverviewData`:

```python
    def test_default_days_matches_previous_fixed_two_week_window(self):
        coach_id = _create_user("window-coach1@uphill.ai")
        athlete_id = _create_user("window-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        window_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] in (4, 5)]
        for w in window_workouts[:4]:
            update_workout_log(w["id"], is_completed=1)
        update_workout_log(window_workouts[4]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id)  # no days arg -> default 14
        assert data["athletes"][0]["adherence_pct"] == 0.8

    def test_days_30_widens_the_window_beyond_two_weeks(self):
        coach_id = _create_user("window-coach2@uphill.ai")
        athlete_id = _create_user("window-athlete2@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id, race_name="Test 50K", race_date="2026-12-01", goal_type="finish",
            target_time_hours=8.0, total_weeks=12, plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = :w WHERE id = :pid"), {"w": 5, "pid": plan_id})
            conn.commit()
        # Weeks 1-5: one workout each, all completed. days=30 -> window_weeks = ceil(30/7) = 5 -> weeks 1-5.
        # days=14 -> window_weeks = 2 -> weeks 4-5 only.
        workouts = [
            {"week_number": wk, "day_of_week": "Monday", "phase": "build", "title": "Run",
             "type": "easy_run", "duration_minutes": 45, "target_zone": "Z2"}
            for wk in range(1, 6)
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        for w in get_plan_workouts(plan_id):
            update_workout_log(w["id"], is_completed=1)

        data_14 = get_roster_overview_data(coach_id, days=14)
        data_30 = get_roster_overview_data(coach_id, days=30)
        # Both are 100% adherence (all completed), but this test's real assertion is in Task 2's
        # roster-wide counts, which do distinguish window width by count. Here we just confirm
        # the call accepts `days` and doesn't error, and adherence is unaffected by window width
        # when every workout in range is completed either way.
        assert data_14["athletes"][0]["adherence_pct"] == 1.0
        assert data_30["athletes"][0]["adherence_pct"] == 1.0

    def test_get_coaching_overview_endpoint_accepts_days_param(self, client):
        coach_headers, coach_id = _make_coach(client, "window-endpoint-coach1@uphill.ai")
        athlete_id = _create_user("window-endpoint-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)

        resp = client.get("/api/coaching/overview?days=30", headers=coach_headers)

        assert resp.status_code == 200
        assert "athletes" in resp.json()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -k "window or days" -v`
Expected: FAIL — `KeyError: 'adherence_pct'` (field is still named `adherence_pct_14d`), and `get_roster_overview_data() got an unexpected keyword argument 'days'`.

- [ ] **Step 3: Implement in `backend/db.py`**

Add `import math` to the top of `db.py` alongside the existing stdlib imports (`db.py:6-9`):

```python
import datetime
import hashlib
import json
import math
import uuid
```

Change the function signature and the window calculation inside `get_roster_overview_data`:

```python
def get_roster_overview_data(coach_id: int, days: int = 14) -> dict[str, Any]:
    """Roster-wide progress, action items, phase alerts, and insights for a
    coach's active roster, over the last `days` days. Backs GET
    /api/coaching/overview.

    'current week' trusts plans.current_week directly (no calendar-date
    derivation -- workouts have no completion timestamp or date column,
    only week_number + day_of_week). `days` is converted to a week-count
    window (window_weeks) rather than filtering by real dates, for the
    same reason."""
    window_weeks = max(1, math.ceil(days / 7))
```

(This replaces the old docstring's fixed "14-day window" line and adds the `window_weeks` line right after the `with engine.connect() as conn:` line — keep it at the top of the function, before the first query, since it's needed throughout.)

Change the per-athlete window filter from the hardcoded `current_week - 1` to `current_week - (window_weeks - 1)`:

```python
        window_wos = [
            w for w in wos_sorted
            if current_week - (window_weeks - 1) <= w["week_number"] <= current_week
        ]
```

Rename `adherence_pct_14d` to `adherence_pct` in both places it's constructed — the no-active-plan branch:

```python
                    "adherence_pct": None,
```

and the has-active-plan branch:

```python
                "adherence_pct": round(adherence, 3) if adherence is not None else None,
```

Add a roster-wide accumulator, initialized alongside the existing `type_counts`/`total_completed_in_window` accumulators (right after `phase_alerts: list[dict[str, Any]] = []`):

```python
    roster_window_wos: list[dict[str, Any]] = []
```

Inside the loop, right after `window_wos = [...]` is computed for that athlete, extend the roster-wide list:

```python
        roster_window_wos.extend(window_wos)
```

Finally, update the return statement's field name is unaffected (the top-level `athletes`/`action_items`/`phase_alerts`/`workout_type_mix` keys don't change in this task) — Tasks 2-4 add new keys to this same return dict.

- [ ] **Step 4: Implement in `backend/main.py`**

Change the endpoint signature:

```python
@app.get("/api/coaching/overview")
def get_coaching_overview(days: int = 14, coach: dict[str, Any] = Depends(require_coach)):
    return get_roster_overview_data(coach["id"], days=days)
```

- [ ] **Step 5: Fix the rename in existing tests and frontend**

In `backend/tests/integration/test_coach_overview.py`, every existing assertion reading `athlete["adherence_pct_14d"]` or `athletes[0]["adherence_pct_14d"]` must be updated to `adherence_pct` (this affects the pre-existing adherence test from the base feature plan). Search the file for `adherence_pct_14d` and replace each occurrence with `adherence_pct` — there is no case where the old name should remain.

In `frontend/src/hooks/useCoachOverview.ts`, rename the field in `CoachOverviewAthlete`:

```typescript
  adherence_pct: number | null;
```

Add the `days` parameter to `fetchOverview` and update `CoachOverview`'s five new fields will be added in later tasks — for this task, just update the fetch call to accept an optional window:

```typescript
  const fetchOverview = async (days?: number) => {
    setOverviewLoading(true);
    setOverviewError("");
    try {
      const url = days ? `${API_BASE_URL}/api/coaching/overview?days=${days}` : `${API_BASE_URL}/api/coaching/overview`;
      const res = await fetch(url, { headers: authHeaders() });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail || "Failed to load overview.");
      }
      setOverview(body);
    } catch (err: any) {
      setOverviewError(err.message || "Failed to load overview.");
      setOverview(null);
    } finally {
      setOverviewLoading(false);
    }
  };
```

In `frontend/src/views/CoachDashboardView.tsx`, every reference to `athlete.adherence_pct_14d` (currently one place, in the roster-progress row rendering) becomes `athlete.adherence_pct`. If the Runner Levels plan has already landed and modified this same rendering block, apply the rename to whatever the current variable/prop name is there — the field being read from the API response is what changed, not the row-rendering structure itself.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -v`
Expected: all tests pass, including the pre-existing ones now reading `adherence_pct`.

Run: `cd frontend && npx tsc --noEmit`
Expected: no new errors.

- [ ] **Step 7: Commit**

```bash
git add backend/db.py backend/main.py backend/tests/integration/test_coach_overview.py frontend/src/hooks/useCoachOverview.ts frontend/src/views/CoachDashboardView.tsx
git commit -m "feat(coaching): parameterize insights window via days param, rename adherence_pct_14d"
```

---

### Task 2: Backend — adherence trend + missed-by-day pattern

**Files:**
- Modify: `backend/db.py`
- Test: `backend/tests/integration/test_coach_overview.py`

**Interfaces:**
- Consumes: `roster_window_wos: list[dict]` from Task 1 (each entry has `week_number`, `day_of_week`, `is_completed`, `is_missed`).
- Produces: `get_roster_overview_data`'s return dict gains `adherence_trend: list[{week_number: int, adherence_pct: float}]` and `missed_by_day: list[{day_of_week: str, count: int}]`.

- [ ] **Step 1: Write the failing tests**

Add to `TestGetRosterOverviewData`:

```python
    def test_adherence_trend_has_one_entry_per_week_with_resolved_data(self):
        coach_id = _create_user("trend-coach1@uphill.ai")
        athlete_id = _create_user("trend-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        # Week 4: mark all 3 completed. Week 5: mark 1 completed, 1 missed, leave 1 unresolved.
        by_week = {}
        for w in get_plan_workouts(plan_id):
            by_week.setdefault(w["week_number"], []).append(w)
        for w in by_week[4]:
            update_workout_log(w["id"], is_completed=1)
        update_workout_log(by_week[5][0]["id"], is_completed=1)
        update_workout_log(by_week[5][1]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id, days=14)
        trend = {row["week_number"]: row["adherence_pct"] for row in data["adherence_trend"]}
        assert trend[4] == 1.0
        assert trend[5] == 0.5  # 1 completed / 2 resolved (1 unresolved excluded)

    def test_missed_by_day_counts_only_missed_workouts_in_window(self):
        coach_id = _create_user("missedday-coach1@uphill.ai")
        athlete_id = _create_user("missedday-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        by_day = {(w["week_number"], w["day_of_week"]): w for w in get_plan_workouts(plan_id)}
        update_workout_log(by_day[(5, "Monday")]["id"], is_missed=1)
        update_workout_log(by_day[(4, "Monday")]["id"], is_missed=1)
        update_workout_log(by_day[(5, "Wednesday")]["id"], is_completed=1)  # not missed -> excluded

        data = get_roster_overview_data(coach_id, days=14)
        by_day_result = {row["day_of_week"]: row["count"] for row in data["missed_by_day"]}
        assert by_day_result["Monday"] == 2
        assert "Wednesday" not in by_day_result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -k "trend or missed_by_day" -v`
Expected: FAIL — `KeyError: 'adherence_trend'` / `KeyError: 'missed_by_day'`.

- [ ] **Step 3: Implement in `backend/db.py`**

Add this computation after the per-athlete loop ends (right before the existing `workout_type_mix = (...)` block), using the `roster_window_wos` list built in Task 1:

```python
    adherence_by_week: dict[int, list[dict[str, Any]]] = {}
    missed_by_day_counts: dict[str, int] = {}
    for w in roster_window_wos:
        adherence_by_week.setdefault(w["week_number"], []).append(w)
        if w["is_missed"]:
            missed_by_day_counts[w["day_of_week"]] = missed_by_day_counts.get(w["day_of_week"], 0) + 1

    adherence_trend = []
    for week_number in sorted(adherence_by_week.keys()):
        week_wos = adherence_by_week[week_number]
        resolved = [w for w in week_wos if w["is_completed"] or w["is_missed"]]
        if not resolved:
            continue
        completed = [w for w in resolved if w["is_completed"]]
        adherence_trend.append(
            {"week_number": week_number, "adherence_pct": round(len(completed) / len(resolved), 3)}
        )

    missed_by_day = [
        {"day_of_week": day, "count": count} for day, count in missed_by_day_counts.items()
    ]
```

Add both to the final return dict:

```python
    return {
        "athletes": athletes,
        "action_items": {
            "draft_plans": draft_plans,
            "pending_workout_approvals": pending_workout_approvals,
        },
        "phase_alerts": phase_alerts,
        "workout_type_mix": workout_type_mix,
        "adherence_trend": adherence_trend,
        "missed_by_day": missed_by_day,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/tests/integration/test_coach_overview.py
git commit -m "feat(coaching): add adherence_trend and missed_by_day insights"
```

---

### Task 3: Backend — RPE distribution

**Files:**
- Modify: `backend/db.py`
- Test: `backend/tests/integration/test_coach_overview.py`

**Interfaces:**
- Consumes: `days` (from Task 1's function signature).
- Produces: `get_roster_overview_data`'s return dict gains `rpe_distribution: {avg_rpe: float | None, by_value: list[{rpe: int, count: int}]}`.

- [ ] **Step 1: Write the failing tests**

Add to `TestGetRosterOverviewData`:

```python
    def test_rpe_distribution_excludes_reviews_outside_window_and_null_rpe(self):
        from db import save_block_review

        coach_id = _create_user("rpe-coach1@uphill.ai")
        athlete_id = _create_user("rpe-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id, race_name="Test 50K", race_date="2026-12-01", goal_type="finish",
            target_time_hours=8.0, total_weeks=12, plan_status="active",
        )
        save_block_review(plan_id, 1, overall_rpe=6, notes=None)
        save_block_review(plan_id, 2, overall_rpe=8, notes=None)
        old_review = save_block_review(plan_id, 3, overall_rpe=9, notes=None)
        save_block_review(plan_id, 4, overall_rpe=None, notes="no rpe given")
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE block_reviews SET created_at = NOW() - INTERVAL '60 days' WHERE id = :id"),
                {"id": old_review["id"]},
            )
            conn.commit()

        data = get_roster_overview_data(coach_id, days=14)
        assert data["rpe_distribution"]["avg_rpe"] == 7.0  # (6 + 8) / 2, excludes the 60-day-old and the null
        by_value = {row["rpe"]: row["count"] for row in data["rpe_distribution"]["by_value"]}
        assert by_value == {6: 1, 8: 1}

    def test_rpe_distribution_empty_when_no_reviews_in_window(self):
        coach_id = _create_user("rpe-coach2@uphill.ai")
        athlete_id = _create_user("rpe-athlete2@uphill.ai")
        _link_active(coach_id, athlete_id)

        data = get_roster_overview_data(coach_id, days=14)
        assert data["rpe_distribution"] == {"avg_rpe": None, "by_value": []}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -k "rpe" -v`
Expected: FAIL — `KeyError: 'rpe_distribution'`.

- [ ] **Step 3: Implement in `backend/db.py`**

Add a new query inside the existing `with engine.connect() as conn:` block in `get_roster_overview_data`, alongside `draft_rows`/`pending_rows` (same connection, same block):

```python
        rpe_rows = conn.execute(
            text("""
                SELECT br.overall_rpe
                FROM block_reviews br
                JOIN plans p ON p.id = br.plan_id
                JOIN coach_athletes ca ON ca.athlete_id = p.user_id AND ca.coach_id = :cid AND ca.status = 'active'
                WHERE br.overall_rpe IS NOT NULL
                  AND br.created_at >= NOW() - (:days || ' days')::INTERVAL
            """),
            {"cid": coach_id, "days": days},
        ).fetchall()
```

After the `with engine.connect()` block ends (alongside where `draft_plans`/`pending_workout_approvals` are built from their row lists), compute the distribution:

```python
    rpe_values = [r[0] for r in rpe_rows]
    rpe_counts: dict[int, int] = {}
    for v in rpe_values:
        rpe_counts[v] = rpe_counts.get(v, 0) + 1
    rpe_distribution = {
        "avg_rpe": round(sum(rpe_values) / len(rpe_values), 3) if rpe_values else None,
        "by_value": [{"rpe": rpe, "count": count} for rpe, count in sorted(rpe_counts.items())],
    }
```

Add to the final return dict:

```python
        "rpe_distribution": rpe_distribution,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/tests/integration/test_coach_overview.py
git commit -m "feat(coaching): add rpe_distribution insight from block_reviews"
```

---

### Task 4: Backend — race readiness, roster totals, most consistent

**Files:**
- Modify: `backend/db.py`
- Test: `backend/tests/integration/test_coach_overview.py`

**Interfaces:**
- Consumes: `athletes[]` (with `adherence_pct`, from Task 1) and `roster_window_wos` (from Task 1) inside `get_roster_overview_data`.
- Produces: return dict gains `race_readiness: {on_track: int, at_risk: int, behind: int}`, `roster_totals: {distance_km: float, duration_hours: float, elevation_gain_m: float, workout_count: int}`, `most_consistent: list[{athlete_id: int, name: str, adherence_pct: float}]` (up to 3 entries).

- [ ] **Step 1: Write the failing tests**

Add to `TestGetRosterOverviewData`:

```python
    def test_race_readiness_buckets_by_adherence_boundaries(self):
        coach_id = _create_user("readiness-coach1@uphill.ai")
        on_track_id = _create_user("readiness-ontrack@uphill.ai")
        at_risk_id = _create_user("readiness-atrisk@uphill.ai")
        behind_id = _create_user("readiness-behind@uphill.ai")
        no_data_id = _create_user("readiness-nodata@uphill.ai")
        for aid in (on_track_id, at_risk_id, behind_id, no_data_id):
            _link_active(coach_id, aid)

        def make_athlete_with_adherence(athlete_id, pct_completed, pct_missed):
            plan_id = create_plan(
                user_id=athlete_id, race_name="R", race_date="2026-12-01", goal_type="finish",
                target_time_hours=8.0, total_weeks=12, plan_status="active",
            )
            with engine.connect() as conn:
                conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
                conn.commit()
            workouts = [
                {"week_number": 5, "day_of_week": d, "phase": "build", "title": "Run",
                 "type": "easy_run", "duration_minutes": 30, "target_zone": "Z2"}
                for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            ]
            save_workouts(plan_id, workouts, auto_approve=True)
            wos = get_plan_workouts(plan_id)
            for w in wos[:pct_completed]:
                update_workout_log(w["id"], is_completed=1)
            for w in wos[pct_completed:pct_completed + pct_missed]:
                update_workout_log(w["id"], is_missed=1)

        make_athlete_with_adherence(on_track_id, 4, 1)  # 4/5 = 0.8 -> on_track
        make_athlete_with_adherence(at_risk_id, 3, 2)  # 3/5 = 0.6 -> at_risk
        make_athlete_with_adherence(behind_id, 1, 4)  # 1/5 = 0.2 -> behind
        # no_data_id: no plan at all -> adherence_pct is null -> excluded

        data = get_roster_overview_data(coach_id, days=14)
        assert data["race_readiness"] == {"on_track": 1, "at_risk": 1, "behind": 1}

    def test_roster_totals_sums_completed_workouts_and_tolerates_null_fields(self):
        coach_id = _create_user("totals-coach1@uphill.ai")
        athlete_id = _create_user("totals-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id, race_name="R", race_date="2026-12-01", goal_type="finish",
            target_time_hours=8.0, total_weeks=12, plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
            conn.commit()
        save_workouts(
            plan_id,
            [
                {"week_number": 5, "day_of_week": "Monday", "phase": "build", "title": "Run",
                 "type": "easy_run", "duration_minutes": 60, "distance_km": 10.0, "elevation_gain_m": 200,
                 "target_zone": "Z2"},
                {"week_number": 5, "day_of_week": "Tuesday", "phase": "build", "title": "Run (no distance logged)",
                 "type": "easy_run", "duration_minutes": 30, "target_zone": "Z2"},  # distance_km/elevation_gain_m omitted -> NULL/0 default
            ],
            auto_approve=True,
        )
        wos = get_plan_workouts(plan_id)
        for w in wos:
            update_workout_log(w["id"], is_completed=1)

        data = get_roster_overview_data(coach_id, days=14)
        totals = data["roster_totals"]
        assert totals["distance_km"] == 10.0
        assert totals["duration_hours"] == 1.5  # (60 + 30) / 60
        assert totals["workout_count"] == 2

    def test_most_consistent_returns_top_3_excluding_null_adherence(self):
        coach_id = _create_user("consistent-coach1@uphill.ai")
        a1 = _create_user("consistent-athlete1@uphill.ai")
        a2 = _create_user("consistent-athlete2@uphill.ai")
        a3 = _create_user("consistent-athlete3@uphill.ai")
        a4_no_plan = _create_user("consistent-athlete4@uphill.ai")
        for aid in (a1, a2, a3, a4_no_plan):
            _link_active(coach_id, aid)

        def full_adherence_athlete(athlete_id):
            plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
            for w in [w for w in get_plan_workouts(plan_id) if w["week_number"] in (4, 5)]:
                update_workout_log(w["id"], is_completed=1)

        full_adherence_athlete(a1)
        full_adherence_athlete(a2)
        full_adherence_athlete(a3)

        data = get_roster_overview_data(coach_id, days=14)
        assert len(data["most_consistent"]) == 3
        assert all(row["adherence_pct"] == 1.0 for row in data["most_consistent"])
        assert a4_no_plan not in {row["athlete_id"] for row in data["most_consistent"]}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -k "readiness or totals or consistent" -v`
Expected: FAIL — `KeyError` for each of `race_readiness`, `roster_totals`, `most_consistent`.

- [ ] **Step 3: Implement in `backend/db.py`**

Add `distance_km`, `elevation_gain_m` to the existing batched workouts query (the one Task 1's `roster_window_wos` is built from):

```python
            stmt = text("""
                SELECT plan_id, week_number, day_of_week, phase, type, is_completed, is_missed,
                       distance_km, duration_minutes, elevation_gain_m
                FROM workouts
                WHERE plan_id IN :plan_ids
            """).bindparams(bindparam("plan_ids", expanding=True))
```

After the `adherence_trend`/`missed_by_day` computation from Task 2 (same location, after the per-athlete loop), add:

```python
    on_track = at_risk = behind = 0
    for a in athletes:
        pct = a["adherence_pct"]
        if pct is None:
            continue
        if pct >= 0.8:
            on_track += 1
        elif pct >= 0.5:
            at_risk += 1
        else:
            behind += 1
    race_readiness = {"on_track": on_track, "at_risk": at_risk, "behind": behind}

    completed_window_wos = [w for w in roster_window_wos if w["is_completed"]]
    roster_totals = {
        "distance_km": round(sum(w["distance_km"] or 0 for w in completed_window_wos), 2),
        "duration_hours": round(sum(w["duration_minutes"] or 0 for w in completed_window_wos) / 60, 2),
        "elevation_gain_m": round(sum(w["elevation_gain_m"] or 0 for w in completed_window_wos), 1),
        "workout_count": len(completed_window_wos),
    }

    eligible = [a for a in athletes if a["adherence_pct"] is not None]
    most_consistent = [
        {"athlete_id": a["athlete_id"], "name": a["name"], "adherence_pct": a["adherence_pct"]}
        for a in sorted(eligible, key=lambda a: (-a["adherence_pct"], a["name"]))[:3]
    ]
```

Add all three to the final return dict:

```python
        "race_readiness": race_readiness,
        "roster_totals": roster_totals,
        "most_consistent": most_consistent,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/tests/integration/test_coach_overview.py
git commit -m "feat(coaching): add race_readiness, roster_totals, most_consistent insights"
```

---

### Task 5: Frontend — hook types for the five new fields + window selector wiring

**Files:**
- Modify: `frontend/src/hooks/useCoachOverview.ts`

**Interfaces:**
- Consumes: the five new fields from Tasks 2-4's backend response.
- Produces: `CoachOverview` gains `adherence_trend`, `missed_by_day`, `rpe_distribution`, `race_readiness`, `roster_totals`, `most_consistent` — all typed, consumed by Task 6/7.

- [ ] **Step 1: Update the `CoachOverview` interface**

In `frontend/src/hooks/useCoachOverview.ts`, extend `CoachOverview`:

```typescript
export interface CoachOverview {
  athletes: CoachOverviewAthlete[];
  action_items: {
    draft_plans: { plan_id: number; athlete_id: number; athlete_name: string; race_name: string }[];
    pending_workout_approvals: { workout_id: number; plan_id: number; athlete_id: number; athlete_name: string; title: string }[];
  };
  phase_alerts: { athlete_id: number; athlete_name: string; phase: string; starts: "this_week" | "next_week" }[];
  workout_type_mix: { type: string; count: number; pct: number }[];
  adherence_trend: { week_number: number; adherence_pct: number }[];
  missed_by_day: { day_of_week: string; count: number }[];
  rpe_distribution: { avg_rpe: number | null; by_value: { rpe: number; count: number }[] };
  race_readiness: { on_track: number; at_risk: number; behind: number };
  roster_totals: { distance_km: number; duration_hours: number; elevation_gain_m: number; workout_count: number };
  most_consistent: { athlete_id: number; name: string; adherence_pct: number }[];
}
```

No other change in this file — `fetchOverview` (already updated in Task 1 to accept `days`) sets the whole payload untyped-at-the-JSON-boundary, so these fields flow through once declared.

- [ ] **Step 2: Verify with the type checker**

Run: `cd frontend && npx tsc --noEmit`
Expected: no new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useCoachOverview.ts
git commit -m "feat(coaching): type the five new insight fields on CoachOverview"
```

---

### Task 6: Frontend — adherence trend + missed-by-day chart components

**Files:**
- Create: `frontend/src/components/AdherenceTrendChart.tsx`
- Test: `frontend/src/components/AdherenceTrendChart.test.tsx`
- Create: `frontend/src/components/MissedByDayChart.tsx`
- Test: `frontend/src/components/MissedByDayChart.test.tsx`

**Interfaces:**
- Consumes: `overview.adherence_trend`/`overview.missed_by_day` shapes from Task 5.
- Produces: default-exported `AdherenceTrendChart({ trend, lang })` and `MissedByDayChart({ missedByDay, lang })` components, plus exported pure helpers `computeSparklinePoints`/`zeroFillDays`, consumed by Task 7.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/AdherenceTrendChart.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { computeSparklinePoints } from "./AdherenceTrendChart";

describe("computeSparklinePoints", () => {
  it("maps adherence_pct (0-1) to y coordinates within the given height, most-recent-highest-x", () => {
    const points = computeSparklinePoints(
      [{ week_number: 4, adherence_pct: 0.5 }, { week_number: 5, adherence_pct: 1.0 }],
      { width: 100, height: 40 }
    );
    expect(points).toHaveLength(2);
    expect(points[0].x).toBeLessThan(points[1].x);
    expect(points[1].y).toBeLessThan(points[0].y); // higher adherence -> smaller y (closer to top)
  });

  it("returns an empty array for empty input", () => {
    expect(computeSparklinePoints([], { width: 100, height: 40 })).toEqual([]);
  });

  it("places a single point at the right edge", () => {
    const points = computeSparklinePoints([{ week_number: 5, adherence_pct: 0.7 }], { width: 100, height: 40 });
    expect(points).toHaveLength(1);
    expect(points[0].x).toBe(100);
  });
});
```

Create `frontend/src/components/MissedByDayChart.test.tsx`:

```typescript
import { describe, it, expect } from "vitest";
import { zeroFillDays } from "./MissedByDayChart";

describe("zeroFillDays", () => {
  it("fills all 7 days in Monday-Sunday order, zero for absent days", () => {
    const filled = zeroFillDays([{ day_of_week: "Wednesday", count: 3 }, { day_of_week: "Monday", count: 5 }]);
    expect(filled.map((d) => d.day_of_week)).toEqual([
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ]);
    expect(filled.find((d) => d.day_of_week === "Wednesday")?.count).toBe(3);
    expect(filled.find((d) => d.day_of_week === "Tuesday")?.count).toBe(0);
  });

  it("returns all-zero for empty input", () => {
    const filled = zeroFillDays([]);
    expect(filled.every((d) => d.count === 0)).toBe(true);
    expect(filled).toHaveLength(7);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/AdherenceTrendChart.test.tsx src/components/MissedByDayChart.test.tsx`
Expected: FAIL — modules don't exist.

- [ ] **Step 3: Implement**

Create `frontend/src/components/AdherenceTrendChart.tsx`:

```tsx
export interface AdherenceTrendPoint {
  week_number: number;
  adherence_pct: number;
}

export function computeSparklinePoints(
  trend: AdherenceTrendPoint[],
  { width, height }: { width: number; height: number }
): { x: number; y: number }[] {
  if (trend.length === 0) return [];
  if (trend.length === 1) {
    return [{ x: width, y: (1 - trend[0].adherence_pct) * height }];
  }
  return trend.map((point, i) => ({
    x: (i / (trend.length - 1)) * width,
    y: (1 - point.adherence_pct) * height,
  }));
}

export default function AdherenceTrendChart({ trend, lang }: { trend: AdherenceTrendPoint[]; lang: "en" | "vi" }) {
  const width = 280;
  const height = 50;
  const points = computeSparklinePoints(trend, { width, height });

  if (points.length === 0) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "Not enough data yet." : "Chưa đủ dữ liệu."}
      </p>
    );
  }

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", maxWidth: `${width}px`, display: "block" }}>
      <path d={path} fill="none" stroke="var(--accent-primary)" strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={trend[i].week_number} cx={p.x} cy={p.y} r={2.5} fill="var(--accent-primary)" />
      ))}
    </svg>
  );
}
```

Create `frontend/src/components/MissedByDayChart.tsx`:

```tsx
const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const DAY_LABELS: Record<string, { en: string; vi: string }> = {
  Monday: { en: "Mon", vi: "T2" },
  Tuesday: { en: "Tue", vi: "T3" },
  Wednesday: { en: "Wed", vi: "T4" },
  Thursday: { en: "Thu", vi: "T5" },
  Friday: { en: "Fri", vi: "T6" },
  Saturday: { en: "Sat", vi: "T7" },
  Sunday: { en: "Sun", vi: "CN" },
};

export interface MissedByDayEntry {
  day_of_week: string;
  count: number;
}

export function zeroFillDays(missedByDay: MissedByDayEntry[]): MissedByDayEntry[] {
  const counts = new Map(missedByDay.map((d) => [d.day_of_week, d.count]));
  return DAY_ORDER.map((day) => ({ day_of_week: day, count: counts.get(day) ?? 0 }));
}

export default function MissedByDayChart({ missedByDay, lang }: { missedByDay: MissedByDayEntry[]; lang: "en" | "vi" }) {
  const filled = zeroFillDays(missedByDay);
  const maxCount = Math.max(...filled.map((d) => d.count), 1);

  if (filled.every((d) => d.count === 0)) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
        {lang === "en" ? "No missed workouts in this window." : "Không có buổi tập nào bị bỏ lỡ trong khoảng này."}
      </p>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "8px", height: "60px" }}>
      {filled.map((d) => (
        <div key={d.day_of_week} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", flex: 1 }}>
          <div
            style={{
              width: "100%",
              height: `${(d.count / maxCount) * 40}px`,
              background: d.count > 0 ? "var(--accent-alert)" : "var(--border-color)",
              borderRadius: "3px",
            }}
          />
          <span style={{ fontSize: "9.5px", color: "var(--text-muted)" }}>{DAY_LABELS[d.day_of_week][lang]}</span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/AdherenceTrendChart.test.tsx src/components/MissedByDayChart.test.tsx`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/AdherenceTrendChart.tsx frontend/src/components/AdherenceTrendChart.test.tsx frontend/src/components/MissedByDayChart.tsx frontend/src/components/MissedByDayChart.test.tsx
git commit -m "feat(coaching): add AdherenceTrendChart and MissedByDayChart components"
```

---

### Task 7: Wire window selector + all new insight cards into `CoachDashboardView.tsx`

**Files:**
- Modify: `frontend/src/views/CoachDashboardView.tsx`

**Interfaces:**
- Consumes: `AdherenceTrendChart` and `MissedByDayChart` (Task 6), `overview.rpe_distribution`/`race_readiness`/`roster_totals`/`most_consistent` (Task 5), `fetchOverview(days?)` (Task 1).
- Produces: no new exports — terminal UI task.

- [ ] **Step 1: Add imports and window state**

Add to the import block:

```tsx
import AdherenceTrendChart from "../components/AdherenceTrendChart";
import MissedByDayChart from "../components/MissedByDayChart";
```

Add state alongside `activeSection`/`rosterFilters` (if the Runner Levels plan has landed) or alongside `activeSection` alone otherwise:

```tsx
  const [insightsDays, setInsightsDays] = useState(14);
```

Update the initial `useEffect` that calls `fetchOverview()` to pass the window:

```tsx
  useEffect(() => {
    fetchRoster();
    fetchMyInvites();
    fetchOverview(insightsDays);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
```

Add a second effect that refetches when the window changes (skip the initial mount, since the effect above already covers it):

```tsx
  useEffect(() => {
    fetchOverview(insightsDays);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [insightsDays]);
```

- [ ] **Step 2: Add the window selector**

Immediately before the existing Workout-type-mix card (`{overview && (<div className="card" ...> ... <ChartBar .../> ... </div>)}`), add a window-selector control and wrap the whole insights section (workout-type-mix card plus the five new cards from Step 3) so the selector applies to all of them:

```tsx
          {overview && (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "8px" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                {lang === "en" ? "Insights window:" : "Khoảng thời gian:"}
              </span>
              <select
                value={insightsDays}
                onChange={(e) => setInsightsDays(Number(e.target.value))}
                style={{
                  padding: "4px 8px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: "1px solid var(--border-color)",
                  background: "var(--bg-secondary, transparent)",
                }}
              >
                <option value={7}>{lang === "en" ? "7 days" : "7 ngày"}</option>
                <option value={14}>{lang === "en" ? "14 days" : "14 ngày"}</option>
                <option value={30}>{lang === "en" ? "30 days" : "30 ngày"}</option>
                <option value={90}>{lang === "en" ? "90 days" : "90 ngày"}</option>
              </select>
            </div>
          )}
```

- [ ] **Step 3: Add the new insight cards**

Change the existing Workout-type-mix card's heading to drop the hardcoded "(last 2 weeks)" text (now driven by the selector above it, not a fixed window):

```tsx
          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <ChartBar size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Workout type mix" : "Loại buổi tập"}
                </h3>
              </div>
              <WorkoutTypeMixChart mix={overview.workout_type_mix} lang={lang} />
            </div>
          )}
```

Add five new cards right after it (each following the same `className="card"` wrapper pattern used throughout this tab):

```tsx
          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Adherence trend" : "Xu hướng tuân thủ"}
              </h3>
              <AdherenceTrendChart trend={overview.adherence_trend} lang={lang} />
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Missed workouts by day" : "Buổi tập bỏ lỡ theo ngày"}
              </h3>
              <MissedByDayChart missedByDay={overview.missed_by_day} lang={lang} />
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Effort (RPE)" : "Mức độ gắng sức (RPE)"}
              </h3>
              {overview.rpe_distribution.avg_rpe === null ? (
                <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                  {lang === "en" ? "No block reviews in this window." : "Chưa có đánh giá khối tập nào trong khoảng này."}
                </p>
              ) : (
                <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
                  <span style={{ fontSize: "28px", fontWeight: 800 }}>{overview.rpe_distribution.avg_rpe.toFixed(1)}</span>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    {lang === "en" ? "average RPE" : "RPE trung bình"}
                  </span>
                </div>
              )}
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Race readiness" : "Sẵn sàng cho giải đấu"}
              </h3>
              <div style={{ display: "flex", gap: "16px" }}>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: 800, color: "#16a34a" }}>{overview.race_readiness.on_track}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "on track" : "đúng tiến độ"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: 800, color: "#d97706" }}>{overview.race_readiness.at_risk}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "at risk" : "có rủi ro"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "22px", fontWeight: 800, color: "var(--accent-alert)" }}>{overview.race_readiness.behind}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "behind" : "chậm tiến độ"}</div>
                </div>
              </div>
            </div>
          )}

          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Roster totals" : "Tổng kết đội"}
              </h3>
              <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontSize: "20px", fontWeight: 800 }}>{overview.roster_totals.distance_km.toFixed(0)} km</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "distance" : "quãng đường"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "20px", fontWeight: 800 }}>{overview.roster_totals.duration_hours.toFixed(1)}h</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "training time" : "thời gian tập"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "20px", fontWeight: 800 }}>{Math.round(overview.roster_totals.elevation_gain_m)} m</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "elevation" : "độ cao"}</div>
                </div>
                <div>
                  <div style={{ fontSize: "20px", fontWeight: 800 }}>{overview.roster_totals.workout_count}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{lang === "en" ? "workouts" : "buổi tập"}</div>
                </div>
              </div>
            </div>
          )}

          {overview && overview.most_consistent.length > 0 && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px" }}>
              <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: "800" }}>
                {lang === "en" ? "Most consistent" : "Đều đặn nhất"}
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {overview.most_consistent.map((a, i) => (
                  <div key={a.athlete_id} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span>{i + 1}. {a.name}</span>
                    <span style={{ fontWeight: 700, color: "#16a34a" }}>{Math.round(a.adherence_pct * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
```

- [ ] **Step 4: Manual verification via the dev server**

1. Start backend and frontend against a seeded coach with a roster spanning multiple weeks of workout history (completed, missed, and unresolved), at least one `block_reviews` row, and varied adherence levels across athletes.
2. Confirm: the window dropdown defaults to 14 days and re-fetches on change (check the network request's `?days=` query param); the adherence trend sparkline renders and updates with the window; missed-by-day shows the correct days; RPE shows the average or the "not enough data" message; race readiness's three counts sum to the number of athletes with an active plan and workouts in the window; roster totals reflect only completed workouts; most-consistent shows up to 3 athletes ranked correctly.
3. Confirm the pre-existing Workout-type-mix card still renders correctly with the heading no longer saying "last 2 weeks."
4. Resize to mobile and confirm no overflow across all the new cards.

- [ ] **Step 5: Run the full test suites and commit**

Run: `cd backend && pytest tests/ -v` and `cd frontend && npm run lint && npx vitest run`
Expected: all PASS.

```bash
git add frontend/src/views/CoachDashboardView.tsx
git commit -m "feat(coaching): wire window selector and expanded insight cards into Overview tab"
```

---

## Self-Review Notes

- **Spec coverage:** dynamic `days` window (Task 1), adherence trend (Task 2), missed-by-day (Task 2), RPE distribution (Task 3), race readiness (Task 4), roster totals (Task 4), most consistent (Task 4), frontend types (Task 5), chart components (Task 6), full UI wiring including empty states (Task 7) — every spec section has a covering task.
- **Type consistency checked:** `AdherenceTrendPoint`/`MissedByDayEntry` (Task 6) match the field names in `CoachOverview` (Task 5) exactly (`week_number`/`adherence_pct`, `day_of_week`/`count`); `race_readiness`/`roster_totals`/`most_consistent` field names used in Task 7's JSX match Task 4's backend keys and Task 5's TS interface verbatim.
- **No placeholders:** every step has runnable code; Task 7 Step 4 is manual by necessity (UI verification), matching this repo's established convention.
- **Rename consistency:** Task 1 is the single place `adherence_pct_14d` → `adherence_pct` happens, across backend, tests, and both frontend files that reference it — no task after Task 1 introduces the old name.

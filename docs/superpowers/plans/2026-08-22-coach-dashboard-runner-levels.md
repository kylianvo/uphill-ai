# Coach Dashboard Runner Levels + Scalable Roster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every athlete in `get_roster_overview_data` a derived `runner_level` and a `needs_attention` flag, and let a coach search/filter their roster by name, level, needs-attention, and race — entirely client-side.

**Architecture:** Two small additions inside the existing `get_roster_overview_data` (`backend/db.py`) — a pure `runner_level()` threshold function and a `needs_attention` boolean folded into the per-athlete loop that already computes `missed_streak`/`phase_alerts`. The frontend adds a pure, unit-tested filter-predicate function and wires search/filter controls into the existing Roster-progress card in `CoachDashboardView.tsx` — no new endpoint, no new fetch.

**Tech Stack:** FastAPI + SQLAlchemy Core (`text()`), no ORM, on the backend; Next.js/React on the frontend; pytest against live Postgres for backend tests, Vitest for frontend tests.

**Spec:** [docs/superpowers/specs/2026-08-22-coach-dashboard-runner-levels-design.md](../specs/2026-08-22-coach-dashboard-runner-levels-design.md)

## Global Constraints

- No new database tables or columns — `runner_level` is derived purely from the existing `users.current_weekly_km` (`backend/db.py:59`, `REAL DEFAULT 30.0`).
- No manual level override in this pass — level is fully derived, not editable by the coach.
- No server-side pagination, virtualization, or new search/filter query params — all filtering happens client-side against the already-fetched `GET /api/coaching/overview` payload.
- Level thresholds (weekly km): Beginner `<20`, Intermediate `20–<50`, Advanced `50–<90`, Elite `>=90`. `None`/missing `current_weekly_km` falls back to the same `30.0` default every other read in this codebase already uses (`backend/db.py:1144`) — which lands in Intermediate.
- `needs_attention = True` when any of: athlete has a phase alert (this week or next week), a draft plan, a pending workout approval, or `missed_streak > 0`.
- Bilingual UI copy (en/vi) required for every new user-facing string, matching the existing `lang === "en" ? "..." : "..."` pattern in `CoachDashboardView.tsx`.

---

## File Structure

- **Modify** `backend/db.py` — add `runner_level()` function and `needs_attention` computation inside `get_roster_overview_data` (currently `db.py:1344-1490`, exact line numbers will shift slightly as earlier fixes land — locate by function name, not line number).
- **Modify** `backend/tests/integration/test_coach_overview.py` — extend with `runner_level`/`needs_attention` coverage.
- **Modify** `frontend/src/hooks/useCoachOverview.ts` — extend `CoachOverviewAthlete` with the two new fields.
- **Create** `frontend/src/utils/coachRosterFilters.ts` — pure `matchesFilters()` predicate, unit-tested in isolation.
- **Create** `frontend/src/utils/coachRosterFilters.test.ts` — tests for the predicate.
- **Modify** `frontend/src/views/CoachDashboardView.tsx` — add search/filter controls and level badges to the Roster-progress card (`CoachDashboardView.tsx:349-395` today).

---

### Task 1: Backend — `runner_level` + `needs_attention`

**Files:**
- Modify: `backend/db.py`
- Test: `backend/tests/integration/test_coach_overview.py`

**Interfaces:**
- Produces: `runner_level(current_weekly_km: float | None) -> str` (module-level function in `db.py`, returns `"beginner" | "intermediate" | "advanced" | "elite"`).
- Produces: `get_roster_overview_data(coach_id)`'s `athletes[]` entries gain two keys: `runner_level: str`, `needs_attention: bool`. No other keys change.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/integration/test_coach_overview.py`, inside the existing `TestGetRosterOverviewData` class (add these as new test methods — do not modify any existing test in that class):

```python
    def test_runner_level_boundaries(self):
        from db import runner_level

        assert runner_level(19.9) == "beginner"
        assert runner_level(20.0) == "intermediate"
        assert runner_level(49.9) == "intermediate"
        assert runner_level(50.0) == "advanced"
        assert runner_level(89.9) == "advanced"
        assert runner_level(90.0) == "elite"
        assert runner_level(None) == "intermediate"  # falls back to the 30.0 default

    def test_athlete_entries_include_runner_level_and_needs_attention(self):
        coach_id = _create_user("levels-coach1@uphill.ai")
        athlete_id = _create_user("levels-athlete1@uphill.ai")
        _link_active(coach_id, athlete_id)
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET current_weekly_km = 95 WHERE id = :id"), {"id": athlete_id}
            )
            conn.commit()

        data = get_roster_overview_data(coach_id)
        athlete = data["athletes"][0]
        assert athlete["runner_level"] == "elite"
        assert athlete["needs_attention"] is False  # no plan, no alerts, no action items

    def test_needs_attention_true_for_draft_plan_only(self):
        coach_id = _create_user("levels-coach2@uphill.ai")
        athlete_id = _create_user("levels-athlete2@uphill.ai")
        _link_active(coach_id, athlete_id)
        create_plan(
            user_id=athlete_id, race_name="Draft Race", race_date="2027-01-01", goal_type="finish",
            target_time_hours=None, total_weeks=10, plan_status="draft",
        )

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_true_for_pending_approval_only(self):
        coach_id = _create_user("levels-coach3@uphill.ai")
        athlete_id = _create_user("levels-athlete3@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id, race_name="Active Race", race_date="2027-01-01", goal_type="finish",
            target_time_hours=None, total_weeks=10, plan_status="active",
        )
        save_workouts(
            plan_id,
            [{"week_number": 1, "day_of_week": "Monday", "phase": "base", "title": "Long run",
              "type": "long_run", "duration_minutes": 60, "target_zone": "Z2"}],
            auto_approve=False,
        )

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_true_for_missed_streak_only(self):
        coach_id = _create_user("levels-coach4@uphill.ai")
        athlete_id = _create_user("levels-athlete4@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = _make_plan_with_workouts(athlete_id, current_week=5)
        past_workouts = [w for w in get_plan_workouts(plan_id) if w["week_number"] <= 5]
        update_workout_log(past_workouts[-1]["id"], is_missed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is True

    def test_needs_attention_false_for_healthy_athlete(self):
        # Deliberately does NOT use _make_plan_with_workouts: that helper always
        # tags the current_week+1 week 'taper', which would always trip the
        # phase-alert condition and make this test's own assertion wrong.
        coach_id = _create_user("levels-coach5@uphill.ai")
        athlete_id = _create_user("levels-athlete5@uphill.ai")
        _link_active(coach_id, athlete_id)
        plan_id = create_plan(
            user_id=athlete_id, race_name="Healthy Race", race_date="2026-12-01", goal_type="finish",
            target_time_hours=8.0, total_weeks=12, plan_status="active",
        )
        with engine.connect() as conn:
            conn.execute(text("UPDATE plans SET current_week = 5 WHERE id = :pid"), {"pid": plan_id})
            conn.commit()
        # All weeks in and around the window tagged 'build' -- no peak/taper/race phase anywhere.
        workouts = [
            {"week_number": wk, "day_of_week": d, "phase": "build", "title": "Run",
             "type": "easy_run", "duration_minutes": 45, "target_zone": "Z2"}
            for wk in (4, 5, 6) for d in ("Monday", "Tuesday", "Wednesday")
        ]
        save_workouts(plan_id, workouts, auto_approve=True)
        for w in get_plan_workouts(plan_id):
            update_workout_log(w["id"], is_completed=1)

        data = get_roster_overview_data(coach_id)
        assert data["athletes"][0]["needs_attention"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -k "runner_level or needs_attention" -v`
Expected: FAIL — `runner_level` doesn't exist / `KeyError: 'runner_level'` on the athlete dict.

- [ ] **Step 3: Implement in `backend/db.py`**

Add `runner_level` near the top-level constants already defined for this feature (alongside `_DAY_ORDER`/`_PHASE_ALERT_SET`, just above `get_roster_overview_data`):

```python
def runner_level(current_weekly_km: float | None) -> str:
    """Derived from users.current_weekly_km -- no manual override, no new
    column. None falls back to the same 30.0 default every other read of
    this field already uses (see the "ckm" default in update_user_profile)."""
    km = current_weekly_km if current_weekly_km is not None else 30.0
    if km < 20:
        return "beginner"
    if km < 50:
        return "intermediate"
    if km < 90:
        return "advanced"
    return "elite"
```

In `get_roster_overview_data`, add `u.current_weekly_km` to the `athlete_rows` SELECT:

```python
        athlete_rows = conn.execute(
            text("""
                SELECT ca.athlete_id, u.name AS athlete_name, u.email AS athlete_email,
                       u.current_weekly_km,
                       p.id AS plan_id, p.race_name, p.race_date, p.current_week, p.total_weeks
                FROM coach_athletes ca
                JOIN users u ON u.id = ca.athlete_id
                LEFT JOIN LATERAL (
                    SELECT * FROM plans
                    WHERE plans.user_id = ca.athlete_id AND plans.plan_status = 'active'
                    ORDER BY plans.created_at DESC, plans.id DESC
                    LIMIT 1
                ) p ON true
                WHERE ca.coach_id = :cid AND ca.status = 'active'
                ORDER BY u.name
            """),
            {"cid": coach_id},
        ).fetchall()
```

Right after `pending_workout_approvals = [_row_to_dict(r) for r in pending_rows]` (before the `athletes: list[...] = []` loop starts), build the two lookup sets:

```python
    draft_athlete_ids = {r["athlete_id"] for r in draft_plans}
    pending_athlete_ids = {r["athlete_id"] for r in pending_workout_approvals}
```

In the no-active-plan branch of the loop, add both new fields:

```python
        if plan_id is None:
            athletes.append(
                {
                    "athlete_id": row["athlete_id"],
                    "name": display_name,
                    "runner_level": runner_level(row["current_weekly_km"]),
                    "needs_attention": (
                        row["athlete_id"] in draft_athlete_ids or row["athlete_id"] in pending_athlete_ids
                    ),
                    "active_plan": None,
                    "adherence_pct_14d": None,
                    "last_completed": None,
                    "missed_streak": 0,
                }
            )
            continue
```

In the has-active-plan branch, compute `has_phase_alert` right after `next_week_phases` is computed (reuses the same sets already built for the `phase_alerts` list, no new query):

```python
        this_week_phases = {w["phase"] for w in wos_sorted if w["week_number"] == current_week}
        next_week_phases = {w["phase"] for w in wos_sorted if w["week_number"] == current_week + 1}
        has_phase_alert = bool((this_week_phases | next_week_phases) & _PHASE_ALERT_SET)
        for phase in sorted(this_week_phases & _PHASE_ALERT_SET):
```

(the two `for phase in ...` loops that follow are unchanged — leave them exactly as they are today). Then, in the final `athletes.append({...})` for this branch, add the two new fields:

```python
        athletes.append(
            {
                "athlete_id": row["athlete_id"],
                "name": display_name,
                "runner_level": runner_level(row["current_weekly_km"]),
                "needs_attention": (
                    has_phase_alert
                    or row["athlete_id"] in draft_athlete_ids
                    or row["athlete_id"] in pending_athlete_ids
                    or missed_streak > 0
                ),
                "active_plan": {
                    "plan_id": plan_id,
                    "race_name": row["race_name"],
                    "race_date": row["race_date"],
                    "current_week": current_week,
                    "total_weeks": row["total_weeks"],
                },
                "adherence_pct_14d": round(adherence, 3) if adherence is not None else None,
                "last_completed": last_completed,
                "missed_streak": missed_streak,
            }
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_coach_overview.py -v`
Expected: all tests pass (existing tests + the new ones from Step 1).

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/tests/integration/test_coach_overview.py
git commit -m "feat(coaching): add runner_level and needs_attention to roster overview"
```

---

### Task 2: Frontend hook types

**Files:**
- Modify: `frontend/src/hooks/useCoachOverview.ts`

**Interfaces:**
- Consumes: `runner_level`/`needs_attention` fields from Task 1's backend response.
- Produces: `CoachOverviewAthlete` gains `runner_level: "beginner" | "intermediate" | "advanced" | "elite"` and `needs_attention: boolean`.

- [ ] **Step 1: Update the interface**

In `frontend/src/hooks/useCoachOverview.ts`, change the `CoachOverviewAthlete` interface:

```typescript
export type RunnerLevel = "beginner" | "intermediate" | "advanced" | "elite";

export interface CoachOverviewAthlete {
  athlete_id: number;
  name: string;
  runner_level: RunnerLevel;
  needs_attention: boolean;
  active_plan: {
    plan_id: number;
    race_name: string;
    race_date: string;
    current_week: number;
    total_weeks: number;
  } | null;
  adherence_pct_14d: number | null;
  last_completed: { week_number: number; day_of_week: string } | null;
  missed_streak: number;
}
```

No other change in this file — `fetchOverview` already fetches and sets the whole payload untyped-at-the-JSON-boundary, so new fields flow through automatically once the interface declares them.

- [ ] **Step 2: Verify with the type checker**

Run: `cd frontend && npx tsc --noEmit`
Expected: no new errors (existing consumers of `CoachOverviewAthlete` don't destructure it exhaustively, so adding fields is non-breaking; if this surfaces an error, read it — it means some code narrows the type in a way that needs the new fields handled explicitly, and that's a real signal to fix, not a false positive).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useCoachOverview.ts
git commit -m "feat(coaching): add runner_level/needs_attention to CoachOverviewAthlete type"
```

---

### Task 3: Frontend — pure roster filter predicate

**Files:**
- Create: `frontend/src/utils/coachRosterFilters.ts`
- Test: `frontend/src/utils/coachRosterFilters.test.ts`

**Interfaces:**
- Consumes: `CoachOverviewAthlete` type from Task 2 (`import type { CoachOverviewAthlete, RunnerLevel } from "../hooks/useCoachOverview"`).
- Produces: `RosterFilters` type and `matchesFilters(athlete: CoachOverviewAthlete, filters: RosterFilters) -> boolean`, consumed by Task 4.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/utils/coachRosterFilters.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { matchesFilters, type RosterFilters } from "./coachRosterFilters";
import type { CoachOverviewAthlete } from "../hooks/useCoachOverview";

function makeAthlete(overrides: Partial<CoachOverviewAthlete> = {}): CoachOverviewAthlete {
  return {
    athlete_id: 1,
    name: "Jane Runner",
    runner_level: "advanced",
    needs_attention: false,
    active_plan: {
      plan_id: 1, race_name: "VMM 70km", race_date: "2026-11-15", current_week: 9, total_weeks: 16,
    },
    adherence_pct_14d: 0.8,
    last_completed: { week_number: 9, day_of_week: "Monday" },
    missed_streak: 0,
    ...overrides,
  };
}

const NO_FILTERS: RosterFilters = { search: "", level: "all", needsAttentionOnly: false, raceSearch: "" };

describe("matchesFilters", () => {
  it("matches everything when all filters are empty/default", () => {
    expect(matchesFilters(makeAthlete(), NO_FILTERS)).toBe(true);
  });

  it("name search matches case-insensitively", () => {
    expect(matchesFilters(makeAthlete({ name: "Jane Runner" }), { ...NO_FILTERS, search: "jane" })).toBe(true);
    expect(matchesFilters(makeAthlete({ name: "Jane Runner" }), { ...NO_FILTERS, search: "bob" })).toBe(false);
  });

  it("level filter matches only the selected level", () => {
    const athlete = makeAthlete({ runner_level: "elite" });
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "elite" })).toBe(true);
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "beginner" })).toBe(false);
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "all" })).toBe(true);
  });

  it("needsAttentionOnly excludes athletes with needs_attention=false", () => {
    expect(matchesFilters(makeAthlete({ needs_attention: false }), { ...NO_FILTERS, needsAttentionOnly: true })).toBe(false);
    expect(matchesFilters(makeAthlete({ needs_attention: true }), { ...NO_FILTERS, needsAttentionOnly: true })).toBe(true);
  });

  it("race search matches active_plan.race_name case-insensitively", () => {
    const athlete = makeAthlete({ active_plan: { plan_id: 1, race_name: "Fansipan Trail", race_date: "2027-01-01", current_week: 1, total_weeks: 10 } });
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "fansipan" })).toBe(true);
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "vmm" })).toBe(false);
  });

  it("race search excludes athletes with no active plan when a race search is set", () => {
    const athlete = makeAthlete({ active_plan: null });
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "vmm" })).toBe(false);
    expect(matchesFilters(athlete, NO_FILTERS)).toBe(true); // empty race search doesn't exclude no-plan athletes
  });

  it("combines all filters with AND", () => {
    const athlete = makeAthlete({
      name: "Alex Chen", runner_level: "elite", needs_attention: true,
      active_plan: { plan_id: 2, race_name: "Fansipan Trail", race_date: "2027-01-01", current_week: 1, total_weeks: 10 },
    });
    expect(matchesFilters(athlete, { search: "alex", level: "elite", needsAttentionOnly: true, raceSearch: "fansipan" })).toBe(true);
    expect(matchesFilters(athlete, { search: "alex", level: "beginner", needsAttentionOnly: true, raceSearch: "fansipan" })).toBe(false);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/utils/coachRosterFilters.test.ts`
Expected: FAIL — cannot find module `./coachRosterFilters`.

- [ ] **Step 3: Implement**

Create `frontend/src/utils/coachRosterFilters.ts`:

```typescript
import type { CoachOverviewAthlete, RunnerLevel } from "../hooks/useCoachOverview";

export interface RosterFilters {
  search: string;
  level: RunnerLevel | "all";
  needsAttentionOnly: boolean;
  raceSearch: string;
}

export function matchesFilters(athlete: CoachOverviewAthlete, filters: RosterFilters): boolean {
  if (filters.search.trim() && !athlete.name.toLowerCase().includes(filters.search.trim().toLowerCase())) {
    return false;
  }
  if (filters.level !== "all" && athlete.runner_level !== filters.level) {
    return false;
  }
  if (filters.needsAttentionOnly && !athlete.needs_attention) {
    return false;
  }
  if (filters.raceSearch.trim()) {
    const raceName = athlete.active_plan?.race_name ?? "";
    if (!raceName.toLowerCase().includes(filters.raceSearch.trim().toLowerCase())) {
      return false;
    }
  }
  return true;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/utils/coachRosterFilters.test.ts`
Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/coachRosterFilters.ts frontend/src/utils/coachRosterFilters.test.ts
git commit -m "feat(coaching): add pure roster filter predicate"
```

---

### Task 4: Wire search/filter UI + level badges into `CoachDashboardView.tsx`

**Files:**
- Modify: `frontend/src/views/CoachDashboardView.tsx`

**Interfaces:**
- Consumes: `matchesFilters`/`RosterFilters` from Task 3; `overview.athletes[].runner_level`/`needs_attention` from Tasks 1-2.
- Produces: no new exports — terminal UI task, verified via the dev server.

- [ ] **Step 1: Add imports and filter state**

Add to the import block at the top of `CoachDashboardView.tsx` (currently lines 3-8):

```tsx
import { Users, PaperPlaneTilt, ArrowRight, X, ChartBar, Warning, ClipboardText, MagnifyingGlass } from "@phosphor-icons/react";
import { useAppContext } from "../contexts/AppContext";
import { useCoachDashboard } from "../hooks/useCoachDashboard";
import { useCoachOverview } from "../hooks/useCoachOverview";
import WorkoutTypeMixChart from "../components/WorkoutTypeMixChart";
import { matchesFilters, type RosterFilters } from "../utils/coachRosterFilters";
```

Inside the component, alongside the existing `activeSection` state, add:

```tsx
  const [rosterFilters, setRosterFilters] = useState<RosterFilters>({
    search: "", level: "all", needsAttentionOnly: false, raceSearch: "",
  });
```

- [ ] **Step 2: Filter the roster list**

Immediately before the Roster-progress card's `{overview && overview.athletes.length > 0 && (` block (`CoachDashboardView.tsx:~345` today, right after the Action-items card closes), compute the filtered list:

```tsx
          {overview && (
            <div className="card" style={{ padding: isMobile ? "20px" : "28px", overflowX: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <Users size={20} weight="duotone" />
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "800" }}>
                  {lang === "en" ? "Roster progress" : "Tiến độ vận động viên"}
                </h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "14px" }}>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <div style={{ position: "relative", flex: "1 1 180px" }}>
                    <MagnifyingGlass
                      size={14}
                      style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}
                    />
                    <input
                      type="text"
                      className="chat-input"
                      style={{ width: "100%", borderRadius: "8px", padding: "8px 10px 8px 30px", fontSize: "12.5px" }}
                      placeholder={lang === "en" ? "Search by name" : "Tìm theo tên"}
                      value={rosterFilters.search}
                      onChange={(e) => setRosterFilters((f) => ({ ...f, search: e.target.value }))}
                    />
                  </div>
                  <input
                    type="text"
                    className="chat-input"
                    style={{ flex: "1 1 180px", borderRadius: "8px", padding: "8px 10px", fontSize: "12.5px" }}
                    placeholder={lang === "en" ? "Search by race" : "Tìm theo giải đấu"}
                    value={rosterFilters.raceSearch}
                    onChange={(e) => setRosterFilters((f) => ({ ...f, raceSearch: e.target.value }))}
                  />
                </div>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
                  {(["all", "beginner", "intermediate", "advanced", "elite"] as const).map((lvl) => (
                    <button
                      key={lvl}
                      onClick={() => setRosterFilters((f) => ({ ...f, level: lvl }))}
                      style={{
                        padding: "4px 10px",
                        fontSize: "11px",
                        fontWeight: 700,
                        borderRadius: "999px",
                        border: "1px solid var(--border-color)",
                        background: rosterFilters.level === lvl ? "var(--accent-primary)" : "transparent",
                        color: rosterFilters.level === lvl ? "#fff" : "var(--text-secondary)",
                        cursor: "pointer",
                        textTransform: "capitalize",
                      }}
                    >
                      {lvl === "all" ? (lang === "en" ? "All" : "Tất cả") : lvl}
                    </button>
                  ))}
                  <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", color: "var(--text-secondary)", marginLeft: "8px", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={rosterFilters.needsAttentionOnly}
                      onChange={(e) => setRosterFilters((f) => ({ ...f, needsAttentionOnly: e.target.checked }))}
                    />
                    {lang === "en" ? "Needs attention only" : "Chỉ cần chú ý"}
                  </label>
                </div>
              </div>
              {(() => {
                const filteredAthletes = overview.athletes.filter((a) => matchesFilters(a, rosterFilters));
                if (overview.athletes.length === 0) {
                  return null; // handled by the separate "No athletes yet" empty state elsewhere in this tab
                }
                if (filteredAthletes.length === 0) {
                  return (
                    <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                      {lang === "en" ? "No runners match your filters." : "Không có vận động viên nào khớp bộ lọc."}
                    </p>
                  );
                }
                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {filteredAthletes.map((athlete) => (
                      <div
                        key={athlete.athlete_id}
                        onClick={() => enterAthleteView(athlete.athlete_id, athlete.name)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "12px 14px",
                          borderRadius: "10px",
                          border: "1px solid var(--border-color)",
                          background: "rgba(255,255,255,0.4)",
                          cursor: "pointer",
                          gap: "12px",
                        }}
                      >
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ fontSize: "13.5px", fontWeight: "700" }}>{athlete.name}</span>
                            <span
                              style={{
                                fontSize: "9.5px",
                                fontWeight: 700,
                                padding: "1px 6px",
                                borderRadius: "999px",
                                background: "var(--border-color)",
                                color: "var(--text-secondary)",
                                textTransform: "capitalize",
                              }}
                            >
                              {athlete.runner_level}
                            </span>
                          </div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            {athlete.active_plan
                              ? `${athlete.active_plan.race_name} — ${lang === "en" ? "Week" : "Tuần"} ${athlete.active_plan.current_week}/${athlete.active_plan.total_weeks}`
                              : lang === "en" ? "No active plan" : "Chưa có kế hoạch"}
                          </div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                          {athlete.adherence_pct_14d !== null && (
                            <span style={{ fontSize: "12px", fontWeight: 700 }}>
                              {Math.round(athlete.adherence_pct_14d * 100)}%
                            </span>
                          )}
                          {athlete.missed_streak > 0 && (
                            <span style={{ fontSize: "11px", color: "var(--accent-alert)", fontWeight: 700 }}>
                              {athlete.missed_streak} {lang === "en" ? "missed in a row" : "buổi bỏ lỡ liên tiếp"}
                            </span>
                          )}
                          <ArrowRight size={14} weight="bold" />
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          )}
```

This **replaces** the existing `{overview && overview.athletes.length > 0 && (...)}` Roster-progress block (`CoachDashboardView.tsx:~345-395` today) in place — same card, now with a search/filter header above the list and a level badge per row. The "No athletes yet" empty-roster message (rendered elsewhere in this tab when `overview.athletes.length === 0`) is untouched and still fires first; the new `filteredAthletes.length === 0` message only shows when there are athletes but none match the active filters.

- [ ] **Step 2: Manual verification via the dev server**

Per this repo's convention for UI changes:

1. Start the backend (`cd backend && uvicorn main:app --reload --port 8000`, or reuse a running dev stack) and frontend (`cd frontend && npm run dev`).
2. Log in as a coach with a roster spanning multiple levels (vary `current_weekly_km` per athlete) and states (draft plan, pending approval, missed streak, healthy).
3. Confirm: level badges render on each row; the search box filters by name; the race search box filters by race name and excludes no-plan athletes when non-empty; level chips filter to exactly that level; "Needs attention only" shows only athletes matching the spec's four conditions; combining filters narrows further (AND semantics); clearing all filters restores the full list; a filter combination matching nothing shows "No runners match your filters" (not a blank card, not the "No athletes yet" message).
4. Resize to mobile width and confirm the search/filter row wraps cleanly, no horizontal overflow.

- [ ] **Step 3: Run the full test suites and commit**

Run: `cd backend && pytest tests/ -v` and `cd frontend && npm run lint && npx vitest run`
Expected: all PASS.

```bash
git add frontend/src/views/CoachDashboardView.tsx
git commit -m "feat(coaching): add roster search/filter UI and level badges"
```

---

## Self-Review Notes

- **Spec coverage:** runner-level classification (Task 1), `needs_attention` signal (Task 1), API shape addition (Task 1), frontend type (Task 2), search/level/needs-attention/race filtering with AND semantics (Task 3), UI wiring including empty states (Task 4) — every spec section has a covering task. Manual-override and volume-staleness are explicitly out of scope per the spec's Non-goals/Open-items and have no task.
- **Type consistency checked:** `RunnerLevel` (Task 2) matches `runner_level()`'s four return values (Task 1) exactly; `RosterFilters`/`matchesFilters` (Task 3) consumed with matching field names in Task 4's `setRosterFilters` calls (`search`, `level`, `needsAttentionOnly`, `raceSearch`).
- **No placeholders:** every step has runnable code; Task 4 Step 2 is manual by necessity (UI verification), matching this repo's established convention for frontend changes.

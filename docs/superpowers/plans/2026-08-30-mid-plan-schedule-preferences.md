# Mid-Plan Schedule Preferences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a runner edit their Schedule Preferences (days per week, preferred days, long run day, double session days, gym access, treadmill use, training environment) as part of generating their next training block, so the new preferences take effect starting with that block.

**Architecture:** Extend the existing `POST /api/coach/generate-next-block` request/flow with optional schedule fields. When present, a new `db.update_plan_schedule` does a partial (COALESCE-based) `UPDATE` on the `plans` row before block generation proceeds — no schema change, since `race_info` is already rebuilt fresh from the live `plans` row on every next-block call. On the frontend, extract the existing "Schedule Preferences" JSX block out of the plan-creation form into a reusable `ScheduleFieldsEditor` component, then reuse it inside the "Generate Next Block" modal, pre-filled from the active plan.

**Tech Stack:** FastAPI + SQLAlchemy Core (`text()`, no ORM) on the backend; Next.js 16 App Router + React state (no external state library) on the frontend; pytest (integration, real Postgres via test fixtures) and vitest (component tests) for testing.

**Spec:** [docs/superpowers/specs/2026-08-30-mid-plan-schedule-preferences-design.md](../specs/2026-08-30-mid-plan-schedule-preferences-design.md)

## Global Constraints

- No new database columns/tables — all 7 fields already exist on `plans` (added by `c3d4e5f6a7b8_add_scheduling_fields_to_plans.py` and `e5f6a7b8c9d0_plan_wise_gym_treadmill_environment.py`). No Alembic migration in this plan.
- No new cross-field validation (e.g. `days_per_week == len(preferred_run_days)`) — stay consistent with plan-creation's existing "UI constrains choices, backend trusts" convention.
- Only the `plans` row is updated — never `users` defaults.
- `preferred_run_days` and `double_session_days` are stored as JSON-encoded TEXT columns; always write with `json.dumps(...)` and read via `_parse_days`-style JSON-or-list parsing (see `services/plan_generator.py:515-523`), matching existing convention.

---

### Task 1: `db.update_plan_schedule` — partial schedule update on `plans`

**Files:**
- Modify: `backend/db.py` (add function near `get_plan_by_id`, around line 676)
- Test: `backend/tests/integration/test_generate_next_block.py` (extend — this task's test calls the function indirectly via a temporary direct-import test, since there is no dedicated db-layer unit test file for `db.py` in this repo; all `plans`-table behavior is tested through integration tests against the real test Postgres)

**Interfaces:**
- Produces: `update_plan_schedule(plan_id: int, preferred_run_days: list | None = None, long_run_day: str | None = None, days_per_week: int | None = None, double_session_days: list | None = None, has_gym_access: bool | None = None, use_treadmill: bool | None = None, training_environment: str | None = None) -> dict[str, Any] | None` — returns the full updated plan row (same shape as `get_plan_by_id`), or `None` if `plan_id` doesn't exist. Any argument left `None` keeps that column's current value.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/integration/test_generate_next_block.py` (new imports at top: add `update_plan_schedule, get_plan_by_id` to the existing `from db import get_plan_workouts, save_workouts` line):

```python
from db import get_plan_by_id, get_plan_workouts, save_workouts, update_plan_schedule
```

Add a new test class at the end of the file:

```python
class TestUpdatePlanSchedule:
    def test_updates_only_provided_fields_and_keeps_others(self, client, auth_headers, mock_plan_generation):
        plan_id, _ = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)

        updated = update_plan_schedule(plan_id, days_per_week=5, long_run_day="Sunday")

        assert updated["days_per_week"] == 5
        assert updated["long_run_day"] == "Sunday"
        # Untouched fields keep their prior value
        assert updated["preferred_run_days"] == before["preferred_run_days"]
        assert updated["training_environment"] == before["training_environment"]

    def test_returns_none_for_unknown_plan_id(self):
        assert update_plan_schedule(plan_id=999999999, days_per_week=5) is None

    def test_json_encodes_list_fields(self, client, auth_headers, mock_plan_generation):
        plan_id, _ = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])

        updated = update_plan_schedule(
            plan_id,
            preferred_run_days=["Tuesday", "Thursday", "Sunday"],
            double_session_days=["Sunday"],
        )

        assert json.loads(updated["preferred_run_days"]) == ["Tuesday", "Thursday", "Sunday"]
        assert json.loads(updated["double_session_days"]) == ["Sunday"]
```

Add `import json` to the top of the test file if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_generate_next_block.py::TestUpdatePlanSchedule -v`
Expected: FAIL with `ImportError: cannot import name 'update_plan_schedule' from 'db'`

- [ ] **Step 3: Implement `update_plan_schedule` in `backend/db.py`**

Insert immediately after `get_plan_by_id` (after line 675):

```python
def update_plan_schedule(
    plan_id: int,
    preferred_run_days: list | None = None,
    long_run_day: str | None = None,
    days_per_week: int | None = None,
    double_session_days: list | None = None,
    has_gym_access: bool | None = None,
    use_treadmill: bool | None = None,
    training_environment: str | None = None,
) -> dict[str, Any] | None:
    """Partial update of a plan's mid-plan-editable schedule columns. Any
    argument left as None keeps that column's current value (COALESCE) --
    lets callers pass only the fields the athlete actually changed."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                UPDATE plans SET
                    preferred_run_days = COALESCE(:preferred_run_days, preferred_run_days),
                    long_run_day = COALESCE(:long_run_day, long_run_day),
                    days_per_week = COALESCE(:days_per_week, days_per_week),
                    double_session_days = COALESCE(:double_session_days, double_session_days),
                    has_gym_access = COALESCE(:has_gym_access, has_gym_access),
                    use_treadmill = COALESCE(:use_treadmill, use_treadmill),
                    training_environment = COALESCE(:training_environment, training_environment)
                WHERE id = :plan_id
                RETURNING *
            """),
            {
                "plan_id": plan_id,
                "preferred_run_days": json.dumps(preferred_run_days) if preferred_run_days is not None else None,
                "long_run_day": long_run_day,
                "days_per_week": days_per_week,
                "double_session_days": json.dumps(double_session_days) if double_session_days is not None else None,
                "has_gym_access": has_gym_access,
                "use_treadmill": use_treadmill,
                "training_environment": training_environment,
            },
        )
        conn.commit()
        row = result.fetchone()
    return _row_to_dict(row) if row else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_generate_next_block.py::TestUpdatePlanSchedule -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/tests/integration/test_generate_next_block.py
git commit -m "feat: add db.update_plan_schedule for partial plan schedule updates"
```

---

### Task 2: Wire schedule fields into `generate-next-block`

**Files:**
- Modify: `backend/main.py` — `GenerateNextBlockRequest` (line 222-233), `_generate_next_block_for_athlete` (line 1762-2026), db import list (line 14-73)
- Test: `backend/tests/integration/test_generate_next_block.py`

**Interfaces:**
- Consumes: `update_plan_schedule(...)` from Task 1 (exact signature above).
- Produces: `GenerateNextBlockRequest` gains 7 new optional fields (`preferred_days`, `long_run_day`, `days_per_week`, `double_session_days`, `has_gym_access`, `use_treadmill`, `training_environment` — same names/types as `PlanGenerateRequest`'s scheduling fields, lines 182-189) that Task 4 (frontend) will send.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/integration/test_generate_next_block.py`:

```python
class TestGenerateNextBlockScheduleEdit:
    def test_schedule_fields_update_plan_row_and_flow_into_generation(self, client, auth_headers):
        plan_id, workout_id = _create_plan_with_two_weeks_of_workouts_no_mock(client, auth_headers["headers"])
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        captured = {}

        async def _capture(*args, **kwargs):
            captured["race_info"] = args[2] if len(args) > 2 else kwargs.get("race_info")
            return []

        with patch(
            "services.plan_generator.PlanGenerator.generate_plan_workouts",
            new=AsyncMock(side_effect=_capture),
        ):
            resp = client.post(
                "/api/coach/generate-next-block",
                headers=auth_headers["headers"],
                json={
                    "plan_id": plan_id,
                    "block_number": 2,
                    "override_gate": True,
                    "days_per_week": 5,
                    "long_run_day": "Sunday",
                    "preferred_days": ["Tuesday", "Thursday", "Sunday"],
                    "double_session_days": ["Sunday"],
                    "has_gym_access": True,
                    "use_treadmill": True,
                    "training_environment": "hilly",
                },
            )
            assert resp.status_code == 200, resp.text
            job_id = resp.json()["job_id"]

            status = None
            for _ in range(20):
                poll = client.get(f"/api/coach/plan-status/{job_id}", headers=auth_headers["headers"])
                status = poll.json()["status"]
                if status == "done":
                    break
                time.sleep(0.05)
            assert status == "done"

        race_info = captured["race_info"]
        assert race_info["days_per_week"] == 5
        assert race_info["long_run_day"] == "Sunday"
        assert race_info["preferred_days"] == json.dumps(["Tuesday", "Thursday", "Sunday"])
        assert race_info["training_environment"] == "hilly"
        assert race_info["has_gym_access"] is True
        assert race_info["use_treadmill"] is True

        updated_plan = get_plan_by_id(plan_id)
        assert updated_plan["days_per_week"] == 5
        assert json.loads(updated_plan["double_session_days"]) == ["Sunday"]

    def test_omitted_schedule_fields_leave_plan_unchanged(self, client, auth_headers, mock_plan_generation):
        plan_id, workout_id = _create_plan_with_two_weeks_of_workouts(client, auth_headers["headers"])
        before = get_plan_by_id(plan_id)
        client.patch(
            "/api/coach/workouts/log",
            headers=auth_headers["headers"],
            json={"workout_id": workout_id, "is_completed": 1},
        )

        resp = client.post(
            "/api/coach/generate-next-block",
            headers=auth_headers["headers"],
            json={"plan_id": plan_id, "block_number": 2, "override_gate": True},
        )
        assert resp.status_code == 200, resp.text

        after = get_plan_by_id(plan_id)
        assert after["days_per_week"] == before["days_per_week"]
        assert after["long_run_day"] == before["long_run_day"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/integration/test_generate_next_block.py::TestGenerateNextBlockScheduleEdit -v`
Expected: FAIL — `race_info["days_per_week"]` still reflects the plan's original value (3-4), not 5, because the request fields aren't wired up yet.

- [ ] **Step 3: Add the new fields to `GenerateNextBlockRequest`**

In `backend/main.py`, replace the `GenerateNextBlockRequest` class (lines 222-233):

```python
class GenerateNextBlockRequest(BaseModel):
    plan_id: int
    block_number: int  # the next block to generate (1-indexed)
    overall_rpe: int | None = None  # optional pre-submission of RPE for current block
    notes: str | None = None
    lang: str | None = None  # current UI language at click time; falls back to the user's saved lang
    override_gate: bool = False  # explicit athlete confirmation to bypass the 70% completion gate
    # Coach-authored forward guidance for THIS block (distinct from `notes`,
    # which is the athlete's own review of the block just finished) -- only
    # meaningful on the coach-triggered path.
    coach_notes: str | None = None
    # Mid-plan schedule preference edits -- optional; any field left unset
    # (None) leaves that column on the `plans` row unchanged. Same shapes as
    # PlanGenerateRequest's scheduling fields.
    preferred_days: list[str] | None = None
    long_run_day: str | None = None
    days_per_week: int | None = None
    double_session_days: list[str] | None = None
    has_gym_access: bool | None = None
    use_treadmill: bool | None = None
    training_environment: str | None = None
```

- [ ] **Step 4: Add `update_plan_schedule` to the db import list**

In `backend/main.py`, in the `from db import (...)` block, insert alphabetically between `update_onboarding_profile` and `update_user_profile` (currently lines 68-69):

```python
    update_onboarding_profile,
    update_plan_schedule,
    update_user_profile,
```

- [ ] **Step 5: Apply the update inside `_generate_next_block_for_athlete`**

In `backend/main.py`, immediately after the ownership check (after line 1778's `raise HTTPException(status_code=404, detail="Plan not found.")`, before the double-submission guard at line 1780's comment), insert:

```python
    # Mid-plan schedule preference edit: if the athlete changed any Schedule
    # Preferences field for this next block, persist it to the plans row
    # BEFORE building race_info below, so this call's own generation uses the
    # new values immediately (nothing else caches the old ones).
    _schedule_fields = (
        request.preferred_days,
        request.long_run_day,
        request.days_per_week,
        request.double_session_days,
        request.has_gym_access,
        request.use_treadmill,
        request.training_environment,
    )
    if any(f is not None for f in _schedule_fields):
        updated_plan = update_plan_schedule(
            plan_id=request.plan_id,
            preferred_run_days=request.preferred_days,
            long_run_day=request.long_run_day,
            days_per_week=request.days_per_week,
            double_session_days=request.double_session_days,
            has_gym_access=request.has_gym_access,
            use_treadmill=request.use_treadmill,
            training_environment=request.training_environment,
        )
        if updated_plan:
            plan = updated_plan
```

This keeps `plan` (already fetched a few lines above via `get_recent_plans`) in sync, so the `race_info` construction later in this function (lines 1954-1973, e.g. `plan.get("preferred_run_days")`) automatically picks up the new values without further changes.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && pytest tests/integration/test_generate_next_block.py -v`
Expected: PASS (all tests in the file, including the pre-existing gate tests — confirms no regression)

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/tests/integration/test_generate_next_block.py
git commit -m "feat: let generate-next-block update Schedule Preferences before generating"
```

---

### Task 3: Extract `ScheduleFieldsEditor` component from the plan-creation form

**Files:**
- Create: `frontend/src/components/ScheduleFieldsEditor.tsx`
- Create: `frontend/src/components/ScheduleFieldsEditor.test.tsx`
- Modify: `frontend/src/views/PlannerView.tsx` (lines 813-960, plus the "Current Weekly Mileage" block at lines 850-864 — see Step 3)

**Interfaces:**
- Consumes: `translations` from `frontend/src/app/translations.ts` (existing keys: `plan_schedule_prefs`, `plan_days_per_week`, `plan_long_run_day`, `plan_preferred_days`, `plan_gym_access`, `plan_use_treadmill`, `plan_training_environment`, `plan_training_environment_flat|hilly|mixed`, `plan_training_environment_help`, `plan_double_session_days`, `plan_double_session_help` — all already present, no new translation keys needed).
- Produces:
  ```ts
  export interface ScheduleFieldsValue {
    days_per_week: number;
    long_run_day: string;
    preferred_days: string[];
    has_gym_access: boolean;
    use_treadmill: boolean;
    training_environment: "flat" | "hilly" | "mixed";
    double_session_days: string[];
  }
  export function ScheduleFieldsEditor(props: {
    lang: string;
    t: (key: keyof typeof translations.en) => string;
    isMobile: boolean;
    value: ScheduleFieldsValue;
    onChange: (patch: Partial<ScheduleFieldsValue>) => void;
  }): JSX.Element
  ```
  Task 4 imports both `ScheduleFieldsEditor` and `ScheduleFieldsValue` from this file.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/ScheduleFieldsEditor.test.tsx`:

```tsx
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ScheduleFieldsEditor, ScheduleFieldsValue } from "./ScheduleFieldsEditor";
import { translations } from "../app/translations";

const t = (key: keyof typeof translations.en) => translations.en[key] || key;

const baseValue: ScheduleFieldsValue = {
  days_per_week: 4,
  long_run_day: "Saturday",
  preferred_days: ["Monday", "Wednesday", "Saturday"],
  has_gym_access: false,
  use_treadmill: false,
  training_environment: "flat",
  double_session_days: [],
};

describe("ScheduleFieldsEditor", () => {
  it("reports the new days-per-week value when a button is clicked", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);

    fireEvent.click(screen.getByText("6"));

    expect(onChange).toHaveBeenCalledWith({ days_per_week: 6 });
  });

  it("toggles a preferred day on and off", () => {
    const onChange = vi.fn();
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={onChange} />);

    fireEvent.click(screen.getByText("Tue"));

    expect(onChange).toHaveBeenCalledWith({ preferred_days: ["Monday", "Wednesday", "Saturday", "Tuesday"] });
  });

  it("only renders double-session-day buttons for days already in preferred_days", () => {
    render(<ScheduleFieldsEditor lang="en" t={t} isMobile={false} value={baseValue} onChange={vi.fn()} />);

    // preferred_days is Mon/Wed/Sat -- Tuesday's double-session button must not render
    const doubleSessionSection = screen.getByText(t("plan_double_session_days")).closest("div")!.parentElement!;
    expect(within(doubleSessionSection).queryAllByText("Tue")).toHaveLength(0);
  });
});
```

Note: the third test needs `within` from `@testing-library/react` — add it to the import on line 3: `import { render, screen, fireEvent, within } from "@testing-library/react";`. Also note preferred-days buttons render short labels ("Mon", "Tue", ...) while double-session buttons render the same short labels when active — since `full` for Tuesday ("Tuesday") is not in `baseValue.preferred_days`, its button is skipped entirely per the existing `if (!preferred_days.includes(full)) return null;` guard this test protects.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/ScheduleFieldsEditor.test.tsx`
Expected: FAIL — `Cannot find module './ScheduleFieldsEditor'`

- [ ] **Step 3: Create `ScheduleFieldsEditor.tsx`**

This is a verbatim extraction of `PlannerView.tsx` lines 814-960 (the `<div>...Schedule Preferences...</div>` box), with all `planForm.X` reads replaced by `value.X` and all `setPlanForm({ ...planForm, X: ... })` writes replaced by `onChange({ X: ... })`. The "Current Weekly Mileage" input (original lines 850-864) is **not** included — it stays in `PlannerView.tsx`'s create-plan form only, moved to sit immediately above this component's usage (see Step 5) since it isn't one of the 7 mid-plan-editable fields.

```tsx
import { translations } from "../app/translations";

export interface ScheduleFieldsValue {
  days_per_week: number;
  long_run_day: string;
  preferred_days: string[];
  has_gym_access: boolean;
  use_treadmill: boolean;
  training_environment: "flat" | "hilly" | "mixed";
  double_session_days: string[];
}

interface ScheduleFieldsEditorProps {
  lang: string;
  t: (key: keyof typeof translations.en) => string;
  isMobile: boolean;
  value: ScheduleFieldsValue;
  onChange: (patch: Partial<ScheduleFieldsValue>) => void;
}

const FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SHORT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const SHORT_DAYS_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

export function ScheduleFieldsEditor({ lang, t, isMobile, value, onChange }: ScheduleFieldsEditorProps) {
  return (
    <div style={{ marginBottom: "16px", padding: "14px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "12px" }}>
      <label style={{ display: "block", fontSize: "12px", fontWeight: "700", marginBottom: "10px", color: "var(--text-secondary)", letterSpacing: "0.04em", textTransform: "uppercase" }}>
        {t("plan_schedule_prefs")}
      </label>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
            {t("plan_days_per_week")}
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            {[3, 4, 5, 6, 7].map(n => (
              <button key={n} type="button" onClick={() => onChange({ days_per_week: n })}
                style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${value.days_per_week === n ? "var(--accent-primary)" : "var(--border-color)"}`, background: value.days_per_week === n ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: value.days_per_week === n ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: "700", fontSize: "13px", cursor: "pointer" }}
              >{n}</button>
            ))}
          </div>
        </div>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
            {t("plan_long_run_day")}
          </label>
          <select className="chat-input" style={{ borderRadius: "8px", width: "100%", height: "38px", padding: "0 8px", fontSize: "13px" }}
            value={value.long_run_day} onChange={e => onChange({ long_run_day: e.target.value })}>
            {FULL_DAYS.map(d => {
              const label = lang === "vi"
                ? d.replace("Monday", "Thứ Hai").replace("Tuesday", "Thứ Ba").replace("Wednesday", "Thứ Tư").replace("Thursday", "Thứ Năm").replace("Friday", "Thứ Sáu").replace("Saturday", "Thứ Bảy").replace("Sunday", "Chủ Nhật")
                : d;
              return (
                <option key={d} value={d}>{label}</option>
              );
            })}
          </select>
        </div>
      </div>

      <div>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_preferred_days")}
        </label>
        <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {SHORT_DAYS.map((short, i) => {
            const full = FULL_DAYS[i];
            const selected = value.preferred_days.includes(full);
            const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
            return (
              <button key={full} type="button"
                onClick={() => {
                  const next = selected ? value.preferred_days.filter((d) => d !== full) : [...value.preferred_days, full];
                  onChange({ preferred_days: next });
                }}
                style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: "pointer" }}
              >{label}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {lang === "en"
            ? "The AI will prioritise these days when building your weekly schedule."
            : "Trí tuệ nhân tạo (AI) sẽ ưu tiên xếp lịch tập vào các ngày này."}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", gap: "12px", marginTop: "12px" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "13px", color: "var(--text-primary)" }}>
          <input type="checkbox" checked={value.has_gym_access}
            onChange={e => onChange({ has_gym_access: e.target.checked })}
            style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
          {t("plan_gym_access")}
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "13px", color: "var(--text-primary)" }}>
          <input type="checkbox" checked={value.use_treadmill}
            onChange={e => onChange({ use_treadmill: e.target.checked })}
            style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />
          {t("plan_use_treadmill")}
        </label>
      </div>

      <div style={{ marginTop: "12px" }}>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_training_environment")}
        </label>
        <div style={{ display: "flex", gap: "6px" }}>
          {(["flat", "hilly", "mixed"] as const).map(env => {
            const selected = value.training_environment === env;
            const envKey = ("plan_training_environment_" + env) as keyof typeof translations.en;
            return (
              <button key={env} type="button" onClick={() => onChange({ training_environment: env })}
                style={{ flex: 1, padding: "7px 0", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: selected ? "700" : "500", fontSize: "13px", cursor: "pointer" }}
              >{t(envKey)}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {t("plan_training_environment_help")}
        </p>
      </div>

      <div style={{ marginTop: "12px" }}>
        <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "6px", color: "var(--text-secondary)" }}>
          {t("plan_double_session_days")}
        </label>
        <div style={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {SHORT_DAYS.map((short, i) => {
            const full = FULL_DAYS[i];
            if (!value.preferred_days.includes(full)) return null;
            const selected = value.double_session_days.includes(full);
            const disabled = !selected && value.double_session_days.length >= 2;
            const label = lang === "vi" ? SHORT_DAYS_VI[i] : short;
            return (
              <button key={full} type="button" disabled={disabled}
                onClick={() => {
                  const next = selected
                    ? value.double_session_days.filter((d) => d !== full)
                    : [...value.double_session_days, full];
                  onChange({ double_session_days: next });
                }}
                style={{ padding: "5px 10px", borderRadius: "8px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`, background: selected ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : disabled ? "var(--text-muted)" : "var(--text-secondary)", fontWeight: selected ? "700" : "500", fontSize: "12px", cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.5 : 1 }}
              >{label}</button>
            );
          })}
        </div>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "5px", margin: "5px 0 0 0" }}>
          {t("plan_double_session_help")}
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/ScheduleFieldsEditor.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 5: Rewire `PlannerView.tsx`'s create-plan form to use the new component**

In `frontend/src/views/PlannerView.tsx`:

1. Add the import near the top (alongside other component imports):
   ```tsx
   import { ScheduleFieldsEditor, ScheduleFieldsValue } from "../components/ScheduleFieldsEditor";
   ```

2. Move the "Current Weekly Mileage" block (original lines 850-864) to sit immediately **before** the `{/* ── Schedule Preferences (shared) ─────────────────── */}` comment (original line 813) instead of inside that box — same JSX, same `planForm.current_weekly_km` binding, unchanged behavior, just relocated one step earlier in the form.

3. Replace the remaining `{/* ── Schedule Preferences (shared) ─────────────────── */}` box (the `<div style={{ marginBottom: "16px", padding: "14px", ... }}>...</div>` spanning original lines 814-960, now containing everything except the mileage input) with:
   ```tsx
   <ScheduleFieldsEditor
     lang={lang}
     t={t}
     isMobile={isMobile}
     value={{
       days_per_week: planForm.days_per_week,
       long_run_day: planForm.long_run_day,
       preferred_days: planForm.preferred_days,
       has_gym_access: planForm.has_gym_access,
       use_treadmill: planForm.use_treadmill,
       training_environment: planForm.training_environment,
       double_session_days: planForm.double_session_days,
     }}
     onChange={(patch) => setPlanForm({ ...planForm, ...patch })}
   />
   ```

- [ ] **Step 6: Manually verify no regression in the create-plan form**

Run: `cd frontend && npm run dev` (or use the project's preview tooling), open the Planner tab's "Plan Settings" form (no active plan), and confirm: days-per-week buttons, long-run-day select, preferred-days chips, gym/treadmill checkboxes, training-environment buttons, and double-session-day chips all render and behave exactly as before (chips still constrained to preferred days, double-session max-2 still enforced), and the mileage input still appears in roughly the same place.

- [ ] **Step 7: Run the full frontend test suite and lint**

Run: `cd frontend && npm run lint && npx vitest run`
Expected: PASS, no new lint errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/ScheduleFieldsEditor.tsx frontend/src/components/ScheduleFieldsEditor.test.tsx frontend/src/views/PlannerView.tsx
git commit -m "refactor: extract ScheduleFieldsEditor from the plan-creation form"
```

---

### Task 4: Add schedule editing to the "Generate Next Block" modal

**Files:**
- Modify: `frontend/src/views/PlannerView.tsx` (state near line 304, `handleGenerateNextBlock` at lines 357-406, modal JSX at lines 1528-1642, the two `setShowBlockReview(true)` call sites at lines 1454 and 1486)
- Modify: `frontend/src/types/index.ts` (`ActivePlan` interface, lines 52-66)

**Interfaces:**
- Consumes: `ScheduleFieldsEditor`, `ScheduleFieldsValue` from Task 3 (`frontend/src/components/ScheduleFieldsEditor.tsx`); `GenerateNextBlockRequest`'s new optional fields from Task 2 (`preferred_days`, `long_run_day`, `days_per_week`, `double_session_days`, `has_gym_access`, `use_treadmill`, `training_environment`).

- [ ] **Step 1: Add the missing raw schedule fields to `ActivePlan`**

In `frontend/src/types/index.ts`, add to the `ActivePlan` interface (after `training_environment`, before `double_session_days`):

```ts
  preferred_run_days?: string; // JSON-encoded array, e.g. '["Monday","Wednesday"]'
  long_run_day?: string;
  days_per_week?: number;
```

- [ ] **Step 2: Add local state for the next-block schedule edit**

In `frontend/src/views/PlannerView.tsx`, near the other block-review state (after line 305's `overrideConfirmed`):

```tsx
  const [nextBlockSchedule, setNextBlockSchedule] = useState<ScheduleFieldsValue>({
    days_per_week: 4,
    long_run_day: "Saturday",
    preferred_days: [],
    has_gym_access: false,
    use_treadmill: false,
    training_environment: "flat",
    double_session_days: [],
  });
```

- [ ] **Step 3: Seed `nextBlockSchedule` from `activePlan` when the modal opens**

Add a helper function near `handleGenerateNextBlock` (before it, so it can be referenced by the two button handlers below):

```tsx
  const openBlockReviewModal = (withOverride: boolean) => {
    const p: any = activePlan || {};
    let preferredDays: string[] = [];
    try { preferredDays = JSON.parse(p.preferred_run_days || "[]"); } catch { preferredDays = []; }
    let doubleSessionDays: string[] = [];
    try { doubleSessionDays = JSON.parse(p.double_session_days || "[]"); } catch { doubleSessionDays = []; }
    setNextBlockSchedule({
      days_per_week: p.days_per_week || 4,
      long_run_day: p.long_run_day || "Saturday",
      preferred_days: preferredDays,
      has_gym_access: !!p.has_gym_access,
      use_treadmill: !!p.use_treadmill,
      training_environment: p.training_environment || "flat",
      double_session_days: doubleSessionDays,
    });
    if (withOverride) setOverrideConfirmed(true);
    setShowBlockReview(true);
  };
```

Then replace the two call sites:
- Line 1454's `onClick={() => setShowBlockReview(true)}` → `onClick={() => openBlockReviewModal(false)}`
- Line 1486's `onClick={() => { setOverrideConfirmed(true); setShowBlockReview(true); }}` → `onClick={() => openBlockReviewModal(true)}`

- [ ] **Step 4: Include the schedule fields in the next-block request body**

In `handleGenerateNextBlock` (`frontend/src/views/PlannerView.tsx:357-406`), extend the `JSON.stringify({...})` body (currently lines 369-377):

```tsx
        body: JSON.stringify({
          plan_id: activePlan.id,
          block_number: nextBlockNum,
          overall_rpe: blockReviewRpe || null,
          notes: blockReviewNotes || null,
          coach_notes: isCoachActingAsAthlete ? (blockCoachNotes || null) : null,
          lang,
          override_gate: overrideConfirmed,
          days_per_week: nextBlockSchedule.days_per_week,
          long_run_day: nextBlockSchedule.long_run_day,
          preferred_days: nextBlockSchedule.preferred_days,
          double_session_days: nextBlockSchedule.double_session_days,
          has_gym_access: nextBlockSchedule.has_gym_access,
          use_treadmill: nextBlockSchedule.use_treadmill,
          training_environment: nextBlockSchedule.training_environment,
        }),
```

- [ ] **Step 5: Render `ScheduleFieldsEditor` inside the Block Review Modal**

In `frontend/src/views/PlannerView.tsx`, inside the modal's inner container (the `<div style={{ background: "rgba(255,255,255,0.97)", ... }}>` at line 1533), two changes:

1. Add scroll handling to that container's style so the taller modal doesn't overflow the viewport on mobile — change:
   ```tsx
   background: "rgba(255,255,255,0.97)", borderRadius: "18px",
   padding: "28px 24px", maxWidth: "420px", width: "100%",
   boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
   ```
   to:
   ```tsx
   background: "rgba(255,255,255,0.97)", borderRadius: "18px",
   padding: "28px 24px", maxWidth: "420px", width: "100%",
   boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
   maxHeight: "90vh", overflowY: "auto" as const,
   ```

2. Insert the editor right after the notes `<textarea>` element closes (the one bound to `blockReviewNotes`, styled with `minHeight: "80px"`) and right before the `{isCoachActingAsAthlete && (...)}` coach-notes block:
   ```tsx
   <div style={{ marginTop: "20px" }}>
     <label style={{ display: "block", fontSize: "12px", fontWeight: "700", color: "var(--text-secondary)", marginBottom: "8px" }}>
       {lang === "en" ? "Update Schedule Preferences (optional)" : "Cập nhật Tùy chọn lịch tập (tùy chọn)"}
     </label>
     <p style={{ fontSize: "11.5px", color: "var(--text-muted)", margin: "0 0 10px" }}>
       {lang === "en"
         ? `These changes apply starting with Block ${nextBlockNum}.`
         : `Thay đổi sẽ áp dụng từ Block ${nextBlockNum}.`}
     </p>
     <ScheduleFieldsEditor
       lang={lang}
       t={t}
       isMobile={isMobile}
       value={nextBlockSchedule}
       onChange={(patch) => setNextBlockSchedule({ ...nextBlockSchedule, ...patch })}
     />
   </div>
   ```

- [ ] **Step 6: Manually verify the full flow in the browser**

Start the dev server and, with an active plan whose current block is unlocked (or use the "Generate anyway" override path): click "Generate Block N", confirm the modal shows the pre-filled Schedule Preferences section with the plan's current values, change days-per-week and preferred days, submit, wait for the job to complete, and confirm the newly generated block's workouts land on the updated days (check the calendar view). Also confirm `activePlan` in the app reflects the new `days_per_week`/`long_run_day` after the job finishes (poller already refreshes `activePlan` from `get_plan_by_id` via the existing `plan-status` response — see Task 2).

- [ ] **Step 7: Run the full frontend test suite, lint, and typecheck**

Run: `cd frontend && npm run lint && npx vitest run && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add frontend/src/views/PlannerView.tsx frontend/src/types/index.ts
git commit -m "feat: let runners edit Schedule Preferences from the Generate Next Block modal"
```

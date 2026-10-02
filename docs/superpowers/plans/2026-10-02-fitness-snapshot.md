# Fitness Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Plan tier and volume baseline come from measured COROS signals (with typed fallbacks), so a high-volume athlete is never demoted to `recreational` by unmeasured AeT/AnT values.

**Architecture:** A new `services/fitness_snapshot.py` assembles a per-athlete snapshot on read from existing tables plus a new append-only `fitness_assessments` table. The snapshot feeds a composite tier (load, performance, experience, physiology, clamped to within one tier of load), supplies `current_weekly_km`, and renders an `ATHLETE FITNESS SNAPSHOT` prompt block. The plan endpoints build it inside their async jobs and store it on `plans.fitness_snapshot`.

**Tech Stack:** FastAPI, SQLAlchemy Core `text()`, Alembic, pytest (+ pytest-asyncio), Next.js 16 / React, vitest.

**Spec:** `docs/superpowers/specs/2026-10-02-fitness-snapshot-design.md`

## Global Constraints

- Every schema change goes in BOTH `backend/db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill).
- `tests/integration` TRUNCATEs every table: run it only against the scratch `uphill_ai_test` database the root `conftest.py` sets up, never a real one.
- `threshold_source` values: exactly `lab | field | estimated | unknown`, default `unknown`. Only `lab` and `field` allow gap demotion.
- Measured volume: last 4 complete Mon–Sun weeks; a week counts only if it starts on/after the athlete's first synced COROS activity and ends on/before `last_sync_at`; at least 3 counted weeks.
- Assessment freshness for tiering: ≤ 60 days. On-demand refresh threshold: 7 days.
- Tier = composite level score: weights load 0.45, performance 0.30, experience 0.15 (lift-only), physiology 0.10 (measured thresholds only); tier = floor(score) clamped to within one tier of the load tier. Anchors: the spec's "Tier rule" table, copied verbatim into `athlete_tier.py`.
- Performance chain: best of {faster of COROS marathon prediction and Riegel road equivalent, UTMB index}; else VO2max; else threshold pace. No field percentiles.
- Chronic cap: effective weekly volume = min(4-week mean, 1.15 × 12-week mean) when ≥ 8 complete covered weeks exist; km and vert scaled by the same factor.
- Road equivalent: Riegel T × (42.195 / D)^1.06, imported VBM road results, 5–42.2 km, last 12 months, not DNF or hidden.
- Volume bands are applied to effort-km = weekly km + weekly vert / 100 (vert only when measured), for every plan.
- Hysteresis on re-plans: keep the previous tier when the composite score is within 0.1 of the boundary between it and the new tier (adjacent tiers only).
- `plans.athlete_tier` is the last resolved tier, never an override: re-plan paths pass it as `previous_tier` and `explicit_tier=None`.
- A COROS failure never blocks or fails a plan.
- Any rendered UI change needs a local screenshot (`ui-screenshot-evidence` skill); Vietnamese copy follows the `uphill-ai-vietnamese-copy` skill.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Golden fixtures and Langfuse datasets hold **synthetic look-alikes only** (`"synthetic": true`, `"provenance": "scheduler"`), never values copied from a real athlete — the `llm-change-process` skill's ground rule, and `golden_eval.py --push-langfuse` refuses non-synthetic items. The two reference athletes (the elite who reported the bug, and the product owner's own account) shape the look-alikes: same tier band, same kind of signal conflict, different numbers, no names, ids or real dates. Never write either athlete's name or email into the repo or Langfuse.
- Prompt changes follow `.claude/skills/llm-change-process/SKILL.md`: draft in Langfuse → eval with `--prompt-label` → `staging` → `production` label → sync the in-code fallback in a follow-up PR.
- Deploys are by hand from the worktree (never `deploy_server.sh`, which rsyncs a worktree `.env` over prod secrets), staging first, with backups, `alembic stamp head` after `init_db`, and `LANGFUSE_RELEASE` set.

## File Structure

| File | Responsibility |
|---|---|
| `backend/db.py` (modify) | Schema in `init_db`; helpers `record_fitness_assessment`, `get_latest_fitness_assessment`, `get_weekly_run_volumes`, `get_first_activity_at`, `set_plan_fitness_snapshot`; `threshold_source` in profile writes; disconnect cleanup |
| `backend/alembic/versions/<rev>_fitness_snapshot.py` (create) | Migration for the three schema changes |
| `backend/services/athlete_tier.py` (modify) | Composite tier: anchors, weights, `level_from`, `performance_level`, `TierDecision`, `explain_tier`; `derive_tier`/`resolve_tier` become wrappers |
| `backend/services/fitness_snapshot.py` (create) | `measured_weekly_volume`, `chronic_weekly_volume`, `best_road_marathon_equivalent` (pure), `FitnessSnapshot`, `build()` |
| `backend/services/coros_sync.py` (modify) | Record assessments on sync; `ensure_fresh_assessment` |
| `backend/services/plan_generator.py` (modify) | Use the snapshot for volume, tier and prompt block when present |
| `backend/main.py` (modify) | Build/store the snapshot in onboarding, generate-plan and next-block jobs; `threshold_source` on profile; `GET /api/auth/fitness-snapshot`; `weekly_km_from_watch` |
| `backend/services/week_rebuild.py` (modify) | Snapshot for adapt-week |
| `backend/services/goal_context.py`, `backend/services/coach_context.py` (modify) | Read predictor / snapshot |
| `backend/scripts/golden_eval.py` (modify) | Scheduler fixtures may carry a `fitness_snapshot` and an `expect` block; tier and week-2 volume scored and gated |
| `backend/tests/golden/scheduler/fixture_snapshot_*.json` (create) | Three synthetic look-alike fixtures |
| `backend/services/plan_signals.py`, `backend/services/observability.py` (modify) | Live `plan_volume_fit` and `plan_tier` scores |
| `docs/runbooks/2026-10-fitness-snapshot-release.md` (create) | Experiment record + deploy log template |
| `frontend/src/views/ProfileSettingsModal.tsx`, `frontend/src/views/OnboardingWizard.tsx`, `frontend/src/views/PlannerView.tsx`, `frontend/src/hooks/usePlanner.ts`, `frontend/src/types/index.ts`, `frontend/src/app/translations.ts` (modify) | Threshold-source select, km prefill + hint |

---

### Task 0: Sync the branch with main

The branch was cut from `2942d0a`; `origin/main` is several commits ahead (LLMOps, auth, iOS native). Line numbers below refer to the pre-sync tree; search by the quoted code, not by line.

- [ ] **Step 1:** Call the ccd_host `sync_with_base_branch` tool. Resolve any conflicts it reports.
- [ ] **Step 2:** On main, `PlanGenerator.generate_plan_workouts` is a thin traced wrapper and the body moved to `_generate_plan_workouts`. Every generator edit in Tasks 2 and 5 goes into `_generate_plan_workouts`; the wrapper only gets the Task 10 signal change.
- [ ] **Step 3:** Find the current Alembic head for Task 1:

Run: `cd backend && alembic heads`
Expected: one revision id (prod was at `43dfcba89eff` on 2026-09-30). Note it as `<HEAD>`.

---

### Task 1: Schema and DB helpers

**Files:**
- Modify: `backend/db.py` (`init_db()`, near the `coros_plan_links` table and the `ALTER TABLE plans ADD COLUMN IF NOT EXISTS athlete_tier TEXT` list; `delete_provider_data`; `update_user_profile`; `format`-free helpers at the end of the activities section near `get_weekly_training_trend`)
- Create: `backend/alembic/versions/b4f1c2d3e5a6_fitness_snapshot.py`
- Modify: `backend/tests/integration/conftest.py` (add `"fitness_assessments"` to `ALL_TABLES`, before `"plans"`)
- Test: `backend/tests/integration/test_fitness_assessments_db.py`

**Interfaces:**
- Produces:
  - `db.record_fitness_assessment(user_id: int, source: str, data: dict) -> bool` — inserts when any of `vo2max, running_level, threshold_pace, pred_5k_sec, pred_10k_sec, pred_hm_sec, pred_marathon_sec` differs from the latest row for `(user_id, source)`; returns True if inserted.
  - `db.get_latest_fitness_assessment(user_id: int) -> dict | None` — latest row, `measured_at` as an aware `datetime`.
  - `db.get_weekly_run_volumes(user_id: int, since: date) -> list[dict]` — `[{"week_start": date, "km": float, "vert_m": float}]`, Mon-start weeks (UTC), on-foot types, duplicates excluded, only weeks with activities.
  - `db.get_first_activity_at(user_id: int, provider: str) -> datetime | None`
  - `db.set_plan_fitness_snapshot(plan_id: int, snapshot: dict) -> None`
  - `users.threshold_source` readable via `get_user_by_id`.

- [ ] **Step 1: Write the failing integration test**

```python
"""fitness_assessments history + weekly run volumes. Scratch DB only."""

from datetime import UTC, date, datetime

from sqlalchemy import text

import db
from db import engine


def _user(email="fs@test.io"):
    with engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name) VALUES (:e, 'FS') RETURNING id"), {"e": email}
        ).scalar_one()
        conn.commit()
    return uid


def _activity(uid, start, km, vert=0.0, kind="trail_run", ext="x"):
    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO activities (user_id, source_provider, external_ids, activity_type,
                                    start_time, duration_seconds, distance_km, elevation_gain_m)
            VALUES (:u, 'coros', CAST(:ext AS jsonb), :k, :s, 3600, :km, :v)
        """),
            {"u": uid, "ext": f'{{"coros": "{ext}"}}', "k": kind, "s": start, "km": km, "v": vert},
        )
        conn.commit()


def test_threshold_source_defaults_to_unknown():
    uid = _user()
    assert db.get_user_by_id(uid)["threshold_source"] == "unknown"


def test_assessment_inserted_only_when_values_change():
    uid = _user()
    data = {"vo2max": 61.0, "running_level": 92.0, "threshold_pace": "3:53", "pred_marathon_sec": 10200.0}
    assert db.record_fitness_assessment(uid, "coros", data) is True
    assert db.record_fitness_assessment(uid, "coros", data) is False
    assert db.record_fitness_assessment(uid, "coros", {**data, "vo2max": 61.0000001}) is False
    assert db.record_fitness_assessment(uid, "coros", {**data, "vo2max": 62.0}) is True
    latest = db.get_latest_fitness_assessment(uid)
    assert latest["vo2max"] == 62.0
    assert latest["pred_marathon_sec"] == 10200.0
    assert latest["measured_at"].tzinfo is not None


def test_weekly_run_volumes_groups_by_monday_and_skips_non_runs():
    uid = _user()
    _activity(uid, datetime(2026, 9, 14, 6, tzinfo=UTC), 20.0, 800, ext="a")
    _activity(uid, datetime(2026, 9, 20, 6, tzinfo=UTC), 30.0, 1200, ext="b")
    _activity(uid, datetime(2026, 9, 21, 6, tzinfo=UTC), 10.0, 0, kind="indoor_run", ext="c")
    _activity(uid, datetime(2026, 9, 21, 7, tzinfo=UTC), 5.0, 0, kind="strength", ext="d")
    rows = db.get_weekly_run_volumes(uid, since=date(2026, 9, 1))
    assert rows == [
        {"week_start": date(2026, 9, 14), "km": 50.0, "vert_m": 2000.0},
        {"week_start": date(2026, 9, 21), "km": 10.0, "vert_m": 0.0},
    ]
    assert db.get_first_activity_at(uid, "coros") == datetime(2026, 9, 14, 6, tzinfo=UTC)


def test_plan_fitness_snapshot_round_trips_and_disconnect_clears_assessments():
    uid = _user()
    with engine.connect() as conn:
        pid = conn.execute(
            text("""INSERT INTO plans (user_id, race_name, race_date, goal_type, total_weeks)
                    VALUES (:u, 'R', '2026-12-01', 'race', 10) RETURNING id"""),
            {"u": uid},
        ).scalar_one()
        conn.commit()
    db.set_plan_fitness_snapshot(pid, {"tier": "sub_elite"})
    with engine.connect() as conn:
        stored = conn.execute(text("SELECT fitness_snapshot FROM plans WHERE id=:p"), {"p": pid}).scalar_one()
    assert stored == {"tier": "sub_elite"}

    db.record_fitness_assessment(uid, "coros", {"vo2max": 50.0})
    db.delete_provider_data(uid, "coros")
    assert db.get_latest_fitness_assessment(uid) is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd backend && pytest tests/integration/test_fitness_assessments_db.py -v`
Expected: FAIL — `KeyError: 'threshold_source'` / `AttributeError: module 'db' has no attribute 'record_fitness_assessment'`.

- [ ] **Step 3: Add the schema to `init_db()`**

After the `CREATE TABLE IF NOT EXISTS coros_push_usage (...)` statement, add:

```python
        CREATE TABLE IF NOT EXISTS fitness_assessments (
            id                SERIAL PRIMARY KEY,
            user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source            TEXT NOT NULL,
            vo2max            REAL,
            running_level     REAL,
            threshold_pace    TEXT,
            pred_5k_sec       REAL,
            pred_10k_sec      REAL,
            pred_hm_sec       REAL,
            pred_marathon_sec REAL,
            measured_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
```

(match the surrounding statement style — each table is its own `conn.execute(text("""..."""))` call), plus:

```python
        "CREATE INDEX IF NOT EXISTS idx_fitness_assessments_user ON fitness_assessments (user_id, measured_at DESC)",
```

And in the idempotent ALTER list next to `"ALTER TABLE plans ADD COLUMN IF NOT EXISTS athlete_tier TEXT"`:

```python
            "ALTER TABLE plans ADD COLUMN IF NOT EXISTS fitness_snapshot JSONB",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS threshold_source TEXT NOT NULL DEFAULT 'unknown'",
```

- [ ] **Step 4: Add the helpers to `db.py`** (after `get_weekly_training_trend`)

```python
_ASSESSMENT_FIELDS = (
    "vo2max", "running_level", "threshold_pace",
    "pred_5k_sec", "pred_10k_sec", "pred_hm_sec", "pred_marathon_sec",
)


def _same(stored: Any, new: Any) -> bool:
    """REAL columns are float32, so 61.3 comes back as 61.2999...; compare with tolerance."""
    if stored is None or new is None:
        return stored is None and new is None
    if isinstance(new, str):
        return stored == new
    return abs(float(stored) - float(new)) < 1e-3


def get_latest_fitness_assessment(user_id: int) -> dict[str, Any] | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("""
            SELECT * FROM fitness_assessments WHERE user_id = :uid
            ORDER BY measured_at DESC, id DESC LIMIT 1
        """),
            {"uid": user_id},
        ).fetchone()
    return _row_to_dict(row) if row else None


def record_fitness_assessment(user_id: int, source: str, data: dict[str, Any]) -> bool:
    """Append an assessment only when it differs from the latest one for this source,
    so repeated syncs do not fill the history with identical rows."""
    values = {f: data.get(f) for f in _ASSESSMENT_FIELDS}
    if all(v is None for v in values.values()):
        return False
    with engine.connect() as conn:
        latest = conn.execute(
            text(f"""
            SELECT {", ".join(_ASSESSMENT_FIELDS)} FROM fitness_assessments
            WHERE user_id = :uid AND source = :src ORDER BY measured_at DESC, id DESC LIMIT 1
        """),
            {"uid": user_id, "src": source},
        ).fetchone()
        if latest and all(_same(getattr(latest, f), values[f]) for f in _ASSESSMENT_FIELDS):
            return False
        conn.execute(
            text(f"""
            INSERT INTO fitness_assessments (user_id, source, {", ".join(_ASSESSMENT_FIELDS)})
            VALUES (:uid, :src, {", ".join(":" + f for f in _ASSESSMENT_FIELDS)})
        """),
            {"uid": user_id, "src": source, **values},
        )
        conn.commit()
    return True


def get_weekly_run_volumes(user_id: int, since: date) -> list[dict[str, Any]]:
    """On-foot km and vert per Monday-start week (UTC), from `since`. Weeks with no
    activity are absent; the caller decides whether such a week was covered by a sync."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT date_trunc('week', start_time AT TIME ZONE 'UTC')::date AS week_start,
                   COALESCE(SUM(distance_km), 0) AS km, COALESCE(SUM(elevation_gain_m), 0) AS vert
            FROM activities
            WHERE user_id = :uid AND duplicate_of IS NULL AND activity_type = ANY(:types)
              AND start_time >= :since
            GROUP BY 1 ORDER BY 1
        """),
            {"uid": user_id, "types": list(_ON_FOOT_TYPES), "since": since},
        ).fetchall()
    return [{"week_start": r.week_start, "km": round(float(r.km), 1), "vert_m": round(float(r.vert), 1)} for r in rows]


def get_first_activity_at(user_id: int, provider: str) -> datetime | None:
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT MIN(start_time) FROM activities WHERE user_id = :uid AND source_provider = :p"),
            {"uid": user_id, "p": provider},
        ).scalar()


def set_plan_fitness_snapshot(plan_id: int, snapshot: dict[str, Any]) -> None:
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE plans SET fitness_snapshot = CAST(:s AS jsonb) WHERE id = :id"),
            {"s": json.dumps(snapshot, default=str), "id": plan_id},
        )
        conn.commit()
```

Check the top of `db.py` imports `date` and `datetime`; add them to the existing `from datetime import ...` line if missing.

- [ ] **Step 5: Disconnect cleanup** — in `delete_provider_data`, inside `if provider == "coros":` add:

```python
            conn.execute(text("DELETE FROM fitness_assessments WHERE user_id = :u AND source = 'coros'"), {"u": user_id})
```

- [ ] **Step 6: Write the Alembic migration** `backend/alembic/versions/b4f1c2d3e5a6_fitness_snapshot.py`

```python
"""fitness snapshot: fitness_assessments history, users.threshold_source, plans.fitness_snapshot

Revision ID: b4f1c2d3e5a6
Revises: <HEAD>
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b4f1c2d3e5a6"
down_revision: str | Sequence[str] | None = "<HEAD>"  # from Task 0 Step 3
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fitness_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("vo2max", sa.REAL()),
        sa.Column("running_level", sa.REAL()),
        sa.Column("threshold_pace", sa.Text()),
        sa.Column("pred_5k_sec", sa.REAL()),
        sa.Column("pred_10k_sec", sa.REAL()),
        sa.Column("pred_hm_sec", sa.REAL()),
        sa.Column("pred_marathon_sec", sa.REAL()),
        sa.Column("measured_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_fitness_assessments_user", "fitness_assessments", ["user_id", sa.text("measured_at DESC")])
    op.add_column("plans", sa.Column("fitness_snapshot", postgresql.JSONB()))
    op.add_column(
        "users", sa.Column("threshold_source", sa.Text(), nullable=False, server_default="unknown")
    )


def downgrade() -> None:
    op.drop_column("users", "threshold_source")
    op.drop_column("plans", "fitness_snapshot")
    op.drop_index("idx_fitness_assessments_user", table_name="fitness_assessments")
    op.drop_table("fitness_assessments")
```

Replace both `<HEAD>` with the id from Task 0 Step 3.

- [ ] **Step 7: Add `"fitness_assessments"` to `ALL_TABLES`** in `backend/tests/integration/conftest.py`, directly before `"plans"`.

- [ ] **Step 8: Run tests**

Run: `cd backend && pytest tests/integration/test_fitness_assessments_db.py -v && alembic upgrade head --sql > /dev/null`
Expected: 4 passed; the offline SQL render succeeds.

- [ ] **Step 9: Commit**

```bash
git add backend/db.py backend/alembic/versions/b4f1c2d3e5a6_fitness_snapshot.py backend/tests/integration/conftest.py backend/tests/integration/test_fitness_assessments_db.py
git commit -m "feat(db): fitness_assessments history, threshold_source, plans.fitness_snapshot"
```

---

### Task 2: Composite tier — four dimensions, load guardrail, hysteresis

Replaces `derive_tier`'s "volume band, then nudges" logic with the composite level score from the spec's "Tier rule" section. Read that section first: the anchor table there is the source of truth for every number below.

**Files:**
- Modify: `backend/services/athlete_tier.py`
- Modify: `backend/services/plan_generator.py` (one call site, Step 6)
- Test: `backend/tests/unit/test_athlete_tier.py`

**Interfaces:**
- Produces (all in `services/athlete_tier.py`):
  - Constants: `WEIGHTS = {"load": 0.45, "performance": 0.30, "experience": 0.15, "physiology": 0.10}`, `MEASURED_THRESHOLD_SOURCES = ("lab", "field")`, `VERT_M_PER_EFFORT_KM = 100.0`, `HYSTERESIS_LEVEL = 0.1`, `FEMALE_PACE_FACTOR = 1.12`, `FEMALE_VO2_FACTOR = 0.9`, anchor lists `LOAD_ANCHORS`, `MARATHON_ANCHORS`, `UTMB_ANCHORS`, `VO2_ANCHORS`, `THRESHOLD_PACE_ANCHORS`, `EXPERIENCE_ANCHORS`, `GAP_ANCHORS`, `ANT_MAX_ANCHORS` — each `list[tuple[float, float]]` of `(value, level)`.
  - `effort_km(weekly_km: float | None, weekly_vert_m: float | None) -> float | None`
  - `level_from(value: float | None, anchors: list[tuple[float, float]]) -> float | None` — piecewise-linear; clamps to the end anchors; result clamped to `[0, 4.99]`.
  - `performance_level(marathon_sec, utmb_index, vo2max, threshold_pace_sec, gender) -> tuple[float, str] | None` — the fallback chain; the str names the source used.
  - `@dataclass TierDecision: tier: str; score: float | None; levels: dict[str, float | None]; reasons: list[str]`
  - `explain_tier(*, goal_type=None, current_weekly_km=None, weekly_vert_m=None, max_continuous_jog_min=None, historical_max_distance_km=None, aet_hr=None, ant_hr=None, max_hr=None, threshold_source=None, marathon_prediction_sec=None, utmb_index=None, vo2max=None, threshold_pace_sec=None, gender=None, previous_tier=None) -> TierDecision`
  - `derive_tier(**same kwargs) -> str` (= `explain_tier(...).tier`)
  - `resolve_tier_explained(explicit_tier=None, **same kwargs) -> TierDecision` and `resolve_tier(explicit_tier=None, **same kwargs) -> str`
  - `aet_ant_gap` unchanged.

- [ ] **Step 1: Rewrite the derivation tests.** In `test_athlete_tier.py`, keep the profile and rules-block test classes untouched. Delete the classes that test derivation, the AeT/AnT gap and `resolve_tier` (they contain `test_weekly_volume_selects_the_band`, `test_a_wide_measured_gap_demotes_a_high_volume_claim` and `test_an_explicit_override_wins`) and replace them with the classes below, which cover the same behaviours under the composite rule. Add imports: `HYSTERESIS_LEVEL, MEASURED_THRESHOLD_SOURCES, TierDecision, effort_km, explain_tier, level_from, performance_level, resolve_tier_explained`.

```python
class TestLevels:
    def test_level_interpolates_between_anchors(self):
        assert level_from(60.0, [(40.0, 2.0), (80.0, 3.0)]) == 2.5

    def test_level_clamps_at_the_ends(self):
        assert level_from(10_000.0, [(40.0, 2.0), (80.0, 3.0)]) == 3.0
        assert level_from(0.0, [(40.0, 2.0), (80.0, 3.0)]) == 2.0
        assert level_from(None, [(40.0, 2.0)]) is None

    def test_decreasing_anchors_work_for_times(self):
        # marathon: lower time is a higher level
        assert level_from(10_500.0, [(11_400.0, 3.0), (9_600.0, 4.0)]) == 3.5

    def test_effort_km(self):
        assert effort_km(127.0, 5800.0) == 185.0
        assert effort_km(70.0, None) == 70.0
        assert effort_km(None, 500.0) is None


class TestPerformanceChain:
    def test_best_of_marathon_and_utmb(self):
        level, source = performance_level(4 * 3600, 720, None, None, "male")
        assert source == "utmb_index" and level > 4.0

    def test_vo2max_only_when_no_race_signal(self):
        assert performance_level(None, None, 55.0, None, "male") == (3.0, "vo2max")
        assert performance_level(3 * 3600, None, 70.0, None, "male")[1] == "marathon"

    def test_threshold_pace_is_the_last_fallback(self):
        assert performance_level(None, None, None, 255.0, "male") == (3.0, "threshold_pace")

    def test_women_are_judged_on_scaled_anchors(self):
        men = performance_level(2 * 3600 + 55 * 60, None, None, None, "male")[0]
        women = performance_level(2 * 3600 + 55 * 60, None, None, None, "female")[0]
        assert women > men

    def test_nothing_gives_none(self):
        assert performance_level(None, None, None, None, None) is None


class TestComposite:
    @pytest.mark.parametrize(
        "weekly_km,expected",
        [(5.0, BEGINNER), (20.0, NOVICE), (60.0, RECREATIONAL), (120.0, SUB_ELITE), (200.0, ELITE)],
    )
    def test_load_alone_reproduces_the_bands(self, weekly_km, expected):
        assert derive_tier(current_weekly_km=weekly_km) == expected

    def test_unknown_volume_and_nothing_else_is_the_default(self):
        assert derive_tier() == DEFAULT_TIER

    def test_beginner_rules_still_win(self):
        assert derive_tier(goal_type="start_running", current_weekly_km=100.0, utmb_index=800) == BEGINNER
        assert derive_tier(max_continuous_jog_min=5, current_weekly_km=100.0) == BEGINNER

    def test_regression_elite_reporter_is_sub_elite_not_recreational(self):
        """REGRESSION (prod, 2026-09): high measured load, 18% AeT/AnT gap of unknown
        source. The old rule demoted this athlete to recreational."""
        d = explain_tier(
            current_weekly_km=134.0, weekly_vert_m=5300.0, marathon_prediction_sec=10380.0,
            historical_max_distance_km=50.0, aet_hr=134, ant_hr=163, max_hr=183,
            threshold_source="unknown", gender="male",
        )
        assert d.tier == SUB_ELITE
        assert d.levels["physiology"] is None
        assert any("not used" in r for r in d.reasons)

    def test_load_only_vert_heavy_athlete_reaches_elite(self):
        assert derive_tier(current_weekly_km=134.0, weekly_vert_m=5300.0) == ELITE

    def test_fast_runner_on_low_volume_moves_up_one(self):
        assert derive_tier(current_weekly_km=50.0, marathon_prediction_sec=2 * 3600 + 35 * 60) == SUB_ELITE

    def test_guardrail_caps_at_one_tier_above_load(self):
        d = explain_tier(
            current_weekly_km=30.0, marathon_prediction_sec=2 * 3600 + 12 * 60,
            aet_hr=165, ant_hr=172, max_hr=182, threshold_source="lab",
        )
        assert d.score >= 3.0
        assert d.tier == RECREATIONAL  # load tier is novice

    @pytest.mark.parametrize("source", MEASURED_THRESHOLD_SOURCES)
    def test_measured_wide_gap_pulls_down(self, source):
        assert derive_tier(current_weekly_km=90.0, aet_hr=110, ant_hr=170, threshold_source=source) == RECREATIONAL

    @pytest.mark.parametrize("source", [None, "unknown", "estimated"])
    def test_unmeasured_gap_is_ignored(self, source):
        assert derive_tier(current_weekly_km=90.0, aet_hr=110, ant_hr=170, threshold_source=source) == SUB_ELITE

    def test_measured_narrow_gap_keeps_a_high_volume_runner(self):
        assert derive_tier(current_weekly_km=90.0, aet_hr=155, ant_hr=169, threshold_source="field") == SUB_ELITE

    def test_measured_gap_never_drops_two_tiers(self):
        assert derive_tier(current_weekly_km=200.0, aet_hr=100, ant_hr=180, threshold_source="lab") == SUB_ELITE

    def test_experience_lifts_but_never_drags(self):
        assert derive_tier(current_weekly_km=50.0, historical_max_distance_km=5.0) == RECREATIONAL
        assert derive_tier(current_weekly_km=10.0, historical_max_distance_km=30.0) == NOVICE

    def test_unusable_threshold_inputs_are_ignored(self):
        assert derive_tier(current_weekly_km=200.0, aet_hr=180, ant_hr=170, threshold_source="lab") == ELITE

    def test_reasons_name_every_dimension(self):
        d = explain_tier(current_weekly_km=70.0, vo2max=57.0, gender="male")
        assert d.levels["load"] is not None and d.levels["performance"] is not None
        text = " ".join(d.reasons)
        assert "load" in text and "performance" in text and "score" in text


class TestHysteresis:
    def test_keeps_previous_tier_just_over_the_boundary(self):
        assert derive_tier(current_weekly_km=84.0, previous_tier=RECREATIONAL) == RECREATIONAL  # score 3.05

    def test_keeps_previous_tier_just_under_the_boundary(self):
        assert derive_tier(current_weekly_km=78.0, previous_tier=SUB_ELITE) == SUB_ELITE  # score 2.95

    def test_moves_once_clearly_past(self):
        assert derive_tier(current_weekly_km=96.0, previous_tier=RECREATIONAL) == SUB_ELITE  # score 3.2

    def test_new_plans_use_the_plain_score(self):
        assert derive_tier(current_weekly_km=84.0) == SUB_ELITE

    def test_never_holds_across_two_tiers(self):
        assert derive_tier(current_weekly_km=134.0, weekly_vert_m=5300.0, previous_tier=RECREATIONAL) == ELITE


class TestResolveTier:
    def test_an_explicit_override_wins(self):
        assert resolve_tier(explicit_tier="elite", current_weekly_km=20.0) == ELITE
        assert resolve_tier_explained(explicit_tier="elite").reasons == ["explicit plan override"]

    def test_an_unrecognised_override_is_ignored(self):
        assert resolve_tier(explicit_tier="pro", current_weekly_km=20.0) == NOVICE

    def test_override_is_case_and_whitespace_insensitive(self):
        assert resolve_tier(explicit_tier="  Sub_Elite ", current_weekly_km=20.0) == SUB_ELITE

    def test_a_stored_tier_no_longer_freezes_a_replan(self):
        """REGRESSION: next block passed plans.athlete_tier as the override, so a plan first
        resolved as recreational stayed recreational forever."""
        assert resolve_tier(explicit_tier=None, current_weekly_km=134.0, previous_tier=RECREATIONAL) == SUB_ELITE
```

Move `test_derived_thresholds_must_not_cap_the_entire_user_base` into `TestComposite` unchanged before deleting its class: its first assertion still holds (no thresholds, 200 km → elite) and its `aet_ant_gap` assertion is untouched.

- [ ] **Step 2: Run to verify failure** — `cd backend && pytest tests/unit/test_athlete_tier.py -v` → FAIL (`ImportError: cannot import name 'TierDecision'`).

- [ ] **Step 3: Implement the anchors and helpers** in `athlete_tier.py`, after `CONTINUOUS_JOG_BEGINNER_CEILING_MIN`. Add `import math` and extend the dataclass import with `field`.

```python
# --- Composite tier --------------------------------------------------------------
# The tier is a weighted mean of four dimensions, each mapped to a continuous level on
# the TIER_ORDER scale (0 beginner .. 4 elite). ALL ANCHORS AND WEIGHTS ARE CONVENTIONAL
# DEFAULTS, UNSOURCED, gathered here so a coach can correct them in one place.
# Spec: docs/superpowers/specs/2026-10-02-fitness-snapshot-design.md ("Tier rule").

WEIGHTS = {"load": 0.45, "performance": 0.30, "experience": 0.15, "physiology": 0.10}
MAX_LEVEL = 4.99
HYSTERESIS_LEVEL = 0.1
VERT_M_PER_EFFORT_KM = 100.0
FEMALE_PACE_FACTOR = 1.12
FEMALE_VO2_FACTOR = 0.9
MEASURED_THRESHOLD_SOURCES = ("lab", "field")

# Matches the old volume bands exactly, so load alone reproduces the old tiers.
LOAD_ANCHORS = [(0.0, 0.0), (15.0, 1.0), (40.0, 2.0), (80.0, 3.0), (160.0, 4.0), (320.0, 5.0)]
MARATHON_ANCHORS = [(25200.0, 0.0), (19800.0, 1.0), (15300.0, 2.0), (11400.0, 3.0), (9600.0, 4.0), (7800.0, 5.0)]
UTMB_ANCHORS = [(250.0, 1.0), (400.0, 2.0), (550.0, 3.0), (700.0, 4.0), (850.0, 5.0)]
VO2_ANCHORS = [(38.0, 1.0), (45.0, 2.0), (55.0, 3.0), (65.0, 4.0), (75.0, 5.0)]
THRESHOLD_PACE_ANCHORS = [(360.0, 1.0), (300.0, 2.0), (255.0, 3.0), (220.0, 4.0), (190.0, 5.0)]
EXPERIENCE_ANCHORS = [(0.0, 0.0), (10.0, 1.0), (21.0, 2.0), (42.0, 3.0), (80.0, 4.0), (160.0, 5.0)]
GAP_ANCHORS = [(0.50, 0.0), (0.35, 1.0), (0.30, 2.0), (0.10, 3.0), (0.07, 4.0), (0.04, 5.0)]
ANT_MAX_ANCHORS = [(0.80, 2.0), (0.87, 3.0), (0.91, 4.0), (0.94, 5.0)]


def effort_km(weekly_km: float | None, weekly_vert_m: float | None) -> float | None:
    """A kilometre plus 100 m of climbing counts as two."""
    if weekly_km is None:
        return None
    return round(weekly_km + (weekly_vert_m or 0.0) / VERT_M_PER_EFFORT_KM, 1)


def level_from(value: float | None, anchors: list[tuple[float, float]]) -> float | None:
    """Piecewise-linear level for `value`; works for rising (km) and falling (time,
    gap) anchors. Clamped to the end anchors and to [0, MAX_LEVEL]."""
    if value is None:
        return None
    pts = sorted(anchors)
    if value <= pts[0][0]:
        level = pts[0][1]
    elif value >= pts[-1][0]:
        level = pts[-1][1]
    else:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if x0 <= value <= x1:
                level = y0 + (y1 - y0) * (value - x0) / (x1 - x0)
                break
    return round(min(max(level, 0.0), MAX_LEVEL), 3)


def _scaled(anchors: list[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(x * factor, y) for x, y in anchors]


def performance_level(
    marathon_sec: float | None,
    utmb_index: float | None,
    vo2max: float | None,
    threshold_pace_sec: float | None,
    gender: str | None,
) -> tuple[float, str] | None:
    """Fallback chain. Race-derived signals first (best of the two); VO2max and threshold
    pace only when there is none, because COROS derives its predictor from them and
    counting both would weight one measurement twice."""
    female = (gender or "").lower() == "female"
    race = [
        (level_from(marathon_sec, _scaled(MARATHON_ANCHORS, FEMALE_PACE_FACTOR if female else 1.0)), "marathon"),
        (level_from(utmb_index, UTMB_ANCHORS), "utmb_index"),
    ]
    race = [(lv, src) for lv, src in race if lv is not None]
    if race:
        return max(race)
    if vo2max:
        return level_from(vo2max, _scaled(VO2_ANCHORS, FEMALE_VO2_FACTOR if female else 1.0)), "vo2max"
    if threshold_pace_sec:
        anchors = _scaled(THRESHOLD_PACE_ANCHORS, FEMALE_PACE_FACTOR if female else 1.0)
        return level_from(threshold_pace_sec, anchors), "threshold_pace"
    return None


def _tier_at(level: float) -> str:
    return TIER_ORDER[min(int(math.floor(level)), len(TIER_ORDER) - 1)]


@dataclass
class TierDecision:
    tier: str
    score: float | None = None
    levels: dict[str, float | None] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
```

Check the level examples in Step 1 against these anchors before moving on: VO2max 55 → 3.0; threshold 255 s (4:15) → 3.0; 60 km → 2.5.

- [ ] **Step 4: Implement `explain_tier` and the wrappers.** Replace the bodies of `derive_tier` and `resolve_tier` (keep the module's existing docstrings where they still describe the behaviour; update the `derive_tier` docstring to describe the composite and point to the spec):

```python
def explain_tier(
    *,
    goal_type: str | None = None,
    current_weekly_km: float | None = None,
    weekly_vert_m: float | None = None,
    max_continuous_jog_min: int | None = None,
    historical_max_distance_km: float | None = None,
    aet_hr: float | None = None,
    ant_hr: float | None = None,
    max_hr: float | None = None,
    threshold_source: str | None = None,
    marathon_prediction_sec: float | None = None,
    utmb_index: float | None = None,
    vo2max: float | None = None,
    threshold_pace_sec: float | None = None,
    gender: str | None = None,
    previous_tier: str | None = None,
) -> TierDecision:
    if (goal_type or "").strip().lower() in BEGINNER_GOAL_TYPES:
        return TierDecision(BEGINNER, reasons=["start-running goal"])
    if max_continuous_jog_min is not None and max_continuous_jog_min < CONTINUOUS_JOG_BEGINNER_CEILING_MIN:
        return TierDecision(BEGINNER, reasons=[f"cannot jog {CONTINUOUS_JOG_BEGINNER_CEILING_MIN} min continuously"])

    reasons: list[str] = []
    levels: dict[str, float | None] = {}

    load = effort_km(current_weekly_km, weekly_vert_m)
    levels["load"] = level_from(load, LOAD_ANCHORS) if load and load > 0 else None
    if levels["load"] is not None:
        reasons.append(f"load {levels['load']:.1f} ({load:.0f} effort-km)")

    perf = performance_level(marathon_prediction_sec, utmb_index, vo2max, threshold_pace_sec, gender)
    levels["performance"] = perf[0] if perf else None
    if perf:
        reasons.append(f"performance {perf[0]:.1f} ({perf[1]})")

    gap = aet_ant_gap(aet_hr, ant_hr)
    measured = (threshold_source or "").lower() in MEASURED_THRESHOLD_SOURCES
    phys = []
    if measured and gap is not None:
        phys.append(level_from(gap, GAP_ANCHORS))
        if max_hr and ant_hr and ant_hr < max_hr:
            phys.append(level_from(ant_hr / max_hr, ANT_MAX_ANCHORS))
    levels["physiology"] = round(sum(phys) / len(phys), 3) if phys else None
    if levels["physiology"] is not None:
        reasons.append(f"physiology {levels['physiology']:.1f} (measured, {threshold_source})")
    elif gap is not None:
        reasons.append(f"physiology not used: AeT/AnT gap {gap:.0%}, source {threshold_source or 'unknown'}")

    def _mean(keys: list[str]) -> float | None:
        present = [(levels[k], WEIGHTS[k]) for k in keys if levels.get(k) is not None]
        if not present:
            return None
        return sum(v * w for v, w in present) / sum(w for _, w in present)

    base_keys = ["load", "performance", "physiology"]
    score = _mean(base_keys)
    # Experience lifts only: a short or missing long run in our data (30-day backfill,
    # no imported races) is not evidence of inexperience.
    exp = level_from(historical_max_distance_km, EXPERIENCE_ANCHORS) if historical_max_distance_km else None
    levels["experience"] = exp
    if exp is not None and (score is None or exp > score):
        score = _mean(base_keys + ["experience"])
        reasons.append(f"experience {exp:.1f} (longest {historical_max_distance_km:.0f} km)")
    elif exp is not None:
        reasons.append(f"experience {exp:.1f} not above the other dimensions, unused")

    if score is None:
        return TierDecision(DEFAULT_TIER, None, levels, ["no usable signal, default tier"])

    tier = _tier_at(score)
    load_tier = _tier_at(levels["load"]) if levels["load"] is not None else DEFAULT_TIER
    lo = max(TIER_ORDER.index(load_tier) - 1, 0)
    hi = min(TIER_ORDER.index(load_tier) + 1, len(TIER_ORDER) - 1)
    clamped = TIER_ORDER[min(max(TIER_ORDER.index(tier), lo), hi)]
    if clamped != tier:
        reasons.append(f"kept within one tier of load ({load_tier})")
        tier = clamped

    if previous_tier in TIER_PROFILES and previous_tier != tier:
        a, b = TIER_ORDER.index(tier), TIER_ORDER.index(previous_tier)
        if abs(a - b) == 1 and abs(score - max(a, b)) <= HYSTERESIS_LEVEL:
            reasons.append(f"within {HYSTERESIS_LEVEL} of the boundary, kept previous tier {previous_tier}")
            tier = previous_tier

    reasons.append(f"score {score:.2f} -> {tier}")
    return TierDecision(tier, round(score, 3), levels, reasons)


def derive_tier(**kwargs: Any) -> str:
    """Tier only; see explain_tier."""
    return explain_tier(**kwargs).tier


def resolve_tier_explained(explicit_tier: str | None = None, **kwargs: Any) -> TierDecision:
    """An explicit per-plan override when one is set, otherwise the composite.
    An unrecognised override is ignored rather than honoured, so a typo degrades to
    derivation instead of silently selecting the default profile."""
    if explicit_tier and explicit_tier.strip().lower() in TIER_PROFILES:
        return TierDecision(explicit_tier.strip().lower(), reasons=["explicit plan override"])
    return explain_tier(**kwargs)


def resolve_tier(explicit_tier: str | None = None, **kwargs: Any) -> str:
    return resolve_tier_explained(explicit_tier, **kwargs).tier
```

`explain_tier` is keyword-only, so an unknown kwarg fails loudly in tests. Add `from typing import Any`. Delete the old `aet_ant_gap_max`-based demotion block and the old long-run promotion block (both subsumed). Leave `TierProfile.aet_ant_gap_max` and `weekly_km_min/max` in place: `test_the_volume_bands_are_contiguous_and_ascending` and prompt rules still read them; add a comment on `weekly_km_min` that `LOAD_ANCHORS` must match these bands.

- [ ] **Step 5: Run tests** — `cd backend && pytest tests/unit/test_athlete_tier.py -v`. Expected: all pass. If a composite example misses by a hair, recompute it from the anchors (the expected levels are in the test comments) — do not loosen an assertion without writing down why in the test.

- [ ] **Step 6: Keep the non-snapshot generator path working.** In `_generate_plan_workouts`, the existing `resolve_tier(...)` call passes `current_weekly_km`, `goal_type`, `max_continuous_jog_min`, `historical_max_distance_km`, `aet_hr`, `ant_hr`, `explicit_tier` by keyword — still valid. Add:

```python
            max_hr=max_hr,
            threshold_source=user_profile.get("threshold_source"),
            gender=gender,
```

Run: `cd backend && pytest tests/unit -q -m "not kafka"` → pass (`test_pace_tier_defaults.py`, `test_kb_seed_tiers.py`, `test_prompt_enrichment.py` included).

- [ ] **Step 7: Commit**

```bash
git add backend/services/athlete_tier.py backend/services/plan_generator.py backend/tests/unit/test_athlete_tier.py
git commit -m "feat(tier): composite level from load, performance, experience, physiology"
```

---

### Task 3: Fitness snapshot service

**Files:**
- Create: `backend/services/fitness_snapshot.py`
- Test: `backend/tests/unit/test_fitness_snapshot.py`

**Interfaces:**
- Consumes: Task 1 db helpers; `db.get_user_by_id`, `db.get_connection(user_id, "coros")`, `db.get_utmb_index`, `db.get_recent_readiness_summary(user_id, days=7)`; Task 2 `resolve_tier_explained`.
- Produces:
  - `measured_weekly_volume(weeks: list[dict], first_activity_at: datetime | None, last_sync_at: datetime | None, today: date) -> tuple[float, float, date] | None` → `(avg_km, avg_vert_m, last_counted_week_end)`
  - `@dataclass FitnessSnapshot` with fields `weekly_km: float`, `weekly_km_source: str`, `weekly_vert_m: float | None`, `volume_as_of: str | None`, `threshold_pace: str | None`, `threshold_pace_source: str | None`, `assessment: dict | None` (fresh, ≤ 60 days, else None), `utmb_index: int | None`, `threshold_source: str`, `gender: str | None`, `readiness: dict | None`, `notes: list[str]`, `tier: str | None = None`, `tier_reasons: list[str]`
  - `FitnessSnapshot.resolve_tier(explicit_tier, goal_type, max_continuous_jog_min, historical_max_distance_km, aet_hr, ant_hr, max_hr=None, previous_tier=None) -> str` — sets and returns `self.tier`; sets `self.tier_reasons`, `self.tier_score`, `self.tier_levels`
  - `FitnessSnapshot.prompt_block(lang: str) -> str`
  - `FitnessSnapshot.to_dict() -> dict`
  - `build(user_id: int, typed_weekly_km: float | None = None, typed_is_override: bool = False, today: date | None = None) -> FitnessSnapshot`

- [ ] **Step 1: Write the failing tests**

```python
"""Snapshot priority rules. DB is stubbed; the pure volume rule is tested directly."""

from datetime import UTC, date, datetime, timedelta

import pytest

from services import fitness_snapshot as fs

TODAY = date(2026, 10, 2)  # Thursday; current week starts Mon Sep 28
WEEKS = [
    {"week_start": date(2026, 8, 31), "km": 148.7, "vert_m": 8146.0},
    {"week_start": date(2026, 9, 7), "km": 125.5, "vert_m": 1837.0},
    {"week_start": date(2026, 9, 14), "km": 126.8, "vert_m": 5808.0},
    {"week_start": date(2026, 9, 21), "km": 27.5, "vert_m": 0.0},
]
FIRST = datetime(2026, 8, 23, tzinfo=UTC)


class TestMeasuredWeeklyVolume:
    def test_partial_week_after_last_sync_is_excluded(self):
        """REGRESSION: sync stopped Sep 25, so the Sep 21 week (27.5 km) is incomplete."""
        km, vert, end = fs.measured_weekly_volume(WEEKS, FIRST, datetime(2026, 9, 25, 1, 54, tzinfo=UTC), TODAY)
        assert km == pytest.approx((148.7 + 125.5 + 126.8) / 3, abs=0.1)
        assert end == date(2026, 9, 20)

    def test_covered_week_without_activity_counts_as_zero(self):
        weeks = [w for w in WEEKS if w["week_start"] != date(2026, 9, 7)]
        km, _, _ = fs.measured_weekly_volume(weeks, FIRST, datetime(2026, 10, 1, tzinfo=UTC), TODAY)
        assert km == pytest.approx((148.7 + 0 + 126.8 + 27.5) / 4, abs=0.1)

    def test_weeks_before_the_first_synced_activity_do_not_count(self):
        assert fs.measured_weekly_volume(WEEKS, datetime(2026, 9, 10, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC), TODAY) is None

    def test_fewer_than_three_weeks_returns_none(self):
        assert fs.measured_weekly_volume(WEEKS, FIRST, datetime(2026, 9, 15, tzinfo=UTC), TODAY) is None

    def test_no_sync_returns_none(self):
        assert fs.measured_weekly_volume(WEEKS, FIRST, None, TODAY) is None


@pytest.fixture
def stub_db(monkeypatch):
    state = {
        "user": {"id": 30, "current_weekly_km": 120.0, "threshold_pace": "4:10", "threshold_source": "unknown",
                 "gender": None, "aet_hr": 134, "ant_hr": 163},
        "connection": {"status": "active", "last_sync_at": datetime(2026, 9, 25, 1, 54, tzinfo=UTC)},
        "assessment": {"vo2max": 61.0, "running_level": 92.0, "threshold_pace": "3:53", "pred_marathon_sec": 10320.0,
                       "pred_hm_sec": 4860.0, "measured_at": datetime(2026, 9, 25, tzinfo=UTC)},
        "utmb": None,
    }
    monkeypatch.setattr(fs.db, "get_user_by_id", lambda uid: state["user"])
    monkeypatch.setattr(fs.db, "get_connection", lambda uid, p: state["connection"])
    monkeypatch.setattr(fs.db, "get_latest_fitness_assessment", lambda uid: state["assessment"])
    monkeypatch.setattr(fs.db, "get_weekly_run_volumes", lambda uid, since: WEEKS)
    monkeypatch.setattr(fs.db, "get_first_activity_at", lambda uid, p: FIRST)
    monkeypatch.setattr(fs.db, "get_utmb_index", lambda uid: state["utmb"])
    monkeypatch.setattr(fs.db, "get_recent_readiness_summary", lambda uid, days=7: {"days_recorded": 0})
    return state


class TestBuild:
    def test_measured_volume_beats_profile_value(self, stub_db):
        snap = fs.build(30, today=TODAY)
        assert snap.weekly_km_source == "coros"
        assert snap.weekly_km == pytest.approx(133.7, abs=0.1)

    def test_measured_volume_beats_a_typed_prefill(self, stub_db):
        assert fs.build(30, typed_weekly_km=90.0, today=TODAY).weekly_km_source == "coros"

    def test_athlete_override_wins(self, stub_db):
        snap = fs.build(30, typed_weekly_km=90.0, typed_is_override=True, today=TODAY)
        assert (snap.weekly_km, snap.weekly_km_source) == (90.0, "self_reported")
        assert any("athlete override" in n for n in snap.notes)

    def test_no_connection_falls_back_to_typed_then_profile(self, stub_db):
        stub_db["connection"] = None
        assert fs.build(30, typed_weekly_km=80.0, today=TODAY).weekly_km == 80.0
        assert fs.build(30, today=TODAY).weekly_km == 120.0

    def test_fresh_assessment_threshold_pace_beats_typed(self, stub_db):
        snap = fs.build(30, today=TODAY)
        assert (snap.threshold_pace, snap.threshold_pace_source) == ("3:53", "coros")

    def test_stale_assessment_is_ignored(self, stub_db):
        stub_db["assessment"]["measured_at"] = datetime(2026, 7, 1, tzinfo=UTC)
        snap = fs.build(30, today=TODAY)
        assert snap.assessment is None
        assert (snap.threshold_pace, snap.threshold_pace_source) == ("4:10", "self_reported")

    def test_regression_tier_is_not_recreational(self, stub_db):
        snap = fs.build(30, today=TODAY)
        tier = snap.resolve_tier(None, "race", None, 80.0, 134, 163)
        assert tier in ("sub_elite", "elite")
        assert snap.to_dict()["tier"] == tier

    def test_prompt_block_lists_sources_and_skips_missing(self, stub_db):
        snap = fs.build(30, today=TODAY)
        snap.resolve_tier(None, "race", None, None, 134, 163)
        block = snap.prompt_block("en")
        assert block.startswith("ATHLETE FITNESS SNAPSHOT")
        assert "134 km/week" in block and "COROS" in block
        assert "Marathon prediction 2:52:00" in block
        assert "UTMB" not in block
        assert "not used" in block
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/unit/test_fitness_snapshot.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.fitness_snapshot'`.

- [ ] **Step 3: Implement `backend/services/fitness_snapshot.py`**

```python
"""What we know about an athlete's current fitness, and where each number came from.

Plan generation used to read the km/week typed into a form and the stored AeT/AnT pair,
and nothing the watch measured. A 130 km/week athlete with default-looking thresholds was
demoted to `recreational` and handed 40-60 km weeks. This module assembles the measured
signals first and falls back to typed values, recording the source of each so a plan's
tier can be audited from plans.fitness_snapshot. Spec:
docs/superpowers/specs/2026-10-02-fitness-snapshot-design.md
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

import db
from services.athlete_tier import resolve_tier_explained

PROVIDER = "coros"
VOLUME_WEEKS = 4
MIN_COUNTED_WEEKS = 3
ASSESSMENT_MAX_AGE = timedelta(days=60)


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def measured_weekly_volume(
    weeks: list[dict[str, Any]],
    first_activity_at: datetime | None,
    last_sync_at: datetime | None,
    today: date,
) -> tuple[float, float, date] | None:
    """Mean km and vert over the last complete weeks a sync actually covered.

    A week counts when it starts on or after the first synced activity (before that we
    simply have no data) and ends before the last sync (after that the week is partial).
    A counted week with no activity is a real zero. None when fewer than
    MIN_COUNTED_WEEKS weeks qualify."""
    if not last_sync_at or not first_activity_at:
        return None
    first_day = _aware(first_activity_at).date()
    sync = _aware(last_sync_at)
    by_start = {w["week_start"]: w for w in weeks}
    counted = []
    for i in range(1, VOLUME_WEEKS + 1):
        start = _monday(today) - timedelta(weeks=i)
        end = datetime.combine(start + timedelta(days=7), datetime.min.time(), tzinfo=UTC)
        if start >= first_day and end <= sync:
            counted.append((start, by_start.get(start, {"km": 0.0, "vert_m": 0.0})))
    if len(counted) < MIN_COUNTED_WEEKS:
        return None
    km = sum(w["km"] for _, w in counted) / len(counted)
    vert = sum(w["vert_m"] for _, w in counted) / len(counted)
    last_end = max(s for s, _ in counted) + timedelta(days=6)
    return round(km, 1), round(vert), last_end


def _pace_sec(pace: str | None) -> float | None:
    """'3:53' -> 233.0; None or unparsable -> None."""
    try:
        m, sec = str(pace).split("/")[0].strip().split(":")
        return int(m) * 60 + float(sec)
    except (AttributeError, ValueError):
        return None


def _hms(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


@dataclass
class FitnessSnapshot:
    weekly_km: float
    weekly_km_source: str
    weekly_vert_m: float | None
    volume_as_of: str | None
    threshold_pace: str | None
    threshold_pace_source: str | None
    assessment: dict[str, Any] | None
    utmb_index: int | None
    threshold_source: str
    gender: str | None
    readiness: dict[str, Any] | None
    notes: list[str] = field(default_factory=list)
    tier: str | None = None
    tier_reasons: list[str] = field(default_factory=list)
    tier_score: float | None = None
    tier_levels: dict[str, float | None] = field(default_factory=dict)

    def resolve_tier(
        self,
        explicit_tier: str | None,
        goal_type: str | None,
        max_continuous_jog_min: int | None,
        historical_max_distance_km: float | None,
        aet_hr: float | None,
        ant_hr: float | None,
        max_hr: float | None = None,
        previous_tier: str | None = None,
    ) -> str:
        a = self.assessment or {}
        marathons = [m for m in (a.get("pred_marathon_sec"), getattr(self, "road_marathon_sec", None)) if m]
        decision = resolve_tier_explained(
            explicit_tier=explicit_tier,
            goal_type=goal_type,
            current_weekly_km=self.weekly_km,
            # Vert only when measured: typed volume has none, and inventing it would
            # move the level on a guess.
            weekly_vert_m=self.weekly_vert_m if self.weekly_km_source == "coros" else None,
            max_continuous_jog_min=max_continuous_jog_min,
            historical_max_distance_km=historical_max_distance_km,
            aet_hr=aet_hr,
            ant_hr=ant_hr,
            max_hr=max_hr,
            threshold_source=self.threshold_source,
            marathon_prediction_sec=min(marathons) if marathons else None,
            utmb_index=self.utmb_index,
            vo2max=a.get("vo2max"),
            threshold_pace_sec=_pace_sec(self.threshold_pace),
            gender=self.gender,
            previous_tier=previous_tier,
        )
        self.tier, self.tier_reasons = decision.tier, decision.reasons
        self.tier_score, self.tier_levels = decision.score, decision.levels
        return self.tier

    def prompt_block(self, lang: str = "en") -> str:
        # English like the rest of the scheduler prompt; `lang` steers the output elsewhere.
        src = {"coros": "COROS", "self_reported": "self-reported"}
        lines = ["ATHLETE FITNESS SNAPSHOT"]
        vol = f"- Volume: {self.weekly_km:.0f} km/week"
        if self.weekly_vert_m:
            vol += f", {self.weekly_vert_m:,.0f} m vert"
        vol += f" ({src[self.weekly_km_source]}"
        vol += f", 4-week avg to {self.volume_as_of})" if self.volume_as_of else ")"
        lines.append(vol)
        a = self.assessment
        if a:
            day = _aware(a["measured_at"]).date().isoformat()
            preds = []
            if a.get("pred_marathon_sec"):
                preds.append(f"Marathon prediction {_hms(a['pred_marathon_sec'])}")
            if a.get("pred_hm_sec"):
                preds.append(f"half {_hms(a['pred_hm_sec'])}")
            if preds:
                lines.append(f"- {', '.join(preds)} (COROS, {day})")
            if a.get("vo2max"):
                lines.append(f"- VO2max {a['vo2max']:.0f} (COROS, {day})")
        if self.threshold_pace:
            lines.append(f"- Threshold pace {self.threshold_pace}/km ({src[self.threshold_pace_source or 'self_reported']})")
        if self.utmb_index:
            lines.append(f"- UTMB index {self.utmb_index}")
        r = self.readiness or {}
        if r.get("days_recorded"):
            bits = []
            if r.get("latest_load_ratio") is not None:
                bits.append(f"load ratio {r['latest_load_ratio']:.2f}")
            if r.get("latest_hrv_status"):
                bits.append(f"HRV {r['latest_hrv_status']}")
            if bits:
                lines.append(f"- {', '.join(bits)} (COROS, last 7 days)")
        if self.tier:
            lines.append(f"- Level: {self.tier} ({'; '.join(self.tier_reasons)})")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build(
    user_id: int,
    typed_weekly_km: float | None = None,
    typed_is_override: bool = False,
    today: date | None = None,
) -> FitnessSnapshot:
    today = today or date.today()
    user = db.get_user_by_id(user_id) or {}
    connection = db.get_connection(user_id, PROVIDER)
    connected = bool(connection and connection.get("status") == "active")
    notes: list[str] = []

    measured = None
    if connected:
        weeks = db.get_weekly_run_volumes(user_id, since=_monday(today) - timedelta(weeks=VOLUME_WEEKS))
        measured = measured_weekly_volume(
            weeks, db.get_first_activity_at(user_id, PROVIDER), connection.get("last_sync_at"), today
        )
        if measured is None:
            notes.append("COROS volume unused: fewer than 3 complete synced weeks")

    fallback_km = typed_weekly_km if typed_weekly_km is not None else user.get("current_weekly_km") or 30.0
    if typed_is_override and typed_weekly_km is not None:
        km, vert, as_of, km_src = float(typed_weekly_km), None, None, "self_reported"
        if measured:
            notes.append(f"athlete override of measured {measured[0]:.0f} km/week")
    elif measured:
        km, vert, as_of, km_src = measured[0], measured[1], measured[2].isoformat(), "coros"
    else:
        km, vert, as_of, km_src = float(fallback_km), None, None, "self_reported"

    assessment = db.get_latest_fitness_assessment(user_id)
    if assessment and today - _aware(assessment["measured_at"]).date() > ASSESSMENT_MAX_AGE:
        notes.append("COROS assessment older than 60 days, unused")
        assessment = None

    if assessment and assessment.get("threshold_pace"):
        tp, tp_src = assessment["threshold_pace"], "coros"
    elif user.get("threshold_pace"):
        tp, tp_src = user["threshold_pace"], "self_reported"
    else:
        tp, tp_src = None, None

    return FitnessSnapshot(
        weekly_km=km,
        weekly_km_source=km_src,
        weekly_vert_m=vert,
        volume_as_of=as_of,
        threshold_pace=tp,
        threshold_pace_source=tp_src,
        assessment=assessment,
        utmb_index=db.get_utmb_index(user_id),
        threshold_source=user.get("threshold_source") or "unknown",
        gender=user.get("gender"),
        readiness=db.get_recent_readiness_summary(user_id, days=7) if connected else None,
        notes=notes,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_fitness_snapshot.py -v`
Expected: all pass. If `test_measured_volume_beats_profile_value` reports 133.7 vs the Task 2 regression's 134, both are fine — the prompt test asserts the rounded `134 km/week`.

- [ ] **Step 5: Commit**

```bash
git add backend/services/fitness_snapshot.py backend/tests/unit/test_fitness_snapshot.py
git commit -m "feat: fitness snapshot assembles measured COROS signals with typed fallbacks"
```

---

### Task 3b: Chronic-load cap on measured volume

**Files:**
- Modify: `backend/services/fitness_snapshot.py`
- Test: `backend/tests/unit/test_fitness_snapshot.py`

**Interfaces:**
- Consumes: Task 3's `measured_weekly_volume`, `build`.
- Produces: `chronic_weekly_volume(weeks, first_activity_at, last_sync_at, today) -> float | None` (12-week mean km over complete covered weeks; None under 8 weeks); `CHRONIC_WEEKS = 12`, `MIN_CHRONIC_WEEKS = 8`, `CHRONIC_SPIKE_ALLOWANCE = 1.15`. `build` applies the cap to measured volume and appends a note when it bites.

- [ ] **Step 1: Failing tests** (append):

```python
def _steady(km, n=12, start=date(2026, 7, 6)):
    return [{"week_start": start + timedelta(weeks=i), "km": km, "vert_m": km * 10} for i in range(n)]


class TestChronicCap:
    SYNC = datetime(2026, 10, 1, tzinfo=UTC)
    FIRST12 = datetime(2026, 7, 1, tzinfo=UTC)

    def test_chronic_mean_needs_eight_weeks(self):
        assert fs.chronic_weekly_volume(_steady(70.0), self.FIRST12, self.SYNC, TODAY) == 70.0
        assert fs.chronic_weekly_volume(_steady(70.0), datetime(2026, 8, 20, tzinfo=UTC), self.SYNC, TODAY) is None

    def test_a_recent_spike_is_capped(self, stub_db, monkeypatch):
        weeks = _steady(60.0, n=8) + [
            {"week_start": date(2026, 8, 31) + timedelta(weeks=i), "km": 120.0, "vert_m": 1200.0} for i in range(4)
        ]
        monkeypatch.setattr(fs.db, "get_weekly_run_volumes", lambda uid, since: weeks)
        monkeypatch.setattr(fs.db, "get_first_activity_at", lambda uid, p: self.FIRST12)
        stub_db["connection"]["last_sync_at"] = self.SYNC
        snap = fs.build(30, today=TODAY)
        chronic = (60.0 * 8 + 120.0 * 4) / 12  # 80.0
        assert snap.weekly_km == pytest.approx(chronic * 1.15, abs=0.1)
        assert snap.weekly_vert_m == pytest.approx(1200.0 * (chronic * 1.15) / 120.0, abs=1)
        assert any("chronic" in n for n in snap.notes)

    def test_a_recent_dip_is_not_raised(self, stub_db, monkeypatch):
        weeks = _steady(100.0, n=8) + [
            {"week_start": date(2026, 8, 31) + timedelta(weeks=i), "km": 50.0, "vert_m": 500.0} for i in range(4)
        ]
        monkeypatch.setattr(fs.db, "get_weekly_run_volumes", lambda uid, since: weeks)
        monkeypatch.setattr(fs.db, "get_first_activity_at", lambda uid, p: self.FIRST12)
        stub_db["connection"]["last_sync_at"] = self.SYNC
        assert fs.build(30, today=TODAY).weekly_km == 50.0

    def test_short_history_skips_the_cap(self, stub_db):
        # the default stub has data from 2026-08-23 only: < 8 weeks, cap not applied
        assert fs.build(30, today=TODAY).weekly_km == pytest.approx(133.7, abs=0.1)
```

- [ ] **Step 2: Run to verify failure** — `cd backend && pytest tests/unit/test_fitness_snapshot.py -v -k Chronic` → FAIL (`chronic_weekly_volume` missing).

- [ ] **Step 3: Implement.** Factor the week-counting loop out of `measured_weekly_volume` so both use it:

```python
CHRONIC_WEEKS = 12
MIN_CHRONIC_WEEKS = 8
# A 4-week block may run this far above the 12-week mean before the cap bites:
# roughly the 10%/week progression ceiling compounded over a short build.
CHRONIC_SPIKE_ALLOWANCE = 1.15


def _counted_weeks(weeks, first_activity_at, last_sync_at, today, n):
    if not last_sync_at or not first_activity_at:
        return []
    first_day = _aware(first_activity_at).date()
    sync = _aware(last_sync_at)
    by_start = {w["week_start"]: w for w in weeks}
    counted = []
    for i in range(1, n + 1):
        start = _monday(today) - timedelta(weeks=i)
        end = datetime.combine(start + timedelta(days=7), datetime.min.time(), tzinfo=UTC)
        if start >= first_day and end <= sync:
            counted.append((start, by_start.get(start, {"km": 0.0, "vert_m": 0.0})))
    return counted


def chronic_weekly_volume(weeks, first_activity_at, last_sync_at, today) -> float | None:
    counted = _counted_weeks(weeks, first_activity_at, last_sync_at, today, CHRONIC_WEEKS)
    if len(counted) < MIN_CHRONIC_WEEKS:
        return None
    return round(sum(w["km"] for _, w in counted) / len(counted), 1)
```

Rewrite `measured_weekly_volume` to call `_counted_weeks(..., VOLUME_WEEKS)` and keep its return value unchanged. In `build`, fetch `since=_monday(today) - timedelta(weeks=CHRONIC_WEEKS)` (one query serves both), and after `measured` is computed:

```python
        if measured:
            chronic = chronic_weekly_volume(weeks, first_at, connection.get("last_sync_at"), today)
            ceiling = chronic * CHRONIC_SPIKE_ALLOWANCE if chronic else None
            if ceiling and measured[0] > ceiling:
                factor = ceiling / measured[0]
                notes.append(
                    f"4-week {measured[0]:.0f} km capped to {ceiling:.0f} km (12-week chronic {chronic:.0f} km x 1.15)"
                )
                measured = (round(ceiling, 1), round(measured[1] * factor), measured[2])
```

(store `first_at = db.get_first_activity_at(user_id, PROVIDER)` in a variable so it is not queried twice).

- [ ] **Step 4: Run tests** — `cd backend && pytest tests/unit/test_fitness_snapshot.py -v` → all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/services/fitness_snapshot.py backend/tests/unit/test_fitness_snapshot.py
git commit -m "feat(snapshot): cap measured volume at 1.15x the 12-week chronic load"
```

---

### Task 3c: Road results as a marathon equivalent (performance signal)

Field percentiles are not used: field depth differs too much between races and countries. Road times are absolute, so a recent road result converted with Riegel feeds the same marathon anchors as the COROS predictor. Trail results already count through the UTMB index.

**Files:**
- Modify: `backend/services/fitness_snapshot.py`
- Test: `backend/tests/unit/test_fitness_snapshot.py`

**Interfaces:**
- Consumes: `services.race_history.list_results(user_id, include_unselected=False) -> list[dict]` (rows of `race_results`: `source`, `discipline`, `race_name`, `race_date` (date or ISO str), `distance_km`, `finish_time_sec`, `is_dnf`, `hidden`); `FitnessSnapshot.resolve_tier` (Task 3) already reads `road_marathon_sec` via `getattr`.
- Produces: `RIEGEL_EXPONENT = 1.06`; `riegel_marathon_sec(finish_sec: float, distance_km: float) -> float`; `best_road_marathon_equivalent(results: list[dict], today: date) -> tuple[float, str] | None` (seconds, label like `"Hanoi HM 2026-03-14"`); `FitnessSnapshot.road_marathon_sec: float | None = None`, `road_marathon_label: str | None = None`.

- [ ] **Step 1: Failing tests** (append to `test_fitness_snapshot.py`; add `monkeypatch.setattr(fs, "_race_results", lambda uid: [])` to the `stub_db` fixture):

```python
def _road(**kw):
    base = {"source": "vbm", "discipline": "road", "race_name": "City HM", "race_date": "2026-03-14",
            "distance_km": 21.0975, "finish_time_sec": 4800, "is_dnf": False, "hidden": False}
    return {**base, **kw}


class TestRoadEquivalent:
    def test_riegel(self):
        # 1:20:00 half -> about 2:46:46 marathon with exponent 1.06
        assert fs.riegel_marathon_sec(4800, 21.0975) == pytest.approx(10006, abs=5)
        assert fs.riegel_marathon_sec(10800, 42.195) == pytest.approx(10800, abs=1)

    def test_fastest_eligible_result_wins(self):
        sec, label = fs.best_road_marathon_equivalent([_road(), _road(race_name="10K", distance_km=10.0, finish_time_sec=2100)], TODAY)
        assert sec == pytest.approx(fs.riegel_marathon_sec(2100, 10.0), abs=1)
        assert "10K" in label

    @pytest.mark.parametrize("bad", [
        {"source": "manual"}, {"source": "utmb"}, {"discipline": "trail"}, {"is_dnf": True}, {"hidden": True},
        {"race_date": "2025-06-01"}, {"distance_km": 3.0}, {"distance_km": 50.0}, {"finish_time_sec": None},
    ])
    def test_ineligible_results_are_ignored(self, bad):
        assert fs.best_road_marathon_equivalent([_road(**bad)], TODAY) is None

    def test_road_result_feeds_the_tier_when_faster_than_the_predictor(self, stub_db, monkeypatch):
        stub_db["assessment"]["pred_marathon_sec"] = 12000.0  # 3:20
        monkeypatch.setattr(fs, "_race_results", lambda uid: [_road()])  # ~2:46:46 equivalent
        snap = fs.build(30, today=TODAY)
        assert snap.road_marathon_sec == pytest.approx(10006, abs=5)
        snap.resolve_tier(None, "race", None, None, None, None)
        assert any("performance" in r and "marathon" in r for r in snap.tier_reasons)
        assert snap.tier_levels["performance"] > 3.7
        assert "Road result" in snap.prompt_block("en")

    def test_race_history_failure_never_blocks(self, stub_db, monkeypatch):
        def boom(uid):
            raise RuntimeError("db down")

        monkeypatch.setattr(fs, "_race_results", boom)
        assert fs.build(30, today=TODAY).road_marathon_sec is None
```

- [ ] **Step 2: Run to verify failure** — `cd backend && pytest tests/unit/test_fitness_snapshot.py -v -k Road` → FAIL (`riegel_marathon_sec` missing).

- [ ] **Step 3: Implement** in `fitness_snapshot.py`:

```python
RIEGEL_EXPONENT = 1.06
MARATHON_KM = 42.195
ROAD_MIN_KM, ROAD_MAX_KM = 5.0, 42.5
RESULT_MAX_AGE = timedelta(days=365)


def _race_results(user_id: int) -> list[dict[str, Any]]:
    from services.race_history import list_results

    return list_results(user_id, include_unselected=False)


def riegel_marathon_sec(finish_sec: float, distance_km: float) -> float:
    """Riegel's rule of thumb; most reliable from 10 km to the marathon."""
    return finish_sec * (MARATHON_KM / distance_km) ** RIEGEL_EXPONENT


def best_road_marathon_equivalent(results: list[dict[str, Any]], today: date) -> tuple[float, str] | None:
    """Fastest marathon equivalent among recent imported road finishes. Road times are
    absolute, unlike field percentiles, which depend on how deep each race's field is."""
    best = None
    for r in results:
        if r.get("source") != "vbm" or r.get("discipline") != "road" or r.get("is_dnf") or r.get("hidden"):
            continue
        km, sec = r.get("distance_km"), r.get("finish_time_sec")
        if not km or not sec or not (ROAD_MIN_KM <= float(km) <= ROAD_MAX_KM):
            continue
        raced = r["race_date"] if isinstance(r["race_date"], date) else date.fromisoformat(str(r["race_date"]))
        if today - raced > RESULT_MAX_AGE:
            continue
        equiv = round(riegel_marathon_sec(float(sec), float(km)))
        if best is None or equiv < best[0]:
            best = (equiv, f"{r['race_name']} {raced.isoformat()}")
    return best
```

Add fields `road_marathon_sec: float | None = None` and `road_marathon_label: str | None = None` to `FitnessSnapshot` after `readiness` (fields with defaults must follow those without). In `build`:

```python
    try:
        road = best_road_marathon_equivalent(_race_results(user_id), today)
    except Exception:
        road = None  # race history must never block a plan
```

and pass `road_marathon_sec=road[0] if road else None, road_marathon_label=road[1] if road else None`. In `resolve_tier`, replace `getattr(self, "road_marathon_sec", None)` with `self.road_marathon_sec`. In `prompt_block`, after the predictions line:

```python
        if self.road_marathon_sec:
            lines.append(f"- Road result: marathon equivalent {_hms(self.road_marathon_sec)} ({self.road_marathon_label})")
```

- [ ] **Step 4: Run tests** — `cd backend && pytest tests/unit/test_fitness_snapshot.py tests/unit/test_athlete_tier.py -v` → all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/services/fitness_snapshot.py backend/tests/unit/test_fitness_snapshot.py
git commit -m "feat(snapshot): recent road results count as a marathon equivalent"
```

---

### Task 4: Record COROS assessments on sync, refresh on demand

**Files:**
- Modify: `backend/services/coros_sync.py`
- Test: `backend/tests/unit/test_coros_sync.py`

**Interfaces:**
- Consumes: `db.record_fitness_assessment`, `db.get_latest_fitness_assessment`, `CorosAdapter.fetch_fitness_overview()` (returns the `parse_fitness_overview` dict: `vo2max, running_level, threshold_pace, prediction_5k_sec, prediction_10k_sec, prediction_half_marathon_sec, prediction_marathon_sec`).
- Produces:
  - `coros_sync.store_overview(user_id: int, overview: dict) -> None`
  - `async coros_sync.ensure_fresh_assessment(user_id: int, max_age: timedelta = timedelta(days=7)) -> None` — never raises.

- [ ] **Step 1: Write the failing tests** (append to `test_coros_sync.py`)

```python
OVERVIEW = {
    "vo2max": 61.0, "running_level": 92.0, "threshold_pace": "3:53",
    "prediction_5k_sec": 1000.0, "prediction_10k_sec": 2100.0,
    "prediction_half_marathon_sec": 4860.0, "prediction_marathon_sec": 10320.0,
}


def test_store_overview_records_history_and_profile(monkeypatch):
    recorded, profile = [], []
    monkeypatch.setattr(coros_sync.db, "record_fitness_assessment", lambda uid, src, d: recorded.append((uid, src, d)) or True)
    monkeypatch.setattr(coros_sync.db, "update_user_fitness", lambda **kw: profile.append(kw) or True)
    coros_sync.store_overview(30, OVERVIEW)
    assert recorded[0][2]["pred_marathon_sec"] == 10320.0
    assert recorded[0][2]["pred_hm_sec"] == 4860.0
    assert profile[0]["coros_vo2max"] == 61.0


@pytest.mark.asyncio
async def test_ensure_fresh_skips_when_recent(monkeypatch):
    monkeypatch.setattr(coros_sync.db, "get_connection", lambda uid, p: {"status": "active"})
    monkeypatch.setattr(
        coros_sync.db, "get_latest_fitness_assessment",
        lambda uid: {"measured_at": datetime.now(UTC) - timedelta(days=2)},
    )

    async def boom(uid):
        raise AssertionError("must not pull")

    monkeypatch.setattr(coros_sync, "sync_fitness", boom)
    await coros_sync.ensure_fresh_assessment(30)


@pytest.mark.asyncio
async def test_ensure_fresh_swallows_coros_failures(monkeypatch):
    monkeypatch.setattr(coros_sync.db, "get_connection", lambda uid, p: {"status": "active"})
    monkeypatch.setattr(coros_sync.db, "get_latest_fitness_assessment", lambda uid: None)

    async def fail(uid):
        raise RuntimeError("COROS down")

    monkeypatch.setattr(coros_sync, "sync_fitness", fail)
    await coros_sync.ensure_fresh_assessment(30)  # no exception


@pytest.mark.asyncio
async def test_ensure_fresh_does_nothing_without_connection(monkeypatch):
    monkeypatch.setattr(coros_sync.db, "get_connection", lambda uid, p: None)

    async def boom(uid):
        raise AssertionError("must not pull")

    monkeypatch.setattr(coros_sync, "sync_fitness", boom)
    await coros_sync.ensure_fresh_assessment(30)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/unit/test_coros_sync.py -v -k "overview or ensure_fresh"`
Expected: FAIL — `AttributeError: module 'services.coros_sync' has no attribute 'store_overview'`.

- [ ] **Step 3: Implement** in `coros_sync.py`. Add:

```python
FITNESS_REFRESH_TIMEOUT_SECONDS = 15


def store_overview(user_id: int, overview: dict[str, Any]) -> None:
    """Keep the profile columns current and append the assessment to the history."""
    db.update_user_fitness(
        user_id=user_id,
        threshold_pace=overview.get("threshold_pace"),
        coros_vo2max=overview.get("vo2max"),
        coros_running_level=overview.get("running_level"),
    )
    db.record_fitness_assessment(
        user_id,
        PROVIDER,
        {
            "vo2max": overview.get("vo2max"),
            "running_level": overview.get("running_level"),
            "threshold_pace": overview.get("threshold_pace"),
            "pred_5k_sec": overview.get("prediction_5k_sec"),
            "pred_10k_sec": overview.get("prediction_10k_sec"),
            "pred_hm_sec": overview.get("prediction_half_marathon_sec"),
            "pred_marathon_sec": overview.get("prediction_marathon_sec"),
        },
    )


async def ensure_fresh_assessment(user_id: int, max_age: timedelta = timedelta(days=7)) -> None:
    """Pull a fitness overview when the latest is missing or older than max_age.
    Best effort: a plan must never wait on, or fail because of, COROS."""
    connection = db.get_connection(user_id, PROVIDER)
    if not connection or connection.get("status") != "active":
        return
    latest = db.get_latest_fitness_assessment(user_id)
    if latest and datetime.now(UTC) - latest["measured_at"] < max_age:
        return
    try:
        await asyncio.wait_for(sync_fitness(user_id), timeout=FITNESS_REFRESH_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("on-demand COROS fitness refresh failed", extra={"fields": {"service": "coros_sync", "event": "fitness_refresh_failed"}})
```

Add `import asyncio` at the top. In `sync_fitness`, replace the `db.update_user_fitness(...)` call with `store_overview(user_id, overview)` (keep its return dict). In `sync_user`, after `return await persist(...)` change to:

```python
        result = await persist(user_id, CorosAdapter(client), days)
        try:
            overview = await CorosAdapter(client).fetch_fitness_overview()
            if overview:
                store_overview(user_id, overview)
        except Exception:
            logger.exception("fitness overview during sync failed", extra={"fields": {"service": "coros_sync", "event": "fitness_overview_failed"}})
        return result
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_coros_sync.py tests/unit/test_coros_sync_route.py -v`
Expected: all pass (existing tests still pass: `persist` is unchanged).

- [ ] **Step 5: Commit**

```bash
git add backend/services/coros_sync.py backend/tests/unit/test_coros_sync.py
git commit -m "feat(coros): keep fitness assessment history; refresh on demand before planning"
```

---

### Task 5: Plan generator reads the snapshot

**Files:**
- Modify: `backend/services/plan_generator.py` (`generate_plan_workouts`: the `current_weekly_km = float(...)` line, the `athlete_tier = resolve_tier(...)` block, the `user_summary` f-string)
- Test: `backend/tests/unit/test_plan_generator_snapshot.py`

**Interfaces:**
- Consumes: `race_info["fitness_snapshot"]: FitnessSnapshot | None` (Task 3).
- Produces: when present, `snapshot.tier`/`tier_reasons` are set after the call; the prompt contains `snapshot.prompt_block(lang)`; `current_weekly_km == snapshot.weekly_km`; pace zones use `snapshot.threshold_pace`.

- [ ] **Step 1: Write the failing test** — same mocking pattern as `tests/unit/test_prompt_enrichment.py::test_plan_prompt_places_race_history_beside_ceiling` (invalid Gemini JSON forces the rule-based fallback after the prompt is sent, so the prompt can be read from the mock):

```python
from unittest.mock import MagicMock, patch

import pytest

from services.fitness_snapshot import FitnessSnapshot
from services.plan_generator import PlanGenerator

PROFILE = {"id": 7, "current_weekly_km": 120.0, "aet_hr": 134, "ant_hr": 163, "max_hr": 183, "resting_hr": 60}
RACE = {"name": "APTRC", "date": "2026-11-27", "goal_type": "race", "course_distance_km": 80.0,
        "course_elevation_gain_m": 4000.0}


def _snapshot():
    return FitnessSnapshot(
        weekly_km=134.0, weekly_km_source="coros", weekly_vert_m=5000.0, volume_as_of="2026-09-20",
        threshold_pace="3:53", threshold_pace_source="coros", assessment=None, utmb_index=None,
        threshold_source="unknown", gender=None, readiness=None,
    )


async def _generate(race_info):
    mock_resp = MagicMock()
    mock_resp.text = "invalid json to trigger fallback"
    client = MagicMock()
    client.models.generate_content.return_value = mock_resp
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("services.race_history.prompt_summary", return_value=""),
        patch("services.race_history.tier_distance", return_value=None),
    ):
        _, tier = await PlanGenerator.generate_plan_workouts(
            plan_id=1, user_profile=dict(PROFILE), race_info=race_info, total_weeks=8, api_key="fake-gemini-key"
        )
    return tier, client.models.generate_content.call_args.kwargs.get("contents", "")


@pytest.mark.asyncio
async def test_snapshot_sets_tier_volume_and_prompt_block():
    snap = _snapshot()
    tier, prompt = await _generate({**RACE, "fitness_snapshot": snap})
    # load 184 effort-km -> 4.15; performance from threshold pace 3:53 -> 3.63; score 3.94
    assert tier == "sub_elite"
    assert snap.tier == "sub_elite" and snap.tier_reasons
    assert "ATHLETE FITNESS SNAPSHOT" in prompt
    assert "Weekly volume base: 134.0 km" in prompt


@pytest.mark.asyncio
async def test_without_snapshot_unknown_threshold_source_no_longer_demotes():
    tier, prompt = await _generate(dict(RACE))
    assert tier == "sub_elite"
    assert "ATHLETE FITNESS SNAPSHOT" not in prompt
```

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/unit/test_plan_generator_snapshot.py -v`
Expected: the first test FAILS (snapshot ignored: no prompt block, volume 120.0). The second already passes after Task 2 (load-only 120 km -> 3.5).

- [ ] **Step 3: Implement.** In `generate_plan_workouts`:

Replace
```python
        current_weekly_km = float(user_profile.get("current_weekly_km", 30.0))
```
with
```python
        snapshot = race_info.get("fitness_snapshot")
        current_weekly_km = (
            float(snapshot.weekly_km) if snapshot else float(user_profile.get("current_weekly_km", 30.0))
        )
        if snapshot and snapshot.threshold_pace:
            user_profile = {**user_profile, "threshold_pace": snapshot.threshold_pace}
```

Replace the `athlete_tier = resolve_tier(...)` call with:

```python
        _tier_args = dict(
            explicit_tier=race_info.get("athlete_tier"),
            goal_type=race_info.get("goal_type") or user_profile.get("goal_type"),
            max_continuous_jog_min=_max_jog_min,
            historical_max_distance_km=(_historical_ceiling or {}).get("max_distance_km"),
            # RAW stored thresholds -- see the comment this replaces about derived values.
            aet_hr=user_profile.get("aet_hr"),
            ant_hr=user_profile.get("ant_hr"),
            previous_tier=race_info.get("previous_tier"),
        )
        if snapshot:
            athlete_tier = snapshot.resolve_tier(**_tier_args, max_hr=max_hr)
        else:
            athlete_tier = resolve_tier(
                **_tier_args,
                current_weekly_km=current_weekly_km,
                threshold_source=user_profile.get("threshold_source"),
                max_hr=max_hr,
                gender=gender,
            )
```

Keep the existing explanatory comment about RAW thresholds above `aet_hr=`.

In the prompt assembly, next to `race_history_notes = f"\n{race_history_text}\n" if race_history_text else ""`, add:

```python
            snapshot_notes = f"\n{snapshot.prompt_block(lang)}\n" if snapshot else ""
```

and append `f"{snapshot_notes}"` right after `f"{race_history_notes}"` in `user_summary`.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit -q -m "not kafka"`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/services/plan_generator.py backend/tests/unit/test_plan_generator_snapshot.py
git commit -m "feat(plan): generator uses the fitness snapshot for tier, volume and prompt"
```

---

### Task 6: Wire the snapshot into every plan path, goal context and coach chat

**Files:**
- Modify: `backend/main.py` (onboarding job `_run_plan_gen`, generate-plan job `_run_gen`, next-block job `_run_next_block`; `GeneratePlanRequest`)
- Modify: `backend/services/week_rebuild.py` (`generate_week_draft`, `write_draft`, `RebuildInputs` users)
- Modify: `backend/services/schedule_proposals.py` (where it calls `db.set_plan_athlete_tier` from a draft)
- Modify: `backend/services/goal_context.py`, `backend/services/coach_context.py`
- Test: `backend/tests/integration/test_plan_fitness_snapshot.py`, `backend/tests/unit/test_goal_context.py` (or the existing goal-context unit test file)

**Interfaces:**
- Consumes: `fitness_snapshot.build`, `coros_sync.ensure_fresh_assessment`, `db.set_plan_fitness_snapshot`.
- Produces: `GeneratePlanRequest.weekly_km_from_watch: bool = False`; `plans.fitness_snapshot` populated after every generation; `WeekDraft.fitness_snapshot: dict | None`.

- [ ] **Step 1: Write the failing integration test.** Copy the client/auth setup from an existing generate-plan integration test (search `tests/integration` for `"/api/coach/generate-plan"`), run with no Gemini key (rule-based), then:

```python
def test_generate_plan_stores_snapshot_and_uses_measured_volume(client, athlete_headers, athlete_id, monkeypatch):
    import dataclasses

    from services import coros_sync, fitness_snapshot

    async def no_refresh(uid, **kw):
        return None

    monkeypatch.setattr(coros_sync, "ensure_fresh_assessment", no_refresh)
    real_build = fitness_snapshot.build
    monkeypatch.setattr(
        fitness_snapshot, "build",
        lambda uid, **kw: dataclasses.replace(real_build(uid, **kw), weekly_km=134.0, weekly_km_source="coros"),
    )
    payload = {**MINIMAL_GENERATE_PAYLOAD, "current_weekly_km": 120, "weekly_km_from_watch": True}
    job = client.post("/api/coach/generate-plan", json=payload, headers=athlete_headers).json()
    wait_for_job(client, job["job_id"], athlete_headers)  # copy helper from the existing test
    with engine.connect() as conn:
        snap = conn.execute(text("SELECT fitness_snapshot FROM plans WHERE id=:p"), {"p": job["plan_id"]}).scalar_one()
    assert snap["weekly_km"] == 134.0
    assert snap["tier"] == "sub_elite"
```

`MINIMAL_GENERATE_PAYLOAD` and `wait_for_job` come from the existing test you copied; import or duplicate them.

- [ ] **Step 2: Run to verify failure**

Run: `cd backend && pytest tests/integration/test_plan_fitness_snapshot.py -v`
Expected: FAIL — `snap` is `None`.

- [ ] **Step 3: Add a shared helper in `main.py`** (near `_assess_new_plan`):

```python
async def _plan_snapshot(user_id: int, typed_weekly_km: float | None = None, typed_is_override: bool = False):
    """Refresh COROS fitness if stale, then assemble the snapshot. Never raises: a plan
    falls back to the profile path rather than failing on fitness data."""
    try:
        await coros_sync.ensure_fresh_assessment(user_id)
        return fitness_snapshot.build(user_id, typed_weekly_km=typed_weekly_km, typed_is_override=typed_is_override)
    except Exception:
        logger.exception("fitness snapshot unavailable; using profile values")
        return None


def _store_plan_snapshot(plan_id: int, snapshot) -> None:
    if snapshot is not None:
        set_plan_fitness_snapshot(plan_id, snapshot.to_dict())
```

Import `fitness_snapshot` and `coros_sync` from `services`, and `set_plan_fitness_snapshot` from `db` alongside `set_plan_athlete_tier`. Use the module's existing logger (search `logger =` in `main.py`; if it only uses `print`, use `print(f"[PlanGen] fitness snapshot unavailable: {exc}")` with `except Exception as exc`).

- [ ] **Step 4: Use it in the three jobs.**
  - Onboarding `_run_plan_gen`: first line inside `try:` → `race_info["fitness_snapshot"] = await _plan_snapshot(user["id"], request.current_weekly_km)`; after `set_plan_athlete_tier(plan_id, resolved_tier)` → `_store_plan_snapshot(plan_id, race_info["fitness_snapshot"])`.
  - Generate-plan `_run_gen`: `race_info["fitness_snapshot"] = await _plan_snapshot(athlete_id, request.current_weekly_km, typed_is_override=not request.weekly_km_from_watch)`; store after `set_plan_athlete_tier`.
  - Next block `_run_next_block`: `race_info["fitness_snapshot"] = await _plan_snapshot(athlete_id)`; store after `set_plan_athlete_tier`.
  - Add `weekly_km_from_watch: bool = False` to the generate-plan request model (the model that declares `current_weekly_km: float  # current training volume, entered fresh for every plan`).

`race_info` is also passed to `generate_week_narrative` in next-block; the snapshot object there is harmless (it only reads known keys). If a JSON dump of `race_info` happens anywhere (search `json.dumps(race_info`), pop the key first.

- [ ] **Step 4b: Unfreeze re-plan tiers.** In the next-block `race_info` (the dict with `# Explicit per-plan tier override; None means the generator derives it.`) and the same dict in `week_rebuild.py`, replace

```python
        # Explicit per-plan tier override; None means the generator derives it.
        "athlete_tier": plan.get("athlete_tier"),
```
with
```python
        # plans.athlete_tier is the LAST RESOLVED tier, not an override. Passing it as
        # the override froze every plan at its first tier; it is now only the
        # hysteresis input, so re-plans follow the athlete's current fitness.
        "athlete_tier": None,
        "previous_tier": plan.get("athlete_tier"),
```

Add a unit test in `tests/unit/test_athlete_tier.py`:

```python
def test_a_stored_tier_no_longer_overrides_a_replan():
    """REGRESSION: next block passed plans.athlete_tier as the explicit override, so a
    plan first resolved as recreational stayed recreational forever."""
    assert resolve_tier(explicit_tier=None, current_weekly_km=134.0, previous_tier=RECREATIONAL) == SUB_ELITE
```

- [ ] **Step 5: Adapt week.** In `week_rebuild.py`, add `fitness_snapshot: dict[str, Any] | None = None` to `WeekDraft`. In `generate_week_draft`:

```python
    from services import coros_sync, fitness_snapshot

    snapshot = None
    try:
        await coros_sync.ensure_fresh_assessment(inputs.user["id"])
        snapshot = fitness_snapshot.build(inputs.user["id"])
    except Exception:
        snapshot = None
    race_info = {**inputs.race_info, "fitness_snapshot": snapshot}
```

pass `race_info` instead of `inputs.race_info` to `generate_plan_workouts`, and return `WeekDraft(..., fitness_snapshot=snapshot.to_dict() if snapshot else None)`. In `write_draft` (and in `schedule_proposals.py` where a proposal draft's `resolved_tier` is applied), after `set_plan_athlete_tier`, add `if draft.fitness_snapshot: db.set_plan_fitness_snapshot(plan["id"], draft.fitness_snapshot)` (for the proposal path read it from `(row.get("draft") or {}).get("fitness_snapshot")`). Check how `WeekDraft` is serialised into a proposal (`asdict`) — the new field is a plain dict, so it serialises.

- [ ] **Step 6: Goal context and coach chat.**
  - `goal_context.gather`: after the VO2max block add:

```python
        assessment = _safe("predictor", db.get_latest_fitness_assessment, missing, uid)
        if assessment and assessment.get("pred_marathon_sec") and use(
            "predictor", f"COROS marathon prediction {_hms(int(assessment['pred_marathon_sec']))}"
        ):
            athlete["marathon_prediction_sec"] = assessment["pred_marathon_sec"]
```

  Add a unit test next to the existing goal-context tests asserting `marathon_prediction_sec` appears when the stubbed assessment has one. If `_hms` is not defined above that point, it is in the same module (line ~48).
  - `coach_context`: add `"threshold_source": athlete_row.get("threshold_source")` and `"fitness_snapshot": _snapshot_or_none(user_id)` to `athlete_context`, where:

```python
def _snapshot_or_none(user_id: int) -> dict[str, Any] | None:
    try:
        from services.fitness_snapshot import build

        return build(user_id).to_dict()
    except Exception:
        return None
```

  Check the coach-context unit tests stub `db` broadly enough; if a test breaks on the new db calls, monkeypatch `coach_context._snapshot_or_none` to `lambda uid: None` in that test's fixture.

- [ ] **Step 7: Run tests**

Run: `cd backend && pytest tests/unit -q -m "not kafka" && pytest tests/integration/test_plan_fitness_snapshot.py tests/integration/test_adapt_week.py -v`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/main.py backend/services/week_rebuild.py backend/services/schedule_proposals.py backend/services/goal_context.py backend/services/coach_context.py backend/tests
git commit -m "feat(plan): build and store the fitness snapshot on every plan path"
```

---

### Task 7: API — threshold source and snapshot endpoint

**Files:**
- Modify: `backend/main.py` (`UpdateProfileRequest`, the onboarding request model with `aet_hr`, `format_user_response`, new route next to `GET /api/auth/pace-zones`)
- Modify: `backend/db.py` (`update_user_profile` and the onboarding profile write)
- Test: `backend/tests/integration/test_threshold_source_api.py`

**Interfaces:**
- Produces: `threshold_source` accepted on profile update and onboarding, returned on the user payload; `GET /api/auth/fitness-snapshot` → `FitnessSnapshot.to_dict()` (no tier fields set).

- [ ] **Step 1: Write the failing test** (copy client/auth fixtures from `tests/integration/test_auth_flow.py`):

```python
def test_profile_update_round_trips_threshold_source(client, user_headers):
    body = {"age": 37, "max_hr": 183, "resting_hr": 60, "aet_hr": 150, "ant_hr": 165, "threshold_source": "field"}
    assert client.put("/api/auth/profile", json=body, headers=user_headers).status_code == 200
    me = client.get("/api/auth/me", headers=user_headers).json()
    assert me["threshold_source"] == "field"


def test_profile_update_rejects_unknown_threshold_source(client, user_headers):
    body = {"age": 37, "max_hr": 183, "resting_hr": 60, "aet_hr": 150, "ant_hr": 165, "threshold_source": "guess"}
    assert client.put("/api/auth/profile", json=body, headers=user_headers).status_code == 422


def test_fitness_snapshot_endpoint_without_coros(client, user_headers):
    snap = client.get("/api/auth/fitness-snapshot", headers=user_headers).json()
    assert snap["weekly_km_source"] == "self_reported"
    assert snap["threshold_source"] in ("unknown", "field")
```

Use the real profile-update route and `me` route names (search `main.py` for `UpdateProfileRequest` usage and `/api/auth/me`).

- [ ] **Step 2: Run to verify failure** — Run: `cd backend && pytest tests/integration/test_threshold_source_api.py -v`. Expected: FAIL (`threshold_source` missing / 404).

- [ ] **Step 3: Implement.**
  - `UpdateProfileRequest` and the onboarding request model: `threshold_source: Literal["lab", "field", "estimated", "unknown"] | None = None` (import `Literal` from `typing` if not already).
  - `update_user_profile` in `db.py`: add `threshold_source = COALESCE(:threshold_source, threshold_source),` to the `SET` list and `"threshold_source": profile_data.get("threshold_source"),` to the params. Do the same in the onboarding profile write (search for the `INSERT`/`UPDATE` that writes `aet_hr` during onboarding).
  - `format_user_response`: add `"threshold_source": user.get("threshold_source") or "unknown",`.
  - New route:

```python
@app.get("/api/auth/fitness-snapshot")
def get_fitness_snapshot(user: dict[str, Any] = Depends(get_current_user)):
    """What the planner would use right now: measured volume (or the profile value),
    threshold pace and the latest COROS assessment, each with its source."""
    return fitness_snapshot.build(user["id"]).to_dict()
```

- [ ] **Step 4: Run tests** — Run: `cd backend && pytest tests/integration/test_threshold_source_api.py tests/integration/test_auth_flow.py -v`. Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/db.py backend/tests/integration/test_threshold_source_api.py
git commit -m "feat(api): threshold_source on profile; GET /api/auth/fitness-snapshot"
```

---

### Task 8: Frontend — threshold-source select and km prefill

**Files:**
- Modify: `frontend/src/types/index.ts` (User type: `threshold_source?: "lab" | "field" | "estimated" | "unknown"`)
- Modify: `frontend/src/app/translations.ts`
- Modify: `frontend/src/views/ProfileSettingsModal.tsx` (AeT block; payload near `aet_hr: parseInt(profileForm.aet_hr)`)
- Modify: `frontend/src/views/OnboardingWizard.tsx` (both AeT inputs; payload near `if (onboardingAnswers.aet_hr) payload.aet_hr = ...`)
- Modify: `frontend/src/views/PlannerView.tsx` (Current Weekly Mileage block), `frontend/src/hooks/usePlanner.ts` (payload near `current_weekly_km: parseFloat(planForm.current_weekly_km)`)
- Test: `frontend/src/views/ProfileSettingsModal.test.tsx` (extend)

- [ ] **Step 1: Translations.** Add to both `en` and `vi` objects (VI per the `uphill-ai-vietnamese-copy` skill):

```ts
  // en
  threshold_source_label: "How did you get your AeT/AnT?",
  threshold_source_lab: "Lab test",
  threshold_source_field: "Field test (e.g. heart-rate drift)",
  threshold_source_estimated: "Estimated (watch or formula)",
  threshold_source_unknown: "Not sure",
  threshold_source_hint: "Only tested values are used to judge your training level.",
  weekly_km_from_watch_hint: "From your COROS: {km} km/week (last 4 complete weeks)",
  // vi
  threshold_source_label: "Bạn có chỉ số AeT/AnT từ đâu?",
  threshold_source_lab: "Đo tại phòng lab",
  threshold_source_field: "Tự test ngoài thực địa (vd. độ trôi nhịp tim)",
  threshold_source_estimated: "Ước tính (đồng hồ hoặc công thức)",
  threshold_source_unknown: "Không rõ",
  threshold_source_hint: "Chỉ số đo bằng test mới được dùng để đánh giá trình độ của bạn.",
  weekly_km_from_watch_hint: "Theo COROS của bạn: {km} km/tuần (4 tuần gần nhất)",
```

- [ ] **Step 2: Failing component test** — in `ProfileSettingsModal.test.tsx`, following the file's existing render/submit pattern, add a test that selects `field` in the select labelled by `t("threshold_source_label")`, submits, and asserts the PUT body contains `threshold_source: "field"`.

Run: `cd frontend && npx vitest run src/views/ProfileSettingsModal.test.tsx` — Expected: FAIL (no such select).

- [ ] **Step 3: Profile select.** Below the AnT input block, add (match the modal's `labelStyle`/`inputStyle`):

```tsx
<div>
  <label style={labelStyle} htmlFor="threshold-source">{t("threshold_source_label")}</label>
  <select
    id="threshold-source"
    style={inputStyle}
    value={profileForm.threshold_source ?? "unknown"}
    onChange={e => setProfileForm({ ...profileForm, threshold_source: e.target.value })}
  >
    {(["lab", "field", "estimated", "unknown"] as const).map(v => (
      <option key={v} value={v}>{t(`threshold_source_${v}`)}</option>
    ))}
  </select>
  <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "4px 0 0 0" }}>{t("threshold_source_hint")}</p>
</div>
```

Initialise `profileForm.threshold_source` from the user (where `aet_hr` is initialised) and send `threshold_source: profileForm.threshold_source` in the payload.

- [ ] **Step 4: Onboarding select.** Add the same `<select>` after each of the two AeT/AnT input pairs in `OnboardingWizard.tsx` (using the wizard's `inputS` style and `setAns("threshold_source", ...)`), and `if (onboardingAnswers.threshold_source) payload.threshold_source = onboardingAnswers.threshold_source;` beside the `aet_hr` payload line.

- [ ] **Step 5: Planner prefill.** In `PlannerView.tsx`:

```tsx
const [watchKm, setWatchKm] = useState<number | null>(null);
const [kmFromWatch, setKmFromWatch] = useState(false);

useEffect(() => {
  const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
  if (!token) return;
  fetch(`${getBackendUrl()}/api/auth/fitness-snapshot`, { headers: { Authorization: `Bearer ${token}` } })
    .then(r => (r.ok ? r.json() : null))
    .then(s => {
      if (s?.weekly_km_source !== "coros") return;
      const km = Math.round(s.weekly_km);
      setWatchKm(km);
      setPlanForm(f => (f.current_weekly_km ? f : { ...f, current_weekly_km: String(km) }));
      setKmFromWatch(true);
    })
    .catch(() => {});
}, []);
```

Use whatever backend-URL helper `PlannerView`/`usePlanner` already imports (`getBackendUrl` or `API_BASE_URL`). In the km input's `onChange`, add `setKmFromWatch(false);`. Under the input, when `watchKm !== null`, render `{t("weekly_km_from_watch_hint").replace("{km}", String(watchKm))}` with the existing hint style. Pass `kmFromWatch` into the generate call and, in `usePlanner.ts`, add `weekly_km_from_watch: kmFromWatch` next to `current_weekly_km` (thread it as a parameter the same way `planForm` reaches that function).

- [ ] **Step 6: Run checks** — Run: `cd frontend && npx tsc --noEmit && npm run lint && npx vitest run`. Expected: clean, all pass.

- [ ] **Step 7: Screenshot evidence.** Follow `.claude/skills/ui-screenshot-evidence/SKILL.md`: run the local stack, open Profile settings (select visible, EN and VI) and the Planner's new-plan form for a user with seeded COROS activities (hint visible, value prefilled). Save the screenshots and attach them to the PR.

- [ ] **Step 8: Commit**

```bash
git add frontend/src
git commit -m "feat(ui): AeT/AnT source select; prefill weekly km from COROS"
```

---

### Task 9: Synthetic look-alike golden fixtures and snapshot-aware eval

**Files:**
- Create: `backend/tests/golden/scheduler/fixture_snapshot_elite_unmeasured_thresholds.json`
- Create: `backend/tests/golden/scheduler/fixture_snapshot_recreational_field_thresholds.json`
- Create: `backend/tests/golden/scheduler/fixture_snapshot_elite_no_coros.json`
- Modify: `backend/scripts/golden_eval.py` (`_run_scheduler`, the scheduler branch of `compare`, `gate_failures`)
- Test: `backend/tests/unit/test_golden_snapshot_fixtures.py`

**Interfaces:**
- Consumes: `FitnessSnapshot` (Task 3); `generate_plan_workouts` returning `(workouts, tier)`.
- Produces: fixture keys `fitness_snapshot` (FitnessSnapshot fields; `assessment.measured_at` as ISO string) and `expect` (`{"tier": str, "week2_km": [lo, hi]}`); scheduler item scores `tier`, `tier_match`, `week2_km`, `week2_in_range`; gate failures on `tier_match is False` or `week2_in_range is False`.

The three cases (numbers invented, shaped on the two reference athletes):

| Fixture | Shaped on | Signal conflict | Expected tier | Week-2 km |
|---|---|---|---|---|
| `elite_unmeasured_thresholds` | The elite who reported the bug | ~136 km + 5,200 m measured (load 4.2) vs 115 typed; predictor 2:53 (performance 3.6); 18% AeT/AnT gap of unknown source (physiology unused); score ≈ 3.93 | `sub_elite` | 110–145 |
| `recreational_field_thresholds` | The product owner's own account | ~71 km + 650 m (load 2.94), predictor 3:20 (2.85), field-tested gap 8.7% and AnT 88% of max (physiology 3.38); score ≈ 2.96, just under the boundary | `recreational` | 55–78 |
| `elite_no_coros` | The elite, if never connected | No snapshot; typed 140 km; same unknown-source gap | `sub_elite` | 115–150 |

- [ ] **Step 1: Write the fixtures.**

`fixture_snapshot_elite_unmeasured_thresholds.json`:

```json
{
  "synthetic": true,
  "provenance": "scheduler",
  "_comment": "Synthetic look-alike of the 2026-09 demotion bug: high measured volume, AeT/AnT stored without provenance and 18% apart. Before the fix this produced a recreational 40-60 km plan. Must stay sub_elite and plan near the measured volume.",
  "user_profile": {
    "age": 36, "gender": "male", "max_hr": 184, "resting_hr": 52,
    "aet_hr": 133, "ant_hr": 162, "threshold_source": "unknown",
    "current_weekly_km": 115.0, "days_per_week": 6, "has_gym_access": false
  },
  "fitness_snapshot": {
    "weekly_km": 136.0, "weekly_km_source": "coros", "weekly_vert_m": 5200.0, "volume_as_of": "2026-09-20",
    "threshold_pace": "3:55", "threshold_pace_source": "coros",
    "assessment": {"vo2max": 60.0, "running_level": 90.0, "threshold_pace": "3:55",
                   "pred_hm_sec": 4920.0, "pred_marathon_sec": 10380.0, "measured_at": "2026-09-24T00:00:00+00:00"},
    "utmb_index": null, "threshold_source": "unknown", "gender": "male", "readiness": null, "notes": []
  },
  "race_info": {
    "lang": "en", "terrain": "trail", "goal_type": "finish", "name": "Trail 80K",
    "date": "2026-11-29", "course_distance_km": 80, "course_elevation_gain_m": 4200
  },
  "total_weeks": 8,
  "expect": {"tier": "sub_elite", "week2_km": [110, 145]}
}
```

`fixture_snapshot_recreational_field_thresholds.json`:

```json
{
  "synthetic": true,
  "provenance": "scheduler",
  "_comment": "Synthetic look-alike of a steady recreational runner with COROS. Measured volume agrees with the profile; field-tested thresholds 8.7% apart must not promote. Guards against the snapshot over-promoting ordinary runners.",
  "user_profile": {
    "age": 26, "gender": "male", "max_hr": 196, "resting_hr": 51,
    "aet_hr": 158, "ant_hr": 173, "threshold_source": "field",
    "current_weekly_km": 70.0, "days_per_week": 6, "has_gym_access": true
  },
  "fitness_snapshot": {
    "weekly_km": 71.0, "weekly_km_source": "coros", "weekly_vert_m": 650.0, "volume_as_of": "2026-09-27",
    "threshold_pace": "4:35", "threshold_pace_source": "coros",
    "assessment": {"vo2max": 56.0, "running_level": 84.0, "threshold_pace": "4:35",
                   "pred_hm_sec": 5700.0, "pred_marathon_sec": 12000.0, "measured_at": "2026-09-29T00:00:00+00:00"},
    "utmb_index": null, "threshold_source": "field", "gender": "male", "readiness": null, "notes": []
  },
  "race_info": {
    "lang": "vi", "terrain": "trail", "goal_type": "finish", "name": "Trail 50K",
    "date": "2026-12-06", "course_distance_km": 50, "course_elevation_gain_m": 2700
  },
  "total_weeks": 9,
  "expect": {"tier": "recreational", "week2_km": [55, 78]}
}
```

`fixture_snapshot_elite_no_coros.json`: same `user_profile` as the elite fixture but `"current_weekly_km": 140.0`, no `fitness_snapshot` key, same `race_info`, `"expect": {"tier": "sub_elite", "week2_km": [115, 150]}`, and `_comment`: `"Same athlete without a watch connection: the typed-volume path must not be demoted by thresholds of unknown provenance."`

- [ ] **Step 2: Write the failing test** (no Gemini: invalid JSON forces the rule tier, which is enough to check the tier wiring):

```python
"""The snapshot fixtures resolve the expected tier through golden_eval's runner."""

import asyncio
import json
import os
from unittest.mock import MagicMock, patch

import pytest

import scripts.golden_eval as golden_eval

NAMES = [
    "fixture_snapshot_elite_unmeasured_thresholds.json",
    "fixture_snapshot_recreational_field_thresholds.json",
    "fixture_snapshot_elite_no_coros.json",
]


@pytest.mark.parametrize("name", NAMES)
def test_fixture_is_synthetic_and_resolves_expected_tier(name, monkeypatch):
    fixture = json.load(open(os.path.join(golden_eval.GOLDEN_DIR, "scheduler", name), encoding="utf-8"))
    assert fixture["synthetic"] is True and fixture["provenance"] == "scheduler"

    resp = MagicMock()
    resp.text = "invalid json to trigger fallback"
    client = MagicMock()
    client.models.generate_content.return_value = resp
    monkeypatch.setattr(golden_eval.settings, "GEMINI_API_KEY", "fake-gemini-key")
    with (
        patch("google.genai.Client", return_value=client),
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
    ):
        workouts, _engine = asyncio.run(golden_eval._run_scheduler(fixture))

    assert workouts
    assert fixture.pop("_resolved_tier") == fixture["expect"]["tier"]


def test_gate_fails_on_tier_mismatch_and_volume_out_of_range():
    items = [{"id": "a", "input": {}}, {"id": "b", "input": {}}]
    scores = [
        {"engine": "gemini", "tier_match": False, "week2_in_range": True},
        {"engine": "gemini", "tier_match": True, "week2_in_range": False},
    ]
    failures = golden_eval.gate_failures("scheduler", items, scores)
    assert any("a" in f and "tier" in f for f in failures)
    assert any("b" in f and "week-2" in f for f in failures)
```

- [ ] **Step 3: Run to verify failure** — Run: `cd backend && pytest tests/unit/test_golden_snapshot_fixtures.py -v`. Expected: FAIL (`KeyError: '_resolved_tier'`; gate returns no failures).

- [ ] **Step 4: Implement in `golden_eval.py`.**

```python
def _snapshot_from_fixture(data: dict):
    from datetime import datetime

    from services.fitness_snapshot import FitnessSnapshot

    data = dict(data)
    a = data.get("assessment")
    if a and isinstance(a.get("measured_at"), str):
        data["assessment"] = {**a, "measured_at": datetime.fromisoformat(a["measured_at"])}
    return FitnessSnapshot(**data)


def _week_km(workouts: list[dict], week: int) -> float:
    return round(sum(float(w.get("distance_km") or 0) for w in workouts if w.get("week_number") == week), 1)
```

In `_run_scheduler`, build `race_info = dict(fixture["race_info"])`; if `fixture.get("fitness_snapshot")`, set `race_info["fitness_snapshot"] = _snapshot_from_fixture(fixture["fitness_snapshot"])`; pass `race_info` instead of `fixture["race_info"]`; keep the returned tier: `workouts, tier = await ...` then `fixture["_resolved_tier"] = tier` before returning. Pass `user_profile=dict(fixture["user_profile"])` so the run cannot mutate the fixture.

In `compare`'s scheduler branch, before `item_score` is built:

```python
            tier = fixture.pop("_resolved_tier", None)
            expect = fixture.get("expect") or {}
            week2 = _week_km(result, 2)
            lo, hi = (expect.get("week2_km") or [None, None])
            lines.append(f"- Tier: **{tier}**" + (f" (expected {expect['tier']})" if expect.get("tier") else ""))
            lines.append(f"- Week-2 volume: **{week2} km**" + (f" (expected {lo}-{hi})" if lo is not None else ""))
```

and add to `item_score`:

```python
                "tier": tier,
                "tier_match": (tier == expect["tier"]) if expect.get("tier") else None,
                "week2_km": week2,
                "week2_in_range": (lo <= week2 <= hi) if lo is not None else None,
```

Do the same `fixture.pop("_resolved_tier", None)` at the top of `capture`'s loop body after `_run` so baselines are not written with it. In `gate_failures`, inside the per-item loop:

```python
        if service == "scheduler" and s.get("tier_match") is False:
            failures.append(f"{item['id']}: tier {s.get('tier')} differs from the expected tier")
        if service == "scheduler" and s.get("week2_in_range") is False:
            failures.append(f"{item['id']}: week-2 volume {s.get('week2_km')} km outside the expected range")
```

`push_experiment` sends every non-None score; `tier` goes as a CATEGORICAL score and the rest as BOOLEAN/NUMERIC, so no observability change is needed for the experiment path.

- [ ] **Step 5: Run tests** — Run: `cd backend && pytest tests/unit/test_golden_snapshot_fixtures.py tests/unit/test_golden_chat_eval.py -v`. Expected: pass.

- [ ] **Step 6: Capture baselines with the CURRENT production prompt** (costs ~3 Gemini calls; needs `GEMINI_API_KEY`; no Langfuse push):

Run: `cd backend && COACH_CHAT_PROMPT_LABEL=production python scripts/golden_eval.py capture --service scheduler`
Expected: three new `fixture_snapshot_*.ref.json` with `engine_used: gemini`; existing baselines skipped. Re-run a fixture whose baseline warns `engine_mismatch`.

- [ ] **Step 7: Commit**

```bash
git add backend/scripts/golden_eval.py backend/tests/golden/scheduler/fixture_snapshot_* backend/tests/unit/test_golden_snapshot_fixtures.py
git commit -m "test(golden): synthetic snapshot fixtures; gate on tier and week-2 volume"
```

---

### Task 10: Live signals — volume fit and tier on every plan trace

**Files:**
- Modify: `backend/services/observability.py` (`_SCORE_SPECS`)
- Modify: `backend/services/plan_signals.py` (`record_generation`)
- Modify: `backend/services/plan_generator.py` (the wrapper `generate_plan_workouts`, where it calls `plan_signals.record_generation`)
- Test: `backend/tests/unit/test_plan_signals_volume_fit.py`, `backend/tests/unit/test_observability_policy.py` (or wherever `_SCORE_SPECS` is tested)

**Interfaces:**
- Produces: scores `plan_tier` (categorical: the five tier keys) and `plan_volume_fit` (unit interval: `min(r, 1/r)` with `r = week-2 planned km / measured weekly km`, only when the volume came from COROS) on the `plan_generation` trace; `record_generation(..., tier: str | None = None, measured_weekly_km: float | None = None)`.

- [ ] **Step 1: Failing test**

```python
from services import plan_signals


def test_volume_fit_and_tier_scored(monkeypatch):
    sent = []
    monkeypatch.setattr(plan_signals.observability, "score", lambda **kw: sent.append(kw))
    monkeypatch.setattr(plan_signals.db, "get_plan_generation_trace", lambda pid: None)
    monkeypatch.setattr(plan_signals.db, "set_plan_generation_trace", lambda *a: None)
    monkeypatch.setattr(plan_signals.plan_checks, "run_checks", lambda w: [])
    monkeypatch.setattr(plan_signals.plan_checks, "pass_share", lambda r: None)
    workouts = [{"week_number": 2, "distance_km": 60.0, "type": "Easy"}, {"week_number": 2, "distance_km": 60.0, "type": "Long Run"}]
    plan_signals.record_generation(
        plan_id=1, user_id=2, block_number=1, workouts=workouts, trace_id="a" * 32,
        tier="sub_elite", measured_weekly_km=150.0,
    )
    by_name = {s["name"]: s["value"] for s in sent}
    assert by_name["plan_tier"] == "sub_elite"
    assert by_name["plan_volume_fit"] == 0.8


def test_no_volume_fit_without_measured_volume(monkeypatch):
    sent = []
    monkeypatch.setattr(plan_signals.observability, "score", lambda **kw: sent.append(kw))
    monkeypatch.setattr(plan_signals.db, "get_plan_generation_trace", lambda pid: None)
    monkeypatch.setattr(plan_signals.db, "set_plan_generation_trace", lambda *a: None)
    plan_signals.record_generation(plan_id=1, user_id=2, block_number=1, workouts=[], trace_id="a" * 32, tier="novice")
    assert "plan_volume_fit" not in {s["name"] for s in sent}
```

Also add to the observability score-spec test: `plan_tier` accepts `"elite"` and rejects `"pro"`; `plan_volume_fit` accepts `0.8` and rejects `1.2`.

- [ ] **Step 2: Run to verify failure** — `cd backend && pytest tests/unit/test_plan_signals_volume_fit.py -v` → FAIL (unexpected keyword `tier`).

- [ ] **Step 3: Implement.** In `_SCORE_SPECS` add:

```python
    # Plans: the tier the plan was written for, and how closely week 2 matches the
    # athlete's measured weekly volume (min(r, 1/r); only when COROS measured it).
    "plan_tier": frozenset({"beginner", "novice", "recreational", "sub_elite", "elite"}),
    "plan_volume_fit": _UNIT_INTERVAL,
```

In `record_generation` add the two keyword parameters (default None) and, as the FIRST statements inside its `try:` (before `plan_checks`, so a plan-checks failure cannot swallow them):

```python
        if tier:
            observability.score(trace_id=trace_id, name="plan_tier", value=tier)
        if measured_weekly_km:
            week2 = sum(float(w.get("distance_km") or 0) for w in workouts if w.get("week_number") == 2)
            if week2 > 0:
                ratio = week2 / measured_weekly_km
                observability.score(trace_id=trace_id, name="plan_volume_fit", value=round(min(ratio, 1 / ratio), 3))
```

In the wrapper `generate_plan_workouts`, pass:

```python
            snap = race_info.get("fitness_snapshot")
            plan_signals.record_generation(
                plan_id=plan_id, user_id=user_id, block_number=block_number, workouts=workouts, trace_id=trace_id,
                tier=tier,
                measured_weekly_km=snap.weekly_km if snap and snap.weekly_km_source == "coros" else None,
            )
```

- [ ] **Step 4:** Create matching score configs in Langfuse (Settings → Scores): `plan_tier` categorical with the five values, `plan_volume_fit` numeric 0–1. Add a "Plan volume fit" widget (avg by release) to the "Uphill AI – Quality" dashboard.

- [ ] **Step 5: Run tests** — `cd backend && pytest tests/unit -q -m "not kafka"` → pass.

- [ ] **Step 6: Commit**

```bash
git add backend/services/observability.py backend/services/plan_signals.py backend/services/plan_generator.py backend/tests/unit
git commit -m "feat(signals): plan_tier and plan_volume_fit scores on plan traces"
```

---

### Task 11: Langfuse prompt experiment — teach plan_generation to use the snapshot

The code (Tasks 1–10) puts the snapshot inside `{{user_summary}}`, so the current template already receives it. This experiment asks whether an explicit instruction makes Gemini follow it better. It is a Langfuse-only change (skill section A); the code ships first, the template follows.

**Files:**
- Create: `docs/runbooks/2026-10-fitness-snapshot-release.md` (record of runs, decision and deploy log; copy the tables below into it)

- [ ] **Step 1: Baseline run** (after Task 9; current `production` template + new code; ~150 Gemini calls for the whole scheduler set):

```bash
cd backend
LANGFUSE_ENVIRONMENT=development COACH_CHAT_PROMPT_LABEL=production \
  python scripts/golden_eval.py compare --service scheduler --push-langfuse --synthetic-only
```

Record the run name (`eval_scheduler_<ts>`) and `tests/golden/report_scheduler.md` results for the three snapshot fixtures.

- [ ] **Step 2: Draft the candidate** in Langfuse → Prompts → `plan_generation` → New version. Copy the current `production` text exactly, and insert this paragraph on its own line directly after `{{user_summary}}`:

```
FITNESS SNAPSHOT RULES (apply only when the athlete summary contains "ATHLETE FITNESS SNAPSHOT"):
- The snapshot is measured watch data. Its weekly volume is the athlete's real current load.
- The first full week (week 2) should total 90-100% of the snapshot's weekly volume, never below 80%,
  unless the readiness line shows fatigue or overreaching, or the athlete notes an injury.
- Weekly vert should start near the snapshot's vert and progress from there.
- Derive threshold and interval targets from the snapshot's threshold pace and race predictions.
- If the snapshot says the AeT/AnT thresholds were "not used", do not apply the Aerobic Deficiency
  Syndrome restrictions on intensity because of them.
- Never mention the snapshot, its sources or the level label to the athlete.
```

Keep every existing `{{variable}}`. Save, then add the custom label `snapshot-exp` to this version (it must NOT carry `staging` or `production` yet). Note its version number.

The ADS line matters: `_generate_plan_workouts` still prints "AEROBIC DEFICIENCY SYNDROME (ADS) DETECTED" from raw AeT/AnT, which would contradict the tier for the elite case. If the experiment shows Gemini cutting intensity because of it, the follow-up is a code change (gate `is_ads` on `threshold_source` like the tier) — record it in the runbook rather than widening this plan.

- [ ] **Step 3: Candidate run**

```bash
cd backend
LANGFUSE_ENVIRONMENT=development \
  python scripts/golden_eval.py compare --service scheduler --push-langfuse --synthetic-only --prompt-label snapshot-exp
```

- [ ] **Step 4: Compare** in Langfuse → Datasets → `uphill_scheduler_golden` → Runs (baseline vs `eval_scheduler_snapshot-exp_*`). Promote only if ALL hold:

| Check | Pass condition |
|---|---|
| Gate | `[gate] PASS scheduler` (no rule-tier fall-through, tier and week-2 checks pass) |
| Snapshot fixtures | `week2_in_range` true on all three, and week-2 km closer to the snapshot than the baseline run on the elite fixture |
| Other fixtures | `plan_checks` not lower than baseline on any fixture; no new `gemini_retry` warnings |
| Cost / latency | mean latency within +20% of baseline |

Write both run names, the table result and the decision into the runbook.

- [ ] **Step 5: If it fails**, edit the candidate (new version, move `snapshot-exp` to it) and repeat Steps 3–4, at most twice. If it still fails, ship the code without the template change (the `production` label stays put) and record why.

- [ ] **Step 6: Commit the runbook**

```bash
git add docs/runbooks/2026-10-fitness-snapshot-release.md
git commit -m "docs: fitness snapshot prompt experiment record"
```

Promotion to `staging`/`production` happens in Task 13, after the code is deployed — a template that references the snapshot is pointless before the code sends one.

---

### Task 12: Verification before PR

- [ ] **Step 1:** Run: `cd backend && ruff check . && ruff format --check . && pytest tests/unit -q -m "not kafka"` — Expected: clean, all pass.
- [ ] **Step 2:** Run against the scratch DB only: `cd backend && pytest tests/integration -q -m "not kafka"` — Expected: all pass.
- [ ] **Step 3:** Confirm no real athlete data entered the repo: ask the product owner for the two reference athletes' names and emails (they are deliberately not written here), then `git diff origin/main | grep -niE "<name1>|<email1>|<name2>|<email2>"` — Expected: no output. Also confirm no fixture contains a real user id or a real activity date copied from prod.
- [ ] **Step 4:** `requirements.txt` unchanged versus main (`git diff origin/main -- backend/requirements.txt` empty) — no prod image dependency gap.
- [ ] **Step 5:** Open the PR with the checklist from the `llm-change-process` skill: prompt name/version and labels ("`plan_generation` vN at `snapshot-exp`, not promoted"), both eval run names and the gate result, the new score names, the screenshots from Task 8, and the migration id.

---

### Task 13: Deploy (staging → production) and promote the prompt

Operational steps; record each with timestamps in `docs/runbooks/2026-10-fitness-snapshot-release.md`. Run from the merged-main worktree. Never use `deploy_server.sh` for the backend.

**Staging** (`/opt/uphill-ai-backend-staging`, port 8001, Postgres 5434):

- [ ] **Step 1:** Checksum dry-run to see what changes:

```bash
rsync -rnc --itemize-changes --exclude '.env*' --exclude 'venv*' --exclude '__pycache__' --exclude 'qdrant_storage' backend/ root@45.119.215.120:/opt/uphill-ai-backend-staging/backend/
```

- [ ] **Step 2:** On the server: `cd /opt/uphill-ai-backend-staging && docker compose stop backend`, rsync for real (same excludes, without `-n`), `docker compose start backend`, wait for `curl -fsS localhost:8001/api/health` (≈100 s), then `docker compose exec backend alembic stamp head` (`init_db` already created the objects; `upgrade` would fail).
- [ ] **Step 3:** Smoke test on staging with a test account: set the AeT/AnT source in Profile, create a plan, then `SELECT fitness_snapshot->>'tier', fitness_snapshot->>'weekly_km_source' FROM plans ORDER BY id DESC LIMIT 1` on the staging DB. Check the Langfuse trace (environment `staging`) carries `plan_tier`.
- [ ] **Step 4:** If Task 11 passed, move the `staging` label to the candidate version; generate one more staging plan and confirm the trace's prompt version is the candidate.

**Production** (`/opt/uphill-ai-backend`, port 8000):

- [ ] **Step 5: Backups** on the server:

```bash
TS=$(date +%Y%m%d-%H%M)
docker exec uphill-ai-backend-db-1 pg_dump -U uphill uphill_ai | gzip > /root/prod-uphill_ai-before-fitness-snapshot-$TS.sql.gz
tar czf /root/prod-backend-code-before-fitness-snapshot-$TS.tgz --exclude qdrant_storage -C /opt/uphill-ai-backend backend
cp /opt/uphill-ai-backend/backend/.env /opt/uphill-ai-backend/backups/backend.env.pre-fitness-snapshot-$TS
```

- [ ] **Step 6:** Set the release tag: in prod `backend/.env`, set `LANGFUSE_RELEASE=<git rev-parse --short HEAD of merged main>` (replace the existing line).
- [ ] **Step 7:** Same stop → rsync (excludes as Step 1) → start → health (`curl -fsS localhost:8000/api/health`, not `docker ps`) → `alembic stamp head` sequence as staging. Then confirm `docker exec uphill-ai-backend-backend-1 printenv ENVIRONMENT` is `production` and `curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8000/api/auth/mock-login` is `404`.
- [ ] **Step 8: Frontend:** merging to main deploys GitHub Pages automatically; confirm the Actions run is green and the Profile select is live. The iOS native app decodes the user payload; an unknown `threshold_source` key is ignored by `Codable`, and the native plan form (if any) does not send `weekly_km_from_watch`, so its typed volume is treated as an override — the pre-fix behaviour, not a regression. Note it as a native follow-up.
- [ ] **Step 9: Verify on the two reference accounts** (read-only queries, no data copied anywhere):
  - Product owner's account: trigger a COROS sync from the app, then `SELECT measured_at, vo2max, pred_marathon_sec FROM fitness_assessments WHERE user_id = <id> ORDER BY measured_at DESC LIMIT 1` shows a row; `GET /api/auth/fitness-snapshot` (in the app's network tab) shows `weekly_km_source: coros` and ~70 km; regenerate a plan and check `plans.fitness_snapshot->>'tier'` is `recreational`.
  - The elite athlete: do NOT regenerate their plans without telling them. Message them (the drafted Vietnamese reply, section 3 now true) and ask them to reconnect/sync COROS (their sync stalled on 2026-09-25, a separate issue) and set their AeT/AnT source. After they do, confirm their snapshot reads `coros` and the next plan's tier is `sub_elite` or `elite`.
- [ ] **Step 10: Promote the prompt** (only if Task 11 passed and Steps 3–4 looked right): move the `production` label to the candidate version. Live within 300 s.
- [ ] **Step 11: Watch for 7 days** — "Uphill AI – LLM Ops" (plan_generation cost, p95 latency, errors) and "Uphill AI – Quality" (`plan_volume_fit` average by release, `plan_tier` distribution, `plan_reworked` rate). Expect the share of `recreational` plans with measured volume ≥ 80 km to drop to zero.
- [ ] **Step 12: Follow-up PR** copying the promoted template text into the `PLAN_GENERATION_PROMPT` constant in `services/plan_generator.py` (fallback sync).

**Rollback:**
- Prompt: move `production` back to the previous `plan_generation` version (no deploy).
- Code: stop backend, restore the code tgz from Step 5, start, health check. The new tables/columns are additive and unused by the old code; leave them, and `alembic stamp <previous head>`.
- Data: restore the DB dump only if data was damaged — this change writes only new rows/columns.

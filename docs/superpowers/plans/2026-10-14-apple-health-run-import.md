# Apple Health Run Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Runs, hikes, stair sessions and strength workouts saved to Apple Health by any app reach Uphill automatically. There they match planned workouts and count as measured weekly volume, as COROS runs already do.

**Architecture:**
- **iOS:** reads HealthKit with an anchored query and gets woken by background delivery. Each workout becomes a summary row, and the rows are posted in batches to a new backend endpoint.
- **Backend:** stores the rows through the existing provider-neutral `db.upsert_activity`, which also catches duplicates across providers, then runs the existing matcher.
- **Fitness snapshot:** stops assuming COROS is the only device source.

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy Core (`text()`), pytest.
- iOS: SwiftUI, Swift 6 strict concurrency, HealthKit (iOS 18 async descriptors), Swift Testing, XcodeGen.

**Spec:** `docs/superpowers/specs/2026-10-14-apple-health-run-import-design.md`. Read it before starting any task.

## Progress (update as tasks land)

| Task | State | Commits |
|---|---|---|
| 1 | done, reviewed | 7255a54 |
| 2 | done, reviewed (fix round 1: malformed rows go to `rejected`, never 422 the batch) | c72db7b, faa4129 |
| 3 | done, reviewed; **golden eval still owed** (no GEMINI_API_KEY locally) | 0e0caaa |
| 4 | done, **not yet reviewed** | 8613f9e |
| 5–9 | not started | |

Decisions made while executing:
- Integration tests used a throwaway Postgres (`postgresql://uphill:uphill_secret@localhost:5440/uphill_ai_test`); port 5433 on the owner's Mac belongs to another stack.
- Fixtures for Task 4 were recorded only for the two new files against a scratch backend; never re-run the whole `record_fixtures.sh` on an empty DB.
- Task 6 keeps the old `loadWatchVolume` closure; Task 7 switches it (build-order fix).
- Deferred minors for the final review: `avg_hr > max_hr` unchecked; oversized `external_id` echoed in `rejected`; `deleted_ids` items unbounded in length; readiness query runs for Apple-only athletes (empty, harmless).

## Global Constraints

- Provider string is exactly `"apple_health"`, everywhere: DB, API, Swift.
- Activity types sent by iOS: `outdoor_run`, `indoor_run`, `hike`, `strength`. Nothing else.
- HealthKit mapping:
  - `.running` → `outdoor_run`, or `indoor_run` when `HKMetadataKeyIndoorWorkout` is true
  - `.hiking`, `.stairClimbing`, `.stairs` → `hike`
  - `.traditionalStrengthTraining`, `.functionalStrengthTraining` → `strength`
  - Never `gps_cardio`/`gym_cardio` (the matcher treats those as strength).
- First import window: 12 weeks (`12 * 7 * 86400` seconds).
- Batch size: at most 500 workouts and 500 deleted ids per request.
- Save the HealthKit anchor only after every batch of a sync returned 2xx.
- Routes and HR series never leave the phone. Upload only the fields in the spec's endpoint body.
- A is read-only:
  - `NSHealthShareUsageDescription` only, no `NSHealthUpdateUsageDescription`
  - `requestAuthorization(toShare: [])`
- `APPLE_HEALTH_ENABLED` setting, default `true`. When false the sync endpoint returns 404 and `/status` reports `enabled: false`.
- No schema change and no Alembic migration.
- **Never run `backend/tests/integration` against `uphill_ai`**: it truncates every table. Use the `uphill_ai_test` scratch DB that `backend/tests/integration/conftest.py` expects.
- iOS rules from Phase 0–2:
  - `@Observable @MainActor` view models, protocols for anything a test fakes
  - fixtures recorded from the local backend with `ios-native/scripts/record_fixtures.sh` and never hand-edited
  - Features depend on Core and DesignSystem only
- Every new user-visible string ships in English and Vietnamese. Load the `uphill-ai-vietnamese-copy` skill before writing VI.
- Every UI change gets an iOS Simulator screenshot in `ios-native/docs/screenshots/apple-health/`.
- **UI design uses Impeccable** (owner decision 2026-10-14). Before writing any view in Tasks 7–8, load the `impeccable:impeccable` skill and design the screen with it. After the screenshots, run its `polish` + `harden` pass on them and apply the findings in SwiftUI. Its browser tools target web DOM, so feed it Simulator screenshots. Record the main findings and what you changed in the commit body. Content and behaviour still come from this plan; Impeccable decides layout, hierarchy, spacing and states.
- Run `ios-native/scripts/test.sh 2>&1 | tail -40` once at the end of each iOS task, not before.

## Review Focus

1. **Signed-out or account switch mid-sync.** Athlete A connects, signs out, athlete B signs in on the same phone. B's runs must never upload under A's identity, and A's anchor must not skip B's history. Pinned by `test_sync_does_not_save_anchor_when_user_changed` and `test_stop_observing_clears_anchor` (Task 5).
2. **Upload fails halfway through a multi-batch first import.** The anchor must not move, so the next sync re-sends everything. Re-sent rows must be no-ops. Pinned by `failedSecondBatchKeepsOldAnchor` (Task 5) and `test_resending_the_same_batch_is_idempotent` (Task 2).
3. **A COROS run and its Apple Health copy (COROS app writes to Health).** It must count once in weekly volume and match once. Pinned by `test_apple_health_copy_of_a_coros_run_is_a_duplicate` (Task 1).
4. **A workout deleted in Health after it matched a planned session.** The row disappears, the planned workout's `matched_activity_id` becomes NULL, and a COROS copy that pointed at it becomes the counted one. Pinned by `test_deleting_the_canonical_row_promotes_its_duplicate` (Task 1).
5. **Wrong data from third-party apps:** a run with no UTC offset, a treadmill run with GPS-noise distance, a 300 bpm HR spike. Each must be rejected or stored sanely, never crash the batch. Pinned by `test_implausible_rows_are_rejected_not_fatal` (Task 2) and `noisyAltitudesDoNotInflateClimb` (Task 4).

---

## File Structure

**Backend**

| File | Change |
|---|---|
| `backend/db.py` | Add `delete_activities_by_external_ids(user_id, provider, external_ids) -> int` |
| `backend/config.py` | Add `APPLE_HEALTH_ENABLED` |
| `backend/routers/integrations.py` | Add the Apple Health request models, `_implausible`, `POST /apple-health/sync`, `DELETE /apple-health`, `apple_health` in `GET /status` |
| `backend/services/fitness_snapshot.py` | `DEVICE_PROVIDERS`, `SOURCE_LABELS`, `_freshest_connection`; `build` and `resolve_tier` use them |
| `backend/services/plan_generator.py:850` | Measured km for any device source |
| `backend/tests/integration/test_activity_persistence.py` | Deletion and duplicate tests |
| `backend/tests/unit/test_apple_health_route.py` | New: endpoint tests with stubbed db |
| `backend/tests/unit/test_fitness_snapshot.py` | Provider-selection tests |

**iOS** (all under `ios-native/`)

| File | Responsibility |
|---|---|
| `UphillAI/Core/Health/AppleHealthModels.swift` | Upload/response DTOs, `AppleHealthConnectionStatus` |
| `UphillAI/Core/Health/AppleHealthAPI.swift` | `AppleHealthUploading` protocol + `AppleHealthAPI` (POST sync, DELETE) |
| `UphillAI/Core/Health/HealthWorkoutMapper.swift` | `HealthWorkoutSample` (plain struct) → `AppleHealthWorkoutUpload`; climb from altitudes |
| `UphillAI/Core/Health/HealthStoring.swift` | `HealthStoring` protocol, `HealthWorkoutPage`, `HealthAnchorStoring` + `UserDefaultsAnchorStore`, `SampleHealthStore` (debug data) |
| `UphillAI/Core/Health/AppleHealthSyncService.swift` | Actor: anchored sync, batching, anchor save, observing on/off |
| `UphillAI/Core/Health/HealthKitStore.swift` | Real `HealthStoring` over `HKHealthStore` |
| `UphillAI/Core/Integrations/DeviceConnectionModels.swift` | `DeviceConnectionStatus.appleHealth` |
| `UphillAI/App/AppModel.swift` | Wiring, connect, disconnect, sync-if-due, sign-out cleanup, watch volume source |
| `UphillAI/App/RootView.swift` | Foreground Apple Health sync |
| `UphillAI/Features/Plan/PlanViewModel.swift` | Extract `applyWatchMatches()` |
| `UphillAI/Features/Plan/PlanView.swift` | Checklist "watch" done for either source |
| `UphillAI/Features/Onboarding/PlanSetupViewModel.swift`, `SetupSteps.swift` | Apple Health connect + source-aware volume label |
| `UphillAI/Features/Integrations/WatchChannelsList.swift` | Apple Health becomes a live channel |
| `UphillAI/Features/Integrations/AppleHealthRow.swift` | New: Me → Connected accounts row |
| `UphillAI/Features/Integrations/AppleHealthExplainerSheet.swift` | New: pre-permission explainer |
| `UphillAI/Features/Me/ProfileView.swift` | Place the row |
| `UphillAI/Features/Me/DeveloperMenu.swift` | "Sample Health data" switch |
| `project.yml`, `UphillAI/UphillAI.entitlements`, `UphillAI/Info.plist`, `UphillAI/Resources/InfoPlist.xcstrings`, `UphillAI/Resources/Localizable.xcstrings` | Capabilities and strings |
| `scripts/record_fixtures.sh`, `UphillAITests/Fixtures/apple_health_sync.json`, `integrations_status.json` | Recorded fixtures |
| `UphillAITests/Health/*.swift` | New tests |

---

### Task 1: Delete Apple Health rows by HealthKit id

**Files:**
- Modify: `backend/db.py` (add after `get_activity_external_ids`, around line 3387)
- Test: `backend/tests/integration/test_activity_persistence.py`

**Interfaces:**
- Produces: `db.delete_activities_by_external_ids(user_id: int, provider: str, external_ids: list[str]) -> int` (rows deleted).

- [ ] **Step 1: Write the failing tests.** Append to `backend/tests/integration/test_activity_persistence.py`:

```python
def test_apple_health_copy_of_a_coros_run_is_a_duplicate(user_id):
    coros = db.upsert_activity(user_id, _activity(external_id="c-run", provider="coros"))
    health = db.upsert_activity(
        user_id, _activity(external_id="HK-1", provider="apple_health", start=START + timedelta(seconds=40))
    )
    with db.engine.connect() as conn:
        dup = conn.execute(text("SELECT duplicate_of FROM activities WHERE id = :i"), {"i": health}).scalar()
    assert dup == coros


def test_delete_activities_by_external_ids_only_touches_that_provider(user_id):
    db.upsert_activity(user_id, _activity(external_id="HK-1", provider="apple_health"))
    db.upsert_activity(user_id, _activity(external_id="HK-2", provider="apple_health", start=START + timedelta(days=1)))
    db.upsert_activity(user_id, _activity(external_id="HK-1", provider="coros", start=START + timedelta(days=2)))
    assert db.delete_activities_by_external_ids(user_id, "apple_health", ["HK-1", "missing"]) == 1
    assert db.get_activity_external_ids(user_id, "apple_health") == {"HK-2"}
    assert db.get_activity_external_ids(user_id, "coros") == {"HK-1"}


def test_delete_activities_by_external_ids_with_no_ids_is_a_no_op(user_id):
    db.upsert_activity(user_id, _activity(external_id="HK-1", provider="apple_health"))
    assert db.delete_activities_by_external_ids(user_id, "apple_health", []) == 0
    assert db.get_activity_external_ids(user_id, "apple_health") == {"HK-1"}


def test_deleting_the_canonical_row_promotes_its_duplicate(user_id):
    health = db.upsert_activity(user_id, _activity(external_id="HK-1", provider="apple_health"))
    coros = db.upsert_activity(
        user_id, _activity(external_id="c-run", provider="coros", start=START + timedelta(seconds=30))
    )
    db.delete_activities_by_external_ids(user_id, "apple_health", ["HK-1"])
    with db.engine.connect() as conn:
        dup = conn.execute(text("SELECT duplicate_of FROM activities WHERE id = :i"), {"i": coros}).scalar()
        gone = conn.execute(text("SELECT count(*) FROM activities WHERE id = :i"), {"i": health}).scalar()
    assert dup is None and gone == 0
```

- [ ] **Step 2: Run and confirm they fail.**

Run: `cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test pytest tests/integration/test_activity_persistence.py -k "apple_health or delete_activities or canonical" -v`
Expected: the first test PASSES (duplicate detection already works). The other three FAIL with `AttributeError: module 'db' has no attribute 'delete_activities_by_external_ids'`.

- [ ] **Step 3: Implement.** In `backend/db.py`, after `get_activity_external_ids`:

```python
def delete_activities_by_external_ids(user_id: int, provider: str, external_ids: list[str]) -> int:
    """Hard-delete one provider's activities by their provider ids (e.g. workouts the
    athlete deleted in Apple Health). A workout matched to a deleted row and another
    provider's copy that pointed at it are both released by ON DELETE SET NULL."""
    if not external_ids:
        return 0
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            DELETE FROM activities
            WHERE user_id = :u AND source_provider = :p AND external_ids ->> :p = ANY(:ids)
            """),
            {"u": user_id, "p": provider, "ids": list(external_ids)},
        )
        conn.commit()
        return result.rowcount
```

- [ ] **Step 4: Run the same command.** Expected: 4 PASS.

- [ ] **Step 5: Commit.**

```bash
git add backend/db.py backend/tests/integration/test_activity_persistence.py
git commit -m "feat(db): delete activities by provider external id"
```

### Task 2: Apple Health sync, disconnect and status endpoints

**Files:**
- Modify: `backend/config.py` (next to the `COROS_*` settings, around line 171)
- Modify: `backend/routers/integrations.py`
- Create: `backend/tests/unit/test_apple_health_route.py`

**Interfaces:**
- Consumes: `db.delete_activities_by_external_ids` (Task 1); `db.upsert_activity`, `db.get_connection`, `db.save_connection`, `db.mark_connection_synced`, `db.delete_provider_data`, `matching_runner.match_user(user_id, since, until, plan_id=, tz_offset_minutes=)`, `_resolve_plan_window(plan_id, user_id)` (existing).
- Produces:
  - `POST /api/integrations/apple-health/sync`
    - body `{workouts: [...], deleted_ids: [str], plan_id: int|null, tz_offset_minutes: int|null}`
    - returns `{accepted: int, rejected: [{external_id, reason}], deleted: int, matching: dict|null}`
  - `DELETE /api/integrations/apple-health` returns `{status: "disconnected"}`.
  - `GET /api/integrations/status` gains `apple_health: {enabled: bool, connected: bool, last_sync_at: str|null}`.

- [ ] **Step 1: Write the failing tests.** Create `backend/tests/unit/test_apple_health_route.py`:

```python
"""POST /apple-health/sync, DELETE /apple-health and GET /status -- no DB.
Every db call the router makes is replaced by an in-memory fake."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config import settings
from routers import integrations

app = FastAPI()
app.include_router(integrations.router, prefix="/api")
client = TestClient(app)

SYNC = "/api/integrations/apple-health/sync"


def _row(external_id="HK-1", **over):
    row = {
        "external_id": external_id,
        "activity_type": "outdoor_run",
        "start_time": "2026-10-12T06:00:00+07:00",
        "end_time": "2026-10-12T07:02:00+07:00",
        "duration_seconds": 3720,
        "distance_km": 10.4,
        "elevation_gain_m": 412,
        "avg_hr": 148,
        "max_hr": 171,
        "calories": 690,
        "source_name": "Apple Watch",
    }
    row.update(over)
    return row


@pytest.fixture
def fake(monkeypatch):
    state = {"connection": None, "stored": {}, "deleted": [], "synced": 0, "matched": [], "provider_deleted": []}

    def upsert(uid, activity):
        state["stored"].setdefault(activity.external_id, activity)
        return list(state["stored"]).index(activity.external_id) + 1

    def save_connection(uid, provider, access_token_enc, refresh_token_enc, token_expires_at, scopes, provider_user_id=None):
        state["connection"] = {"provider": provider, "status": "active", "last_sync_at": None, "scopes": scopes}
        return 1

    def mark_synced(uid, provider):
        state["synced"] += 1
        state["connection"]["last_sync_at"] = datetime(2026, 10, 14, tzinfo=UTC)

    async def match_user(uid, since, until, plan_id=None, tz_offset_minutes=None):
        state["matched"].append((since, until, plan_id, tz_offset_minutes))
        return {"matched": 1, "suggested": 0, "unmatched": 0, "skipped_manual": 0}

    monkeypatch.setattr(integrations.db, "get_connection", lambda uid, p: state["connection"] if p == "apple_health" else None)
    monkeypatch.setattr(integrations.db, "save_connection", save_connection)
    monkeypatch.setattr(integrations.db, "upsert_activity", upsert)
    monkeypatch.setattr(
        integrations.db,
        "delete_activities_by_external_ids",
        lambda uid, p, ids: state["deleted"].extend(ids) or len(ids),
    )
    monkeypatch.setattr(integrations.db, "mark_connection_synced", mark_synced)
    monkeypatch.setattr(integrations.db, "delete_provider_data", lambda uid, p: state["provider_deleted"].append(p))
    monkeypatch.setattr(integrations.db, "get_user_by_id", lambda uid: {"id": uid})
    monkeypatch.setattr(integrations.matching_runner, "match_user", match_user)
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", True)
    app.dependency_overrides[integrations.get_current_user] = lambda: {"id": 7}
    yield state
    app.dependency_overrides.pop(integrations.get_current_user, None)


def test_first_sync_creates_the_connection_and_stores_rows(fake):
    resp = client.post(SYNC, json={"workouts": [_row()], "deleted_ids": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == 1 and body["rejected"] == [] and body["deleted"] == 0
    assert fake["connection"]["provider"] == "apple_health"
    activity = fake["stored"]["HK-1"]
    assert activity.provider == "apple_health"
    assert activity.device_model == "Apple Watch"
    assert activity.avg_pace_sec_per_km == pytest.approx(3720 / 10.4)
    assert fake["synced"] == 1
    assert body["matching"]["matched"] == 1


def test_resending_the_same_batch_is_idempotent(fake):
    client.post(SYNC, json={"workouts": [_row()]})
    client.post(SYNC, json={"workouts": [_row()]})
    assert list(fake["stored"]) == ["HK-1"]


def test_empty_sync_still_marks_the_connection_synced(fake):
    resp = client.post(SYNC, json={"workouts": [], "deleted_ids": []})
    assert resp.status_code == 200
    assert fake["synced"] == 1


def test_deleted_ids_are_forwarded(fake):
    resp = client.post(SYNC, json={"workouts": [], "deleted_ids": ["HK-9", "HK-8"]})
    assert resp.json()["deleted"] == 2
    assert fake["deleted"] == ["HK-9", "HK-8"]


def test_implausible_rows_are_rejected_not_fatal(fake):
    future = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    rows = [
        _row("ok"),
        _row("backwards", end_time="2026-10-12T05:00:00+07:00"),
        _row("naive", start_time="2026-10-12T06:00:00", end_time="2026-10-12T07:02:00"),
        _row("spike", max_hr=300),
        _row("too-fast", distance_km=40.0),
        _row("future", start_time=future, end_time=future),
        _row("cycling", activity_type="cycling"),
        _row("long", duration_seconds=49 * 3600),
    ]
    body = client.post(SYNC, json={"workouts": rows}).json()
    assert body["accepted"] == 1
    assert {r["external_id"] for r in body["rejected"]} == {
        "backwards", "naive", "spike", "too-fast", "future", "cycling", "long"
    }
    assert list(fake["stored"]) == ["ok"]


def test_strength_without_distance_is_accepted(fake):
    row = _row("gym", activity_type="strength", distance_km=None, elevation_gain_m=None)
    body = client.post(SYNC, json={"workouts": [row]}).json()
    assert body["accepted"] == 1
    assert fake["stored"]["gym"].avg_pace_sec_per_km is None


def test_batch_over_500_is_a_422(fake):
    rows = [_row(f"HK-{i}") for i in range(501)]
    assert client.post(SYNC, json={"workouts": rows}).status_code == 422


def test_matching_failure_does_not_fail_the_sync(fake, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("matcher down")

    monkeypatch.setattr(integrations.matching_runner, "match_user", boom)
    resp = client.post(SYNC, json={"workouts": [_row()]})
    assert resp.status_code == 200
    assert resp.json()["matching"] is None


def test_disabled_flag_returns_404(fake, monkeypatch):
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", False)
    assert client.post(SYNC, json={"workouts": []}).status_code == 404


def test_disconnect_deletes_provider_data(fake):
    resp = client.delete("/api/integrations/apple-health")
    assert resp.status_code == 200
    assert fake["provider_deleted"] == ["apple_health"]


def test_status_reports_apple_health(fake):
    client.post(SYNC, json={"workouts": []})
    body = client.get("/api/integrations/status").json()
    assert body["apple_health"]["enabled"] is True
    assert body["apple_health"]["connected"] is True
    assert body["apple_health"]["last_sync_at"] is not None
```

- [ ] **Step 2: Run and confirm they fail.**

Run: `cd backend && pytest tests/unit/test_apple_health_route.py -v`
Expected: FAIL. The sync and delete routes 404/405, and `settings` has no `APPLE_HEALTH_ENABLED`.

- [ ] **Step 3: Add the setting.** In `backend/config.py`, below `COROS_DAILY_PUSH_LIMIT`:

```python
    # Hides Apple Health in the app (via /api/integrations/status) and 404s its sync
    # endpoint, without an app release.
    APPLE_HEALTH_ENABLED: bool = os.getenv("APPLE_HEALTH_ENABLED", "true").lower() != "false"
```

- [ ] **Step 4: Implement the router.** In `backend/routers/integrations.py`:

Change the pydantic import to `from pydantic import BaseModel, Field`. Add `from datetime import UTC` to the existing datetime import line, so it reads `from datetime import UTC, date, datetime, timedelta`. Add `from services.providers.base import CanonicalActivity`. Then add, below `CorosPushRequest`/the push routes:

```python
APPLE_HEALTH = "apple_health"
APPLE_HEALTH_TYPES = frozenset({"outdoor_run", "indoor_run", "hike", "strength"})
APPLE_HEALTH_RUN_TYPES = frozenset({"outdoor_run", "indoor_run"})
APPLE_HEALTH_BATCH = 500
# Faster than 2:30/km is a world-record pace held for the whole run: a distance glitch.
MIN_RUN_PACE_SEC_PER_KM = 150
MAX_DURATION_SECONDS = 48 * 3600


class AppleHealthWorkout(BaseModel):
    external_id: str = Field(min_length=1, max_length=64)
    activity_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float = Field(gt=0)
    distance_km: float | None = Field(default=None, ge=0)
    elevation_gain_m: float | None = Field(default=None, ge=0)
    avg_hr: int | None = None
    max_hr: int | None = None
    calories: int | None = Field(default=None, ge=0)
    source_name: str | None = Field(default=None, max_length=100)


class AppleHealthSyncRequest(BaseModel):
    workouts: list[AppleHealthWorkout] = Field(default_factory=list, max_length=APPLE_HEALTH_BATCH)
    deleted_ids: list[str] = Field(default_factory=list, max_length=APPLE_HEALTH_BATCH)
    plan_id: int | None = None
    tz_offset_minutes: int | None = None


def _implausible(w: AppleHealthWorkout, now: datetime) -> str | None:
    """Why a row from Apple Health can't be trusted, or None. Third-party apps write
    to Health too, so a bad row is skipped rather than failing the athlete's batch."""
    if w.activity_type not in APPLE_HEALTH_TYPES:
        return "unsupported activity_type"
    if w.start_time.tzinfo is None or w.end_time.tzinfo is None:
        return "start_time and end_time need a UTC offset"
    if w.end_time <= w.start_time:
        return "end_time is not after start_time"
    if w.duration_seconds > MAX_DURATION_SECONDS:
        return "duration over 48 h"
    if w.start_time > now + timedelta(days=1):
        return "start_time in the future"
    for hr in (w.avg_hr, w.max_hr):
        if hr is not None and not 25 <= hr <= 250:
            return "heart rate out of range"
    if w.activity_type in APPLE_HEALTH_RUN_TYPES and w.distance_km:
        if w.duration_seconds / w.distance_km < MIN_RUN_PACE_SEC_PER_KM:
            return "pace faster than 2:30/km"
    return None


def _to_canonical(w: AppleHealthWorkout) -> CanonicalActivity:
    pace = None
    if w.activity_type in APPLE_HEALTH_RUN_TYPES and w.distance_km and w.distance_km >= 0.1:
        pace = w.duration_seconds / w.distance_km
    return CanonicalActivity(
        external_id=w.external_id,
        provider=APPLE_HEALTH,
        activity_type=w.activity_type,
        start_time=w.start_time,
        end_time=w.end_time,
        duration_seconds=w.duration_seconds,
        distance_km=w.distance_km,
        elevation_gain_m=w.elevation_gain_m,
        avg_hr=w.avg_hr,
        max_hr=w.max_hr,
        avg_pace_sec_per_km=pace,
        calories=w.calories,
        device_model=w.source_name,
    )


@router.post("/apple-health/sync")
async def apple_health_sync(body: AppleHealthSyncRequest, user: dict[str, Any] = Depends(get_current_user)):
    """Stores workout summaries the iOS app read from Apple Health, then matches them.
    Idempotent: a re-sent workout is a no-op (upsert on the HealthKit UUID)."""
    if not settings.APPLE_HEALTH_ENABLED:
        raise HTTPException(status_code=404, detail="Apple Health is not available.")
    user_id = user["id"]
    if db.get_connection(user_id, APPLE_HEALTH) is None:
        # No tokens: HealthKit access lives on the phone, not with us.
        db.save_connection(
            user_id,
            APPLE_HEALTH,
            access_token_enc=None,
            refresh_token_enc=None,
            token_expires_at=None,
            scopes="read",
        )

    now = datetime.now(UTC)
    accepted = 0
    rejected: list[dict[str, str]] = []
    for workout in body.workouts:
        reason = _implausible(workout, now)
        if reason:
            rejected.append({"external_id": workout.external_id, "reason": reason})
            continue
        db.upsert_activity(user_id, _to_canonical(workout))
        accepted += 1
    deleted = db.delete_activities_by_external_ids(user_id, APPLE_HEALTH, body.deleted_ids)
    db.mark_connection_synced(user_id, APPLE_HEALTH)
    if rejected:
        logger.info(
            "apple health rows rejected",
            extra={
                "fields": {
                    "service": "integrations",
                    "provider": APPLE_HEALTH,
                    "event": "rows_rejected",
                    "user_id": user_id,
                    "count": len(rejected),
                }
            },
        )

    if body.plan_id is not None:
        since, until = _resolve_plan_window(body.plan_id, user_id)
    else:
        until = date.today()
        since = until - timedelta(days=30)
    try:
        matching = await matching_runner.match_user(
            user_id, since, until, plan_id=body.plan_id, tz_offset_minutes=body.tz_offset_minutes
        )
    except Exception:
        # The workouts are stored; the next sync re-runs matching.
        logger.exception("apple health matching failed")
        matching = None
    return {"accepted": accepted, "rejected": rejected, "deleted": deleted, "matching": matching}


@router.delete("/apple-health")
async def apple_health_disconnect(user: dict[str, Any] = Depends(get_current_user)):
    db.delete_provider_data(user["id"], APPLE_HEALTH)
    return {"status": "disconnected"}
```

Then replace the `return` of `integration_status` (keep its existing `connection = ...` and `profile = ...` lines) with:

```python
    health = db.get_connection(user["id"], "apple_health")
    return {
        "coros": {
            "connected": bool(connection and connection.get("status") == "active"),
            "last_sync_at": connection.get("last_sync_at") if connection else None,
            "threshold_pace": profile.get("threshold_pace"),
            "coros_vo2max": profile.get("coros_vo2max"),
            "coros_running_level": profile.get("coros_running_level"),
            "pace_zone_model": profile.get("pace_zone_model") or "5_zone",
        },
        "apple_health": {
            "enabled": settings.APPLE_HEALTH_ENABLED,
            "connected": bool(health and health.get("status") == "active"),
            "last_sync_at": health.get("last_sync_at") if health else None,
        },
    }
```

The `"coros"` block is today's, unchanged. `"apple_health"` is a literal here because `integration_status` sits above the `APPLE_HEALTH` constant in the file.

- [ ] **Step 5: Run the tests.**

Run: `cd backend && pytest tests/unit/test_apple_health_route.py tests/unit/test_coros_sync_route.py -v`
Expected: all PASS. The COROS route tests prove the shared router still works.

- [ ] **Step 6: Lint.** Run: `cd backend && ruff check routers/integrations.py config.py && ruff format --check routers/integrations.py config.py`. Expected: clean (run `ruff format` on the two files if not).

- [ ] **Step 7: Commit.**

```bash
git add backend/config.py backend/routers/integrations.py backend/tests/unit/test_apple_health_route.py
git commit -m "feat(integrations): Apple Health sync, disconnect and status endpoints"
```

### Task 3: Provider-neutral measured volume

**Files:**
- Modify: `backend/services/fitness_snapshot.py`
- Modify: `backend/services/plan_generator.py:850`
- Test: `backend/tests/unit/test_fitness_snapshot.py`

**Interfaces:**
- Produces:
  - `fitness_snapshot.DEVICE_PROVIDERS = ("coros", "apple_health")`
  - `fitness_snapshot.SOURCE_LABELS: dict[str, str]`
  - `fitness_snapshot._freshest_connection(user_id) -> tuple[str, dict] | None`
  - `FitnessSnapshot.weekly_km_source` may now be `"apple_health"`.

- [ ] **Step 1: Write the failing tests.** Append to `backend/tests/unit/test_fitness_snapshot.py`:

```python
class TestDeviceProviders:
    def _connections(self, monkeypatch, by_provider):
        monkeypatch.setattr(fs.db, "get_connection", lambda uid, p: by_provider.get(p))

    def test_apple_health_alone_is_measured(self, stub_db, monkeypatch):
        self._connections(
            monkeypatch,
            {"apple_health": {"status": "active", "last_sync_at": datetime(2026, 8, 28, 6, 17, tzinfo=UTC)}},
        )
        snap = fs.build(30, today=TODAY)
        assert snap.weekly_km_source == "apple_health"
        assert snap.weekly_km == pytest.approx(137.4, abs=0.1)
        assert "Apple Health" in snap.prompt_block("en")

    def test_fresher_provider_wins(self, stub_db, monkeypatch):
        self._connections(
            monkeypatch,
            {
                "coros": {"status": "active", "last_sync_at": datetime(2026, 8, 20, tzinfo=UTC)},
                "apple_health": {"status": "active", "last_sync_at": datetime(2026, 8, 28, tzinfo=UTC)},
            },
        )
        assert fs.build(30, today=TODAY).weekly_km_source == "apple_health"

    def test_tie_keeps_coros(self, stub_db, monkeypatch):
        same = datetime(2026, 8, 28, tzinfo=UTC)
        self._connections(
            monkeypatch,
            {
                "coros": {"status": "active", "last_sync_at": same},
                "apple_health": {"status": "active", "last_sync_at": same},
            },
        )
        assert fs.build(30, today=TODAY).weekly_km_source == "coros"

    def test_inactive_connection_is_ignored(self, stub_db, monkeypatch):
        self._connections(
            monkeypatch,
            {"apple_health": {"status": "revoked", "last_sync_at": datetime(2026, 8, 28, tzinfo=UTC)}},
        )
        assert fs.build(30, today=TODAY).weekly_km_source == "self_reported"

    def test_apple_health_vert_reaches_the_tier(self, stub_db, monkeypatch):
        self._connections(
            monkeypatch,
            {"apple_health": {"status": "active", "last_sync_at": datetime(2026, 8, 28, 6, 17, tzinfo=UTC)}},
        )
        seen = {}
        real = fs.resolve_tier_explained

        def spy(**kwargs):
            seen.update(kwargs)
            return real(**kwargs)

        monkeypatch.setattr(fs, "resolve_tier_explained", spy)
        fs.build(30, today=TODAY).resolve_tier(None, "race", None, None, 138, 168)
        assert seen["weekly_vert_m"] is not None
```

- [ ] **Step 2: Run and confirm they fail.**

Run: `cd backend && pytest tests/unit/test_fitness_snapshot.py -v`
Expected: the new `TestDeviceProviders` tests FAIL (source stays `"coros"` or `"self_reported"`); the existing tests PASS.

- [ ] **Step 3: Implement** in `backend/services/fitness_snapshot.py`:

Replace `PROVIDER = "coros"` with:

```python
DEVICE_PROVIDERS = ("coros", "apple_health")
SOURCE_LABELS = {"coros": "COROS", "apple_health": "Apple Health", "self_reported": "self-reported"}
```

Add below `_aware`:

```python
def _freshest_connection(user_id: int) -> tuple[str, dict[str, Any]] | None:
    """The active device connection synced most recently. On a tie the earlier entry
    in DEVICE_PROVIDERS wins, so an athlete with both keeps COROS as before."""
    best: tuple[str, dict[str, Any]] | None = None
    for provider in DEVICE_PROVIDERS:
        conn = db.get_connection(user_id, provider)
        if not conn or conn.get("status") != "active":
            continue
        if best is None:
            best = (provider, conn)
            continue
        new_at, best_at = conn.get("last_sync_at"), best[1].get("last_sync_at")
        if new_at and (best_at is None or _aware(new_at) > _aware(best_at)):
            best = (provider, conn)
    return best
```

In `resolve_tier`, change `weekly_vert_m=self.weekly_vert_m if self.weekly_km_source == "coros" else None,` to:

```python
            weekly_vert_m=self.weekly_vert_m if self.weekly_km_source in DEVICE_PROVIDERS else None,
```

In `prompt_block`, delete the local `src = {...}` line and replace each `src[` with `SOURCE_LABELS[`.

In `build`, replace the connection lines and the measured block's provider uses:

```python
    freshest = _freshest_connection(user_id)
    connected = freshest is not None
    notes: list[str] = []

    measured = None
    if freshest:
        provider, connection = freshest
        # One query serves both the 4-week mean and the 12-week chronic cap.
        weeks = db.get_weekly_run_volumes(user_id, since=_monday(today) - timedelta(weeks=CHRONIC_WEEKS))
        first_at = db.get_first_activity_at(user_id, provider)
        last_sync_at = connection.get("last_sync_at")
        measured = measured_weekly_volume(weeks, first_at, last_sync_at, today)
        if measured is None:
            notes.append(f"{SOURCE_LABELS[provider]} volume unused: fewer than 3 complete synced weeks")
        else:
            ...the chronic-cap block stays exactly as it is...
```

and in the `elif measured:` branch, change `"coros"` to `freshest[0]`:

```python
    elif measured:
        km, vert, as_of, km_src = measured[0], measured[1], measured[2].isoformat(), freshest[0]
```

Leave the threshold-pace `"coros"` source and the readiness line unchanged: assessments and daily metrics are still COROS-only in A.

- [ ] **Step 4: plan_generator.** At `backend/services/plan_generator.py:850` change:

```python
                measured_weekly_km=snap.weekly_km if snap and snap.weekly_km_source == "coros" else None,
```

to

```python
                measured_weekly_km=snap.weekly_km
                if snap and snap.weekly_km_source in fitness_snapshot.DEVICE_PROVIDERS
                else None,
```

and add `fitness_snapshot` to the inline `from services import plan_signals` line just above, so it reads `from services import fitness_snapshot, plan_signals`.

- [ ] **Step 5: Run the backend unit suite.**

Run: `cd backend && pytest tests/unit -q -x 2>&1 | tail -15`
Expected: all PASS. Any other test that monkeypatched `fs.PROVIDER` must be updated to `DEVICE_PROVIDERS`; check with `grep -rn "fitness_snapshot.PROVIDER\|fs.PROVIDER" backend`.

- [ ] **Step 6: Golden eval.** This changes a value inside the plan prompt for Apple Health athletes only. Confirm COROS/self-reported athletes are unchanged:

Run: `cd backend && python scripts/golden_eval.py compare --service scheduler`
Expected: no regression versus the stored baseline. Paste the summary into the PR. If the baseline is missing, run `capture` on `main` first (`git stash`-free: check out `main` in a scratch worktree), then `compare` here. Prompt *templates* are untouched, so there's no Langfuse prompt version to bump.

- [ ] **Step 7: Commit.**

```bash
git add backend/services/fitness_snapshot.py backend/services/plan_generator.py backend/tests/unit/test_fitness_snapshot.py
git commit -m "feat(fitness): measured volume from any device provider, freshest first"
```

### Task 4: iOS DTOs, API client and workout mapper

**Files:**
- Create: `ios-native/UphillAI/Core/Health/AppleHealthModels.swift`
- Create: `ios-native/UphillAI/Core/Health/AppleHealthAPI.swift`
- Create: `ios-native/UphillAI/Core/Health/HealthWorkoutMapper.swift`
- Modify: `ios-native/UphillAI/Core/Integrations/DeviceConnectionModels.swift`
- Modify: `ios-native/scripts/record_fixtures.sh`
- Create (recorded): `ios-native/UphillAITests/Fixtures/apple_health_sync.json`, `integrations_status.json`
- Create: `ios-native/UphillAITests/Health/AppleHealthModelsTests.swift`, `HealthWorkoutMapperTests.swift`

**Interfaces:**
- Consumes: the Task 2 endpoints (running locally).
- Produces:

```swift
struct AppleHealthWorkoutUpload: Codable, Sendable, Equatable {
    let externalId: String; let activityType: String
    let startTime: String; let endTime: String          // ISO 8601 with offset
    let durationSeconds: Double
    let distanceKm: Double?; let elevationGainM: Double?
    let avgHr: Int?; let maxHr: Int?; let calories: Int?
    let sourceName: String?
}
struct AppleHealthSyncBody: Encodable, Sendable { let workouts: [AppleHealthWorkoutUpload]; let deletedIds: [String]; let planId: Int?; let tzOffsetMinutes: Int }
struct AppleHealthSyncResult: Decodable, Sendable, Equatable { let accepted: Int; let rejected: [Rejected]; let deleted: Int }
struct AppleHealthConnectionStatus: Codable, Sendable, Equatable { let enabled: Bool; let connected: Bool; let lastSyncAt: String? }
protocol AppleHealthUploading: Sendable { func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult; func disconnect() async throws }
struct AppleHealthAPI: AppleHealthUploading   // init(client: APIClient)
struct HealthWorkoutSample: Sendable, Equatable   // see code
enum HealthWorkoutMapper { static func upload(for: HealthWorkoutSample, timeZone: TimeZone = .current) -> AppleHealthWorkoutUpload?; static func climb(altitudes: [Double], threshold: Double = 3) -> Double }
// DeviceConnectionStatus gains: let appleHealth: AppleHealthConnectionStatus?
```

- [ ] **Step 1: Record the fixtures.** Start the local backend (`docker compose up -d --build` from the repo root, or `uvicorn main:app --port 8000` in `backend/`). In `ios-native/scripts/record_fixtures.sh`, find the main (no-argument) section where `TOKEN=` is set for the fixtures user, the block that records `active_plan.json`. Directly after it, add:

```bash
# Apple Health: one plausible workout and one with end before start (lands in "rejected").
curl -sf -X POST "$BASE/api/integrations/apple-health/sync" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"workouts":[{"external_id":"6F1C2E9A-0000-4000-8000-000000000001","activity_type":"outdoor_run","start_time":"2026-10-12T06:00:00+07:00","end_time":"2026-10-12T07:02:00+07:00","duration_seconds":3720,"distance_km":10.4,"elevation_gain_m":412,"avg_hr":148,"max_hr":171,"calories":690,"source_name":"Apple Watch"},{"external_id":"6F1C2E9A-0000-4000-8000-000000000002","activity_type":"outdoor_run","start_time":"2026-10-12T08:00:00+07:00","end_time":"2026-10-12T07:00:00+07:00","duration_seconds":60}],"deleted_ids":[]}' \
  | scrub > "$OUT/apple_health_sync.json"
curl -sf "$BASE/api/integrations/status" -H "Authorization: Bearer $TOKEN" | scrub > "$OUT/integrations_status.json"
```

Run: `ios-native/scripts/record_fixtures.sh`. Check: `apple_health_sync.json` has `"accepted": 1` and one rejected row; `integrations_status.json` has an `apple_health` object with `"connected": true`. Don't hand-edit either file.

- [ ] **Step 2: Write the failing tests.** Create `ios-native/UphillAITests/Health/AppleHealthModelsTests.swift`:

```swift
import Foundation
import Testing
@testable import UphillAI

struct AppleHealthModelsTests {
    @Test func decodesSyncResult() throws {
        let result = try Fixture.decode(AppleHealthSyncResult.self, "apple_health_sync.json")
        #expect(result.accepted == 1)
        #expect(result.rejected.map(\.externalId) == ["6F1C2E9A-0000-4000-8000-000000000002"])
    }

    @Test func decodesStatusWithAppleHealth() throws {
        let status = try Fixture.decode(DeviceConnectionStatus.self, "integrations_status.json")
        #expect(status.appleHealth?.enabled == true)
        #expect(status.appleHealth?.connected == true)
    }

    @Test func statusWithoutAppleHealthStillDecodes() throws {
        let status = try JSONCoding.decoder.decode(DeviceConnectionStatus.self, from: Data(#"{"coros":{"connected":false}}"#.utf8))
        #expect(status.appleHealth == nil)
    }

    @Test func uploadEncodesSnakeCaseAndOmitsNils() throws {
        let body = AppleHealthSyncBody(
            workouts: [AppleHealthWorkoutUpload(externalId: "A", activityType: "strength", startTime: "2026-10-12T06:00:00+07:00",
                                                endTime: "2026-10-12T06:40:00+07:00", durationSeconds: 2400, distanceKm: nil,
                                                elevationGainM: nil, avgHr: 120, maxHr: nil, calories: nil, sourceName: "Apple Watch")],
            deletedIds: ["B"], planId: nil, tzOffsetMinutes: 420)
        let json = try #require(String(data: JSONCoding.encoder.encode(body), encoding: .utf8))
        #expect(json.contains(#""external_id":"A""#))
        #expect(json.contains(#""deleted_ids":["B"]"#))
        #expect(json.contains(#""tz_offset_minutes":420"#))
        #expect(!json.contains("distance_km"))
        #expect(!json.contains("plan_id"))
    }
}
```

Create `ios-native/UphillAITests/Health/HealthWorkoutMapperTests.swift`:

```swift
import Foundation
import Testing
@testable import UphillAI

struct HealthWorkoutMapperTests {
    private let saigon = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
    private let start = Date(timeIntervalSince1970: 1_791_759_600) // 2026-10-12T06:00:00+07:00

    private func sample(_ kind: HealthWorkoutSample.Kind, indoor: Bool = false, distance: Double? = 10_400,
                        ascended: Double? = nil, altitudes: [Double]? = nil) -> HealthWorkoutSample {
        HealthWorkoutSample(uuid: UUID(uuidString: "6F1C2E9A-0000-4000-8000-000000000001")!, kind: kind, isIndoor: indoor,
                            start: start, end: start.addingTimeInterval(3720), duration: 3720,
                            distanceMeters: distance, elevationAscendedMeters: ascended, routeAltitudes: altitudes,
                            averageHeartRate: 147.6, maxHeartRate: 171.2, activeEnergyKcal: 689.7, sourceName: "Apple Watch")
    }

    @Test(arguments: [
        (HealthWorkoutSample.Kind.running, false, "outdoor_run"),
        (.running, true, "indoor_run"),
        (.hiking, false, "hike"),
        (.stairs, false, "hike"),
        (.strength, false, "strength"),
    ])
    func mapsKinds(kind: HealthWorkoutSample.Kind, indoor: Bool, expected: String) {
        #expect(HealthWorkoutMapper.upload(for: sample(kind, indoor: indoor), timeZone: saigon)?.activityType == expected)
    }

    @Test func otherKindsAreSkipped() {
        #expect(HealthWorkoutMapper.upload(for: sample(.other)) == nil)
    }

    @Test func convertsUnitsAndFormatsTimesWithOffset() throws {
        let upload = try #require(HealthWorkoutMapper.upload(for: sample(.running, ascended: 412.4), timeZone: saigon))
        #expect(upload.externalId == "6F1C2E9A-0000-4000-8000-000000000001")
        #expect(upload.startTime == "2026-10-12T06:00:00+07:00")
        #expect(upload.endTime == "2026-10-12T07:02:00+07:00")
        #expect(upload.distanceKm == 10.4)
        #expect(upload.elevationGainM == 412.4)
        #expect(upload.avgHr == 148 && upload.maxHr == 171 && upload.calories == 690)
        #expect(upload.sourceName == "Apple Watch")
    }

    @Test func metadataClimbBeatsRoute() {
        let upload = HealthWorkoutMapper.upload(for: sample(.running, ascended: 300, altitudes: [0, 50, 100]), timeZone: saigon)
        #expect(upload?.elevationGainM == 300)
    }

    @Test func routeClimbIsTheFallback() {
        let upload = HealthWorkoutMapper.upload(for: sample(.hiking, altitudes: [100, 120, 110, 160]), timeZone: saigon)
        #expect(upload?.elevationGainM == 70)
    }

    @Test func noClimbDataLeavesItNil() {
        #expect(HealthWorkoutMapper.upload(for: sample(.running), timeZone: saigon)?.elevationGainM == nil)
    }

    @Test func climbFollowsRealClimbs() {
        #expect(HealthWorkoutMapper.climb(altitudes: [0, 10, 20]) == 20)
        #expect(HealthWorkoutMapper.climb(altitudes: [100, 101, 102, 101, 103, 106, 104, 110]) == 10)
    }

    @Test func noisyAltitudesDoNotInflateClimb() {
        #expect(HealthWorkoutMapper.climb(altitudes: [100, 101, 100, 101, 100, 102, 100]) == 0)
        #expect(HealthWorkoutMapper.climb(altitudes: []) == 0)
    }

    @Test func strengthWithoutDistanceHasNilDistance() {
        #expect(HealthWorkoutMapper.upload(for: sample(.strength, distance: nil), timeZone: saigon)?.distanceKm == nil)
    }
}
```

- [ ] **Step 3: Implement the models.** `ios-native/UphillAI/Core/Health/AppleHealthModels.swift`:

```swift
import Foundation

/// One workout summary for POST /api/integrations/apple-health/sync. Routes and HR series
/// never leave the phone; these fields are all the backend gets.
struct AppleHealthWorkoutUpload: Codable, Sendable, Equatable {
    let externalId: String
    let activityType: String
    let startTime: String
    let endTime: String
    let durationSeconds: Double
    let distanceKm: Double?
    let elevationGainM: Double?
    let avgHr: Int?
    let maxHr: Int?
    let calories: Int?
    let sourceName: String?
}

struct AppleHealthSyncBody: Encodable, Sendable {
    let workouts: [AppleHealthWorkoutUpload]
    let deletedIds: [String]
    let planId: Int?
    let tzOffsetMinutes: Int
}

struct AppleHealthSyncResult: Decodable, Sendable, Equatable {
    struct Rejected: Decodable, Sendable, Equatable {
        let externalId: String
        let reason: String
    }

    let accepted: Int
    let rejected: [Rejected]
    let deleted: Int
}

public struct AppleHealthConnectionStatus: Codable, Sendable, Equatable {
    public let enabled: Bool
    public let connected: Bool
    public let lastSyncAt: String?
}
```

In `DeviceConnectionModels.swift`, change `DeviceConnectionStatus` to:

```swift
public struct DeviceConnectionStatus: Codable, Sendable, Equatable {
    public let coros: CorosConnectionStatus?
    /// Absent on backends older than the Apple Health release.
    public let appleHealth: AppleHealthConnectionStatus?

    public init(coros: CorosConnectionStatus? = nil, appleHealth: AppleHealthConnectionStatus? = nil) {
        self.coros = coros
        self.appleHealth = appleHealth
    }

    public var isCorosConnected: Bool {
        coros?.connected ?? false
    }
}
```

- [ ] **Step 4: Implement the API.** `ios-native/UphillAI/Core/Health/AppleHealthAPI.swift`:

```swift
import Foundation

protocol AppleHealthUploading: Sendable {
    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult
    func disconnect() async throws
}

struct AppleHealthAPI: AppleHealthUploading {
    let client: APIClient

    private struct EmptyResponse: Decodable {}

    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult {
        try await client.send(.send(.post, "/api/integrations/apple-health/sync", body: body))
    }

    /// Deletes everything Uphill received from Apple Health. HealthKit permission itself
    /// can only be revoked by the athlete in Settings.
    func disconnect() async throws {
        let _: EmptyResponse = try await client.send(.delete("/api/integrations/apple-health"))
    }
}
```

- [ ] **Step 5: Implement the mapper.** `ios-native/UphillAI/Core/Health/HealthWorkoutMapper.swift`:

```swift
import Foundation

/// What HealthKitStore reads from one HKWorkout, as plain values so the mapping is testable
/// without HealthKit. `routeAltitudes` is read only when the workout has no climb metadata.
struct HealthWorkoutSample: Sendable, Equatable {
    enum Kind: Sendable, Equatable { case running, hiking, stairs, strength, other }

    let uuid: UUID
    let kind: Kind
    let isIndoor: Bool
    let start: Date
    let end: Date
    let duration: TimeInterval
    let distanceMeters: Double?
    let elevationAscendedMeters: Double?
    let routeAltitudes: [Double]?
    let averageHeartRate: Double?
    let maxHeartRate: Double?
    let activeEnergyKcal: Double?
    let sourceName: String
}

enum HealthWorkoutMapper {
    /// nil for kinds Uphill doesn't import.
    static func upload(for s: HealthWorkoutSample, timeZone: TimeZone = .current) -> AppleHealthWorkoutUpload? {
        let type: String
        switch s.kind {
        case .running: type = s.isIndoor ? "indoor_run" : "outdoor_run"
        // COROS files hikes as "hike" too; volume counts it on foot and matching scores it as endurance.
        case .hiking, .stairs: type = "hike"
        case .strength: type = "strength"
        case .other: return nil
        }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        formatter.timeZone = timeZone
        let climb = s.elevationAscendedMeters ?? s.routeAltitudes.map { climb(altitudes: $0) }
        return AppleHealthWorkoutUpload(
            externalId: s.uuid.uuidString,
            activityType: type,
            startTime: formatter.string(from: s.start),
            endTime: formatter.string(from: s.end),
            durationSeconds: s.duration.rounded(),
            distanceKm: s.distanceMeters.map { ($0 / 1000 * 1000).rounded() / 1000 },
            elevationGainM: climb.map { ($0 * 10).rounded() / 10 },
            avgHr: s.averageHeartRate.map { Int($0.rounded()) },
            maxHr: s.maxHeartRate.map { Int($0.rounded()) },
            calories: s.activeEnergyKcal.map { Int($0.rounded()) },
            sourceName: s.sourceName
        )
    }

    /// Metres climbed, counting a rise only once it clears `threshold` above the last
    /// low point, so GPS altitude jitter doesn't add up to fake vert.
    static func climb(altitudes: [Double], threshold: Double = 3) -> Double {
        guard var reference = altitudes.first else { return 0 }
        var gain = 0.0
        for altitude in altitudes.dropFirst() {
            if altitude - reference >= threshold {
                gain += altitude - reference
                reference = altitude
            } else if reference - altitude >= threshold {
                reference = altitude
            }
        }
        return gain
    }
}
```

The distance rounding expression keeps 3 decimals, so 10_400 m becomes 10.4.

- [ ] **Step 6: Run the tests.** Run: `ios-native/scripts/test.sh 2>&1 | tail -40`. Expected: "Tests passed". If `routeClimbIsTheFallback` disagrees: [100,120,110,160] gives 20, then the 110 dip of 10 resets the reference, then +50, so 70. Fix the code, not the test.

- [ ] **Step 7: Commit.**

```bash
git add ios-native/UphillAI/Core/Health ios-native/UphillAI/Core/Integrations/DeviceConnectionModels.swift ios-native/scripts/record_fixtures.sh ios-native/UphillAITests/Fixtures/apple_health_sync.json ios-native/UphillAITests/Fixtures/integrations_status.json ios-native/UphillAITests/Health
git commit -m "feat(ios): Apple Health DTOs, API client and workout mapper"
```

### Task 5: Sync service (anchored, batched, anchor saved only on success)

**Files:**
- Create: `ios-native/UphillAI/Core/Health/HealthStoring.swift`
- Create: `ios-native/UphillAI/Core/Health/AppleHealthSyncService.swift`
- Create: `ios-native/UphillAITests/Health/AppleHealthSyncServiceTests.swift`

**Interfaces:**
- Consumes: `HealthWorkoutSample`, `HealthWorkoutMapper`, `AppleHealthUploading`, `AppleHealthSyncBody`, `AppleHealthSyncResult` (Task 4).
- Produces:

```swift
struct HealthWorkoutPage: Sendable { let samples: [HealthWorkoutSample]; let deleted: [UUID]; let anchor: Data? }
protocol HealthStoring: Sendable {
    var isAvailable: Bool { get }
    func requestAuthorization() async throws
    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws
    func stopObserving() async
}
protocol HealthAnchorStoring: Sendable {
    func anchor(for userId: Int) -> Data?
    func setAnchor(_ anchor: Data?, for userId: Int)
    var observingUserId: Int? { get }
    func setObservingUserId(_ id: Int?)
}
final class UserDefaultsAnchorStore: HealthAnchorStoring   // init(defaults: UserDefaults = .standard)
struct SampleHealthStore: HealthStoring                    // debug data, used in Task 6/7
struct AppleHealthSyncOutcome: Sendable, Equatable { let accepted: Int; let rejected: Int; let deleted: Int; let nothingFound: Bool }
enum AppleHealthSyncError: Error, Equatable { case notObserving, unavailable }
actor AppleHealthSyncService {
    init(store: any HealthStoring, api: any AppleHealthUploading, anchors: any HealthAnchorStoring,
         planId: @escaping @Sendable () async -> Int?, now: @escaping @Sendable () -> Date = { .now }, timeZone: TimeZone = .current)
    static let backfill: TimeInterval   // 12 weeks
    static let batchSize: Int           // 500
    var isAvailable: Bool { get }
    func isObserving(userId: Int) -> Bool
    func connect(userId: Int) async throws -> AppleHealthSyncOutcome   // authorize, observe, first sync
    func sync() async throws -> AppleHealthSyncOutcome                 // coalesces concurrent calls
    func resumeObservingIfNeeded() async                               // app launch
    func stopObserving(userId: Int) async                              // disconnect
    func stopObservingForSignOut() async                               // sign-out: whoever connected on this phone
}
```

- [ ] **Step 1: Write the failing tests.** `ios-native/UphillAITests/Health/AppleHealthSyncServiceTests.swift`:

```swift
import Foundation
import Synchronization
import Testing
@testable import UphillAI

final class FakeHealthStore: HealthStoring {
    let pages = Mutex<[HealthWorkoutPage]>([])
    let requestedSince = Mutex<[Date]>([])
    let requestedAnchors = Mutex<[Data?]>([])
    let observing = Mutex(false)
    let authorizeError = Mutex<Error?>(nil)
    var isAvailable: Bool { true }

    func requestAuthorization() async throws { if let e = authorizeError.withLock({ $0 }) { throw e } }
    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        requestedAnchors.withLock { $0.append(anchor) }
        requestedSince.withLock { $0.append(start) }
        return pages.withLock { $0.isEmpty ? HealthWorkoutPage(samples: [], deleted: [], anchor: anchor) : $0.removeFirst() }
    }
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws { observing.withLock { $0 = true } }
    func stopObserving() async { observing.withLock { $0 = false } }
}

final class FakeUploader: AppleHealthUploading {
    let bodies = Mutex<[AppleHealthSyncBody]>([])
    /// Index of the call (0-based) that throws, if any.
    let failOnCall = Mutex<Int?>(nil)
    let disconnects = Mutex(0)
    /// Runs inside each upload, e.g. to sign the athlete out mid-sync.
    let onSync = Mutex<(@Sendable () -> Void)?>(nil)

    func sync(_ body: AppleHealthSyncBody) async throws -> AppleHealthSyncResult {
        let index = bodies.withLock { $0.append(body); return $0.count - 1 }
        onSync.withLock { $0 }?()
        if failOnCall.withLock({ $0 }) == index { throw APIError.server(status: 503, message: "down") }
        return AppleHealthSyncResult(accepted: body.workouts.count, rejected: [], deleted: body.deletedIds.count)
    }
    func disconnect() async throws { disconnects.withLock { $0 += 1 } }
}

final class MemoryAnchorStore: HealthAnchorStoring {
    let anchors = Mutex<[Int: Data]>([:])
    let observer = Mutex<Int?>(nil)
    func anchor(for userId: Int) -> Data? { anchors.withLock { $0[userId] } }
    func setAnchor(_ anchor: Data?, for userId: Int) { anchors.withLock { $0[userId] = anchor } }
    var observingUserId: Int? { observer.withLock { $0 } }
    func setObservingUserId(_ id: Int?) { observer.withLock { $0 = id } }
}

private func run(_ n: Int) -> HealthWorkoutSample {
    let start = Date(timeIntervalSince1970: 1_791_759_600 + Double(n) * 86_400)
    return HealthWorkoutSample(uuid: UUID(), kind: .running, isIndoor: false, start: start, end: start.addingTimeInterval(3600),
                               duration: 3600, distanceMeters: 10_000, elevationAscendedMeters: 100, routeAltitudes: nil,
                               averageHeartRate: 140, maxHeartRate: 160, activeEnergyKcal: 600, sourceName: "Apple Watch")
}

struct AppleHealthSyncServiceTests {
    let store = FakeHealthStore()
    let api = FakeUploader()
    let anchors = MemoryAnchorStore()
    let now = Date(timeIntervalSince1970: 1_792_000_000)

    func service() -> AppleHealthSyncService {
        AppleHealthSyncService(store: store, api: api, anchors: anchors, planId: { 42 }, now: { [now] in now },
                               timeZone: TimeZone(identifier: "UTC")!)
    }

    @Test func connectAuthorizesObservesAndBackfillsTwelveWeeks() async throws {
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([1]))] }
        let outcome = try await service().connect(userId: 7)
        #expect(outcome == AppleHealthSyncOutcome(accepted: 1, rejected: 0, deleted: 0, nothingFound: false))
        #expect(store.observing.withLock { $0 })
        #expect(anchors.observingUserId == 7)
        #expect(store.requestedSince.withLock { $0 } == [now.addingTimeInterval(-12 * 7 * 86_400)])
        #expect(anchors.anchor(for: 7) == Data([1]))
        #expect(api.bodies.withLock { $0.first?.planId } == 42)
    }

    @Test func firstSyncWithNothingSaysSo() async throws {
        let outcome = try await service().connect(userId: 7)
        #expect(outcome.nothingFound)
    }

    @Test func emptyIncrementalSyncStillCallsTheServer() async throws {
        anchors.setObservingUserId(7)
        anchors.setAnchor(Data([9]), for: 7)
        let outcome = try await service().sync()
        #expect(!outcome.nothingFound)
        #expect(api.bodies.withLock { $0.count } == 1)
        #expect(store.requestedAnchors.withLock { $0 } == [Data([9])])
    }

    @Test func splitsIntoBatchesOf500() async throws {
        anchors.setObservingUserId(7)
        let samples = (0..<1001).map(run)
        let deleted = (0..<3).map { _ in UUID() }
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: samples, deleted: deleted, anchor: Data([2]))] }
        let outcome = try await service().sync()
        let sizes = api.bodies.withLock { $0.map(\.workouts.count) }
        #expect(sizes == [500, 500, 1])
        #expect(api.bodies.withLock { $0.flatMap(\.deletedIds).count } == 3)
        #expect(outcome.accepted == 1001 && outcome.deleted == 3)
    }

    @Test func failedSecondBatchKeepsOldAnchor() async throws {
        anchors.setObservingUserId(7)
        anchors.setAnchor(Data([1]), for: 7)
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: (0..<600).map(run), deleted: [], anchor: Data([2]))] }
        api.failOnCall.withLock { $0 = 1 }
        await #expect(throws: APIError.self) { try await service().sync() }
        #expect(anchors.anchor(for: 7) == Data([1]))
    }

    @Test func syncWithoutObservingThrows() async {
        await #expect(throws: AppleHealthSyncError.notObserving) { try await service().sync() }
    }

    @Test func test_sync_does_not_save_anchor_when_user_changed() async throws {
        anchors.setObservingUserId(7)
        let svc = service()
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [run(1)], deleted: [], anchor: Data([3]))] }
        // Sign-out lands while the upload is in flight.
        let anchors = self.anchors
        api.onSync.withLock { $0 = { anchors.setObservingUserId(nil) } }
        await #expect(throws: AppleHealthSyncError.notObserving) { try await svc.sync() }
        #expect(anchors.anchor(for: 7) == nil)
    }

    @Test func signOutStopsObservingWhoeverConnected() async throws {
        let svc = service()
        _ = try await svc.connect(userId: 7)
        await svc.stopObservingForSignOut()
        #expect(anchors.observingUserId == nil && anchors.anchor(for: 7) == nil)
    }

    @Test func test_stop_observing_clears_anchor() async throws {
        let svc = service()
        _ = try await svc.connect(userId: 7)
        await svc.stopObserving(userId: 7)
        #expect(anchors.observingUserId == nil)
        #expect(anchors.anchor(for: 7) == nil)
        #expect(!store.observing.withLock { $0 })
    }

    @Test func concurrentSyncsShareOneRun() async throws {
        anchors.setObservingUserId(7)
        let svc = service()
        async let a = svc.sync()
        async let b = svc.sync()
        _ = try await (a, b)
        #expect(api.bodies.withLock { $0.count } <= 2)
        #expect(store.requestedAnchors.withLock { $0.count } == api.bodies.withLock { $0.count })
    }

    @Test func otherKindsAreDroppedBeforeUpload() async throws {
        anchors.setObservingUserId(7)
        var other = run(1)
        other = HealthWorkoutSample(uuid: other.uuid, kind: .other, isIndoor: false, start: other.start, end: other.end,
                                    duration: other.duration, distanceMeters: nil, elevationAscendedMeters: nil, routeAltitudes: nil,
                                    averageHeartRate: nil, maxHeartRate: nil, activeEnergyKcal: nil, sourceName: "Yoga App")
        store.pages.withLock { $0 = [HealthWorkoutPage(samples: [other, run(2)], deleted: [], anchor: Data([4]))] }
        _ = try await service().sync()
        #expect(api.bodies.withLock { $0.first?.workouts.count } == 1)
    }
}
```

Check the `APIError` case used by `FakeUploader`: open `ios-native/UphillAI/Core/Networking/APIError.swift` and use whichever existing case carries a 5xx (adapt `.server(status:message:)` to its real name).

- [ ] **Step 2: Run and confirm they fail** (compile errors: unknown types). Run: `ios-native/scripts/test.sh 2>&1 | tail -40`.

- [ ] **Step 3: Implement `HealthStoring.swift`.**

```swift
import Foundation

struct HealthWorkoutPage: Sendable {
    let samples: [HealthWorkoutSample]
    let deleted: [UUID]
    /// Archived HKQueryAnchor to resume from next time.
    let anchor: Data?
}

/// The HealthKit surface the sync needs, so tests and the debug sample data can stand in for it.
protocol HealthStoring: Sendable {
    var isAvailable: Bool { get }
    func requestAuthorization() async throws
    /// Workouts added or deleted since `anchor`; with no anchor, those starting after `start`.
    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage
    /// Registers background delivery; `onUpdate` runs when a workout is saved to Health.
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws
    func stopObserving() async
}

protocol HealthAnchorStoring: Sendable {
    func anchor(for userId: Int) -> Data?
    func setAnchor(_ anchor: Data?, for userId: Int)
    /// The athlete who connected Apple Health on this phone. Background wakes can come
    /// before the session is restored, so the sync identifies the athlete from this.
    var observingUserId: Int? { get }
    func setObservingUserId(_ id: Int?)
}

/// UserDefaults is thread-safe; the class only holds it.
final class UserDefaultsAnchorStore: HealthAnchorStoring, @unchecked Sendable {
    private let defaults: UserDefaults
    private static let observingKey = "UPHILL_HEALTH_OBSERVING_USER"

    init(defaults: UserDefaults = .standard) { self.defaults = defaults }

    func anchor(for userId: Int) -> Data? { defaults.data(forKey: "UPHILL_HEALTH_ANCHOR_\(userId)") }
    func setAnchor(_ anchor: Data?, for userId: Int) { defaults.set(anchor, forKey: "UPHILL_HEALTH_ANCHOR_\(userId)") }
    var observingUserId: Int? { defaults.object(forKey: Self.observingKey) as? Int }
    func setObservingUserId(_ id: Int?) { defaults.set(id, forKey: Self.observingKey) }
}

/// Debug-only stand-in for HealthKit (Developer menu → Sample Health data): three workouts
/// from this week on the first sync, nothing after.
struct SampleHealthStore: HealthStoring {
    static let defaultsKey = "UPHILL_SAMPLE_HEALTH"
    var isAvailable: Bool { true }

    func requestAuthorization() async throws {}
    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws {}
    func stopObserving() async {}

    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        guard anchor == nil else { return HealthWorkoutPage(samples: [], deleted: [], anchor: anchor) }
        let day: TimeInterval = 86_400
        let base = Calendar.current.startOfDay(for: .now).addingTimeInterval(6 * 3600)
        func sample(_ id: String, _ kind: HealthWorkoutSample.Kind, daysAgo: Double, minutes: Double, meters: Double?, climb: Double?) -> HealthWorkoutSample {
            let s = base.addingTimeInterval(-daysAgo * day)
            return HealthWorkoutSample(uuid: UUID(uuidString: id)!, kind: kind, isIndoor: false, start: s,
                                       end: s.addingTimeInterval(minutes * 60), duration: minutes * 60, distanceMeters: meters,
                                       elevationAscendedMeters: climb, routeAltitudes: nil, averageHeartRate: 142,
                                       maxHeartRate: 168, activeEnergyKcal: minutes * 10, sourceName: "Apple Watch")
        }
        return HealthWorkoutPage(samples: [
            sample("5A3E0000-0000-4000-8000-000000000001", .running, daysAgo: 1, minutes: 62, meters: 10_400, climb: 412),
            sample("5A3E0000-0000-4000-8000-000000000002", .hiking, daysAgo: 2, minutes: 95, meters: 7_200, climb: 680),
            sample("5A3E0000-0000-4000-8000-000000000003", .strength, daysAgo: 3, minutes: 40, meters: nil, climb: nil),
        ], deleted: [], anchor: Data("sample".utf8))
    }
}
```

- [ ] **Step 4: Implement `AppleHealthSyncService.swift`.**

```swift
import Foundation

struct AppleHealthSyncOutcome: Sendable, Equatable {
    let accepted: Int
    let rejected: Int
    let deleted: Int
    /// The first sync found no workouts in 12 weeks. HealthKit never reports a denied
    /// read, so this is the only sign the athlete may have turned access off.
    let nothingFound: Bool
}

enum AppleHealthSyncError: Error, Equatable {
    case notObserving
    case unavailable
}

/// Reads new and deleted workouts from Apple Health and sends them to Uphill. The anchor
/// moves only after every batch was accepted, so a failed upload is retried, never lost.
actor AppleHealthSyncService {
    static let backfill: TimeInterval = 12 * 7 * 86_400
    static let batchSize = 500

    private let store: any HealthStoring
    private let api: any AppleHealthUploading
    private let anchors: any HealthAnchorStoring
    private let planId: @Sendable () async -> Int?
    private let now: @Sendable () -> Date
    private let timeZone: TimeZone
    private var running: Task<AppleHealthSyncOutcome, Error>?

    init(store: any HealthStoring, api: any AppleHealthUploading, anchors: any HealthAnchorStoring,
         planId: @escaping @Sendable () async -> Int?, now: @escaping @Sendable () -> Date = { .now },
         timeZone: TimeZone = .current) {
        self.store = store
        self.api = api
        self.anchors = anchors
        self.planId = planId
        self.now = now
        self.timeZone = timeZone
    }

    var isAvailable: Bool { store.isAvailable }

    func isObserving(userId: Int) -> Bool { anchors.observingUserId == userId }

    func connect(userId: Int) async throws -> AppleHealthSyncOutcome {
        guard store.isAvailable else { throw AppleHealthSyncError.unavailable }
        try await store.requestAuthorization()
        if anchors.observingUserId != userId { anchors.setAnchor(nil, for: userId) }
        anchors.setObservingUserId(userId)
        try await startObserving()
        return try await sync()
    }

    func resumeObservingIfNeeded() async {
        guard anchors.observingUserId != nil else { return }
        try? await startObserving()
    }

    func stopObserving(userId: Int) async {
        await store.stopObserving()
        anchors.setAnchor(nil, for: userId)
        if anchors.observingUserId == userId { anchors.setObservingUserId(nil) }
    }

    /// Sign-out runs after the session's user is gone, so it uses whoever connected on this phone.
    func stopObservingForSignOut() async {
        guard let id = anchors.observingUserId else { return }
        await stopObserving(userId: id)
    }

    /// A second call while one runs waits for the first instead of uploading twice.
    func sync() async throws -> AppleHealthSyncOutcome {
        if let running { return try await running.value }
        let task = Task { try await self.performSync() }
        running = task
        defer { running = nil }
        return try await task.value
    }

    private func startObserving() async throws {
        try await store.startObserving { [weak self] in
            _ = try? await self?.sync()
        }
    }

    private func performSync() async throws -> AppleHealthSyncOutcome {
        guard let userId = anchors.observingUserId else { throw AppleHealthSyncError.notObserving }
        let previous = anchors.anchor(for: userId)
        let page = try await store.workouts(after: previous, since: now().addingTimeInterval(-Self.backfill))
        let uploads = page.samples.compactMap { HealthWorkoutMapper.upload(for: $0, timeZone: timeZone) }
        let deleted = page.deleted.map(\.uuidString)
        let plan = await planId()
        let offset = timeZone.secondsFromGMT(for: now()) / 60

        var accepted = 0, rejected = 0, removed = 0
        // At least one request, even when nothing changed: it advances last_sync_at, which
        // tells the fitness snapshot the recent weeks were covered.
        let batches = max(1, Int((Double(max(uploads.count, deleted.count)) / Double(Self.batchSize)).rounded(.up)))
        for i in 0..<batches {
            let range = { (count: Int) in min(i * Self.batchSize, count)..<min((i + 1) * Self.batchSize, count) }
            let body = AppleHealthSyncBody(workouts: Array(uploads[range(uploads.count)]),
                                           deletedIds: Array(deleted[range(deleted.count)]),
                                           planId: plan, tzOffsetMinutes: offset)
            let result = try await api.sync(body)
            accepted += result.accepted
            rejected += result.rejected.count
            removed += result.deleted
        }
        // Signed out or switched athlete while uploading: don't move anyone's anchor.
        guard anchors.observingUserId == userId else { throw AppleHealthSyncError.notObserving }
        anchors.setAnchor(page.anchor, for: userId)
        return AppleHealthSyncOutcome(accepted: accepted, rejected: rejected, deleted: removed,
                                      nothingFound: previous == nil && uploads.isEmpty)
    }
}
```

- [ ] **Step 5: Run the tests.** Run: `ios-native/scripts/test.sh 2>&1 | tail -40`. Expected: "Tests passed".

- [ ] **Step 6: Commit.**

```bash
git add ios-native/UphillAI/Core/Health ios-native/UphillAITests/Health
git commit -m "feat(ios): Apple Health sync service with anchored, batched uploads"
```

### Task 6: HealthKit store, capabilities and app wiring

**Files:**
- Create: `ios-native/UphillAI/Core/Health/HealthKitStore.swift`
- Modify: `ios-native/project.yml`, `ios-native/UphillAI/UphillAI.entitlements` (regenerated by XcodeGen from `project.yml`; commit both)
- Create: `ios-native/UphillAI/Resources/InfoPlist.xcstrings`
- Modify: `ios-native/UphillAI/App/AppModel.swift`, `ios-native/UphillAI/App/RootView.swift`
- Modify: `ios-native/UphillAI/Features/Plan/PlanViewModel.swift`, `ios-native/UphillAI/Features/Plan/PlanView.swift:201`
- Test: `ios-native/UphillAITests/App/AppModelTests.swift` (existing tests must still pass)

**Interfaces:**
- Consumes: `AppleHealthSyncService`, `HealthStoring`, `UserDefaultsAnchorStore`, `SampleHealthStore`, `AppleHealthAPI` (Tasks 4–5).
- Produces (on `AppModel`, all `@MainActor`):

```swift
let appleHealth: AppleHealthSyncService
var appleHealthEnabled: Bool            // from /status
var appleHealthConnected: Bool          // server says connected OR this phone observes
var appleHealthLastSync: String?        // ISO from /status
var appleHealthSyncing: Bool
var appleHealthMessage: String?         // nothing-found hint or error text
func loadAppleHealthStatus() async
func connectAppleHealth() async          // sets appleHealthMessage on failure
func syncAppleHealthIfDue(now: Date = .now) async   // 5-minute gate
func disconnectAppleHealth() async
// PlanViewModel:
func applyWatchMatches() async
```

- [ ] **Step 1: Capabilities.** In `ios-native/project.yml`, under `targets.UphillAI.info.properties` add:

```yaml
        NSHealthShareUsageDescription: "Uphill AI reads your runs, hikes and strength workouts so it can mark planned sessions done and start your plan from your real weekly mileage."
```

and under `targets.UphillAI.entitlements.properties`:

```yaml
        com.apple.developer.healthkit: true
        com.apple.developer.healthkit.access: []
        com.apple.developer.healthkit.background-delivery: true
```

Create `ios-native/UphillAI/Resources/InfoPlist.xcstrings` with the key `NSHealthShareUsageDescription`: the English text above plus a Vietnamese translation. Load the `uphill-ai-vietnamese-copy` skill and write the VI per its rules. Format:

```json
{
  "sourceLanguage" : "en",
  "strings" : {
    "NSHealthShareUsageDescription" : {
      "extractionState" : "manual",
      "localizations" : {
        "en" : { "stringUnit" : { "state" : "translated", "value" : "Uphill AI reads your runs, hikes and strength workouts so it can mark planned sessions done and start your plan from your real weekly mileage." } },
        "vi" : { "stringUnit" : { "state" : "translated", "value" : "<VI from the skill>" } }
      }
    }
  },
  "version" : "1.0"
}
```

Run `cd ios-native && xcodegen generate --quiet`, then check that `UphillAI/UphillAI.entitlements` now contains the three HealthKit keys.

- [ ] **Step 2: `HealthKitStore.swift`** (not unit-tested: it is HealthKit itself; verified on the Simulator in Task 8 and on a device in Task 9):

```swift
import CoreLocation
import Foundation
import HealthKit

/// HealthStoring over HKHealthStore. Read-only: Uphill never writes to Health.
final class HealthKitStore: HealthStoring, @unchecked Sendable {
    private let store = HKHealthStore()
    private var observer: HKObserverQuery?
    private let lock = NSLock()

    private static let activityTypes: [HKWorkoutActivityType] = [
        .running, .hiking, .stairClimbing, .stairs, .traditionalStrengthTraining, .functionalStrengthTraining,
    ]

    var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }

    func requestAuthorization() async throws {
        let read: Set<HKObjectType> = [
            .workoutType(), HKSeriesType.workoutRoute(),
            HKQuantityType(.heartRate), HKQuantityType(.distanceWalkingRunning), HKQuantityType(.activeEnergyBurned),
        ]
        try await store.requestAuthorization(toShare: [], read: read)
    }

    func workouts(after anchor: Data?, since start: Date) async throws -> HealthWorkoutPage {
        let types = NSCompoundPredicate(orPredicateWithSubpredicates: Self.activityTypes.map { HKQuery.predicateForWorkouts(with: $0) })
        let window = HKQuery.predicateForSamples(withStart: start, end: nil)
        let predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [types, window])
        let queryAnchor = anchor.flatMap { try? NSKeyedUnarchiver.unarchivedObject(ofClass: HKQueryAnchor.self, from: $0) }
        let descriptor = HKAnchoredObjectQueryDescriptor(predicates: [.workout(predicate)], anchor: queryAnchor)
        let result = try await descriptor.result(for: store)
        var samples: [HealthWorkoutSample] = []
        for workout in result.addedSamples {
            samples.append(await sample(from: workout))
        }
        let newAnchor = try NSKeyedArchiver.archivedData(withRootObject: result.newAnchor, requiringSecureCoding: true)
        return HealthWorkoutPage(samples: samples, deleted: result.deletedObjects.map(\.uuid), anchor: newAnchor)
    }

    func startObserving(onUpdate: @escaping @Sendable () async -> Void) async throws {
        await stopObserving()
        let query = HKObserverQuery(sampleType: .workoutType(), predicate: nil) { _, completion, error in
            // HealthKit's completion handler isn't Sendable; it is safe to call from any thread.
            nonisolated(unsafe) let done = completion
            guard error == nil else { done(); return }
            Task { await onUpdate(); done() }
        }
        lock.withLock { observer = query }
        store.execute(query)
        try await store.enableBackgroundDelivery(for: .workoutType(), frequency: .immediate)
    }

    func stopObserving() async {
        let current = lock.withLock { () -> HKObserverQuery? in defer { observer = nil }; return observer }
        if let current { store.stop(current) }
        try? await store.disableBackgroundDelivery(for: .workoutType())
    }

    private func sample(from workout: HKWorkout) async -> HealthWorkoutSample {
        let kind: HealthWorkoutSample.Kind = switch workout.workoutActivityType {
        case .running: .running
        case .hiking: .hiking
        case .stairClimbing, .stairs: .stairs
        case .traditionalStrengthTraining, .functionalStrengthTraining: .strength
        default: .other
        }
        let bpm = HKUnit.count().unitDivided(by: .minute())
        let hr = workout.statistics(for: HKQuantityType(.heartRate))
        let ascended = (workout.metadata?[HKMetadataKeyElevationAscended] as? HKQuantity)?.doubleValue(for: .meter())
        let altitudes = (ascended == nil && kind != .strength) ? try? await routeAltitudes(for: workout) : nil
        return HealthWorkoutSample(
            uuid: workout.uuid,
            kind: kind,
            isIndoor: workout.metadata?[HKMetadataKeyIndoorWorkout] as? Bool ?? false,
            start: workout.startDate,
            end: workout.endDate,
            duration: workout.duration,
            distanceMeters: workout.statistics(for: HKQuantityType(.distanceWalkingRunning))?.sumQuantity()?.doubleValue(for: .meter()),
            elevationAscendedMeters: ascended,
            routeAltitudes: altitudes ?? nil,
            averageHeartRate: hr?.averageQuantity()?.doubleValue(for: bpm),
            maxHeartRate: hr?.maximumQuantity()?.doubleValue(for: bpm),
            activeEnergyKcal: workout.statistics(for: HKQuantityType(.activeEnergyBurned))?.sumQuantity()?.doubleValue(for: .kilocalorie()),
            sourceName: workout.sourceRevision.source.name
        )
    }

    /// Altitudes along the workout's route, used only to compute climb on the phone.
    private func routeAltitudes(for workout: HKWorkout) async throws -> [Double]? {
        let routes = try await HKSampleQueryDescriptor(
            predicates: [.workoutRoute(HKQuery.predicateForObjects(from: workout))], sortDescriptors: []
        ).result(for: store)
        guard let route = routes.first else { return nil }
        var altitudes: [Double] = []
        for try await location in HKWorkoutRouteQueryDescriptor(route).results(for: store) where location.verticalAccuracy >= 0 {
            altitudes.append(location.altitude)
        }
        return altitudes.isEmpty ? nil : altitudes
    }
}
```

If the iOS 18 SDK rejects a name here (for example `HKWorkoutRouteQueryDescriptor(route)`'s label), look it up with the context7 MCP (`resolve-library-id` "HealthKit") and use the SDK's spelling. Record the adaptation in the PR.

- [ ] **Step 3: `PlanViewModel.applyWatchMatches()`.** In `PlanViewModel.swift`, replace the tail of `autoSyncWatch()` with a call to a new shared method:

```swift
    func autoSyncWatch() async {
        guard athleteId == nil, cachedAt == nil, !isSyncingWatch, let plan = snapshot?.plan else { return }
        isSyncingWatch = true
        defer { isSyncingWatch = false }
        guard (try? await service.syncWatch(planID: plan.id)) != nil else { return }
        await applyWatchMatches()
    }

    /// Reloads the plan and marks settled matches done. Shared by COROS and Apple Health syncs.
    func applyWatchMatches() async {
        guard athleteId == nil else { return }
        await load()
        let marked = await markMatchedWorkoutsDone()
        if marked > 0 {
            autoSyncSummary = marked == 1 ? L("1 run from your watch marked done") : L("%lld runs from your watch marked done", marked)
        }
    }
```

- [ ] **Step 4: AppModel wiring.** In `AppModel.swift`:

Add the stored property next to `deviceConnectionService`:

```swift
    let appleHealth: AppleHealthSyncService
```

Add state next to `corosConnected`:

```swift
    /// Apple Health, for Me → Connected accounts and onboarding's watch step.
    var appleHealthEnabled = false
    var appleHealthConnected = false
    var appleHealthLastSync: String?
    var appleHealthSyncing = false
    var appleHealthMessage: String?
    private var lastAppleHealthSync: Date?
```

In `loadCorosStatus()`, read Apple Health from the same response:

```swift
    func loadCorosStatus() async {
        guard let status = try? await deviceConnectionService.fetchStatus() else { return }
        corosConnected = status.isCorosConnected
        await applyAppleHealthStatus(status.appleHealth)
    }

    func loadAppleHealthStatus() async {
        if let status = try? await deviceConnectionService.fetchStatus() { await applyAppleHealthStatus(status.appleHealth) }
    }

    private func applyAppleHealthStatus(_ status: AppleHealthConnectionStatus?) async {
        appleHealthEnabled = (status?.enabled ?? false) && (await appleHealth.isAvailable)
        let observing = if let id = session.user?.id { await appleHealth.isObserving(userId: id) } else { false }
        appleHealthConnected = (status?.connected ?? false) || observing
        appleHealthLastSync = status?.lastSyncAt
    }
```

Add the actions:

```swift
    func connectAppleHealth() async {
        guard let userID = session.user?.id, !appleHealthSyncing else { return }
        appleHealthSyncing = true
        defer { appleHealthSyncing = false }
        do {
            let outcome = try await appleHealth.connect(userId: userID)
            appleHealthConnected = true
            lastAppleHealthSync = .now
            appleHealthMessage = outcome.nothingFound
                ? L("No workouts found. Check Settings → Health → Data Access & Devices → Uphill AI.")
                : nil
            await plan.applyWatchMatches()
            await loadAppleHealthStatus()
        } catch AppleHealthSyncError.unavailable {
            appleHealthMessage = L("Apple Health isn't available on this device.")
        } catch {
            // Connected locally; the next foreground or background wake retries the upload.
            appleHealthConnected = await appleHealth.isObserving(userId: userID)
            appleHealthMessage = L("Couldn't sync with Uphill. I'll try again next time you open the app.")
        }
    }

    /// App open / foreground: at most every 5 minutes, only for the athlete who connected on this phone.
    func syncAppleHealthIfDue(now: Date = .now) async {
        guard let userID = session.user?.id, actingAsAthlete == nil, !appleHealthSyncing,
              await appleHealth.isObserving(userId: userID) else { return }
        if let last = lastAppleHealthSync, now.timeIntervalSince(last) < 5 * 60 { return }
        lastAppleHealthSync = now
        appleHealthSyncing = true
        defer { appleHealthSyncing = false }
        guard let outcome = try? await appleHealth.sync() else { return }
        if outcome.accepted > 0 || outcome.deleted > 0 { await plan.applyWatchMatches() }
    }

    func disconnectAppleHealth() async {
        guard let userID = session.user?.id else { return }
        do {
            try await AppleHealthAPI(client: client).disconnect()
            await appleHealth.stopObserving(userId: userID)
            appleHealthConnected = false
            appleHealthLastSync = nil
            appleHealthMessage = nil
        } catch {
            appleHealthMessage = L("Couldn't disconnect. Check your connection and try again.")
        }
    }
```

In `init`, after `deviceConnectionService = DeviceConnectionService(client: client)` (before `plan` is assigned, so read the plan id lazily through a box set right after):

```swift
        let planIdBox = PlanIdBox()
        #if DEBUG
        let healthStore: any HealthStoring = UserDefaults.standard.bool(forKey: SampleHealthStore.defaultsKey)
            ? SampleHealthStore() : HealthKitStore()
        #else
        let healthStore: any HealthStoring = HealthKitStore()
        #endif
        let health = AppleHealthSyncService(store: healthStore, api: AppleHealthAPI(client: client),
                                            anchors: UserDefaultsAnchorStore(), planId: { await planIdBox.value() })
        appleHealth = health
```

After `plan = PlanViewModel(...)`:

```swift
        planIdBox.model = plan
```

and as the **last line of `init`** (after every stored property is set):

```swift
        // Background delivery must be registered on every launch, including background wakes.
        Task { await health.resumeObservingIfNeeded() }
```

and in `onSignedOut`, add:

```swift
            self?.lastAppleHealthSync = nil
            self?.appleHealthConnected = false
            self?.appleHealthLastSync = nil
            self?.appleHealthMessage = nil
            Task { [weak self] in await self?.appleHealth.stopObservingForSignOut() }
```

Add `PlanIdBox` at the bottom of `AppModel.swift`:

```swift
/// Lets the Apple Health sync read the active plan id without capturing AppModel before init ends.
@MainActor
final class PlanIdBox: Sendable {
    weak var model: PlanViewModel?
    nonisolated init() {}
    func value() -> Int? { model?.snapshot?.plan.id }
}
```

(`PlanIdBox` is `@MainActor`, so `await planIdBox.value()` hops to the main actor. If the compiler rejects `Sendable` with a `weak var`, drop `Sendable`: `@MainActor` classes are implicitly Sendable.)

Change `makeSetup`'s `loadWatchVolume` closure to return the whole `WatchVolume` for either device source (Task 7 consumes it):

```swift
                                       loadWatchVolume: { [client] in
                                           guard let snapshot = try? await client.send(Endpoint<WatchVolume>.get("/api/auth/fitness-snapshot")),
                                                 ["coros", "apple_health"].contains(snapshot.weeklyKmSource) else { return nil }
                                           return snapshot
                                       },
                                       connectAppleHealth: { [weak self] in
                                           await self?.connectAppleHealth()
                                           return self?.appleHealthMessage
                                       })
```

(This won't compile until Task 7 changes `PlanSetupViewModel`'s init. Do Task 7 Step 1–3 before building, or temporarily keep the old closure and switch it in Task 7.)

- [ ] **Step 5: RootView.** In `RootView.swift`, extend both foreground hooks:

```swift
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                Task {
                    await app.autoSyncWatchIfDue()
                    await app.syncAppleHealthIfDue()
                }
            }
        }
        .task(id: app.session.user?.id) {
            if app.session.user != nil {
                await app.autoSyncWatchIfDue()
                await app.syncAppleHealthIfDue()
            }
        }
```

- [ ] **Step 6: Checklist.** In `PlanView.swift:201`, pass `corosConnected: app.corosConnected || app.appleHealthConnected`.

- [ ] **Step 7: Run all tests.** Run: `ios-native/scripts/test.sh 2>&1 | tail -40`. Expected: "Tests passed", including the existing `AppModelTests` and `PlanViewModelTests` (`autoSyncWatch` behaviour is unchanged).

- [ ] **Step 8: Commit.**

```bash
git add ios-native/project.yml ios-native/UphillAI ios-native/UphillAITests
git commit -m "feat(ios): HealthKit store, entitlements and Apple Health sync wiring"
```

### Task 7: Apple Health in onboarding and plan-setup volume

**Files:**
- Modify: `ios-native/UphillAI/Features/Onboarding/PlanSetupViewModel.swift`
- Modify: `ios-native/UphillAI/Features/Onboarding/SetupSteps.swift` (watch step around line 109; volume label around line 466)
- Modify: `ios-native/UphillAI/Features/Integrations/WatchChannelsList.swift`
- Modify: `ios-native/UphillAI/Resources/Localizable.xcstrings`
- Test: `ios-native/UphillAITests/Plan/PlanSetupViewModelTests.swift`

**Interfaces:**
- Consumes: `WatchVolume`, `AppModel.connectAppleHealth()` (Task 6).
- Produces:
  - `PlanSetupViewModel.init(..., loadWatchVolume: (@Sendable () async -> WatchVolume?)?, connectAppleHealth: (@MainActor () async -> String?)? = nil)`
  - `PlanSetupViewModel.watchVolumeSource: String?`
  - `PlanSetupViewModel.appleHealthConnected: Bool`
  - `PlanSetupViewModel.connectAppleHealth() async -> String?`

- [ ] **Step 0: Impeccable.** Load the `impeccable:impeccable` skill and use it to shape this task's screens before coding, per Global Constraints. At the screenshot step, run Impeccable `polish` + `harden` on the shots and apply its findings.

- [ ] **Step 1: Update and add the tests.** In `PlanSetupViewModelTests.swift`:
  - Change the `make` helper parameter to `loadWatchVolume: (@Sendable () async -> WatchVolume?)? = nil` and add `connectAppleHealth: (@MainActor () async -> String?)? = nil`, passing both through.
  - Change the existing test at line 128 to `make(.newPlan, loadWatchVolume: { WatchVolume(weeklyKm: 41.6, weeklyKmSource: "coros") })`.
  - Add:

```swift
    @Test func appleHealthVolumeIsLabelledAsAppleHealth() async {
        let (model, _, _, _) = make(.newPlan, loadWatchVolume: { WatchVolume(weeklyKm: 52.4, weeklyKmSource: "apple_health") })
        await model.prefillWatchVolume()
        #expect(model.draft.currentWeeklyKm == 52)
        #expect(model.watchVolumeSource == "apple_health")
    }

    @Test func connectingAppleHealthMarksItAndPrefills() async {
        let (model, _, _, _) = make(.newPlan,
                                    loadWatchVolume: { WatchVolume(weeklyKm: 60, weeklyKmSource: "apple_health") },
                                    connectAppleHealth: { nil })
        let error = await model.connectAppleHealth()
        #expect(error == nil)
        #expect(model.appleHealthConnected)
        #expect(model.draft.currentWeeklyKm == 60)
    }

    @Test func appleHealthConnectErrorIsReturned() async {
        let (model, _, _, _) = make(.newPlan, connectAppleHealth: { "Apple Health isn't available on this device." })
        #expect(await model.connectAppleHealth() == "Apple Health isn't available on this device.")
        #expect(!model.appleHealthConnected)
    }
```

Also check the `.watch` step's "Skip for now" rule (`PlanSetupViewModel.swift:123`): once Apple Health is connected, the button must read the normal Next label. Extend the existing test for that rule, or add:

```swift
    @Test func watchStepIsNotSkipOnceAppleHealthIsConnected() async {
        let (model, _, _, _) = make(.onboarding, connectAppleHealth: { nil })
        _ = await model.connectAppleHealth()
        model.jump(to: .watch)
        #expect(model.primaryTitle != L("Skip for now"))
    }
```

(Use the real name of the property that returns the bottom button title around line 123. Read it first.)

- [ ] **Step 2: Run and confirm they fail** (compile errors). Run: `ios-native/scripts/test.sh 2>&1 | tail -40`.

- [ ] **Step 3: Implement in `PlanSetupViewModel.swift`:**
  - `private let loadWatchVolume: (@Sendable () async -> WatchVolume?)?`
  - `private let appleHealthConnect: (@MainActor () async -> String?)?`
  - `private(set) var watchVolumeSource: String?`
  - `private(set) var appleHealthConnected = false`
  - In `init` add the `connectAppleHealth` parameter (default `nil`) and store it.
  - Where status is loaded (line ~63), also set `appleHealthConnected = status.appleHealth?.connected ?? false`.

```swift
    func prefillWatchVolume() async {
        guard let loadWatchVolume, let volume = await loadWatchVolume() else { return }
        watchWeeklyKm = volume.weeklyKm.rounded()
        watchVolumeSource = volume.weeklyKmSource
        if !editedWeeklyKm {
            draft.currentWeeklyKm = volume.weeklyKm.rounded()
            draft.weeklyKmFromWatch = true
        }
    }

    func connectAppleHealth() async -> String? {
        guard let appleHealthConnect else { return nil }
        if let error = await appleHealthConnect() { return error }
        appleHealthConnected = true
        await prefillWatchVolume()
        return nil
    }
```

In the "Skip for now" rule, use `!corosConnected && !appleHealthConnected`.

The nothing-found hint isn't an error in onboarding. In `AppModel.makeSetup`'s `connectAppleHealth` closure from Task 6, return the message only when the connection failed:

```swift
                                       connectAppleHealth: { [weak self] in
                                           guard let self else { return nil }
                                           await self.connectAppleHealth()
                                           return self.appleHealthConnected ? nil : self.appleHealthMessage
                                       })
```

- [ ] **Step 4: Views.**

In `WatchChannelsList.swift`:
- Remove `("Apple Health", "heart.fill")` from `upcoming`.
- Add parameters `healthConnected: Bool`, `healthAvailable: Bool`, `connectHealth: () async -> String?`.
- Render an Apple Health block styled like the COROS block (same `channelBadge(symbol: "heart.fill", live: true)`, same card) with:
  - Title: `Text(verbatim: "Apple Health")`
  - Caption: `Text("Runs, hikes and strength sessions from your iPhone, Apple Watch or any app that saves to Health.")`
  - When connected: `Text("Connected. I'll use your recent workouts to set your starting mileage.")`
  - Button: `Text("Connect Apple Health")`, `.accessibilityIdentifier("setup.connectAppleHealth")`
  - Its own `isConnecting`/`error` state, mirroring COROS.
- Hide the block when `!healthAvailable`.

In `SetupSteps.swift` at the `.watch` case:

```swift
                WatchChannelsList(connected: model.corosConnected, available: model.deviceService != nil,
                                  healthConnected: model.appleHealthConnected, healthAvailable: model.canConnectAppleHealth,
                                  connect: { await model.connectCoros() },
                                  connectHealth: { await model.connectAppleHealth() })
```

Add `var canConnectAppleHealth: Bool { appleHealthConnect != nil }` to the view model. Update the other `WatchChannelsList(` call sites found by `grep -rn "WatchChannelsList(" ios-native/UphillAI` the same way, passing `healthAvailable: false` where there is no closure.

Replace the volume label (around line 467):

```swift
                Label(model.watchVolumeSource == "apple_health"
                      ? L("From Apple Health: %lld km a week over the last 4 full weeks", Int(km))
                      : L("From your COROS: %lld km a week over the last 4 full weeks", Int(km)),
                      systemImage: "applewatch.radiowaves.left.and.right")
```

- [ ] **Step 5: Strings.** Load the `uphill-ai-vietnamese-copy` skill. Add EN + VI to `Localizable.xcstrings` for every new key in Tasks 6–7:
  - "Runs, hikes and strength sessions from your iPhone, Apple Watch or any app that saves to Health."
  - "Connected. I'll use your recent workouts to set your starting mileage."
  - "Connect Apple Health"
  - "From Apple Health: %lld km a week over the last 4 full weeks"
  - "No workouts found. Check Settings → Health → Data Access & Devices → Uphill AI."
  - "Apple Health isn't available on this device."
  - "Couldn't sync with Uphill. I'll try again next time you open the app."
  - "Couldn't disconnect. Check your connection and try again."

Keep "Apple Health" untranslated (product name); the VI Settings path uses iOS's Vietnamese labels ("Cài đặt → Sức khỏe → Truy cập dữ liệu & thiết bị"). Confirm them with the skill.

- [ ] **Step 6: Run the tests.** Run: `ios-native/scripts/test.sh 2>&1 | tail -40`. Expected: "Tests passed".

- [ ] **Step 7: Screenshots.** Boot the Simulator (iPhone 16, iOS 18), run against the local backend with Developer menu → Sample Health data on (Task 8 Step 1 adds the switch; if you're doing tasks in order, take these shots in Task 8 Step 4 instead). Save `ios-native/docs/screenshots/apple-health/onboarding-watch.png` and `onboarding-volume-apple-health.png`.

- [ ] **Step 8: Commit.**

```bash
git add ios-native/UphillAI ios-native/UphillAITests ios-native/docs/screenshots/apple-health
git commit -m "feat(ios): connect Apple Health in onboarding; volume label names its source"
```

### Task 8: Connected Accounts row, explainer and debug sample data

**Files:**
- Create: `ios-native/UphillAI/Features/Integrations/AppleHealthRow.swift`
- Create: `ios-native/UphillAI/Features/Integrations/AppleHealthExplainerSheet.swift`
- Modify: `ios-native/UphillAI/Features/Me/ProfileView.swift` (after both `ConnectedAccountsView(...)` calls, lines ~89 and ~166)
- Modify: `ios-native/UphillAI/Features/Me/DeveloperMenu.swift`
- Modify: `ios-native/UphillAI/Resources/Localizable.xcstrings`
- Create: `ios-native/docs/screenshots/apple-health/*.png`

**Interfaces:**
- Consumes: `AppModel.appleHealthEnabled/Connected/LastSync/Syncing/Message`, `connectAppleHealth()`, `syncAppleHealthIfDue`, `disconnectAppleHealth()`, `loadAppleHealthStatus()` (Task 6); `SampleHealthStore.defaultsKey` (Task 5).
- Produces: `AppleHealthRow(app: AppModel)`, `AppleHealthExplainerSheet(onContinue: () -> Void)`.

- [ ] **Step 0: Impeccable.** Load the `impeccable:impeccable` skill and use it to shape this task's screens before coding, per Global Constraints. At the screenshot step, run Impeccable `polish` + `harden` on the shots and apply its findings.

- [ ] **Step 1: Developer switch.** In `DeveloperMenu.swift` add `@AppStorage(SampleHealthStore.defaultsKey) private var sampleHealth = false`, and inside the `Form` after the backend caption:

```swift
                Section {
                    Toggle("Sample Health data", isOn: $sampleHealth)
                } footer: {
                    Text("Uses three made-up workouts instead of HealthKit. Relaunch the app after changing it.")
                }
```

(Debug-only screen; these strings stay English.)

- [ ] **Step 2: Explainer sheet.** `AppleHealthExplainerSheet.swift`:

```swift
import SwiftUI

/// Shown before the system Health permission sheet: what Uphill reads, why, and what leaves the phone.
struct AppleHealthExplainerSheet: View {
    let onContinue: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    Image(systemName: "heart.fill").font(.largeTitle).foregroundStyle(UH.Palette.accentInk)
                    Text("Connect Apple Health").font(UH.TextStyle.screenTitle)
                    point("figure.run", "What I read",
                          "Runs, hikes, stair sessions and strength workouts from the last 12 weeks, then each new one as it's saved.")
                    point("checkmark.circle", "Why",
                          "To mark your planned sessions done and start your plan from your real weekly mileage.")
                    point("lock", "What I send to Uphill",
                          "Time, distance, climb, heart rate and calories for each workout. Your GPS routes stay on your phone.")
                    point("square.and.pencil", "Nothing written", "I never write to Apple Health.")
                }
                .padding(UH.Space.section)
            }
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: UH.Space.small) {
                    Button("Continue") { dismiss(); onContinue() }
                        .buttonStyle(.uhPrimary)
                        .accessibilityIdentifier("health.explainer.continue")
                    Button("Not now") { dismiss() }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(UH.Space.section)
                .background(UH.Palette.surface)
            }
        }
        .presentationDetents([.large])
    }

    private func point(_ symbol: String, _ title: LocalizedStringKey, _ body: LocalizedStringKey) -> some View {
        HStack(alignment: .top, spacing: UH.Space.regular) {
            Image(systemName: symbol).foregroundStyle(UH.Palette.accentInk).frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text(body).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}
```

Check the token names (`UH.Space.section`, `.uhPrimary`, `UH.Palette.surface`, `UH.TextStyle.screenTitle`) against `DesignSystem/`. They're used in `WatchChannelsList` and `SetupSteps`; adapt if one differs.

- [ ] **Step 3: The row.** `AppleHealthRow.swift`. Match `ConnectedAccountsView`'s COROS card: open `ConnectedAccountsView.swift` and copy its card padding, background, stroke and button styles. The row's states:

```swift
import SwiftUI

/// Me → Connected accounts: connect, sync, or disconnect Apple Health.
struct AppleHealthRow: View {
    let app: AppModel
    @State private var showExplainer = false
    @State private var showDisconnect = false

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            HStack(spacing: UH.Space.regular) {
                Image(systemName: "heart.fill").foregroundStyle(UH.Palette.accentInk)
                VStack(alignment: .leading, spacing: 2) {
                    Text(verbatim: "Apple Health").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text(subtitle).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer(minLength: 0)
                if app.appleHealthSyncing { ProgressView() }
            }
            if let message = app.appleHealthMessage {
                Text(message).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("health.message")
            }
            if app.appleHealthConnected {
                HStack {
                    Button("Sync now") { Task { await app.connectAppleHealth() } }
                        .disabled(app.appleHealthSyncing)
                        .accessibilityIdentifier("health.syncNow")
                    Spacer()
                    Button("Disconnect", role: .destructive) { showDisconnect = true }
                        .accessibilityIdentifier("health.disconnect")
                }
                .font(UH.TextStyle.label)
            } else {
                Button("Connect Apple Health") { showExplainer = true }
                    .buttonStyle(.uhPrimary)
                    .disabled(app.appleHealthSyncing)
                    .accessibilityIdentifier("health.connect")
            }
        }
        .trainingCard()
        .sheet(isPresented: $showExplainer) {
            AppleHealthExplainerSheet { Task { await app.connectAppleHealth() } }
        }
        .confirmationDialog("Disconnect Apple Health?", isPresented: $showDisconnect, titleVisibility: .visible) {
            Button("Disconnect", role: .destructive) { Task { await app.disconnectAppleHealth() } }
        } message: {
            Text("Workouts received from Apple Health are deleted from Uphill AI. To stop sharing completely, turn off access in Settings → Health → Data Access & Devices.")
        }
        .task { await app.loadAppleHealthStatus() }
    }

    private var subtitle: String {
        if app.appleHealthSyncing { return L("Syncing…") }
        if app.appleHealthConnected, let last = app.appleHealthLastSync, let date = ISO8601DateFormatter().date(from: last) {
            return L("Last synced %@", date.formatted(.relative(presentation: .named)))
        }
        if app.appleHealthConnected { return L("Connected") }
        return L("Runs, hikes and strength sessions from your iPhone, Apple Watch or any app that saves to Health.")
    }
}
```

`"Sync now"` calls `connectAppleHealth()`, which is idempotent: authorization is a no-op once granted, and it re-registers observing. This also repairs a phone where the server says connected but this phone isn't observing (reinstall, new phone). Use `.trainingCard()` only if `ConnectedAccountsView` uses it; otherwise copy its modifiers. If `last_sync_at` arrives with fractional seconds, `ISO8601DateFormatter` needs `.withFractionalSeconds`. Check `integrations_status.json` and match `ConnectedAccountsView`'s COROS "Last synced" parsing.

- [ ] **Step 4: Place it.** In `ProfileView.swift`, directly after each `ConnectedAccountsView(service: app.deviceConnectionService)`:

```swift
                        if app.appleHealthEnabled { AppleHealthRow(app: app) }
```

and make sure the enclosing view triggers `await app.loadCorosStatus()` (or `loadAppleHealthStatus()`) on appear. If `appleHealthEnabled` is never loaded on this screen, add `.task { await app.loadAppleHealthStatus() }` to the container. Without it the row never appears.

- [ ] **Step 5: Strings.** With the `uphill-ai-vietnamese-copy` skill, add EN + VI for:
  - "Connect Apple Health"
  - "What I read"
  - "Runs, hikes, stair sessions and strength workouts from the last 12 weeks, then each new one as it's saved."
  - "Why"
  - "To mark your planned sessions done and start your plan from your real weekly mileage."
  - "What I send to Uphill"
  - "Time, distance, climb, heart rate and calories for each workout. Your GPS routes stay on your phone."
  - "Nothing written"
  - "I never write to Apple Health."
  - "Continue"
  - "Not now"
  - "Sync now"
  - "Disconnect"
  - "Disconnect Apple Health?"
  - "Workouts received from Apple Health are deleted from Uphill AI. To stop sharing completely, turn off access in Settings → Health → Data Access & Devices."
  - "Syncing…"
  - "Last synced %@"
  - "Connected"

Skip any key already in the catalog.

- [ ] **Step 6: Tests and screenshots.** Run `ios-native/scripts/test.sh 2>&1 | tail -40` (expect pass). Then, on the Simulator (iPhone 16, iOS 18) against the local backend, signed in as the seeded `ios-preview@uphill.ai` athlete with Developer → Sample Health data on, capture into `ios-native/docs/screenshots/apple-health/`:
  - `me-not-connected.png`
  - `explainer.png`
  - `me-connected.png`
  - `plan-matched-health-run.png`: a matched run card showing "Apple Watch"
  - `me-nothing-found.png`: turn sample data off, connect against an empty Simulator Health store, and the hint shows
  - `explainer-vi.png`: Vietnamese, via the in-app language switch
  - `me-large-text.png`: one Dynamic Type XXXL shot

Look at each once and fix anything clipped.

- [ ] **Step 7: Commit.**

```bash
git add ios-native/UphillAI ios-native/docs/screenshots/apple-health
git commit -m "feat(ios): Apple Health in Connected accounts with explainer and sample data"
```

### Task 9: End-to-end checks, docs and PR

**Files:**
- Modify: `docs/superpowers/specs/2026-10-01-ios-native-app-design.md` (the 2026-10-14 status note)
- Modify: `CLAUDE.md` (one paragraph under "Knowledge-base RAG engine…"'s sibling sections, about the Apple Health integration)

- [ ] **Step 1: Full suites.**
  - `cd backend && pytest tests/unit -q 2>&1 | tail -5` → all pass
  - `cd backend && DATABASE_URL=postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test pytest tests/integration/test_activity_persistence.py -q` → all pass
  - `ios-native/scripts/test.sh 2>&1 | tail -40` → pass
  - `ios-native/scripts/e2e.sh 2>&1 | tail -40` → pass

- [ ] **Step 2: Local end-to-end by hand.** With the local backend and Sample Health data on:
  1. Connect from Me.
  2. In the backend, `SELECT source_provider, activity_type, device_model FROM activities WHERE user_id = <preview id> ORDER BY start_time DESC LIMIT 5;` against `uphill_ai` (read-only query) shows three `apple_health` rows: `outdoor_run`, `hike`, `strength`.
  3. Disconnect and the rows are gone.
  4. Reconnect and the rows return, with no duplicates on a second "Sync now".

Note the results in the PR.

- [ ] **Step 3: Docs.** In the roadmap's status note, change the Phase 4 line to say sub-project A is built (PR link) and B/C remain. In root `CLAUDE.md`, add after the "Training venues" paragraph:

```markdown
**Apple Health** (spec `docs/superpowers/specs/2026-10-14-apple-health-run-import-design.md`): the iOS app reads runs, hikes/stairs (`hike`) and strength workouts from HealthKit (any app's, read-only, 12-week first import, background delivery) and posts summaries to `POST /api/integrations/apple-health/sync`; rows land in `activities` as `source_provider='apple_health'` and go through the same duplicate check and matcher as COROS. `fitness_snapshot` takes measured volume from whichever device provider synced most recently. `APPLE_HEALTH_ENABLED=false` hides it without an app release. Routes and HR series never leave the phone.
```

- [ ] **Step 4: Commit.**

```bash
git add docs/superpowers/specs/2026-10-01-ios-native-app-design.md CLAUDE.md
git commit -m "docs: Apple Health run import in CLAUDE.md and the native roadmap"
```

- [ ] **Step 5: PR.** Push the branch and open a PR titled "Apple Health, sub-project A: run import". Body:
  - summary
  - spec link
  - the golden-eval summary (Task 3)
  - screenshots
  - local end-to-end results
  - SDK name adaptations
  - **owner steps before TestFlight:**
    1. Enable HealthKit (and background delivery) on the `uphill.ai.app` App ID in the developer portal and regenerate the profile.
    2. Deploy the backend (additive; no migration; `APPLE_HEALTH_ENABLED` defaults to true; diff prod `.env` keys after deploy).
    3. TestFlight build.
    4. Real-device check: record a short run on an Apple Watch and confirm it appears and matches without opening the app.
  - **owner steps before public App Store release:** Phase 7 Privacy screen describing Health use, in-app account deletion, "Health & Fitness" privacy label, review notes.

  End the body with the attribution line. Then use the ccd_pr tools (`get_status`, `bind_pr` if needed) per the session rules.

---

## Self-review notes (for the executor)

- **Spec coverage:**

  | Spec item | Task |
  |---|---|
  | Endpoint, deletion, status, flag | 1–2 |
  | Provider-neutral volume and the `plan_generator` line | 3 |
  | Mapper, vert fallback, DTOs | 4 |
  | Anchor-on-success, batching, observing | 5 |
  | Entitlements, HealthKit, foreground and background sync | 6 |
  | Onboarding and source label | 7 |
  | Connected Accounts, explainer, silent-denial hint, sample data | 8 |
  | Tests, docs, rollout | 9 |

- **Not in this plan, by design:** recovery metrics (B), WorkoutKit (C), race-history evidence, web Apple Health UI.

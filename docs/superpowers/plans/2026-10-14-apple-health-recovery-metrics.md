# Apple Health Recovery Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resting HR, HRV and sleep from Apple Health reach `daily_metrics` and drive the readiness that plan generation, adapt week, the Goal Determiner and Coach Uphill already (or newly) read. Apple Watch, Garmin, Suunto and Polar athletes get recovery-aware plans, as COROS athletes already do.

**Architecture:**
- **iOS:** reads three daily values with statistics queries plus a sleep sample query. A pure mapper turns them into one row per local date. The rows ride on A's sync request.
- **Backend:** stores them through the existing `upsert_daily_metric` and computes a personal HRV baseline and status. Readiness reads one provider at a time, so COROS RMSSD and Apple SDNN never average together.

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy Core (`text()`), Alembic, pytest.
- iOS: SwiftUI, Swift 6, HealthKit, Swift Testing, XcodeGen.

**Spec:** `docs/superpowers/specs/2026-10-14-apple-health-recovery-metrics-design.md`. Read it before any task.

## Progress (update as tasks land)

| Task | State | Commits |
|---|---|---|
| 1 | todo | |
| 2 | todo | |
| 3 | todo | |
| 4 | todo | |
| 5 | todo | |
| 6 | todo | |
| 7 | todo | |
| 8 | todo | |
| 9 | todo | |

## Global Constraints

- **Dual schema:**
  - Every column goes into both `db.py:init_db()` and a hand-written Alembic migration (see the `db-migration` skill).
  - Alembic has two heads today (`a713c9e6f024`, `a7c4e2f9b1d3`). Task 1's revision merges them.
- **Database access:** raw SQL via `text()` only, as `db.py` already does.
- **Integration tests:** `backend/tests/integration` TRUNCATEs every table. Run it only against a throwaway Postgres (for example `postgresql://uphill:uphill_secret@localhost:5440/uphill_ai_test`), never on :5433 or the dev DB.
- **Privacy:** only daily aggregates leave the phone. No sleep stages, no HR or HRV samples, no source bundle ids.
- **Failure isolation:** one bad metric row never fails a batch, and a metric failure never fails the workout sync. Metrics are stored after workouts, inside their own try/except, logged and reported in `daily_metrics.rejected`.
- **LLM changes:** any change to prompt text follows `.claude/skills/llm-change-process/SKILL.md`, and its checklist goes in the PR body.
- **UI changes:** need a Simulator screenshot as evidence.
- **Swift 6 strict concurrency:** no new warnings. Task 7 removes the existing `onSignedOut` warning.
- **Copy:** every user-facing string ships in EN and VI.

## Review Focus

- Provider selection in readiness: the tie rule and the "no rows" cases.
- Baseline math off-by-ones: the window excludes the day itself, and the 3-day mean includes it.
- The sleep wake-date boundary across DST and timezone travel (use the phone's current `Calendar`).
- The first-sync window must not re-send 35 days on every launch.

## File Structure

| File | Change |
|---|---|
| `backend/db.py` | `sleep_minutes` column (`init_db` + ALTER), `upsert_daily_metric` writes it, readiness provider filter + sleep, `get_latest_daily_metrics` filter, new `get_daily_hrv(user_id, start, end, provider)` |
| `backend/alembic/versions/<rev>_daily_metrics_sleep_minutes.py` | new merge revision |
| `backend/services/providers/base.py` | `CanonicalDailyMetric.sleep_minutes` |
| `backend/services/recovery_baseline.py` | new, pure `hrv_status_for` + `refresh(user_id, dates)` |
| `backend/config.py` | `APPLE_HEALTH_RECOVERY_ENABLED` |
| `backend/routers/integrations.py` | `daily_metrics` in the sync body, `_implausible_metric`, `recovery_enabled` in `/status` |
| `backend/services/plan_generator.py` | readiness block: sleep line and source name |
| `backend/services/coach_context.py`, `coach_prompts.py` | `recovery` context and a rendered section |
| `ios-native/UphillAI/Core/Health/AppleHealthModels.swift` | `AppleHealthDailyMetricUpload`, body field, result field, `recoveryEnabled` |
| `ios-native/UphillAI/Core/Health/HealthDailyMetricMapper.swift` | new, pure |
| `ios-native/UphillAI/Core/Health/HealthStoring.swift`, `HealthKitStore.swift` | `dailyMetrics(from:to:)`, read types, observers; sample store data |
| `ios-native/UphillAI/Core/Health/AppleHealthSyncService.swift` | metric windows, seeded flag |
| `ios-native/UphillAI/App/AppModel.swift` | `onSignedOut` capture fix; clear the seeded flag |
| `ios-native/UphillAI/Features/Integrations/AppleHealthRow.swift`, `AppleHealthExplainerSheet.swift` | "Add recovery data" button and copy |
| `ios-native/project.yml`, `Info.plist`, `InfoPlist.xcstrings`, `Localizable.xcstrings` | usage text and strings |

---

### Task 1: `sleep_minutes` column and merge migration

- [ ] Add `sleep_minutes INTEGER` to `CREATE TABLE daily_metrics` in `init_db`, and `ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS sleep_minutes INTEGER` next to the other self-migrating ALTERs.
- [ ] `alembic revision -m "daily_metrics sleep_minutes"`, then edit it by hand: `down_revision = ("a713c9e6f024", "a7c4e2f9b1d3")`; `upgrade` adds the column with `op.add_column`, `downgrade` drops it.
- [ ] `CanonicalDailyMetric.sleep_minutes: int | None = None`. In `upsert_daily_metric`, add `sleep_minutes` to the INSERT column list and set it to `COALESCE(EXCLUDED.sleep_minutes, daily_metrics.sleep_minutes)` in the ON CONFLICT clause.
- [ ] Test (unit, mocked engine as in `test_prompt_enrichment.py`): the upsert SQL carries `sleep_minutes`.
- [ ] Verify on the scratch DB: `alembic upgrade head`, then `alembic heads` shows exactly one head.
- [ ] Commit.

### Task 2: HRV baseline and status

New `backend/services/recovery_baseline.py`:

```python
"""Personal HRV baseline for providers that report raw HRV without a status (Apple Health)."""
from statistics import mean, pstdev

BASELINE_DAYS = 28
MIN_BASELINE_DAYS = 14


def hrv_status_for(history: list[float], last3: list[float]) -> tuple[float | None, str | None]:
    """history: the previous 28 days' HRV values (excluding the day). last3: the day and up to
    two days before it. Returns (baseline_ms, status), status "low" | "normal" | None."""
    if len(history) < MIN_BASELINE_DAYS or not last3:
        return None, None
    base, sd = mean(history), pstdev(history)
    return round(base, 1), ("low" if mean(last3) < base - sd else "normal")
```

- [ ] `refresh(user_id, dates)`:
  - Recomputes `hrv_baseline_ms`/`hrv_status` for each date in `dates` and the 3 days after it.
  - It only touches existing `apple_health` rows that have `hrv_ms`.
  - It reads with one `db.get_daily_hrv(user_id, start, end, "apple_health")` over `min(dates) − 31` to `max(dates) + 3` and writes with a single UPDATE per row.
- [ ] Tests:
  - 13 history values give `(None, None)`.
  - 28 steady values at 60 ± 3 with last3 = [50, 52, 51] give "low".
  - The same history with last3 = [60, 61, 59] gives "normal".
  - `refresh` writes only apple_health rows (mocked db).
- [ ] Commit.

### Task 3: Readiness reads one provider, plus sleep

In `db.get_recent_readiness_summary`:

- [ ] Fetch `source_provider, sleep_minutes` along with the existing columns.
- [ ] Choose the provider whose newest `metric_date` is the latest. On a tie, `coros` wins, so the order matches `DEVICE_PROVIDERS` in `fitness_snapshot`. Drop the other providers' rows.
- [ ] Add `source_provider`, `nights_recorded` (rows with `sleep_minutes`) and `avg_sleep_minutes` (rounded int) to both return shapes. The empty shape gets `None`/`0`.
- [ ] `readiness_flag`: after the HRV/recovery `fatigued` check, also `fatigued` when `nights_recorded >= 3 and avg_sleep_minutes < 360`. The overreaching precedence stays unchanged.
- [ ] `get_latest_daily_metrics`: same provider choice (newest row wins, with the COROS tie rule), and add `sleep_minutes` and `source_provider` to the SELECT.
- [ ] Tests (`tests/unit/test_prompt_enrichment.py` style):
  - COROS only: unchanged output plus the new keys.
  - Apple only.
  - Both, Apple newer: only Apple's HRV is averaged.
  - Both on the same day: COROS.
  - Sleep at 5h30 over 4 nights gives `fatigued`.
  - Sleep over only 2 nights doesn't count.
- [ ] Run the existing readiness and fitness-snapshot unit tests; they must still pass.
- [ ] Commit.

### Task 4: Sync endpoint accepts `daily_metrics`

In `routers/integrations.py`:

```python
APPLE_HEALTH_METRIC_BATCH = 60
METRIC_MAX_AGE_DAYS = 60


class AppleHealthDailyMetric(BaseModel):
    date: date
    resting_hr: int | None = None
    hrv_sdnn_ms: float | None = None
    sleep_minutes: int | None = None


def _implausible_metric(m: AppleHealthDailyMetric, today: date) -> str | None:
    if m.resting_hr is None and m.hrv_sdnn_ms is None and m.sleep_minutes is None:
        return "no values"
    if m.date > today + timedelta(days=1) or m.date < today - timedelta(days=METRIC_MAX_AGE_DAYS):
        return "date out of range"
    if m.resting_hr is not None and not 25 <= m.resting_hr <= 120:
        return "resting_hr out of range"
    if m.hrv_sdnn_ms is not None and not 5 <= m.hrv_sdnn_ms <= 300:
        return "hrv out of range"
    if m.sleep_minutes is not None and not 0 <= m.sleep_minutes <= 1080:
        return "sleep out of range"
    return None
```

- [ ] `AppleHealthSyncRequest.daily_metrics: list[dict[str, Any]] = Field(default_factory=list, max_length=60)`.
  - Parse each item with `AppleHealthDailyMetric.model_validate` inside a try block, as A does for workouts, so a malformed row is rejected and never returns 422 for the batch.
  - Duplicate dates: the last one wins.
- [ ] After the workout upserts:
  - If `settings.APPLE_HEALTH_RECOVERY_ENABLED`, upsert each valid row as `CanonicalDailyMetric(metric_date=m.date, provider=APPLE_HEALTH, resting_hr=…, hrv_ms=m.hrv_sdnn_ms, sleep_minutes=…)`, then call `recovery_baseline.refresh(user_id, dates)`.
  - Wrap it in try/except with `logger.exception`.
  - Response: `"daily_metrics": {"accepted": n, "rejected": [{"date", "reason"}]}`. When the flag is off: `{"accepted": 0, "rejected": [], "disabled": true}`.
- [ ] `config.py`: `APPLE_HEALTH_RECOVERY_ENABLED: bool = env bool, default True`. Add it to `/status` as `apple_health.recovery_enabled`.
- [ ] Unit tests:
  - Each rejection reason.
  - A malformed item (string HR) is rejected and the workouts in the batch are still stored.
  - The flag off stores nothing.
  - Duplicate dates.
- [ ] Integration test (scratch DB):
  - Post 30 days of metrics, then rows exist and the last days have `hrv_status`.
  - Re-post the last 3 days with new values, which overwrite the old ones.
  - `DELETE /apple-health` removes them.
- [ ] Commit.

### Task 5: Prompts: readiness block and Coach Uphill (LLM change process)

- [ ] `plan_generator.py` readiness block:
  - Header becomes `7-DAY WEARABLE BIOLOGICAL READINESS & LOAD RATIO ({source}):`, where `{source}` is "Apple Health" or "COROS" (`readiness_summary["source_provider"]`).
  - Add the line `- Sleep: {h}h{mm:02d} avg ({n} nights)` when `nights_recorded > 0`.
  - Add sleep to the FATIGUED guidance bullet: `(Low HRV / Recovery < 45% / Sleep < 6h avg)`.
  - Apple rows have no ACWR, so ACWR shows `N/A` as it does today.
- [ ] `coach_context.build_chat_context`: `"recovery": summary if summary["days_recorded"] else None`, where `summary = db.get_recent_readiness_summary(user_id, days=7)` inside a try block (`None` on error).
- [ ] `coach_prompts`: when `context["recovery"]` is set, append

  ```
  ### Recovery (last 7 days, Apple Health)
  - HRV 54 ms (status: low) | Resting HR 52 bpm
  - Sleep 6h10 avg over 6 nights
  - Readiness: FATIGUED
  ```
  Omit any line whose values are all `None`.
- [ ] Check whether the `coach_chat` Langfuse template needs guidance text about using recovery: suggest easing off, never diagnose, and hand medical concerns to a professional.
  - If it does, create a new `coach_chat` version labelled `staging`, with the in-code fallback updated to the same text.
  - Run `python scripts/golden_eval.py compare --service coach` and push the results to Langfuse.
- [ ] Run `python scripts/golden_eval.py compare --service scheduler` and compare against main's known baseline (2 week-2 volume failures are pre-existing).
- [ ] Unit tests: block text with and without sleep; source name; coach section rendering; `recovery` omitted when `days_recorded == 0`.
- [ ] Commit, with the llm-change-process checklist copied into the PR draft.

### Task 6: iOS DTOs and the pure mapper

- [ ] `AppleHealthModels.swift`:
  - `struct AppleHealthDailyMetricUpload: Codable, Sendable, Equatable { let date: String; let restingHr: Int?; let hrvSdnnMs: Double?; let sleepMinutes: Int? }`, where `date` is `yyyy-MM-dd` in the local calendar.
  - `AppleHealthSyncBody.dailyMetrics: [AppleHealthDailyMetricUpload]`.
  - The result's optional `dailyMetrics` with `accepted`/`rejected`.
  - `AppleHealthConnectionStatus.recoveryEnabled: Bool?`, which defaults to true when it is missing so the app works against an older backend.
- [ ] `HealthDailyMetricMapper.swift` (pure, no HealthKit import in the core functions; inputs are plain structs):
  - `struct SleepInterval { let start: Date; let end: Date; let source: String; let asleep: Bool }`.
  - `static func sleepMinutes(_ intervals: [SleepInterval], calendar: Calendar) -> [String: Int]`:
    - Bucket each asleep interval to the wake date: the date of `end`, kept only when `end` falls between the previous day's 18:00 and 14:00 on that date. Anything else, such as an afternoon nap, is dropped.
    - Group by source and merge overlaps within each source.
    - Per date, keep the source with the largest total.
  - `static func rows(restingHr: [String: Double], hrv: [String: Double], sleep: [String: Int]) -> [AppleHealthDailyMetricUpload]`: unions the dates, rounds resting HR to Int and HRV to 0.1, drops empty rows, and sorts by date.
- [ ] Swift Testing:
  - Two overlapping Watch intervals are counted once.
  - Watch 400 min vs AutoSleep 430 min picks 430.
  - A 15:00 nap is excluded.
  - A 23:30–06:45 night lands on the wake date.
  - A DST night in a timezone that has DST (America/New_York) gives the right minutes.
  - JSON encoding is snake_case through the existing API encoder.
- [ ] Commit.

### Task 7: HealthKit store, sync windows, background delivery

- [ ] `HealthStoring.dailyMetrics(from: Date, to: Date) async throws -> [AppleHealthDailyMetricUpload]`.
- [ ] `HealthKitStore`:
  - Add `.restingHeartRate`, `.heartRateVariabilitySDNN` and `.sleepAnalysis` to the read set.
  - Resting HR and HRV come from `HKStatisticsCollectionQueryDescriptor` with `.discreteAverage`, a daily interval and an anchor at `calendar.startOfDay`.
  - Sleep comes from `HKSampleQueryDescriptor` over `from − 1 day` to `to`. Map the values `asleepCore/Deep/REM/Unspecified` to `asleep = true` and use `sourceRevision.source.name` as the source; the name is used only on the phone.
  - Feed the mapper.
- [ ] `startObserving` also registers `HKObserverQuery` and `enableBackgroundDelivery` for `sleepAnalysis` (`.hourly`) and `restingHeartRate` (`.daily`), through the same `onUpdate`. `stopObserving` stops them.
- [ ] The sample store (`UPHILL_SAMPLE_HEALTH`) returns 35 days: resting HR 50–54, HRV around 62 with days −4 to −1 at 48–50 (giving "low"), sleep 380–460 min.
- [ ] `AppleHealthSyncService.performSync`:
  - Read the metrics: 35 days when `appleHealthMetricsSeeded[userId]` is false, otherwise 3 days ending today.
  - Skip them when the last status said `recoveryEnabled == false`.
  - Put them in the first batch's body only.
  - Set the seeded flag only after a 2xx response, with the same user guard as the anchor.
  - A metric read failure logs and sends `[]`. It never blocks the workouts.
- [ ] `AppModel.swift:203-240`: replace the mutable `var onSignedOut` captured by the sendable closure with a `final class SignOutHook: @unchecked Sendable { @MainActor var run: () -> Void = {} }` box, or an equivalent that needs no var capture. Clear the seeded flag in it.
- [ ] Swift Testing with fake stores:
  - The first sync asks for 35 days, the second for 3.
  - A failed upload leaves the flag unset.
  - `recoveryEnabled=false` sends `[]`.
  - Sign-out clears the flag.
- [ ] Build with zero new warnings. Commit.

### Task 8: Permission button and copy

- [ ] `AppleHealthRow`: when connected and `appleHealthRecoveryAsked[userId]` is false, show a secondary button "Add recovery data" / "Thêm dữ liệu hồi phục" (accessibility id `appleHealth.addRecovery`). Tapping it calls `requestAuthorization()`, sets the flag and triggers `sync()`. New connections set the flag on connect, because they already asked for everything.
- [ ] `AppleHealthExplainerSheet`:
  - Add a row for "Resting heart rate, HRV and sleep, as daily totals" / "Nhịp tim nghỉ, HRV và giấc ngủ, dạng tổng theo ngày".
  - The "stays on your phone" line gains "sleep stages" / "các giai đoạn ngủ".
- [ ] `NSHealthShareUsageDescription` (project.yml, Info.plist, InfoPlist.xcstrings EN/VI): "Uphill AI reads your runs, hikes and strength workouts, plus resting heart rate, HRV and sleep, so it can mark sessions done, measure your weekly mileage and adjust training to how you're recovering." Write a matching VI line.
- [ ] UI test: sign in to an A-connected account with sample Health data, confirm the button exists, tap it, confirm it is gone.
- [ ] Screenshots `07-add-recovery.png` and `08-explainer-recovery.png`, downscaled with `sips -Z 1311`.
- [ ] Commit.

### Task 9: End-to-end checks, docs and PR

- [ ] Backend: `pytest tests/unit` plus the integration suite on the scratch DB; `ruff`.
- [ ] iOS: `xcodegen generate` with no unexpected diff; `scripts/test.sh`; `scripts/e2e.sh`.
- [ ] By hand on the Simulator with sample Health data:
  1. Connect, then check that `daily_metrics` has 35 apple_health rows and the last days are "low".
  2. Check that adapt week's prompt (log at debug level, or a unit-level call) shows the sleep line and "Apple Health".
  3. Ask Coach Uphill "how am I recovering?"; the answer should cite HRV and sleep.
  4. Disconnect, and check the rows are gone.
- [ ] Update `CLAUDE.md`'s Apple Health paragraph with one sentence on recovery metrics, the `APPLE_HEALTH_RECOVERY_ENABLED` flag and readiness using one provider.
- [ ] Open a PR. The body carries the llm-change-process checklist, the golden eval numbers, screenshots, and the rollout steps from the spec (Alembic merge revision on prod, then `alembic heads` shows one head).

## Self-review notes (for the executor)

- `get_recent_readiness_summary` has three callers (`main.py` plan creation, `week_rebuild.py`, `fitness_snapshot.py`) plus the new coach one. The new keys are additive, so no caller should need a change beyond Task 5.
- COROS's `hrv_status` vocabulary is passed through unchanged. Only apple_health rows get computed statuses.
- `delete_provider_data` already removes `daily_metrics` for the provider. Don't add a second delete.
- If the coach golden eval is noisy, compare against a fresh `main` run made the same day, as Task 3 of sub-project A did for the scheduler.

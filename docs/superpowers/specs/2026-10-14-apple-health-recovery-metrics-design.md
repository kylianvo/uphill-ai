# Apple Health, sub-project B: recovery metrics

Date: 2026-10-14
Status: draft design, for review. Implementation plan: `docs/superpowers/plans/2026-10-14-apple-health-recovery-metrics.md`.
Builds on sub-project A (`2026-10-14-apple-health-run-import-design.md`, shipped in #126 and #128).

## Why

Adapt week, plan generation and the Goal Determiner already read a 7-day readiness summary from `daily_metrics`. Today only COROS fills that table, so most athletes, who use an Apple Watch, Garmin, Suunto or Polar, get plans that ignore how they are recovering. Every one of those devices writes resting HR, HRV and sleep to Apple Health. B reads those three values, so readiness works for everyone with an iPhone.

## What already exists (reuse, don't rebuild)

| Piece | Where | State |
|---|---|---|
| `daily_metrics` table, unique `(user_id, metric_date, source_provider)` | `db.py:init_db` | resting_hr, hrv_ms, hrv_baseline_ms, hrv_status, load and recovery columns. **No sleep column.** |
| `db.upsert_daily_metric(user_id, CanonicalDailyMetric)` | `db.py` | COALESCE upsert, used by COROS |
| `db.get_recent_readiness_summary(user_id, days)` | `db.py` | **Mixes all providers** |
| Readiness block in the plan prompt ("7-DAY WEARABLE BIOLOGICAL READINESS") | `plan_generator.py` ~1424 | Fed by plan creation (`main.py`), adapt week (`week_rebuild.py`), fitness snapshot |
| `db.get_latest_daily_metrics` | `goal_context.py` | Goal Determiner recovery context |
| `db.delete_provider_data(user, "apple_health")` | Apple Health disconnect | Already deletes the `daily_metrics` rows too |
| `_freshest_connection` | `fitness_snapshot.py` | Picks the device provider that synced most recently |

Coach Uphill chat (`coach_context.build_chat_context` → `coach_prompts`) has **no** recovery data today.

## Scope

**In B:**
- Three daily values from Health, from any source app: **resting HR**, **HRV (SDNN)** and **sleep duration**.
- A personal HRV baseline and status for Apple Health rows, computed on the server, because Apple does not provide a status the way COROS does.
- Readiness uses one provider at a time, plus sleep in the readiness summary.
- Recovery appears in Coach Uphill chat context.
- The iOS permission request, the sync, and background delivery for the new types.

**Not in B:** a recovery dashboard or chart in the app, sleep stages, VO2max, respiratory rate, wrist temperature, readiness on web/Android, WorkoutKit (C).

## Decisions

1. **Never mix providers.** COROS reports overnight RMSSD; Apple Health reports SDNN. The two use different scales: SDNN is often 1.5–2× RMSSD for the same night. `get_recent_readiness_summary` reads only the rows of a single provider: the one in the window with the newest `metric_date`, ties going to COROS (the same rule as `_freshest_connection`). The summary gains a `source_provider` key.
2. **Status comes from a personal baseline, not population numbers.** For each `apple_health` day:
   - `hrv_baseline_ms` is the mean of the previous 28 days' HRV (at least 14 days with a value).
   - `hrv_status` is `"low"` when the 3-day mean is below baseline − 1 SD of that window, `"normal"` otherwise, and `NULL` with fewer than 14 days.
   - `"low"` is already in the `fatigued` vocabulary `get_recent_readiness_summary` uses, so adapt week and the plan prompt react with no logic change.
   - It runs in a pure function, `services/recovery_baseline.py`, and is recomputed for the days a sync touched (plus the 3 days after them).
3. **Sleep is one number per night:** `sleep_minutes`, the asleep time (core + deep + REM + unspecified, never "in bed" or "awake"). It is assigned to the date the athlete **wakes up** and covers the window from 18:00 the day before to 14:00 on that date, in local time. Several apps write sleep, so the phone keeps the single source with the most asleep time that night and does not add sources together. Stage data stays on the phone.
4. **Resting HR** is Health's own `restingHeartRate` daily value (the day's average sample). It is not derived from workout HR.
5. **Sleep in readiness:**
   - The summary gains `avg_sleep_minutes` and `nights_recorded`.
   - `readiness_flag` becomes `fatigued` also when at least 3 nights are recorded and the average is under 6 h (360 min).
   - The prompt's readiness block gains one line: `Sleep: 6h40 avg (5 nights)`.
   - This is a prompt-visible change, so it goes through the LLM change process (below).
6. **Windows:**
   - The first sync after B sends **35 days**: 28 for the baseline, plus 7 for the readiness window.
   - Each later sync re-sends the **last 3 days**, because late Watch writes and overnight sleep firm up after the first read. The upsert fills nulls and overwrites values.
7. **One endpoint, one flag:**
   - The metrics ride on the existing `POST /api/integrations/apple-health/sync` as an optional `daily_metrics` list, so no new route, auth or connection state is needed.
   - New setting `APPLE_HEALTH_RECOVERY_ENABLED` (default `true`). When it is off, the server ignores the list and `/status` reports `recovery_enabled: false`, so the app stops reading metrics without a release.

## Backend

### Schema

`daily_metrics.sleep_minutes INTEGER`, added in both `init_db` (column plus an idempotent `ALTER TABLE … ADD COLUMN IF NOT EXISTS`) and a hand-written Alembic migration. Alembic currently has **two heads** (`a713c9e6f024`, `a7c4e2f9b1d3`). The new revision is a merge revision with `down_revision = ("a713c9e6f024", "a7c4e2f9b1d3")`, which fixes the split at the same time. `CanonicalDailyMetric` gains `sleep_minutes: int | None = None`, and `upsert_daily_metric` writes it with the same COALESCE rule.

### Endpoint change

```
POST /api/integrations/apple-health/sync
{
  ...A's fields unchanged...,
  "daily_metrics": [{                 // optional, at most 60
    "date": "2026-10-13",             // athlete's local calendar date
    "resting_hr": 52,                 // optional, 25–120
    "hrv_sdnn_ms": 61.4,              // optional, 5–300
    "sleep_minutes": 412              // optional, 0–1080
  }]
}
→ { ...A's fields..., "daily_metrics": { "accepted": n, "rejected": [{"date", "reason"}] } }
```

- Validation follows A's model: a bad row is rejected with a reason and never fails the batch.
- A row is rejected when its date is more than one day in the future or more than 60 days old, a value is out of range, or all three values are null.
- Duplicate dates in a single batch: the last one wins.
- Stored with `provider = "apple_health"`, `hrv_ms = hrv_sdnn_ms`. Then `recovery_baseline.refresh(user_id, dates)` sets `hrv_baseline_ms`/`hrv_status`.
- `_implausible` stays workout-only; a sibling `_implausible_metric` handles the metric rows.

### Readiness

`get_recent_readiness_summary`:
- picks the provider (decision 1);
- adds `source_provider`, `avg_sleep_minutes` and `nights_recorded`;
- adds the sleep rule to `readiness_flag` (decision 5).

Callers keep working because the new keys are additive. `get_latest_daily_metrics` gets the same provider filter.

### Prompts (LLM change process)

- **Plan generation / adapt week:**
  - The readiness block gains the sleep line and names the source ("Apple Health" or "COROS").
  - The block is built in code from `feedback_instruction`, so no Langfuse template version is needed.
  - The output still changes, so run a scheduler golden eval.
- **Coach Uphill:**
  - `build_chat_context` adds `recovery` (the readiness summary when `days_recorded > 0`).
  - `coach_prompts` renders it as `### Recovery (last 7 days, <source>)` with HRV vs baseline, resting HR, sleep and the flag, in 4 lines at most.
  - If the `coach_chat` Langfuse template needs guidance text (for example, "use recovery to suggest easing off, never to diagnose"), that is a new prompt version on `staging`, promoted after the coach golden eval.
- The PR description carries the `.claude/skills/llm-change-process/SKILL.md` checklist.

## iOS

- **`HealthKitStore`:**
  - The read set gains `HKQuantityType(.restingHeartRate)`, `HKQuantityType(.heartRateVariabilitySDNN)` and `HKCategoryType(.sleepAnalysis)`.
  - New `dailyMetrics(from:to:) async throws -> [HealthDailyMetric]`.
  - Resting HR and HRV use `HKStatisticsCollectionQuery` (daily `discreteAverage`, anchored at local midnight).
  - Sleep uses an `HKSampleQuery` over the window, mapped by a pure function.
- **`HealthDailyMetricMapper` (new, pure, unit-tested):** sleep samples go to `sleep_minutes` per wake date (decision 3, picking the source with the most asleep time and merging overlapping intervals within that source). Daily statistics go to rows. Rows with no values are dropped.
- **`HealthStoring`:** the protocol and the debug sample store (`UPHILL_SAMPLE_HEALTH`) gain the metrics: 35 days of plausible values with one 5-night low-HRV stretch, so the sample data shows a "low" status.
- **`AppleHealthSyncService`:**
  - It sends `daily_metrics` with the workout sync: 35 days on the first B sync (tracked by a new defaults key, `appleHealthMetricsSeeded`), 3 days after that.
  - It skips the metrics when `/status` says `recovery_enabled: false`.
  - Sign-out clears the key along with the existing sync state, through the same `onSignedOut` hook. Fix its Sendable-capture warning (`AppModel.swift:240`) in the same change.
- **Background delivery:** add an `HKObserverQuery` and `enableBackgroundDelivery` for `sleepAnalysis` (`.hourly`) and `restingHeartRate` (`.daily`). They share the existing background sync entry point, so a morning wake-up sends last night's sleep.
- **Permission:**
  - New connections ask for all types in one sheet.
  - Athletes already connected under A get the new types the next time they tap "Sync now": it re-runs connect, which calls `requestAuthorization` with every type, so HealthKit shows the sheet with only the new ones. No separate button.
  - The app never prompts unasked on launch.
  - Health never reports read denial, so the button hides after a single tap whatever the answer.
- **Copy (EN and VI):**
  - The explainer sheet lists "Resting heart rate, HRV and sleep, as daily totals" under what Uphill reads, and says sleep stages and heart-rate streams stay on the phone.
  - Update `NSHealthShareUsageDescription` to mention recovery.
  - Update the App Store privacy label (Health & Fitness, already declared in A) if the review form asks per type.

## Testing

- **Backend unit tests:**
  - metric validation and rejections;
  - `recovery_baseline` (under 14 days gives no status; a low 3-day dip gives "low"; a recovery returns to "normal");
  - provider selection in readiness (COROS-only, Apple-only, both with Apple newer, a tie);
  - the sleep flag;
  - the readiness block text and the coach context rendering.
- **Backend integration tests** (scratch DB): a sync with metrics stores rows and statuses; a re-sync overwrites the last 3 days; disconnect deletes them; the flag turns it off.
- **iOS unit tests:** `HealthDailyMetricMapper` (overlap within a source; two sources where the larger wins; a nap at 15:00 excluded; the wake-date boundary), and the sync payload windows (35 days first, then 3).
- **Screenshots:** the explainer's "turn them all on" step and the nothing-found state with Open Settings, in `ios-native/docs/screenshots/apple-health/` (07–08).
- **Golden eval:** `scripts/golden_eval.py compare --service scheduler` and `--service coach`, with no regressions against main's baseline (the 2 known week-2 volume failures are pre-existing).
- **By hand on a device:** wear the Watch overnight, open Uphill, and confirm that `daily_metrics` holds last night's `sleep_minutes`, today's resting HR and HRV, and that adapt week's prompt shows the sleep line.

## Rollout

1. Merge the backend, then deploy by hand. Run the merge-revision Alembic upgrade on prod and check `alembic heads` shows a single head.
2. Build an iOS TestFlight build (next build number in `native-app-release-process` memory).
3. Turn on the coach prompt version after the golden eval: promote the Langfuse `staging` label to `production`.
4. If readiness misbehaves, `APPLE_HEALTH_RECOVERY_ENABLED=false` stops new rows. Existing rows can be removed with `DELETE FROM daily_metrics WHERE source_provider='apple_health'`.

## Open questions

- Should a "low" HRV with an "optimal" ACWR override to `fatigued`? Today's logic already does, since HRV is checked before the fresh/optimal branches. B keeps that behavior.
- Should a 7-day sleep debt also trigger a deload in adapt week, or only the existing tempo-to-easy swap? B keeps only the swap, through the `fatigued` flag.

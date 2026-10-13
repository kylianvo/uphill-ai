# Apple Health, sub-project A: run import

Date: 2026-10-14
Status: approved design; implementation plan to follow (`superpowers:writing-plans`).
Roadmap: Phase 4 of `docs/superpowers/specs/2026-10-01-ios-native-app-design.md`.

## Why

Uphill matches finished runs to planned workouts and measures starting mileage only for COROS users. Garmin's developer programme is closed and Strava's API terms ban AI use, so Apple Watch, Garmin, Suunto and Polar athletes have no way in. Most of those apps write workouts to Apple Health. Reading Health from the native app gives all of them matching and measured volume.

## Scope

Apple Health ships as three sub-projects, each with its own spec, plan and TestFlight build, in this order:

| | Sub-project | Contents |
|---|---|---|
| **A** | **Run import (this spec)** | Read workouts from Health, upload summaries, match them to the plan, count them in the fitness snapshot |
| B | Recovery metrics | Resting HR, HRV, sleep into `daily_metrics`, used by adapt week and Coach Uphill (prompt changes go through the LLM change process) |
| C | WorkoutKit push | Send planned workouts to Apple Watch as structured workouts |

B and C reuse A's entitlement, permission flow and the Apple Health connection.

**In A:**
- Workouts from **any app** that writes to Health (Apple Watch, Garmin Connect, COROS, Strava, …). COROS copies are caught by the existing cross-provider duplicate check.
- Types: running, hiking, stair climbing, strength training. Walking and cycling are left out: daily walks would flood the matching review.
- First import goes back **12 weeks**, which is what the fitness snapshot needs for chronic volume.
- Background delivery, so runs reach Uphill without the athlete opening the app.

**Not in A:** daily metrics (B), writing to Health or WorkoutKit (C), uploading routes or HR series, counting Health runs as race-history evidence (`race_history.verify_results`), Android / Health Connect.

## Backend

### Endpoint

`POST /api/integrations/apple-health/sync` in `routers/integrations.py`:

```
{
  "workouts": [{
    "external_id": "<HKWorkout UUID>",
    "activity_type": "outdoor_run" | "indoor_run" | "gps_cardio" | "gym_cardio" | "strength",
    "start_time": "<ISO 8601 with offset>",
    "end_time": "<ISO 8601 with offset>",
    "duration_seconds": 3720,
    "distance_km": 10.4,          // optional
    "elevation_gain_m": 412,      // optional
    "avg_hr": 148, "max_hr": 171, // optional
    "calories": 690,              // optional
    "source_name": "Apple Watch"  // HKSource name, stored as device_model
  }],                             // at most 500
  "deleted_ids": ["<HKWorkout UUID>"],
  "plan_id": 123,                 // optional, matching window
  "tz_offset_minutes": 420        // optional, passed to matching
}
→ { "stored": n, "skipped_duplicates": n, "rejected": [{"external_id", "reason"}], "deleted": n, "matching": {...} }
```

- Pydantic validates each row. Implausible rows (pace under 2:30 /km, HR over 250, duration over 48 h, end before start) go to `rejected`; the rest are stored. One bad row never blocks a batch.
- Each row goes through `db.upsert_activity` with `provider = "apple_health"`. It is idempotent on `(user, provider, external_id)`, and `_find_duplicate` links copies of a COROS run.
- `deleted_ids`: new `db.delete_activities_by_external_ids(user_id, "apple_health", ids)`. It deletes those rows. The schema already handles what pointed at them: a workout's `matched_activity_id` and another activity's `duplicate_of` are both `ON DELETE SET NULL`, and the following matching run re-evaluates the affected workouts.
- On the first sync, create the connection with `db.save_connection(user_id, "apple_health", access_token_enc=None, refresh_token_enc=None, token_expires_at=None, scopes="read")` (the token columns are nullable; the function signature stays as it is). Every successful sync calls `db.mark_connection_synced`, then `matching_runner.match_user` over the plan window (`_resolve_plan_window`) or the last 30 days. A matching failure is logged; the import still returns success.
- The endpoint takes `user_id` only from the session. It never accepts one in the body.

`DELETE /api/integrations/apple-health` calls `db.delete_provider_data(user_id, "apple_health")`, as COROS disconnect does.

`GET /api/integrations/status` gains `"apple_health": {"enabled", "connected", "last_sync_at"}`. `enabled` comes from a new `APPLE_HEALTH_ENABLED` setting (default `true`), so the iOS row can be hidden without a new build.

### Provider-neutral "measured" volume

Today `services/fitness_snapshot.py` reads only COROS (`PROVIDER = "coros"`), and `plan_generator.py:850` plus the snapshot's vert line trust only `weekly_km_source == "coros"`. Without a change, Health runs would match workouts but never set starting mileage.

- `fitness_snapshot.build` picks the connected device provider with the latest `last_sync_at` among `("coros", "apple_health")`. It uses that provider's connection for `last_sync_at` and its first activity for `first_activity_at`. Weekly sums already exclude `duplicate_of` rows, so a run seen through both providers counts once.
- `weekly_km_source` can be `"coros"`, `"apple_health"` or `"self_reported"`. The prompt label map gains `"apple_health": "Apple Health"`.
- `plan_generator.py` and the vert condition check "source is a device" (`in DEVICE_SOURCES`) instead of `== "coros"`.
- Threshold pace from a COROS assessment stays COROS-only.
- This changes a value inside the `plan_generation` prompt, not the template. Run `scripts/golden_eval.py compare --service plan` once; COROS users must show no difference.

### Schema

No new tables or columns. `activities`, `athlete_connections` and `daily_metrics` already fit, so there is no Alembic migration.

## iOS

### Capabilities

- Entitlements `com.apple.developer.healthkit` and `com.apple.developer.healthkit.background-delivery` in `UphillAI.entitlements` and `project.yml`.
- `NSHealthShareUsageDescription` in English and Vietnamese. A is read-only, so there is no update usage string.
- Read types: `HKWorkoutType`, `HKSeriesType.workoutRoute()`, heart rate, running distance, active energy.
- **Manual step (owner):** enable HealthKit on the `uphill.ai.app` App ID in the developer portal and regenerate the provisioning profile before the TestFlight build.

### `Core/Health/`

- **`HealthStoring`**: a protocol over `HKHealthStore` (request authorization, anchored workout query, per-workout statistics, route locations, observer and background delivery). `HealthKitStore` is the real implementation; tests use a fake.
- **`HealthWorkoutMapper`**: a pure function from a plain `HealthWorkoutSample` struct to the upload DTO.
  - `.running` → `outdoor_run`, or `indoor_run` when `HKMetadataKeyIndoorWorkout` is true. We don't guess `trail_run`: Health has no trail flag.
  - `.hiking` → `gps_cardio`
  - `.stairClimbing`, `.stairs` → `gym_cardio`
  - `.traditionalStrengthTraining`, `.functionalStrengthTraining` → `strength`
  - Distance: `statistics(for: distanceWalkingRunning).sumQuantity()`. HR: average and max from `statistics(for: heartRate)`. Calories: active energy sum.
  - Vert: `HKMetadataKeyElevationAscended` when present. Otherwise route altitudes, summing only climbs over a 3 m threshold so GPS noise doesn't inflate it. Otherwise nil.
  - The plan checks that `gps_cardio` and `gym_cardio` match hike and stair workouts in `services/matching`. If they don't, the plan adjusts the mapping rather than the matcher.
- **`AppleHealthSyncService`** (actor):
  - Runs an anchored query from the stored anchor. With no anchor, it reads from 12 weeks ago.
  - Uploads new workouts and deleted UUIDs in batches of up to 500.
  - **Saves the new anchor only after a 2xx response**, so a failed upload is retried and nothing is lost.
  - Stores the anchor per user id in UserDefaults (`UPHILL_HEALTH_ANCHOR_<userId>`). Sign-out and disconnect clear it.
  - Only one sync runs at a time; a second call while one is running waits for the first.
- **Background delivery:** while connected, register an `HKObserverQuery` and `enableBackgroundDelivery(for: .workoutType(), frequency: .immediate)` on every launch. The callback runs a sync and calls the completion handler either way.
- **Foreground safety net:** sync when `scenePhase` becomes `.active` (`RootView` already observes it). Skip it if the last sync was under 5 minutes ago.

### UI

- **Connected Accounts** (`ConnectedAccountsView`): an Apple Health row under COROS, hidden when `/status` says `enabled: false`.
  - **Connect** opens our explainer sheet first: what we read, why, that routes stay on the phone, and that we never write to Health in this version. Then the system permission sheet, then the first sync with a progress state.
  - **Connected:** "Last synced …", "Sync now" and "Disconnect". Disconnect confirms that data received from Apple Health will be deleted, calls `DELETE`, stops the observers and clears the anchor. The app can't revoke Health permission itself, so it links to Settings → Health.
  - **Silent denial:** HealthKit never reports a denied read. If the first sync finds no workouts in 12 weeks, the row shows "No workouts found. Check Settings → Health → Data Access & Devices → Uphill AI." instead of an error.
- **Onboarding watch step** (`WatchChannelsList`): Apple Health moves from `upcoming` to a live channel with its own Connect button, so the starting mileage can come from Health.
- **Matching:** `WatchMatchSheet` and the run cards are unchanged. Apple Health runs show `device_model` ("Apple Watch", "Garmin Connect").
- Every new string ships in English and Vietnamese (`uphill-ai-vietnamese-copy` skill).
- **Debug only:** the developer menu gets "Seed sample workouts", which saves three synthetic workouts (run, hike, strength) to the Simulator's Health store, because the Simulator has none.

## Privacy and App Review

- Uploaded fields are only those in the endpoint above. Routes and HR series stay on the device.
- Health data is not used for advertising, is not sent to analytics, and is not exported to Langfuse (`LANGFUSE_EXPORT_CONTENT=false`).
- App Store privacy labels add "Health & Fitness" (linked to the user, not used for tracking). The review notes explain the read-only use.
- **Blockers for the public App Store release (not for TestFlight):** the Phase 7 Privacy screen and policy describing Health use, and in-app account deletion (`DELETE /api/auth/account`).

## Errors

| Case | Behaviour |
|---|---|
| Offline or 5xx | Anchor not saved; the next background or foreground wake retries |
| 401 | Existing flow: session cleared; the anchor is cleared with it |
| Bad rows | Stored rows succeed; rejected rows are listed in `rejected` and logged by the app, not retried |
| Matching fails after store | Logged on the server; the sync still succeeds |
| Permission denied | Indistinguishable from "no workouts"; the row shows the Settings hint |

## Testing

- **Backend unit:**
  - validation and the `rejected` list
  - re-uploading the same batch is a no-op
  - `deleted_ids`
  - a COROS run and its Health copy produce one counted activity
  - `last_sync_at` is set
  - disconnect deletes the data
  - `fitness_snapshot` picks the freshest provider and labels the source
- **Integration tests:** only against a scratch database, never `uphill_ai`; they truncate every table.
- **Golden eval:** `plan_generation` compare after the provider-neutral change.
- **iOS (Swift Testing):**
  - a mapper table test for each type
  - vert from metadata, from the route, and with GPS noise
  - the sync service with a fake store and a fake API: anchor saved only on 2xx, 500-row batching, deletions forwarded, one sync at a time
  - DTO decoding against a fixture recorded from the local backend
- **Screenshots:** Simulator (iPhone 16, iOS 18): the explainer, Connected Accounts in its states (not connected, syncing, connected, nothing found), the onboarding watch step, and a matched Health run.
- **Device check:** a TestFlight build on a real iPhone and Apple Watch. Record a short run and confirm it appears and matches without opening the app (background delivery).

## Rollout

1. Backend (additive, no migration) deployed to prod; `APPLE_HEALTH_ENABLED=true`.
2. Enable HealthKit on the App ID; TestFlight build with A.
3. If App Review or a bug requires it, set `APPLE_HEALTH_ENABLED=false` to hide the row without a new build.

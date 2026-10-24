# Notification Content v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the notification settings with one switch, send coach-voiced content (purpose line, Monday brief, recognition, missed-session fix) at times we choose, and enforce a budget so it never nags.

**Architecture:** All selection stays in the pure `services/notification_rules.py` (context in, candidates out), all wording in `services/notification_copy.py`, persistence in `services/notification_store.py`. The worker (`services/notifications.py`) only gains one more context field. iOS shrinks the settings view and adds one notification category with a "Less like this" action.

**Tech Stack:** FastAPI + SQLAlchemy Core `text()`, Postgres, pytest; SwiftUI, Swift 6 strict concurrency, swift-testing, XcodeGen.

**Spec:** `docs/superpowers/specs/2026-10-24-notification-content-design.md`

## Global Constraints

- Branch from `main` **after PR #189 is merged** (Task 7 extends its `NotificationDelegateTests` and must keep its main-thread completion pattern).
- No LLM call anywhere in the notification path. Copy is fixed templates plus the athlete's own numbers.
- Every schema change goes in `notification_store.SCHEMA` (run by `init_db`) **and** a new hand-written Alembic revision whose `down_revision` is the output of `alembic heads` at the time (the db-migration skill).
- Budget: ≤1 proactive per local day (existing), ≤4 proactive in any rolling 7 days; `plan_ready` exempt from both.
- Quiet hours fixed 21:00–07:00, ignoring the stored `quiet_start`/`quiet_end`.
- Times: workout = usual start − 75 min, clamped to 06:00–20:00, fallback 07:00 (needs ≥4 activities in the weekday or weekend group over 28 days); `week_brief` Monday 07:30; `planning`, `unlogged`, `checklist`, `knowledge`, `taper`, `race` 18:00; `recognition` ≥30 min after activity start + duration, within 24 h.
- Back-off: 3 consecutive delivered (`status='accepted'`) but unopened (`opened_at IS NULL`) events of one coaching kind → skip that kind for 14 days. `workout` and `plan_ready` exempt.
- Mutable kinds (category `coaching`): `week_brief`, `recognition`, `unlogged`, `checklist`, `knowledge`, `taper`, `race`, `planning`. Not mutable (category `plain`): `workout`, `plan_ready`.
- Priority (lower wins): race 0, planning 1, unlogged 2, taper 3, recognition 4, week_brief 5, workout 6, checklist 7, knowledge 8.
- Copy is exactly the spec's EN/VI tables. VI follows `.claude/skills/uphill-ai-vietnamese-copy/SKILL.md`: no exclamation marks, banned-word grep clean.
- Retired kind: `recovery` (no new candidates; old rows stay).

## Review Focus

1. **Athlete with no synced activities at all** (manual ticks only): workout reminder at 07:00, no recognition, nothing crashes on empty lists. Test in Task 3.
2. **Plan without `race_name` or `course_elevation_gain_m`**: long-run and hill purpose lines fall back to "race day" wording, never "None" or "0 m". Test in Task 5.
3. **Usual start before 07:00 (05:30 runner)**: 05:30 − 75 min = 04:15 → clamp to 06:00, then quiet hours push it to 07:00, which is after the run. Expected: still send at 07:00 (the reminder is for today's session, late is better than never). Test in Task 3.
4. **Un-muting via PATCH must not let a client add kinds or arbitrary strings**: PATCH may only remove from `muted_kinds`; unknown values are rejected with 422. Test in Task 2.
5. **Old app builds (2026102402) after the backend ships**: they still PATCH `workout_time`, `quiet_start` etc. These must keep validating and simply be ignored for scheduling. Test in Task 2.

---

### Task 1: Rule timing (usual start, fixed slots, fixed quiet hours)

**Files:**
- Modify: `backend/services/notification_rules.py` (`candidate`, `delivery_window`, new `usual_start`)
- Modify: `backend/services/notifications.py` (`load_context`: add `activities`)
- Test: `backend/tests/unit/test_notification_rules.py`

**Interfaces:**
- Produces: `usual_start(activities: list[dict], timezone: str, weekend: bool) -> datetime.time | None` (median local start of activities in the last 28 days in that group; `None` below 4).
- Produces: `slot_time(context: dict, kind: str, day: date) -> datetime.time` implementing the Global Constraints times (workout uses `usual_start`; week_brief 07:30; others 18:00).
- Produces: `candidate(context, now, kind, key, destination, priority, source=None)` keeps its signature but takes its due time from `slot_time(context, kind, today)`.
- Produces: `QUIET = (time(21), time(7))`; `delivery_window(due, prefs, expires_at)` uses `QUIET`, not prefs.
- Produces: context key `activities`: rows `{id, start_time (aware UTC), duration_seconds, distance_km, elevation_gain_m, matched_workout_id}` for the user, `duplicate_of IS NULL`, either `start_time >= now − 28 days` or matched to a workout of the active plan.

- [ ] **Step 1: Write failing tests**

```python
def test_usual_start_needs_four_and_splits_weekend(): ...
    # 4 weekday runs at 06:00, 06:10, 06:20, 18:00 Sydney → time(6, 15); 3 weekend runs → None
def test_workout_slot_is_75_min_before_usual_start(): ...
    # usual 08:00 weekday → reminder due 06:45 local
def test_workout_slot_falls_back_to_0700_without_history(): ...   # Review Focus 1
def test_early_runner_clamps_then_quiet_hours_push_to_0700(): ...  # usual 05:30 → due 07:00 local, Review Focus 3
def test_week_brief_slot_is_0730_and_coaching_is_1800(): ...
def test_stored_quiet_hours_are_ignored(): ...
    # prefs quiet 23:00–05:00, due 22:00 local → window starts 07:00 next day
```

- [ ] **Step 2: Run** `cd backend && .venv/bin/pytest tests/unit/test_notification_rules.py -q`. Expected: the new tests FAIL (`usual_start` undefined).
- [ ] **Step 3: Implement** `usual_start`, `slot_time`, `QUIET`, and the `candidate`/`delivery_window` changes. In `load_context`, add one query on `activities` (the index `idx_activities_user_start` covers it) and pass `activities` into the context.
- [ ] **Step 4: Run** the full notification unit and integration tests. Expected: PASS. Update existing tests that asserted 07:00/18:00 from prefs only where they now take times from history.
- [ ] **Step 5: Commit** `feat(notifications): choose send times from activity history, fixed quiet hours`

### Task 2: Mutes, feedback endpoint, schema

**Files:**
- Modify: `backend/services/notification_store.py` (`SCHEMA`, `PREFERENCE_FIELDS`, new `mute_kind`)
- Create: `backend/alembic/versions/<new>_notification_muted_kinds.py`
- Modify: `backend/routers/notifications.py` (`PreferencesPatch.muted_kinds`, new `POST /{notification_id}/feedback`)
- Test: `backend/tests/integration/test_notification_api.py`

**Interfaces:**
- Produces: column `notification_preferences.muted_kinds TEXT[] NOT NULL DEFAULT '{}'`, returned by `GET /preferences` as a JSON list.
- Produces: `MUTABLE_KINDS = frozenset({"week_brief","recognition","unlogged","checklist","knowledge","taper","race","planning"})` in `notification_store`.
- Produces: `mute_kind(user_id: int, kind: str) -> None` (append if absent and in `MUTABLE_KINDS`).
- Produces: `POST /api/notifications/{id}/feedback`, body `{"less": true}` → 200 `{}`; 404 when the event isn't the caller's; mutes the event's `kind`; no-op for non-mutable kinds.

- [ ] **Step 1: Write failing tests**

```python
def test_feedback_mutes_the_events_kind(client, auth_headers): ...   # insert a week_brief event, POST feedback, GET prefs → muted_kinds == ["week_brief"]
def test_feedback_is_owner_checked(client, auth_headers): ...        # random uuid → 404
def test_patch_can_only_shrink_muted_kinds(client, auth_headers): ...  # Review Focus 4
    # muted ["week_brief"]; PATCH ["week_brief","knowledge"] → 422; PATCH ["bogus"] → 422; PATCH [] → 200, []
def test_old_build_time_fields_still_accepted(client, auth_headers): ...  # Review Focus 5: PATCH workout_time/quiet_start → 200
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/integration/test_notification_api.py -q` against the scratch DB (`uphill_ai_test`). Expected: new tests FAIL.
- [ ] **Step 3: Implement**: the `ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS muted_kinds TEXT[] NOT NULL DEFAULT '{}'` in `SCHEMA` and the migration; `muted_kinds: list[str] | None` on `PreferencesPatch`, validated as a subset of the stored list and of `MUTABLE_KINDS`; the feedback route mirroring `/opened`.
- [ ] **Step 4: Run** the notification integration tests and `alembic heads` (exactly one head). Expected: PASS, one head.
- [ ] **Step 5: Commit** `feat(notifications): per-kind mute with feedback endpoint`

### Task 3: Budget (weekly cap, back-off, mute filter)

**Files:**
- Modify: `backend/services/notification_rules.py` (`candidates`)
- Modify: `backend/services/notification_store.py` (`claim_event`)
- Test: `backend/tests/unit/test_notification_rules.py`, `backend/tests/integration/test_notification_worker.py`

**Interfaces:**
- Consumes: `MUTABLE_KINDS`, `muted_kinds` (Task 2); `context["history"]` rows (already loaded: `kind, status, claimed_at, opened_at`).
- Produces: `backed_off(history: list[dict], kind: str, now: datetime) -> bool` (Global Constraints rule).
- Produces: `candidates()` drops muted and backed-off kinds. `claim_event()` refuses a proactive claim when 4 proactive events have `claimed_at` within the past 7 days.

- [ ] **Step 1: Write failing tests**

```python
def test_muted_kind_is_never_a_candidate(): ...
def test_three_unopened_week_briefs_back_off_for_14_days(): ...   # 15 days later → allowed again
def test_unopened_workout_reminders_never_back_off(): ...
def test_one_opened_in_the_last_three_resets_back_off(): ...
def test_fifth_proactive_in_seven_days_is_refused(auth_headers): ...   # integration, claim_event
def test_plan_ready_ignores_weekly_cap(auth_headers): ...              # integration
def test_rules_with_no_activities_and_no_history(): ...                # Review Focus 1: candidates() returns workout only, no exception
```

- [ ] **Step 2: Run** the two test files. Expected: new tests FAIL.
- [ ] **Step 3: Implement** `backed_off` and the filters in `candidates`; the 7-day count inside `claim_event`'s existing locked transaction, next to the daily check.
- [ ] **Step 4: Run** all notification tests. Expected: PASS.
- [ ] **Step 5: Commit** `feat(notifications): weekly cap, back-off and mute in selection`

### Task 4: New kinds (week_brief, recognition; retire recovery; missed → adapt)

**Files:**
- Modify: `backend/services/notification_rules.py` (`coaching_candidates`, new `week_brief_candidate`, `recognition_candidates`)
- Test: `backend/tests/unit/test_notification_coaching.py`

**Interfaces:**
- Consumes: `context["activities"]` (Task 1), `slot_time` (Task 1).
- Produces candidates:
  - `week_brief`: Mondays only, when the current plan week has ≥1 actionable workout. Key `week_brief:{plan_id}:{week}`. Destination `{"kind":"plan","plan_id":…,"week_number":…,"intent":"week"}`. Source `{"week_number": n}`.
  - `recognition`: for a done workout that `is_priority` or has type `Long Run`, with an activity matched to it whose end (`start_time + duration_seconds`) is within 24 h. Due = max(slot, end + 30 min). Key `recognition:{workout_id}`. Destination `{"kind":"workout",…}`. Source `{"workout_id":…, "activity_id":…}`.
  - `unlogged` destination becomes `{"kind":"plan","plan_id":…,"week_number":…,"intent":"adapt"}`, source `{"workout_id": <most important missed>}` (priority first, then longest).
  - Monday with both workout and week_brief eligible: only `week_brief` is returned.
  - No `recovery` candidates.
  - `checklist` waits 30 days after the last one (was 14, in `content_candidates`).

- [ ] **Step 1: Write failing tests**

```python
def test_week_brief_only_on_monday_with_workouts(): ...
def test_monday_brief_replaces_workout_reminder(): ...
def test_recognition_requires_matched_activity(): ...       # manual tick (no activity) → none
def test_recognition_due_30_min_after_activity_end(): ...
def test_recognition_expires_24h_after_activity_end(): ...
def test_unlogged_names_the_priority_session_and_opens_adapt(): ...
def test_recovery_is_retired(): ...
def test_checklist_waits_30_days(): ...                     # claimed 20 days ago → none; 31 days → allowed
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/unit/test_notification_coaching.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the candidates with the priorities from Global Constraints. Week boundaries come from `dated_workouts` (existing).
- [ ] **Step 4: Run** all notification tests. Expected: PASS.
- [ ] **Step 5: Commit** `feat(notifications): Monday brief, recognition, missed session opens adapt`

### Task 5: Copy

**Files:**
- Modify: `backend/services/notification_copy.py`
- Test: `backend/tests/unit/test_notification_copy.py` (create)

**Interfaces:**
- Consumes: candidate `kind`, `source`, `context` (plan has `race_name`, `course_elevation_gain_m`, `total_weeks`; workouts have `type`, `phase`, `title`, `duration_minutes`, `target_zone`, `distance_km`, `day_of_week`, `is_priority`).
- Produces: `render_notification(candidate, context) -> tuple[str, str]` (signature unchanged), covering every kind with the spec's exact EN/VI strings. Purpose lookup is a module-level table `PURPOSE: dict[str, tuple[str, str]]` keyed by family (`taper, easy, long, quality, hill, strength`), so the review is one diff.
- Highlight for recognition: compare the matched activity against all activities matched to this plan's workouts: most `elevation_gain_m` → "biggest climb" line; else most `distance_km` → "longest run" line; ties count as most.

- [ ] **Step 1: Write failing tests**

```python
def test_long_run_purpose_names_the_race(): ...
    # race_name "UTMB 100K" → body endswith "Time on feet for UTMB 100K. Easy is the point."
def test_missing_race_and_d_plus_fall_back_to_race_day(): ...   # Review Focus 2: no "None", no "0 m"
def test_taper_phase_overrides_session_purpose(): ...
def test_week_brief_title_and_today_suffix_en_vi(): ...
    # "Week 6 of 16: Build" / "Tuần 6/16: Build"; Monday workout → body endswith "Today: Easy Run, 45 min."
def test_recognition_highlight_only_when_true(): ...
def test_every_kind_renders_with_optional_values_missing(): ...   # parametrize over kinds × en/vi
def test_vi_copy_has_no_banned_words_or_exclamation_marks(): ...  # scan PURPOSE and all templates
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/unit/test_notification_copy.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the templates exactly as in the spec tables (A–E). VI weekday names: Thứ Hai … Chủ Nhật. Hours rounded to 0.5 h; durations as `2h41` or `45 min` / `45 phút`.
- [ ] **Step 4: Run** all notification tests. Expected: PASS.
- [ ] **Step 5: Commit** `feat(notifications): coach-voiced EN/VI copy`

### Task 6: APNs category

**Files:**
- Modify: `backend/services/apns.py` (`build_payload`)
- Test: `backend/tests/unit/test_apns.py`

**Interfaces:**
- Consumes: `MUTABLE_KINDS` (Task 2).
- Produces: `payload["aps"]["category"] == "coaching"` for mutable kinds, `"plain"` otherwise.

- [ ] **Step 1: Write failing test** `test_category_marks_mutable_kinds`: a `week_brief` event → `coaching`; `workout` → `plain`.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/unit/test_apns.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the category field. The 4 KB trimming loop is unchanged.
- [ ] **Step 4: Run** the full backend suite `.venv/bin/pytest -q -p no:warnings`. Expected: PASS (scratch DB).
- [ ] **Step 5: Commit** `feat(notifications): APNs category for mutable kinds`

### Task 7: iOS: one switch, muted list, "Less like this"

**Files:**
- Modify: `ios-native/UphillAI/Core/Notifications/NotificationModels.swift` (`mutedKinds: [String]?`; route `intent == "adapt"`)
- Modify: `ios-native/UphillAI/Core/Notifications/NotificationService.swift` (`feedback(id:)`; keep stripping read-only `available`)
- Modify: `ios-native/UphillAI/Core/Notifications/NotificationCoordinator.swift` (`setEnabled(_:)`, `unmute(_:)`, `lessLikeThis(id:)`, register category at init)
- Modify: `ios-native/UphillAI/App/NotificationAppDelegate.swift` (handle action `LESS`)
- Modify: `ios-native/UphillAI/Features/Me/NotificationSettingsView.swift` (rewrite to the spec layout)
- Modify: `ios-native/UphillAI/Features/Plan/PlanView.swift` (`intent == "adapt"` opens the existing Adapt week flow from Manage)
- Modify: `ios-native/UphillAI/Resources/Localizable.xcstrings` (spec strings; remove retired time, units and quiet-hour labels)
- Test: `ios-native/UphillAITests/Notifications/NotificationDelegateTests.swift`, `NotificationServiceTests.swift`

**Interfaces:**
- Consumes: `POST /api/notifications/{id}/feedback` (Task 2), `aps.category` (Task 6), `muted_kinds` in preferences (Task 2).
- Produces: `UNNotificationCategory(identifier: "coaching", actions: [UNNotificationAction(identifier: "LESS", title: L("Less like this"), options: [])])` plus an empty `"plain"` category, registered in `NotificationCoordinator.init`.
- Produces: `setEnabled(_ on: Bool) async` writes `workoutsEnabled = coachingEnabled = resultsEnabled = on` (asking permission when turning on).
- Kind display names (EN → VI) from the spec table, keyed by kind.

- [ ] **Step 1: Write failing tests**

```swift
@Test func lessLikeThisPostsFeedbackAndCompletesOnMain() throws   // action "LESS" → service.feedback called once; completion on main thread before return
@Test func switchWritesAllThreeCategories() async                 // setEnabled(true) → PATCH body has all three true
@Test func unmuteSendsShrunkList() async                          // muted ["week_brief","knowledge"], unmute("knowledge") → PATCH muted_kinds ["week_brief"]
@Test func adaptIntentRouteIsValid()                              // {"kind":"plan","plan_id":1,"week_number":2,"intent":"adapt"} parses
```

- [ ] **Step 2: Run** `xcodebuild … test -only-testing:UphillAITests/NotificationDelegateTests -only-testing:UphillAITests/NotificationServiceTests -only-testing:UphillAITests/NotificationRoutingTests` (simulator, `CODE_SIGNING_ALLOWED=NO`). Expected: FAIL.
- [ ] **Step 3: Implement.** The action handler stays synchronous on the main actor: start a `Task` for the network call and call `completionHandler()` before returning (the PR #189 rule). The settings view uses existing `Form` components only.
- [ ] **Step 4: Run** the full `UphillAITests` suite. Expected: PASS except `KeychainTokenStoreTests` (fails on unsigned builds on main too).
- [ ] **Step 5: Screenshot** the settings screen in EN and VI on the simulator (ui-screenshot-evidence skill), with the muted list showing one item. Check that nothing truncates.
- [ ] **Step 6: Commit** `feat(ios): one notification switch, muted list, Less like this`

### Task 8: Ship

**Files:**
- Modify: `docs/ios-notifications-operations.md` (Ship plan: one line on v2)

- [ ] **Step 1:** Open the PR with the spec link and the Review Focus list, and wait for green CI.
- [ ] **Step 2:** After merge, deploy main with `deploy_main_prod.sh` (dry run, then `--go`). Confirm `alembic current` shows the new head and `muted_kinds` exists.
- [ ] **Step 3:** Archive TestFlight build `2026102403` or later. On user 5's phone: switch on/off, long-press "Less like this" mutes and the muted list shows it, Monday 07:30 brief opens the week, and the reminder time follows history.
- [ ] **Step 4:** Commit the docs line; record the build and deploy in memory.

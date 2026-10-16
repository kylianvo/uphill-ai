# Native iOS Coaching Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver all eight approved coaching notification cases plus requested-plan completion, with accurate eligibility, secure native navigation and bounded delivery.

**Architecture:** The existing FastAPI process runs a notification worker backed by Postgres, following the race-history worker pattern. Deterministic rules select a single proactive message and a small APNs transport delivers it. Native SwiftUI owns permission, installation registration, preferences and exact destination routing.

**Tech Stack:** Python/FastAPI, SQLAlchemy Core/Postgres/Alembic, HTTPX HTTP/2, existing PyJWT/cryptography, Swift 6/SwiftUI/UserNotifications, pytest, Swift Testing, XcodeGen.

**Spec:** `docs/superpowers/specs/2026-10-16-ios-notifications-design.md` (approved in chat after commit `e8fae1d`). Read the entire spec before executing.

## Global Constraints

- "One proactive notification per account per local date. Also require 20 hours between proactive sends to prevent rapid duplicates after timezone changes."
- "Requested-result notifications are separate and capped at three per local day; further results remain visible in the app."
- "Use a 60-minute delivery window after a proactive notification's chosen time."
- "Default to no sends until the athlete explicitly enables notifications and the device grants authorization."
- "No notifications while paused, including results."
- "For the first version send to one installation: the most recently active, authorized installation."
- "Explicit retryable APNs responses use delays of 1, 5 and 15 minutes, bounded by expiry, maximum three retries."
- "A worker crash while sending leaves an ambiguous result; mark unknown and do not resend."
- "No Redis, Celery, Firebase, campaign platform, LLM call per notification, generic rules engine, notification inbox, silent-push dependency, or local fallback scheduler."
- "English and Vietnamese copy uses reviewed templates and existing vocabulary conventions."
- "APNs acceptance is not a display receipt."
- "All four slices are required to fulfill the approved feature scope."
- Native iOS only. Keep existing Google/COROS callbacks, coach approval and workout matching semantics. No frontend/Capacitor changes.
- Use the repository Vietnamese-copy skill when writing implementation copy. Do not invent medical advice: reviewed existing knowledge content only.
- Integration tests truncate tables: use only a database whose name contains `test` or `scratch`; never production.
- This document authorizes no deployment or sends. Development stays delivery-disabled until the real-device verification step is explicitly arranged with the user.

## Review Focus

1. A token rotates or an installation changes accounts while an event is claimed: revalidate ownership and never deliver the former account's data (Tasks 2, 5, 7).
2. A coach is viewing another athlete when tapping their own push: restore own context before resolving the route (Task 7).
3. DST gaps/overlaps and travel between dates: no skipped valid scheduling window or second daily send (Tasks 3, 5).
4. A bundled and server knowledge card share ID 1: a server notification must never fall back to bundled ID 1 (Task 10).
5. A worker crashes after APNs acceptance but before DB acknowledgment: mark unknown, consume allowance, never blindly resend (Task 5).

## Execution and scope map

This is one subsystem with shared delivery state, not independent projects. Execute sequentially; do not split database contracts across parallel implementers. Recommended handoff: Native execution, followed by a fresh whole-branch review. Do not start implementation until the user reviews this plan and chooses the method.

At execution start inspect worktree attachments and status; reuse this suitable isolated checkout. Read applicable repository instructions. Baseline only the tests for the first affected area, record unrelated failures, and never erase user edits. Resolve the current Alembic head before authoring the migration; do not assume filename sorting identifies it.

File responsibilities:

| Unit | Files |
| --- | --- |
| Schema and existing mutation boundaries | `backend/db.py`; new `backend/alembic/versions/a6f2c8d9e104_notifications.py`; existing matching/generation writers |
| Notification SQL | new `backend/services/notification_store.py` |
| Pure scheduling and selection | new `backend/services/notification_rules.py` |
| Reviewed templates | new `backend/services/notification_copy.py` |
| Delivery transport | new `backend/services/apns.py` |
| Evaluation and worker lifecycle | new `backend/services/notifications.py`; `backend/main.py`, `backend/config.py`, `backend/telemetry.py` |
| Authenticated HTTP surface | new `backend/routers/notifications.py` |
| Swift models/API | new `ios-native/UphillAI/Core/Notifications/NotificationModels.swift`, `NotificationService.swift` |
| Native lifecycle/routing | new `ios-native/UphillAI/Core/Notifications/NotificationCoordinator.swift`, `ios-native/UphillAI/App/NotificationAppDelegate.swift`; existing AppModel/RootView/UphillAIApp/PlanView |
| Preferences | new `ios-native/UphillAI/Features/Me/NotificationSettingsView.swift`; existing ProfileView and SharpenChecklistCard |
| Knowledge | existing KnowledgeService/KnowledgeHubScreen/KnowledgeCard; new `Features/Knowledge/KnowledgeDetailScreen.swift` |
| Deployment instructions | new `docs/operations/ios-notifications.md`; existing native project.yml/entitlements and backend requirements |

Backend commands below run with `workdir=backend` and the repository Python environment. iOS commands run from repository root via `ios-native/scripts/test.sh`; it selects an available simulator and regenerates the Xcode project. Each task uses its listed test file/suite for red and green cycles. Existing tests are expanded where their contracts change.

## Shared contracts

Use existing dictionaries/SQL rows rather than introducing a domain framework. New pure helpers accept aware UTC `datetime` arguments; no hidden wall clock in rule tests.

```python
# notification_rules.py
# Candidate dictionaries have exactly these required keys:
# event_key:str, kind:str, destination:dict, due_at:datetime,
# expires_at:datetime, priority:int, source:dict.
# Context uses: user, preferences, plan, workouts, matches,
# requests, connections, checklist, cards, history (existing rows/list values).
def is_done(workout: dict) -> bool:
    matched = workout.get('matched_activity_id') is not None or (workout.get('matched_distance_km') or 0) > 0
    return workout.get('is_completed') == 1 or (workout.get('is_completed') != 0 and matched)
```

Wire payload: `{"v":1,"notification_id":"UUID","destination":{"kind":"workout","plan_id":123,"workout_id":456}}`. Other supported kinds: `plan` (plan_id and optional week_number/block_number), `checklist` (item_id), `knowledge` (card_id, lang, namespace=`server`), `review` (plan_id, week_number). APNs adds `aps.alert.title/body`; no credentials or arbitrary executable URL.

Preference keys: `workouts_enabled`, `coaching_enabled`, `results_enabled`, `workout_time`, `coaching_time`, `quiet_start`, `quiet_end`, `timezone`, `language`, `distance_unit`, `paused_until`, `checklist_snoozed_until`. Times are `HH:MM`, language `en|vi`, distance `km|mi`, dates ISO 8601. All enabled flags default false. Suggested times are 07:00/18:00/21:00/07:00. Missing timezone prevents scheduled sends. Reject equal quiet-start/end instead of silently interpreting a 24-hour quiet window.

---

### Task 1: Persistent notification state

**Files:** Modify `backend/db.py`, `backend/tests/integration/conftest.py`, `backend/tests/conftest.py`; create the migration above, `backend/services/notification_store.py`, `backend/tests/integration/test_notification_store.py`.

**Interfaces:** Produce `get_preferences(user_id:int)->dict`, `update_preferences(user_id:int, values:dict)->dict`, `insert_event(conn, user_id:int, candidate:dict)->str` in notification_store. `insert_event` uses the caller's transaction and returns the existing UUID on conflict.

- [ ] Add a schema test using existing `client`/`auth_headers` fixtures:

```python
def test_preferences_default_off(auth_headers):
    from services.notification_store import get_preferences
    p = get_preferences(auth_headers['user_id'])
    assert not any(p[k] for k in ('workouts_enabled','coaching_enabled','results_enabled'))
    assert p['timezone'] is None
```

- [ ] Run `python -m pytest tests/integration/test_notification_store.py -q`; expect missing module/schema failure before implementation.
- [ ] Implement five tables in both init_db and the Alembic revision: installations, preferences, events, knowledge opens, notification generation requests, and no separate tombstone table (retain minimal terminal event rows). Events need UUID PK; `(user_id,event_key)` unique; timestamps due/expiry/claim/accepted/opened/next-attempt; status check; destination/source JSONB; installation ID; attempts; result code and suppression reason. Index pending state/next-attempt and user/history. Requests have request UUID, actor/recipient, plan/coverage, status, updated_at and result reference. Opens use `(user_id,card_id,lang)` uniqueness. Every user FK cascades; source deletion must not cascade away a deduplication event prematurely. Preferences hold last proactive timestamp/date, result-day/count and indexed next_evaluation_at for bounded worker selection. Installations have UUID, token, environment, permission, last_active_at, disabled_at, registration_revision and user binding; unique token/environment. Increment registration_revision on token or account changes; claims record that revision so an old APNs error cannot disable a newly rotated token. Include nullable workouts.missed_origin and workouts.first_completed_at, and knowledge_cards.notification_reviewed default false, in this initial schema revision; Tasks 8 and 10 add their behavior.

```sql
INSERT INTO notification_preferences (user_id) VALUES (:user_id)
ON CONFLICT (user_id) DO NOTHING;
-- insert_event must execute on the supplied connection, never commit it.
INSERT INTO notification_events
    (id,user_id,event_key,kind,destination,source,due_at,expires_at,status)
VALUES (:id,:user_id,:event_key,:kind,:destination,:source,:due_at,:expires_at,'pending')
ON CONFLICT (user_id,event_key) DO UPDATE SET event_key=EXCLUDED.event_key
RETURNING id;
```

- [ ] Add/run tests for duplicate keys, caller rollback, FK account cleanup, old-schema upgrade and repeated init_db. Add new tables to scratch truncation and set `NOTIFICATION_WORKER_ENABLED=false` in root test conftest. Validate migration on scratch only with `python -m alembic heads` then upgrade to the new head; preserve existing branch topology.
- [ ] Commit only this task's files: `git commit -m "feat: persist notification preferences and outbox"`.

### Task 2: Authenticated preferences and installation API

**Files:** Create `backend/routers/notifications.py`, `backend/tests/integration/test_notification_api.py`; modify notification_store, `backend/main.py`, `backend/config.py`.

**Interfaces:** Produce `upsert_installation(user_id:int, installation_id:str, token:str, environment:str, permission:str, now:datetime)->dict`, `remove_installation(user_id:int, installation_id:str)->None`; routes GET/PATCH `/api/notifications/preferences`, PUT/DELETE `/api/notifications/installations/{installation_id}`, POST `/api/notifications/{notification_id}/opened`. Own-account only. Environment limited to sandbox/production and deployment allowlist; bundle topic is server configuration, never client input.

- [ ] Write API tests:

```python
def test_invalid_timezone_rejected(client, auth_headers):
    r = client.patch('/api/notifications/preferences', headers=auth_headers['headers'],
                     json={'timezone':'Not/AZone'})
    assert r.status_code == 422

def test_registration_requires_login(client):
    assert client.put('/api/notifications/installations/00000000-0000-0000-0000-000000000001',
                      json={'token':'a'*64,'environment':'sandbox','permission':'authorized'}).status_code == 401
```

- [ ] Run `python -m pytest tests/integration/test_notification_api.py -q`; expect 404/missing routes before changes.
- [ ] Use Pydantic models with forbidden extra fields and explicit token/UUID/time/locale limits. Validate timezone with `ZoneInfo`. Follow existing integration router authentication using `verify_session`; avoid a circular import of main. Bind account from auth, not payload. Token rebinding must invalidate old-owner unsent claims in the same transaction. Acknowledgment updates only an owned event using `COALESCE(opened_at,:now)`; missing/foreign event returns 404. Installation delete is idempotent and ownership checked.

```python
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def validate_timezone(value: str | None) -> str | None:
    if value is not None:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError('Invalid timezone') from exc
    return value
```

- [ ] Add/run ownership, invalid token, token rotation, rebinding, unauthorized preference fields, locale/units, equal quiet bounds, idempotent open and pause tests. Never return token values from preferences or logging.
- [ ] Commit: `git commit -m "feat: add authenticated notification controls"`.

### Task 3: Workout eligibility and local-time scheduling

**Files:** Create `backend/services/notification_rules.py`, `backend/services/notification_copy.py`, `backend/tests/unit/test_notification_rules.py`; later tasks extend these files.

**Interfaces:** Produce `local_due(day:date, wall_time:time, timezone:str)->datetime`, `delivery_window(due:datetime, prefs:dict, expires_at:datetime)->tuple[datetime,datetime]|None`, `workout_candidate(context:dict, now:datetime)->dict|None`, `choose_candidate(candidates:list[dict], now:datetime)->dict|None`; `render_notification(candidate:dict, context:dict)->tuple[str,str]` in notification_copy. Use shared is_done contract above.

- [ ] Add completion and DST tests:

```python
from datetime import date, time
from services.notification_rules import is_done, local_due

def test_explicit_incomplete_overrides_match():
    assert not is_done({'is_completed':0,'matched_activity_id':7})
    assert is_done({'is_completed':None,'matched_activity_id':7})

def test_sydney_dst_gap_advances_to_first_valid_minute():
    value = local_due(date(2026,10,4), time(2,30), 'Australia/Sydney')
    assert value.isoformat() == '2026-10-03T16:00:00+00:00'
```

- [ ] Run `python -m pytest tests/unit/test_notification_rules.py -q`; expect import failure.
- [ ] Implement calendar resolution by reusing workout_calendar helpers; filter active/approved, non-rest, not done/missed, local-today workouts. Choose priority then AM/PM then ID; no precise start-time inference. Resolve local times by testing fold=0/1 UTC round trips; select earliest valid instant, advancing minute-by-minute through a gap. Quiet hours spanning midnight shift to quiet_end only within expiry. A due window is `[due, min(due+60 minutes, expiry))`. Stable event key uses user/workout/local-date. Choose eligible candidates by priority then event_key; never a future candidate.

```python
eligible = [c for c in candidates if c['due_at'] <= now < c['expires_at']]
return min(eligible, key=lambda c: (c['priority'], c['event_key']), default=None)
```

- [ ] Expand tests for missing timezone/date, DST overlap, quiet boundaries, no workout/rest/draft, changed plan/date, doubles, absent distance, units and missing target zone. Add reviewed EN/VI templates under the Vietnamese-copy skill; test selected numeric values without asserting incidental punctuation.
- [ ] Commit: `git commit -m "feat: select current workout reminders in athlete timezone"`.

### Task 4: Direct APNs transport

**Files:** Create `backend/services/apns.py`, `backend/tests/unit/test_apns.py`; modify config and `backend/requirements.txt` (`httpx` to `httpx[http2]`).

**Interfaces:** Produce `classify_response(status:int, reason:str|None)->str` returning accepted/retryable/invalid_token/configuration_error/permanent_failure; `send_notification(installation:dict, event:dict, title:str, body:str)->dict` returning outcome/apns_id/reason. Transport exceptions with uncertain acceptance return unknown. Configure APNS_KEY_ID, APNS_TEAM_ID, APNS_PRIVATE_KEY_PATH, APNS_TOPIC and allowed environments; never put private keys in fixtures.

- [ ] Add response tests:

```python
from services.apns import classify_response

def test_response_classes():
    assert classify_response(200,None) == 'accepted'
    assert classify_response(410,'Unregistered') == 'invalid_token'
    assert classify_response(429,'TooManyRequests') == 'retryable'
    assert classify_response(403,'InvalidProviderToken') == 'configuration_error'
```

- [ ] Run `python -m pytest tests/unit/test_apns.py -q`; expect missing transport failure.
- [ ] Use HTTPX HTTP/2, existing ES256 PyJWT signing, bounded connection/read timeout and cached signing token refreshed before one hour. Send to fixed Apple sandbox/production hosts, `/3/device/{token}`, topic from trusted config, push-type alert, expiration from event, stable event UUID apns-id and a <=64-byte hashed collapse ID. Sanitize 4 KB payload length by truncating body safely, never IDs; reject an oversized fixed payload. Catch uncertain network outcomes as unknown.

```python
headers = {'apns-push-type':'alert', 'apns-topic':settings.APNS_TOPIC,
           'apns-id':str(event['id']),
           'apns-expiration':str(int(event['expires_at'].timestamp()))}
# Authorization is added from the ES256 token, never logged.
```

- [ ] Mock HTTP transport; verify sandbox/production host, expiry, Unicode payload size, expired JWT refresh, HTTP 500/503 retries, invalid credentials, malformed response and timeout. Assert logs contain neither token nor payload. No real APNs call.
- [ ] Commit: `git commit -m "feat: deliver native alerts through APNs"`.

### Task 5: Atomic selection, worker and delivery lifecycle

**Files:** Create `backend/services/notifications.py`, `backend/tests/integration/test_notification_worker.py`; modify notification_store, main startup/shutdown, config and telemetry.

**Interfaces:** Produce `load_context(user_id:int, now:datetime)->dict`, `claim_event(user_id:int, candidate:dict, now:datetime)->dict|None`, `record_delivery(event_id:str, result:dict, now:datetime)->None`, `run_once(now:datetime)->int`, `run_worker(stop_event)->None`. Worker imports APNs send function so tests can replace it. Use existing schema joins for matches and active plans, never the network to query activity state. Context history contains prior event timestamps, knowledge opens and last proactive reservation; unknown connection freshness must not be fabricated.

- [ ] Add an integration test with two threads calling claim_event for different proactive candidates at the same instant; insert an opted-in preference and authorized installation using Task 2 helpers, use candidate shape from Shared contracts, and assert only one result is non-null. Add restart recovery test by inserting a sending row and invoking run_once with mocked APNs.

```python
# Core assertion after the two concurrent claims:
assert sum(result is not None for result in results) == 1
# Core crash-recovery assertion:
assert recovered['status'] == 'unknown'
assert sends == []
```

- [ ] Run `python -m pytest tests/integration/test_notification_worker.py -q`; expect missing claim/worker behavior.
- [ ] Lock preferences row with `SELECT ... FOR UPDATE`; recheck categories/pause, latest authorized installation, local-date allowance, 20-hour spacing or result count, unique key and window. Insert/claim event and reserve allowance in that transaction. Release before network I/O. Recheck current eligibility and installation ownership immediately before send. Ineligible claims become suppressed; allowance stays consumed. A global evaluator advisory lock guards run_once; acquire it before marking stale sending rows unknown so another live worker is not mistaken for a crash. Use 60-second interruptible stop_event.wait. Register independently of the race-worker flag (its current early return must not bypass this worker).

```python
if not settings.NOTIFICATION_WORKER_ENABLED:
    return 0
# run_once obtains the session advisory lock; finally releases it.
# Retry schedule after explicit APNs rejection:
retry_delays = (60, 300, 900)
```

- [ ] Test timezone travel, three-result cap, rest-day coaching time, no replay after downtime, claim rollback, newest installation only, stale token/account binding, kill switch, global pause, safe retry completion recheck, invalid-token response after token rotation (disable only the claimed registration revision), unknown timeout, worker shutdown and credential failure circuit. Add bounded batch selection (100 due accounts per tick ordered by notification_preferences.next_evaluation_at, not an unbounded full-account scan; advance this timestamp to the next window or retry, and invalidate it on relevant preference, plan, workout and generation changes). Track pending age, heartbeat, outcomes and low-cardinality suppression reasons with existing metrics conventions.
- [ ] Commit: `git commit -m "feat: run durable notification delivery worker"`.

### Task 6: Native permission, settings and registration

**Files:** Create NotificationModels/NotificationService/NotificationCoordinator, NotificationAppDelegate, NotificationSettingsView from file map; modify `App/UphillAIApp.swift`, `App/AppModel.swift`, `App/RootView.swift`, `Features/Me/ProfileView.swift`, `Resources/Localizable.xcstrings`, `ios-native/project.yml`, `ios-native/UphillAI/UphillAI.entitlements`; create `ios-native/UphillAITests/Notifications/NotificationSettingsTests.swift`, `NotificationServiceTests.swift` and `Support/FakeNotificationService.swift`.

**Interfaces:** `NotificationPreferences: Codable, Sendable` mirrors shared keys with JSONCoding snake-case mapping. `NotificationServicing` methods: `preferences() async throws -> NotificationPreferences`, `updatePreferences(_ value: NotificationPreferences) async throws -> NotificationPreferences`, `registerInstallation(id:UUID,token:String,permission:String) async throws`, `removeInstallation(id:UUID) async throws`, `opened(id:UUID) async throws`. Service uses existing APIClient. Coordinator is @MainActor @Observable, owns preferences, registration and permission status; UIApplicationDelegate forwards token callbacks to it.

- [ ] Add a decoding contract test and fake service recording requests:

```swift
@Test func preferencesStartDisabled() throws {
    let data = Data(#"{"workouts_enabled":false,"coaching_enabled":false,"results_enabled":false,"workout_time":"07:00","coaching_time":"18:00","quiet_start":"21:00","quiet_end":"07:00","timezone":null,"language":"en","distance_unit":"km"}"#.utf8)
    let value = try JSONCoding.decoder.decode(NotificationPreferences.self, from: data)
    #expect(!value.workoutsEnabled && !value.coachingEnabled && !value.resultsEnabled)
}
```

- [ ] Run `ios-native/scripts/test.sh -only-testing:UphillAITests/NotificationSettingsTests`; expect missing model failure.
- [ ] Add settings using existing UH controls/styles. Prompt only after an explicit enable action, request alert/sound, register with APNs when granted, and retain disabled state after denial. Show a Settings link for denied permission. Use an installation UUID persisted on this device, not a user ID. Encode token bytes with `map { String(format: "%02x", $0) }.joined()`. Detect timezone/locale/units/permission changes on foreground; avoid an API update when nothing changed. Configure APNs entitlement through project.yml with correct development/production signing; preserve HealthKit/Apple Sign In. No background-notification mode is needed.
- [ ] Add/run tests for denial, failed preference save, settings cache per account, token rotation, foreground refresh, pause, offline settings error and no permission prompt on launch. Run NotificationServiceTests against StubURLProtocol to verify exact paths and owned requests. Ensure accessibility labels, Dynamic Type and EN/VI copy.
- [ ] Commit: `git commit -m "feat: add native notification opt-in and settings"`.

### Task 7: Safe notification navigation and logout

**Files:** Extend NotificationModels/Coordinator/AppDelegate, AppModel/RootView and `Features/Plan/PlanView.swift`, `Features/Plan/PlanViewModel.swift`; create `ios-native/UphillAITests/Notifications/NotificationRoutingTests.swift`; update affected fake services only if their interfaces change.

**Interfaces:** Add `NotificationRoute: Equatable, Sendable` with cases workout(planID:Int,workoutID:Int), plan(planID:Int,week:Int?,block:Int?), checklist(itemID:String), knowledge(cardID:Int,lang:String), review(planID:Int,week:Int). `init?(payload:[AnyHashable:Any])` validates v=1 and server namespace. Coordinator exposes `receive(payload:)`, one `pendingRoute`, and `resumePendingRoute() async`. Expose a minimal one-shot workout/plan presentation request in PlanViewModel rather than a second navigation stack.

- [ ] Add parser and login/context tests:

```swift
@Test func refusesUnknownPayloadVersion() {
    #expect(NotificationRoute(payload: ["v":99,"destination":["kind":"plan","plan_id":1]]) == nil)
}
@Test func serverKnowledgeRequiresNamespace() {
    #expect(NotificationRoute(payload: ["v":1,"destination":["kind":"knowledge","card_id":1,"lang":"en"]]) == nil)
}
```

- [ ] Run `ios-native/scripts/test.sh -only-testing:UphillAITests/NotificationRoutingTests`; expect missing route failure.
- [ ] Parse payload, wait for restored session, exit actingAsAthlete, fetch own authorized target and select proper tab. Reuse PlanView's WorkoutDetailSheet/WeekReviewSheet/NextWeekSheet/GoalSheet presentation. Checklist maps existing IDs to TrainingDestination. Queue at most the latest tap while login/another sheet is active; consume after the target opens. Do not switch active plan as a side effect merely to read an old result: fetch a read-only authorized snapshot, or give unavailable/current-plan fallback. Record opened idempotently after destination display. Suppress foreground banner only when that exact destination is visible.

```swift
// Preserve callback handling; push routing is a separate delegate path.
if GIDSignIn.sharedInstance.handle(url) { return }
Task { await app.handleOpenURL(url) }
```

- [ ] Test cold launch, signed-out tap, permission revoked, different account, coaching context, deleted/replaced target, fetch failure/retry and sheet collision. On logout unregister while credentials remain available, clear local notifications/pending routes and account caches. If offline, preserve a cleanup obligation but no plaintext credential: defer authenticated cleanup until the old account next authenticates, while token rebinding on a different login clears the old owner. Document that offline unregistration cannot be guaranteed; never claim otherwise.
- [ ] Commit: `git commit -m "feat: route notification taps to authorized app content"`.

### Task 8: Completion/skip provenance without changing matching semantics

**Files:** Modify db.py logging functions, `backend/services/matching/runner.py`, `backend/routers/integrations.py`, `backend/main.py`; create `backend/tests/integration/test_notification_workout_state.py`; extend notification_rules tests.

**Interfaces:** Extend `update_workout_log` with keyword-only `missed_origin:str|None=None`; persist `missed_origin` and `first_completed_at`. Existing positional callers stay valid. First timestamp is written only on a transition to completed and never overwritten; existing historical rows remain null. Clearing missed clears its origin. Manual route supplies athlete; matching supplies matching. New notification candidate builders consume these fields without altering scoring.

- [ ] Add a provenance regression to an existing integration workout fixture:

```python
# Invoke the existing update_workout_log on the fixture workout:
update_workout_log(workout_id, is_missed=1, missed_origin='matching')
# Read the row with a SQLAlchemy text() SELECT.
assert row['is_missed'] == 1 and row['missed_origin'] == 'matching'
update_workout_log(workout_id, is_completed=1)
# Reread: completion and missed remain mutually exclusive.
assert row_after['is_missed'] == 0 and row_after['missed_origin'] is None
```

- [ ] Run `python -m pytest tests/integration/test_notification_workout_state.py -q`; expect signature/schema failure.
- [ ] Audit every `update_workout_log` caller and direct UPDATE of is_completed/is_missed before changing the shared function. Retain all existing validation, mutual exclusion and return values. Add first completion timestamp through SQL CASE/COALESCE in the same transaction. Do not backfill timestamps from migration time. Keep matching shadow mode and manual incomplete override unchanged.

```sql
first_completed_at = CASE WHEN :completed = 1 AND is_completed IS DISTINCT FROM 1
                         THEN COALESCE(first_completed_at, NOW())
                         ELSE first_completed_at END
```

- [ ] Run new tests plus existing matching/manual-link tests. Assert completing twice does not reset timestamp; reversal suppresses pending recovery; historical import never sends a backlog; unknown missed origin remains unknown rather than becoming an athlete skip.
- [ ] Commit: `git commit -m "feat: preserve workout decision provenance for reminders"`.

### Task 9: Durable plan completion and Sunday planning

**Files:** Modify db.py, main.py, `backend/services/week_rebuild.py`, `backend/services/schedule_proposals.py`, notification_store/rules/notifications; create `backend/tests/integration/test_notification_generation.py` and `backend/tests/unit/test_notification_planning.py`.

**Interfaces:** `save_workouts` gains optional keyword-only `conn=None`, preserving its standalone commit behavior; internal save body uses a supplied connection without commit. Produce `start_generation(conn, request:dict)->None`, `finish_generation(conn, request_id:str, result:dict, now:datetime)->None`, `fail_generation(request_id:str, now:datetime)->None` in notification_store. finish_generation updates request and inserts the owned plan-ready event transactionally. `planning_candidates(context:dict, now:datetime)->list[dict]` supplies Sunday candidates.

- [ ] Add rollback test with a scratch generation request and fixture plan: inside `engine.begin()` call save_workouts(conn=conn), finish_generation, then raise RuntimeError; assert neither new workout rows nor plan-ready event survives. Add Sunday tests with following-week coverage, live request and stale request.

```python
with pytest.raises(RuntimeError):
    with engine.begin() as conn:
        save_workouts(plan_id, workouts, conn=conn)
        finish_generation(conn, request_id, {'plan_id':plan_id}, now)
        raise RuntimeError('force rollback')
assert ready_event_count == 0
```

- [ ] Run the two listed test files; expect missing interfaces/eligibility failure.
- [ ] Persist request before launching asynchronous generation; update timestamps at existing lifecycle boundaries. Mark in-process requests older than 30 minutes error without pretending work is resumable; a late successful result may still transition to done exactly once if genuinely saved and not superseded. Cover onboarding, new plan, next block and adaptation save paths. Use durable rebuild proposal state where present, inserting event at result persistence, preserving coach draft visibility and recipient ownership. Leave existing plan_jobs API shape intact. Avoid wrapping LLM/network calls inside DB transactions.

```python
with engine.begin() as conn:
    save_workouts(plan_id, workouts, conn=conn)
    finish_generation(conn, request_id, {'plan_id':plan_id, 'block_number':block_number}, now)
# Only now expose the in-memory job as done.
```

- [ ] Test duplicate callbacks, private draft recipients, request errors, restart, plan replacement, existing next-week coverage, 24-hour result expiry and quiet hours. Sunday routes to existing eligible block action; never generates automatically or bypasses plan completion prerequisites. Rerun existing generation/rebuild DB tests.
- [ ] Commit: `git commit -m "feat: notify saved plans and missing next-week coverage"`.

### Task 10: Checklist snooze and exact knowledge content

**Files:** Extend notification_store/rules/copy/router and main knowledge routes; modify native `Core/Knowledge/KnowledgeService.swift`, `Features/Knowledge/KnowledgeHubScreen.swift`, `Features/Plan/KnowledgeCard.swift`, SharpenChecklistCard and coordinator; create KnowledgeDetailScreen, `backend/tests/unit/test_notification_content.py`, `backend/tests/integration/test_notification_knowledge.py`, `ios-native/UphillAITests/Notifications/NotificationKnowledgeTests.swift`; update SharpenChecklistTests.

**Interfaces:** `content_candidates(context:dict, now:datetime)->list[dict]`; exact GET `/api/knowledge/cards/{card_id}?lang=...` and idempotent POST `/api/knowledge/cards/{card_id}/opened?lang=...` using existing auth rules. Register exact path after `/random` to avoid route capture. Extend KnowledgeServicing with `fetchCard(id:Int,lang:String) async throws -> KnowledgeCardModel` and `markOpened(id:Int,lang:String) async throws`. Exact fetch never uses curated fallback.

- [ ] Write collision test using StubURLProtocol: exact server ID 1 returns 404; assert fetchCard throws rather than returning curatedCards[0]. Add checklist parity fixture from existing SharpenChecklistTests and a server preference snooze test.

```python
def test_future_checklist_snooze_suppresses(context, now):
    # Define context/now fixtures in this test module from Shared contracts.
    context['preferences']['checklist_snoozed_until'] = now + timedelta(days=14)
    assert all(c['kind'] != 'checklist' for c in content_candidates(context, now))
```

- [ ] Run listed Python content/knowledge files and `ios-native/scripts/test.sh -only-testing:UphillAITests/NotificationKnowledgeTests`; expect missing exact fetch/rules.
- [ ] Mirror the five existing checklist conditions and ordering, including field source != default, in backend rules with parity fixtures. Import valid local snooze once into account preferences using the later expiry; cap import to 14 days from original snooze, not 14 days per login. Native hides checklist using server/cache value. Card candidates come only from reviewed server content, match phase/topic/tags deterministically, exclude known opens and deliveries within 90 days, cap two per seven days. Use the notification_reviewed eligibility marker introduced in Task 1; curate IDs only after reading actual deployed content through the normal authorized workflow, never seed invented IDs. No eligible content means no message.
- [ ] Add a `namespace` discriminator to KnowledgeCardModel so bundled cards cannot record server opens. Set server/curated origin in each fetch path without changing existing decoding of API cards. KnowledgeDetailScreen fetches the exact server card and records open on actual display; instrument normal hub server-card expansion similarly. Test language mismatch, unknown card, network retry, signed-out opens, snooze offline sync, repeat exclusion and all-done checklist. Review EN/VI templates.
- [ ] Commit: `git commit -m "feat: add respectful checklist and knowledge notifications"`.

### Task 11: Recovery, adaptation, taper and race rules

**Files:** Extend notification_rules/copy/notifications; create `backend/tests/unit/test_notification_coaching.py`; extend NotificationRoutingTests and PlanView presentation.

**Interfaces:** `coaching_candidates(context:dict, now:datetime)->list[dict]`; same Candidate contract. No new scheduler or tables.

- [ ] Create minimal context fixtures for approved plan/workouts/history, and a provenance-specific check-in test:

```python
def test_explicit_skips_do_not_trigger_checkin(context, now):
    for workout in context['workouts']:
        workout.update(is_completed=0, is_missed=1, missed_origin='athlete')
    assert all(c['kind'] != 'unlogged' for c in coaching_candidates(context, now))
```

- [ ] Run `python -m pytest tests/unit/test_notification_coaching.py -q`; expect missing builder failure.
- [ ] Implement each spec rule as a plain function called by coaching_candidates: recovery only for confirmed priority runs with fresh evidence; unlogged after two unresolved sessions in seven days, oldest >=2 local days, known failing sync suppresses, seven-day cooldown; taper once per contiguous explicit phase segment; race D-7/D-1 against active goal. Use plan calendar and actual activity end when present, never the observation time alone for a historical import. Unlogged key uses plan and local weekly cooldown window; recovery uses user/workout; taper uses plan/segment start; race uses plan/race-date/milestone. Keys for generic checklist/knowledge include local eligibility date to permit later intentional repeats within their cooldown rules.

```python
# Freshness is source evidence, not merely that the worker just saw a row.
fresh_activity = ended_at is not None and now - timedelta(hours=24) <= ended_at <= now
fresh_schedule = scheduled_day in (local_today, local_today - timedelta(days=1))
```

- [ ] Test thresholds at day 2/3, rest exclusions, explicit versus automatic skips, sync failure, reversal, duplicate completion, historical import, taper gap/new segment, changed/canceled race and race passed. Test exact precedence from spec and consumed-slot behavior: combine one reviewed relevant line with workout copy or drop recovery, never send a second push. Assert none of these rules writes workout/plan state. Test review route opens existing review/adapt controls without executing them.
- [ ] Commit: `git commit -m "feat: add contextual recovery taper and race coaching"`.

### Task 12: Operational controls, retention and full verification

**Files:** Create `docs/operations/ios-notifications.md`, `backend/tests/integration/test_notification_retention.py`; finish config/telemetry/notifications retention; update `ios-native/README.md` only for push setup.

**Interfaces:** `prune_history(now:datetime)->int` in notification_store strips terminal payload/error metadata after 90 days while retaining unique key/account/kind/source identity/status/sent timestamp for deduplication and cooldowns. Remove those tombstones when source lifetime ends; generic date-window keys can expire after all associated cooldowns. Account FKs delete all account state. Do not delete durable open history merely because delivery records age out.

- [ ] Write retention tests: age an accepted event by 91 days, prune, then attempt insert of same logical event; assert original identity returned and no pending event created. Delete scratch account and assert all notification rows disappear.

```python
assert after['id'] == before['id']
assert after['status'] == 'accepted'
assert after['destination'] == {}
```

- [ ] Run `python -m pytest tests/integration/test_notification_retention.py -q`; expect missing pruning behavior.
- [ ] Implement daily maintenance inside existing worker tick, bounded SQL batches; configure `NOTIFICATION_WORKER_ENABLED=false` by default, `NOTIFICATION_DELIVERY_ENABLED=false`, and account allowlist. Disabled delivery must not consume user allowance. Add operator instructions for secret key mounting, APNs capability/provisioning, sandbox versus TestFlight production, schema deployment before worker, credential rotation, metric inspection, rollback by kill switch and known offline-logout/completion races. Declare no real delivery success from simulator tests.
- [ ] Run focused notification unit/integration suites, affected generation/matching/checklist tests, then the repository backend unit suite and native suite once. Commands:

```bash
python -m pytest tests/unit/test_notification_rules.py tests/unit/test_apns.py tests/unit/test_notification_planning.py tests/unit/test_notification_content.py tests/unit/test_notification_coaching.py -q
python -m pytest tests/integration/test_notification_store.py tests/integration/test_notification_api.py tests/integration/test_notification_worker.py tests/integration/test_notification_workout_state.py tests/integration/test_notification_generation.py tests/integration/test_notification_knowledge.py tests/integration/test_notification_retention.py -q
python -m pytest tests/unit -q
# From repository root:
ios-native/scripts/test.sh
git diff --check
```

- [ ] Arrange a user-owned test device and allowlisted account before enabling actual pushes. Verify sandbox and TestFlight delivery, terminated-app taps, exact workout/card, completion suppression, quiet hours, revoked permission and account switching. Record build/environment/results in operations doc, explicitly marking unavailable hardware/credentials as unverified. Take settings screenshots in EN/VI and inspect Dynamic Type/VoiceOver labels. No production-wide enablement follows implicitly.
- [ ] Commit: `git commit -m "docs: verify and document notification rollout"`.

## Final review and execution handoff

Self-review mapping: spec intent/all eight cases → Tasks 3, 9–11; consent/security/account binding → 2, 6–7; timing/collisions → 3, 5, 11; durable state/provenance → 1, 8–10; APNs/failures → 4–5; native routes/knowledge identity → 7, 10; operational rollout/retention → 12. Review Focus items have owning test tasks above.

No tests were run while writing this plan; example code is implementation guidance, not a claim of passing software. Product code remains unchanged. Once this plan is reviewed, use the selected execution skill, keep checkbox progress current, and request one final whole-branch review according to that execution method. Report outstanding real-device delivery checks separately from code completion.

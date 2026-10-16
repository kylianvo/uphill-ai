# Native iOS coaching notifications

Date: 2026-10-16 (Australia/Sydney)
Status: Written design for user review; implementation not authorized by this document.

## Intent and agreed direction

Build a supportive daily workout companion with occasional contextual coaching. A notification should offer one useful next action and open the exact workout, knowledge card, or planning flow. Success means relevant reminders, suppression when the action is no longer needed, accurate navigation, and useful adaptation without guilt or notification overload.

The user approved backend-controlled delivery through APNs, deterministic rules, existing Postgres/worker patterns, and dropping stale reminders instead of adding local offline fallbacks. The defaults and detailed rules below are proposed for written-spec review.

All eight requested cases remain in scope: today's workout, better plan inputs, knowledge cards, Sunday planning, recovery after priority runs, taper, race preparation, and a gentle check-in after unlogged training. Requested-plan completion is also included. Other brainstormed cases are deferred unless explicitly covered here.

## Existing code and constraints

- Native target: `ios-native/UphillAI`; older Capacitor helpers in `frontend/src/utils/notifications.ts` are not the implementation target.
- `Core/Models/Plan.swift` exposes priority, phase, session slot, duration, distance, zone, completion and matched activities. `Workout.isDone` is `isCompleted == 1 || (isCompleted != 0 && isMatched)`. Preserve explicit incomplete overrides; do not change matching behavior as part of notifications.
- `backend/services/workout_calendar.py` resolves dates from the plan start and retains legacy race-anchored fallback. Reuse it; do not implement another date calculator. Suppress a candidate when required date inputs cannot be resolved safely.
- `backend/services/matching/runner.py` both auto-completes matches and auto-marks past workouts missed. `is_missed` alone cannot distinguish an athlete decision from an automatic classification.
- `SharpenChecklist` defines watch, race history, thresholds, paces and injury-context inputs. `SharpenChecklistCard` currently stores a 14-day snooze locally.
- `backend/main.py` includes in-memory generation jobs; persisted notification events must not depend on those surviving restarts.
- `backend/services/race_history.py` demonstrates a process worker with durable Postgres state and an advisory lock. Follow its pattern in a separate notification worker; do not attach notification behavior to race-history jobs.
- `AppModel.handleOpenURL` currently handles COROS authentication, not general content routing.
- KnowledgeService has both server cards and a bundled fallback with numeric IDs. These namespaces must never be confused when resolving a notification.

## Architecture and boundaries

One backend notification service evaluates deterministic rules against current account state and renders reviewed English/Vietnamese templates. One small APNs transport handles signing, HTTP/2 requests and response classification. One authenticated notifications router owns preferences, installations and open acknowledgments. One native notification coordinator owns authorization, registration, foreground handling and pending destinations.

A worker ticks every 60 seconds. Use a Postgres advisory lock so only one evaluator claims work across API processes. Persist claims before network I/O; never hold a database transaction open during an APNs call. Shutdown stops new claims. A startup feature flag independently controls this worker.

No Redis, Celery, Firebase, campaign platform, LLM call per notification, generic rules engine, notification inbox, silent-push dependency, or local fallback scheduler. HTTPX, PyJWT and cryptography already exist; explicitly enable HTTPX HTTP/2 support if absent from the resolved installation. APNs credentials are server secrets.

## Consent, preferences and scheduling

Default to no sends until the athlete explicitly enables notifications and the device grants authorization. Present workout reminders and coaching tips as separate controls, plus requested-result updates. Suggested settings: 07:00 workout time, 18:00 coaching time, quiet hours 21:00–07:00. These times are preferences, not inferred workout start times. Offer a pause-until date and turn-off control.

Store an IANA account timezone, language and distance units. The most recently active opted-in installation updates these values on launch/foreground and detected changes. Validate timezone and preference values at the API boundary. Missing timezone means no scheduled proactive sends. Store actual timestamps in UTC; compute calendar dates in the account timezone. On a DST gap, use the first valid time after the gap; on a repeated time, use the first occurrence. Event deduplication prevents a second send.

Use a 60-minute delivery window after a proactive notification's chosen time. Quiet hours move a candidate to the next permitted time only if it remains useful; otherwise expire it. A proactive message cannot cross its local-day or event-specific expiry. Do not replay missed windows after outages. Update candidate eligibility when preferences change.

One proactive notification per account per local date. Also require 20 hours between proactive sends to prevent rapid duplicates after timezone changes. Requested-result notifications are separate and capped at three per local day; further results remain visible in the app. No notifications while paused, including results.

For the first version send to one installation: the most recently active, authorized installation. Do not fan out to every device. Account-level consent is distinct from device permission. Refresh permission status when the app becomes active; remote revocation may be unknown until then.

## Selection and collision policy

At the day's workout reminder time choose the highest-priority currently eligible candidate. On days without an actionable workout, use coaching time. If the daily slot is consumed, do not send another proactive message later that day.

Precedence: race preparation, Sunday planning, unlogged-session check-in, taper transition, workout reminder, recovery, checklist, general knowledge. Requested results use their separate allowance. A relevant recovery/taper tip may be included in the workout message using a reviewed template, while retaining a single primary destination. Do not concatenate unrelated messages.

Recovery after a run uses the next available proactive slot within 24 hours of confirmed completion. If the slot is already consumed or an upcoming workout wins, merge a suitable recovery line into that workout reminder or drop the standalone message. This intentionally means a runner does not receive every eligible content type.

## Event rules

| Event | Eligibility and cadence | Destination and expiry |
| --- | --- | --- |
| Workout | Approved, non-rest session in the active plan today; not done or marked missed. At most one daily reminder. With multiple sessions choose priority first, then AM/PM order, then ID; mention another session only if space permits. | Selected workout. Expires at the earlier of delivery-window end and local day end. |
| Better plan inputs | Coaching enabled; at least one incomplete SharpenChecklist item; at least 14 days since last checklist send and outside snooze. Choose first incomplete item in existing checklist order. Never expose injury details. | Specific checklist input screen. 60-minute window. |
| Knowledge | Coaching enabled; at most two per rolling seven days; reviewed server card relevant to current phase or session; no delivery of that card in 90 days and no known card-open record. No suitable card means no send. | Exact server card and language. 60-minute window. |
| Sunday planning | Sunday, active approved plan, no generated/approved upcoming block covering the following week, and no active generation request for that coverage. Use existing block-generation eligibility; never generate automatically. | Plan screen with the appropriate existing generation action. 60-minute window and Sunday expiry. |
| Priority-run recovery | A priority running session becomes completed; first observation must concern a workout scheduled today/yesterday or an activity that actually ended within 24 hours. No historical-import backlog. Once per workout. | Completed workout feedback, with contextual recovery guidance. Expires 24 hours after relevant completion evidence. |
| Taper | Active plan enters an explicitly designated taper phase. Once per plan's contiguous taper segment. Do not infer a universal taper duration from race distance. | Reviewed taper card. Eligible during first two local dates of the segment; each attempt respects the daily window. |
| Race preparation | Active target race at D-7 and D-1, one event per milestone. Select reviewed race-preparation content; prefer stored race-specific preparation when present. No countdown for an expired/inactive goal. | Plan/race preparation context showing the target race. Expires on milestone date. |
| Unlogged training | At least two past non-rest sessions within seven days lacking completion evidence, with the oldest at least two calendar days old. Exclude explicit athlete skips; include automatic/unknown missed classifications but ask neutrally. At most once per seven days. If sync is known to be failing, suppress this prompt. | Plan review focused on those sessions; runner can log or open existing adaptation flow. 60-minute window. |
| Requested plan ready | A user-requested plan/block/adaptation result is durably saved and visible to that recipient. One event per request. Coach-only drafts do not notify athletes as if approved. | Exact generated plan/week or reviewable result. Defer through quiet hours, expire after 24 hours. |

All candidates are reevaluated immediately before first send and every safe retry. A send never marks done, generates a plan, changes a schedule, or edits athlete data. Rest days do not generate generic workout prompts.

## Necessary state additions

1. `notification_installations`: installation ID, authenticated account, APNs token, trusted application environment/topic, permission status, last-active time, disabled time. Token/environment uniqueness; ownership moves safely on login. Do not trust a client-supplied account ID or arbitrary APNs topic.
2. `notification_preferences`: account key, category flags, times, quiet hours, timezone, locale/units, pause-until, checklist-snooze-until and last proactive reservation timestamp/date. Server defaults are opt-out.
3. `notification_events`: account, unique logical event key, type, destination, source reference, due/expiry timestamps, state, claimed installation, attempt count, next attempt, APNs ID/result, accepted/opened timestamps and suppression reason. This table is the outbox and audit trail. Store no complete training/profile snapshot.
4. Minimal workout logging provenance: a nullable origin for the latest missed-state decision (`athlete`, `matching`, or unknown) and first completion-transition timestamp. Update shared logging paths and direct affected writers; existing rows remain unknown, not retrospectively labeled athlete decisions. Completion reversal invalidates pending recovery but does not permit repeated recovery for the same workout.
5. Knowledge open history keyed by account, server card ID and language; upsert when a server card detail is actually displayed from any entry point. This records opening, not proof of reading. No backfill of assumed read history.
6. Durable generation-request markers for affected plan paths: request ID, actor/recipient, target coverage, generating/done/error state, update time and result reference. Persist alongside the request lifecycle so Sunday suppression and result events survive a process restart. Reuse existing durable proposal/job state where it already exists. Mark stale in-process jobs failed after 30 minutes; this adds notification-safe tracking, not resumable generation.

The extra provenance and generation state are necessary to avoid false skip assumptions and inaccurate plan-ready alerts, not a general job-system rewrite.

## Transaction and failure semantics

Create plan-ready outbox entries in the same transaction that saves the relevant final result. Thread an existing connection through the necessary persistence helper rather than commit the result and hope a later notification write succeeds. Audit all plan creation, next-block and adaptation success paths, including durable coach proposal paths. Preserve their current approval and ownership behavior.

Use unique logical keys, e.g. workout/user/local-date, plan/taper-segment, race/milestone, and generation-request/recipient. Atomically reserve the user's daily allowance and claim the event. Once claimed, the daily allowance stays consumed even if delivery fails; fewer messages are preferable to accidental extra messages.

States: pending, sending, accepted, suppressed, expired, failed, unknown. A worker crash while sending leaves an ambiguous result; mark unknown and do not resend. Explicit retryable APNs responses use delays of 1, 5 and 15 minutes, bounded by expiry, maximum three retries. Network failures with uncertain acceptance are unknown, not automatically retried. Recheck consent, installation ownership, content and expiry at every retry. An invalid token disables that registration. Authentication/configuration errors stop transport attempts and raise an operational alert without disabling every user's token.

APNs collapse IDs coalesce related requests but are not exactly-once delivery. Set expiration to event expiry, and keep the same logical identifier on a safe retry. APNs acceptance is not a display receipt. Record opened only through an authenticated, idempotent acknowledgment.

No design can atomically couple a server completion update with presentation on an offline phone. A run completed after the final check, offline data, Focus settings, or delayed delivery can still produce a stale or unseen alert.

## Native integration and API contract

Add authenticated endpoints to upsert/remove the current installation, read/update own preferences, and acknowledge a notification opening. Add exact server-card retrieval and card-open tracking if no existing endpoint supports them. All referenced private content remains subject to current account authorization. Limit client input lengths and accepted destination kinds.

Use a versioned payload with notification ID, destination kind, entity IDs and content language. Payloads contain no access tokens and no arbitrary URL to execute. Workout destinations include parent plan ID; plan destinations can include week/block. Checklist destinations use the existing TrainingDestination enum. Knowledge references explicitly use the server-card namespace; never resolve a server ID against the bundled fallback array.

The native coordinator queues one pending destination across cold launch/login, then fetches current authorized data before navigation. Preserve Google/COROS URL behavior. If a target was removed, replaced, or belongs to another account, show a short unavailable message and open the appropriate current screen without exposing the old content. Network failure offers retry; it must not silently display a different card with the same numeric ID.

When already viewing the destination, update content without an interrupting foreground banner. Otherwise use the normal foreground notification presentation. Do not add badge counts or quick actions in this version.

On logout remove the installation binding before dropping credentials when online and clear local pending/delivered app notifications. On an offline logout, local cleanup still occurs but server unregistration cannot be guaranteed; retry cleanup on reconnection and never include sensitive profile information in push text. On account switching, atomically rebind the installation and invalidate unsent events claimed for its previous owner.

Import an existing local checklist snooze once at first preference synchronization, preserving the later valid expiry, then use server state. Hide the native checklist and suppress its notifications from the same snooze value. Retain a cache for offline display.

English and Vietnamese copy uses reviewed templates and existing vocabulary conventions. No new Vietnamese copy is approved by this English design; implementation must apply the repository's Vietnamese-copy skill. Include only available workout values and the runner's units. Never infer medical conditions or failure from missing activity data.

## Change surface and rollout

Backend: schema/init/migration conventions in `db.py` and Alembic, notification service/router/transport, worker startup/shutdown, configuration, logging/matching writers, plan persistence/job paths, knowledge endpoints and tests. HTTP/2 support is the only anticipated dependency adjustment.

Native: app notification delegate/coordinator, AppModel/RootView navigation, preferences UI using existing components, API models/services, checklist snooze, server-card detail/open handling, logout/account switching, entitlements/project configuration, localization, fixtures and navigation/settings tests.

Deployment: APNs signing key, key ID, team ID and bundle topic; development versus production configuration; push entitlement/provisioning; worker enabled only after schema and credentials exist. Secrets stay outside Git. No changes to Capacitor reminders in this native-only scope.

Roll out with an allowlist in configuration, then opt-in accounts. A global kill switch stops new delivery without deleting preferences. Use existing logging/Prometheus conventions for candidate/suppression counts, APNs outcomes, oldest pending age and worker heartbeat. Never log tokens or health-detail payloads. Purge terminal delivery records after 90 days; retain the minimal event-key tombstone for the lifetime of its source plan/request to prevent replay. Delete notification state on account deletion.

## Verification and acceptance

- Frozen-clock rule tests: today/rest/double-session cases, explicit incomplete override, automatic versus athlete skip, approved versus draft, plan replacement, next-week coverage, stale generation, priority completion reversal, no historical recovery, snooze, phase and race milestones, knowledge open/repeat exclusion.
- Scheduling tests: Sydney DST gap/overlap, travel across dates, 20-hour guard, quiet hours, outage window, pause, category controls and one-slot precedence.
- Database tests: concurrent workers cannot reserve two proactive events; event/result transaction rolls back together; lifecycle ownership and unique keys; migration compatibility with existing rows; no duplicate after restart or unknown send.
- Transport tests: APNs acceptance, invalid token, explicit retryable response, credential failure, ambiguous timeout and expiry while retrying. Assert no sensitive payload/log data.
- Native tests: denied permission, token refresh, logout/account switch, cold start/login navigation, removed target, server/bundled card-ID collision, offline retry and shared checklist snooze.
- Real-device checks in development and TestFlight: authorization, receiving and tapping each destination, completed-workout suppression, quiet hours and app termination. APNs credentials and deployment uptime must be verified before enabling delivery.

Delivery order: (1) complete workout reminder vertical slice including consent, secure registration, durable deduplication and navigation; (2) Sunday/requested-result rules with durable job tracking; (3) checklist/knowledge; (4) completion provenance, recovery/unlogged check-in, taper and race rules. Reliability is included in each slice, not postponed until the end. All four slices are required to fulfill the approved feature scope.

Deferred: generic motivation, streaks, weather, standalone weekly summaries, watch-disconnection alerts, post-race/return-from-break sequences, race-morning encouragement, tomorrow's-session reminders, gear/fueling result pushes and coach-change alerts. These can later use the same service without being added now.

## References and review handoff

Apple APNs requests: https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns

Apple background delivery limitations: https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app

This document is the written-spec review gate. After user approval, invoke the Superpowers writing-plans skill to produce the implementation plan. Do not begin product implementation from architectural approval alone.

# Garmin Connect integration plan

Date: 2026-10-24. Status: access requested (Starter tier), not approved yet.

## Goal

Garmin works like COROS does today: connect the account, completed runs land in
`activities` and get matched to the plan, recovery metrics feed readiness, and the
plan's workouts appear on the watch. On top of that, Garmin adds things COROS can't
give us: the race course on the watch, and Body Battery, stress and VO2 max.

## What Garmin offers (Starter tier)

Source: <https://developer.garmin.com/gc-developer-program/overview/>.

| | Starter (what we applied for) | Enterprise |
|---|---|---|
| APIs | Activity (JSON + FIT), Health, Training, Courses, Women's Health | same + Golf |
| Delivery | **Push only** | Push or Ping/Pull |
| Historical data | **None** | 1 month+ |
| Users | Limited (reported as ~1,000) | Unlimited |
| Support | none | included |

How Starter changes the design compared with COROS:

- **No pull, no backfill.** COROS's `sync_user(days=30)` pulls history on demand.
  Garmin only POSTs data to our webhook when the watch syncs *after* the user has
  connected. A new user starts with an empty history. For older runs we already
  have manual FIT upload (`parsers/fit_parser.py`), and Apple Health also brings in
  Garmin runs for iOS users.
- **Webhook-first.** We have to answer every push with HTTP 200 within a few
  seconds and do the processing afterwards. Garmin retries failed deliveries, so
  the same data can arrive twice: upsert on Garmin's `summaryId`/`activityId`.
  The endpoint must be publicly reachable over HTTPS, so testing needs staging or a
  tunnel, not localhost.
- **Evaluation key first.** Garmin issues an evaluation app first. Production needs
  "Partner Verification" in their API Tools. They may disable an evaluation app
  that real users are on.

Auth is OAuth 2.0 with PKCE, the same shape as `services/coros_oauth.py`.

## Agreement terms that affect us

From the Garmin Connect Developer Program Agreement
(<https://www8.garmin.com/en-US/GARMINCONNECTDEVELOPERPROGRAMAGREEMENT/GARMINCONNECTDEVELOPERPROGRAMAGREEMENT_EN.pdf>):

- **§15.10 AI Transparency Statement.** Garmin data goes to Gemini, so the privacy
  policy needs a prominent AI statement (ours has one, in §4). The agreement also
  requires *explicit consent that's easy to withdraw*. We have no consent toggle
  today. **We have to build one before production** (see Phase 0).
- **§6 Attribution.** Wherever Garmin data is shown, it carries Garmin branding per
  the Garmin API Brand Guidelines (like `CorosAttribution`).
- **§5.2(e)/(o).** We can't resell or re-expose Garmin data through any API of our
  own. Sharing with a coach is fine because it's part of our own app and happens
  only with the athlete's consent.
- **§15.4 / Annex A.** Data-subject rights, and keep data no longer than needed.
  When access is revoked we delete the data (our privacy notice already promises
  this within 24 h).

## What we reuse

| Need | Existing piece |
|---|---|
| Provider-neutral shapes | `services/providers/base.py` (`CanonicalActivity`, `CanonicalDailyMetric`; its docstring already plans for Garmin) |
| Connection + tokens | `athlete_connections` table (`provider` column) |
| Activity storage, dedupe, matching | `activities` with `source_provider`, `services/matching/*`; Apple Health already goes through the same path |
| Daily recovery | `daily_metrics` (unique per user/date/provider), `services/recovery_baseline.py`, the one-provider-at-a-time rule in `db.get_recent_readiness_summary` |
| FIT detail (laps, HR, elevation) | `parsers/fit_parser.py` |
| OAuth PKCE | `services/coros_oauth.make_pkce_pair`, `_PENDING_AUTH` in `routers/integrations.py` |
| Workout to steps | `services/coros_workouts.py` already parses the Process chain into warm-up / intervals / cooldown with HR targets |
| UI | `ConnectedAccounts`, `CorosAttribution`, `CorosPushButton` (web); iOS Connected accounts section |

## Phases

### Phase 0: while waiting for approval (no Garmin key needed)

1. **AI consent toggle** (needed for §15.10, and it covers COROS and Apple Health
   too). Add a per-user "Use my device data for AI coaching" consent, stored with a
   timestamp, which can be switched off in Profile. While it's off, device data
   stays out of Gemini prompts and the coach uses only plan data. Needs the
   `db-migration` skill (dual schema).
2. Privacy notice: name Garmin next to COROS (data categories, attribution,
   revocation), en + vi.
3. Make sure `viet.vo@uphill-ai.io.vn` accepts mail from `garmin.com`,
   `health.garmin.com` and `developer.garmin.com`. The approval and portal invite
   come by email.

### Phase 1: connect + activities (parity with COROS ingest)

- `config.py`: `GARMIN_ENABLED` (kill switch, default off), `GARMIN_CLIENT_ID`,
  `GARMIN_CLIENT_SECRET`, `GARMIN_REDIRECT_URI`.
- `services/garmin_oauth.py`: authorize URL, code exchange, refresh. Copy the
  shape of `coros_oauth.py`. After connecting, fetch the Garmin user ID and store
  it on `athlete_connections`, because pushes are keyed by it.
- Routes in `routers/integrations.py`: `GET /garmin/connect`,
  `GET /garmin/callback`, `DELETE /garmin` (calls Garmin's deregistration endpoint,
  then deletes our data).
- `POST /integrations/garmin/webhook`: one URL for every data type (configured in
  Garmin API Tools). It reads the top-level key (`activities`, `activityDetails`,
  `activityFiles`, `dailies`, `sleeps`, `hrv`, `userMetrics`, `stressDetails`,
  `deregistrations`, `userPermissionsChange`, …), returns 200 straight away and
  processes in a background task. Pushes for unknown Garmin user IDs are dropped.
  Only the payload's shape is logged, never its content (same rule as the COROS
  webhook).
- `services/providers/garmin.py`: `GarminAdapter` maps the activity summary to
  `CanonicalActivity`. Running, trail running, treadmill, track, hiking and
  strength go into the same `activity_type` vocabulary as `SPORT_TYPE_NAMES` in
  `coros.py`. Laps and HR come from the FIT file through `FitParser`.
- Deregistration / permission change: deleting the connection deletes that user's
  Garmin rows (`activities`, `daily_metrics` where `source_provider='garmin'`).
- Tests: adapter mapping from recorded sample payloads (the API Tools sandbox has
  synthetic data), webhook idempotency (same push twice gives one row), and that
  deregistration deletes the rows.

### Phase 2: recovery (parity with COROS readiness)

- `dailies` → `resting_hr`; `sleeps` → `sleep_minutes`, `sleep_start/end`;
  `hrv` → `hrv_ms` (overnight average), plus Garmin's own HRV status and baseline
  range into `hrv_status`, `hrv_range_low/high`, so we don't recompute them (unlike
  Apple Health).
- Readiness keeps the one-provider rule: newest wins, so a user with both COROS
  and Garmin isn't mixed.
- `fitness_snapshot` already takes volume from the provider that synced most
  recently. Check that `'garmin'` is counted as a device provider there.

### Phase 3: push workouts to the watch (Training API)

- Pull the provider-neutral step parsing out of `coros_workouts.py` (the Process
  chain into steps with zone/HR targets) and leave the COROS JSON emitter in
  place. Add a Garmin emitter: steps with duration (time/distance/lap button),
  target (HR range, or a **pace range**, which COROS couldn't do for trail runs),
  repeat groups.
- Garmin schedules **individual workouts on dates** (create the workout, then add
  a schedule entry), which is simpler than COROS's plan-library sync. Keep a
  `garmin_workout_links` table (plan workout id → Garmin workout id) so a moved or
  regenerated session updates or deletes its Garmin copy.
- Same entry point as COROS: a "Send to Garmin" button next to `CorosPushButton`,
  and an auto-push of the coming week when the plan changes (copy what COROS
  push does, including rate limiting by usage like `coros_push_usage`).

### Phase 4: features beyond COROS

1. **Race course on the watch (Courses API).** We already keep GPX-derived course
   profiles for races (`race_courses` → `course_profiles`). "Send race course to
   watch" from the plan header/goal race, so the athlete gets turn-by-turn and
   ClimbPro on the actual route for recon runs and race day.
2. **Body Battery and stress** (`dailies`, `stressDetails`) as extra readiness
   signals in the morning check and in Coach Uphill's context (number-grounded
   like the HRV wording).
3. **VO2 max / fitness age** (`userMetrics`) as one more input to the Goal
   Determiner's watch trend (`services/goal_context.py`).
4. **Running dynamics / power** from the FIT file (cadence, ground contact, power)
   for the uphill-efficiency trend. Lowest priority.
5. Women's Health API: not requested. Revisit only if a cycle-aware feature is
   planned.

### Phase 5: go live

1. Evaluation app → pass Partner Verification in API Tools → production key.
2. Flip `GARMIN_ENABLED` in prod. Diff the env keys after deploy (the prod `.env`
   clobber gotcha).
3. Web + iOS release with the Garmin connect UI and attribution.
4. Request Enterprise when we come near the Starter user cap, or if missing
   history hurts onboarding.

## To check in the portal specs after approval

The full specs are only in the Developer Portal. Before writing code, confirm:
exact OAuth/token URLs and scopes, the push payload format for each data type
(inline data or a callback URL to fetch), whether pushes are signed (if not, use a
secret token in the webhook path), HRV field names and units, the Training API
workout JSON (step types, pace target units, sport types for trail running), the
Courses API input format (GPX/FIT), and rate limits.

## Appendix: answers submitted on the access request form

- Company: Uphill AI Vietnam (early-stage, not yet a registered entity). Site
  <https://uphill-ai.io.vn>, privacy <https://uphill-ai.io.vn/privacy>.
- Contact: Viet Vo, Founder, viet.vo@uphill-ai.io.vn. Country Viet Nam.
- Business service: Coaching & Training Programs. Industry: Personal Training & Coaching.
- APIs: Activity, Courses, Health, Training. Users in 12 months: 100–1000.
  Prior Garmin contact: No.
- Overview / business model / third parties: free beta now, two human-coach
  subscriptions (Review, Coached) later. Third parties named: Gemini API, Langfuse
  (metadata only), self-hosted Postgres/Qdrant/Grafana/Metabase, Google/Facebook
  sign-in.

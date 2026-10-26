# Athletes tab: coach workbench (iOS)

Date: 2026-10-23 · Platform: iOS native (`ios-native/`) + backend · Web Athletes tab: out of scope

## Why

Uphill AI will sell two coaching subscriptions. A human coach with 20–30+ runners (possibly more) uses the iOS **Athletes** tab to serve both:

- **Review** runners build their own plan with the app. The coach reviews each new plan **once** when it's created, fixes what needs fixing, then only steps in when something flags.
- **Coached** runners have the coach build the plan for them.

Today the tab (`Features/Coaching/CoachDashboardView.swift`, titled "Coach Hub") is a report. It shows roster-wide charts and a list where every runner has an unexplained orange dot. A coach can't tell who needs them, why, or what to do. The backend already stores the signals a coach needs (missed-session reasons including *pain*/*sick*, HRV/resting HR/sleep, last watch sync, per-session RPE, block reviews, B/A path, plan checks), but none of them reach the tab.

The goal: **the coach opens the tab, clears the day's work in one sitting, and can trust that every runner not flagged is fine.** The coach also needs an overall view of how the roster and each group is training, and a timely nudge to encourage runners at important moments (race close, peak, milestones).

## Goals

1. Fix the existing bugs (Phase 1).
2. Replace the two-section Overview/Roster screen with one **triage screen** (Phase 2):
   - filters and an overall view on top
   - a highlights strip
   - an inbox sorted by urgency, where each runner shows a one-line plain-language takeaway
3. Make a runner's **Plan tab** the detail view, with one new **coach card** carrying the reason and the actions. Add the missing coach actions: build and publish a plan, review a runner's plan, mark it reviewed (Phase 3).
4. Let the coach mark each runner as **Review** or **Coached**.

## Non-goals

- Payment, subscription billing or entitlement. The plan type is a label the coach sets by hand.
- Two-way messaging. `coach_notes` stays coach → athlete. The runner's own voice in the tab comes from the missed reasons and the session RPE they already log.
- Web Athletes tab changes. Backend changes stay additive so the web tab keeps working unchanged.
- Push notifications to the coach.
- Any LLM call in the triage. Every flag is a deterministic rule a coach can trace.

## Anti-goals (a failure even if it "works")

- A runner who logged pain or illness ending up in "On track", or anywhere below the fold.
- Alert noise. One draft plan showing as 9 alerts, or rest days counted as approvals.
- A new plan screen that looks different from the app's Plan tab.
- An overview that is slow with 50+ runners (it must be one request, with no per-athlete round trips).

## Constraints

- SwiftUI and the house design system (`DesignSystem/`, `UH.*`, `.trainingCard()`). Reuse the existing Plan views (`PlanView`, `SummaryCarousel`, `CoachReviewCard`, `DayRow`, `PlanCalendarGridView`, `AdaptWeekSheet`) rather than building new ones.
- Copy in **English and Vietnamese**. Strings go in `Resources/Localizable.xcstrings`; follow the `uphill-ai-vietnamese-copy` skill.
- Schema changes go in **both** `db.py:init_db()` and a hand-written Alembic migration (`db-migration` skill).
- Changes to the `/api/coaching/overview` response are **additive only**: no existing field is removed or retyped, because the web tab reads it.
- **UI direction (decided by you): Apple design.** Native iOS patterns first (`List`/sections, `Menu` filters, swipe actions, `.searchable`, SF Symbols, Dynamic Type, system materials), in a calm minimalist style: warm monochrome base, one accent for status, flat cards, no gradients or heavy shadows. Build UI with the `impeccable` and `taste-skill:minimalist-ui` skills; build the backend with the `ponytail` skill (smallest complete change, reuse what exists).
- UI work needs simulator screenshots as evidence (`ui-screenshot-evidence` skill). `Phase6CoachScreenshots` is the place to put them.

---

## Phase 1: Bug fixes

| # | Bug | Where | Fix |
|---|-----|-------|-----|
| 1 | The refresh button does nothing once data is loaded | `CoachDashboardView.loadData()` returns early when overview and roster are set | Split it into "show cache" and "fetch"; refresh always fetches |
| 2 | Tapping a race opens Roster with the race name as the search, which only matches name and email, so the list is empty | race card callback | Superseded by Phase 2's Race filter; until then, filter by the athletes in that race entry |
| 3 | Approvals double-count: a draft plan shows as 1 draft **plus** one "needs approval" row per workout, Rest Days included | `get_roster_overview_data` `pending_rows` query | Exclude every workout on draft plans from `pending_workout_approvals` (a draft is one item). On active plans keep all pending workouts, rest included: a coach turning a session into rest (`make_rest_day`) is a real edit waiting for approval |
| 4 | Taps can silently do nothing: every "View" looks the runner up in `roster`; if that fetch failed, nothing happens. Errors only go to `print` | `CoachDashboardView` | Build the athlete reference from overview data (`athlete_id` + `name`) when the roster lookup misses; show load errors inline with Retry |
| 5 | Title "Coach Hub" vs tab label "Athletes" | `navigationTitle` | "Athletes" |
| 6 | **Build plan for an athlete creates a plan for the coach**: `GenerationService.generatePlan` always posts to `/api/coach/generate-plan` and ignores the athlete scope | `Core/Generation/GenerationService.swift` | Use `"\(prefix)/generate-plan"`, so a coach-scoped call hits `/api/coaching/athletes/{id}/generate-plan` (draft plan) |
| 7 | `pendingInvites` is fetched on the coach tab but never shown (the athlete-side invite banner already lives in `PlanView`) | `loadData()` | Stop fetching it here |

Each fix gets a unit test where it can be tested (1, 3, 4, 6).

---

## Phase 2: Triage screen

### Data model

- `coach_athletes.plan_type TEXT NOT NULL DEFAULT 'review'`, values `review` | `coached`.
  - Existing links default to `review`.
  - The coach changes it from the runner's ⋯ menu.
- New endpoint `PATCH /api/coaching/roster/{link_id}` with body `{ "plan_type": "review" | "coached" }`, coach-only, 404 if the link isn't theirs.
- Roster rows (`GET /api/coaching/roster`) and overview athletes include `plan_type`.

### Overview response additions (`GET /api/coaching/overview`)

Each entry in `athletes[]` gains these fields:

```jsonc
{
  "plan_type": "review",
  "phase": "build",                  // phase of the current plan week, null without a plan
  "race_date": "2026-12-19",         // null without a plan
  "days_to_race": 57,
  "week": {                          // the runner's current plan week
    "sessions_planned": 6, "sessions_done": 4,
    "key_planned": 2, "key_done": 1,       // key = long run or quality session
    "minutes_planned": 410, "minutes_done": 265
  },
  "prev_weeks": [ /* same shape, the 3 previous plan weeks, newest first */ ],
  "load_4w_minutes": [380, 420, 455, 265],   // completed minutes, oldest → newest
  "adherence_14d": 0.62,
  "last_sync_at": "2026-10-21T06:12:00Z",    // newest activities row, null if none
  "signals": [ /* see below, most severe first */ ],
  "status": "act_now"                // act_now | review_build | check_in | on_track
}
```

Top-level fields gain `"generated_at"`. All existing fields stay.

Filters are applied **on the device**: plan type, race, level and phase. The overall numbers and group bars are summed on the device from each runner's `week` / `prev_weeks`. One request covers every filter combination, so changing a filter needs no network call. The existing `days` / `athlete_id` / `level` query params keep working for the web tab.

### Signals

A pure function, `services/coach_signals.py: signals_for(athlete_ctx, today) -> list[Signal]`, unit-tested rule by rule. Each signal is `{code, severity, params}`, where `severity` is one of `act_now | review_build | check_in | highlight`. The **device** turns `code` + `params` into a localized sentence. `status` is the most severe non-highlight signal, or `on_track`.

| Severity | Code | Rule (my call; easy to tune later) | Example sentence |
|---|---|---|---|
| act_now | `reported_pain` / `reported_sick` | a session missed with reason `pain` / `sick` in the last 7 days | "Logged pain Tue" |
| act_now | `missed_many` | ≥3 sessions missed in the last 7 days | "Missed 3 sessions this week" |
| act_now | `overload` | completed minutes in the current or previous week > 130% of planned (planned ≥ 60 min) | "Ran 78 km vs 52 planned" |
| review_build | `plan_to_review` | any runner (Review **or** Coached) whose active plan was created by the athlete (`created_by_user_id = athlete`) and whose latest generated block is newer than the last reviewed block (`generated_block > coalesce(coach_reviewed_block, 0)`, see Phase 3). `params`: `block`, and `waiting_hours` since `plans.created_at` for block 1 (later blocks have no generation timestamp, so no wait time is shown) | "New plan · waiting 31 h" / "Week 5 to review" |
| review_build | `needs_plan` | Coached runner with no active and no draft plan | "No plan yet" |
| review_build | `draft_unpublished` | any runner with a draft plan (only coaches create drafts) | "Draft plan not published" |
| review_build | `next_block_due` | the last **generated** week of the plan (current block) ends in ≤7 days and `total_weeks` is not reached | "Next block due in 5 days" |
| review_build | `changes_to_approve` | N > 0 pending workouts on the **active** plan, rest included (coach edits waiting for approval) | "3 changes to approve" |
| check_in | `no_sync` | active plan and no activity for ≥5 days (or none since the plan started) | "No watch sync for 6 days" |
| check_in | `missed_key` | a long run or quality session missed in the last 7 days | "Missed Thu tempo" |
| check_in | `adherence_drop` | `adherence_14d` < 0.6, or ≥20 points below the previous 14 days | "Adherence 70% → 40%" |
| check_in | `hrv_low` | `daily_metrics.hrv_status = 'low'` on ≥2 of the last 3 days (newest provider, as in readiness) | "HRV low 3 days" |
| check_in | `hard_easy_days` | RPE ≥ "hard" on ≥2 easy sessions in the last 7 days | "Easy days felt hard" |
| highlight | `race_soon` | race in ≤14 days | "Races VMM 42K in 9 days" |
| highlight | `phase_start` | peak, taper or race phase starts this week or next | "Starts Peak Monday" |
| highlight | `longest_long_run` | the longest completed long run of the plan happened in the last 7 days | "Longest long run: 4 h 10" |
| highlight | `block_done` | a block finished in the last 7 days | "Finished Base block" |
| highlight | `new_result` | a `race_results` row added in the last 7 days | "New result: Dalat 21K 2:48" |

Rules for every signal:
- A runner with any `act_now` signal is listed under 🔴, whatever else is true.
- Signals read only data already stored. If a source is missing (no watch, no Apple Health), its rules stay silent; they never guess.
- Queries are batched per table for the whole roster, with no N+1. Target: the overview responds in under 500 ms for 100 runners on prod hardware.

### Screen (approved mockup: "Mix" v2)

Top to bottom, one scroll, title **Athletes**, **＋** in the toolbar (invite runner):

1. **Filters**
   - Plan type chips: `All N` · `Review N` · `Coached N`.
   - Menus: **Race ▾**, **Level ▾**, **Phase ▾**.
   - Filters apply to everything below, counts included, and are remembered for the session.
2. **This week · roster**
   - Three figures: sessions done %, key sessions done %, volume vs plan %.
   - A week stepper (this week and up to 3 back).
   - A **Group by** card (Race / Level / Plan type) with a done-% bar per group and the training mix (easy / long / quality by completed minutes).
3. **Highlights**: a horizontal strip of `highlight` signals. Tapping one opens that runner.
4. **Inbox sections**, each hidden when empty:
   - 🔴 **Act now**, 🔵 **Review & build**, 🟠 **Check in**.
   - Each runner appears **once**, in their most severe section.
   - A card shows: name, plan-type tag, the top signal's sentence (bold reason), a meta line (race · week/total · phase · days to race), and **one** primary action button picked from the top signal:

     | Top signal | Button |
     |---|---|
     | pain / sick / overload / missed_many | Adapt week |
     | plan_to_review | Review plan |
     | needs_plan | Build plan |
     | draft_unpublished | Open draft |
     | next_block_due | Build next block |
     | changes_to_approve | Review changes |
     | check_in signals | Note |

   - Further signals show as a compact second line.
5. 🟢 **On track** as a compact table: runner, week + phase, done % (14 d), and a 4-week load sparkline. Sortable by name / race date / done %. All runners are always reachable here or above.

The old Roster section goes away:
- Invite moves to **＋**.
- Pending invites (status `invited`) show as a small "Invited (2)" row at the end of the list, with the X / remove there.
- Remove-from-roster moves to the runner's ⋯ menu, keeping its confirmation dialog.
- The old charts (workout mix, missed-by-day, adherence trend, race breakdown) are removed from iOS. The Group-by card replaces them.

Empty states:
- No runners: one card with the invite field.
- Everyone on track: a "Nothing needs you today" line above the table.

---

## Phase 3: Runner detail = Plan tab + coach card

Tapping a runner calls the existing `app.enterAthleteView` and switches to the Plan tab, which already renders that runner's plan as they see it and shows the dark **Coaching X** banner with Exit. Nothing in the Plan tab's existing layout changes.

**New: `CoachFocusCard`**, inserted in `PlanView` directly under the race header, only while `actingAsAthlete != nil`. It's styled like `CoachReviewCard`, with the border colour following the status.

- **Why you're here:** the runner's signals as sentences, most severe first. If the runner is on track, it says so plus the next key session.
- **Recovery row**, only if data exists:
  - HRV status
  - resting HR vs the 28-day baseline
  - 7-day sleep average
  - last sync time
- **Latest coach note** to this runner, if any.
- **Actions** depend on the situation:
  - Pain / overload / missed → **Adapt this week**. Opens the existing `AdaptWeekSheet`, already coach-scoped through `adapt-week`.
  - Review plan → **Mark reviewed + note**. The card also shows the **plan check** (below).
  - Coached, no plan → **Build plan**. Opens the existing plan setup flow scoped to the athlete (requires Phase 1 #6); the result is a draft.
  - Draft → **Publish plan** (below).
  - Next block due → **Build next block**. Uses the existing `generate-next-block`, scoped.
  - Always available: **Note** (adds a `coach_notes` row, `target_type='general'`) and **Profile & zones** (the existing `CoachedAthleteProfileView` / `CoachEditPhysiologySheet`).
- **⋯ menu:** switch Review ↔ Coached, race history, remove from roster.

**Plan check for review** (new): `GET /api/coaching/athletes/{id}/plans/{plan_id}/review` returns:

```jsonc
{ "generated_block": 2, "reviewed_block": 1, "reviewed_at": "...", "reviewed_by": 12,
  "issues": [{ "code": "VOLUME_JUMP", "week": 9, "message": "..." }],   // services/plan_lint.lint_weeks over the stored workouts; the card lists issues in the unreviewed block(s) first
  "feasibility": "stretch",                                             // goal_feasibility verdict, null when there's no goal
  "levers": ["..."] }
```

- It is computed on read and nothing is stored, because lint findings aren't persisted today.
- `plan_lint.Issue` is only `{code, week, message}`, and `message` is English text written for the model retry prompt. So the device shows **one EN/VI sentence per `code`** plus the week number ("Week 9: volume jumps too fast"), and falls back to the raw `message` for an unknown code. `plan_lint.py` is not changed.
- **Review happens per block, and a block is one week today** (`settings.WEEKS_PER_BLOCK = 1`), so **every new week a runner generates comes back to the coach** (decided by you, knowing it means weekly reviews). The next block's weeks are written into the **same** `plans` row (`_generate_next_block_for_athlete` saves into `request.plan_id`), so the review state is the last reviewed block number, not a single flag.
- `generated_block` = the block containing the plan's highest generated `week_number` (`db.week_range_for_block` / `WEEKS_PER_BLOCK`).
- `POST .../review` with `{ "note": "optional" }` sets `coach_reviewed_block = generated_block`, `coach_reviewed_at = NOW()`, `coach_reviewed_by`, and saves the note as a `coach_notes` row (`target_type='plan'`, `target_id=plan_id`). Calling it again for the same block changes nothing (idempotent).
- Adapting a week does **not** clear the reviewed state. Generating the next block raises `generated_block`, so the plan shows up as "to review" again. When the **coach** generates the next block (`/api/coaching/athletes/{id}/generate-next-block`), that job also sets `coach_reviewed_block` to the new block on success: the coach built it, so there's nothing to review. A brand-new plan is a new row and starts unreviewed.

**Publish** (new): `POST /api/coaching/athletes/{id}/plans/{plan_id}/publish` approves every pending workout on the plan and flips a draft plan to active (reusing `approve_plan`), in one transaction. The same endpoint backs **Approve changes (N)** on an active plan. Per-workout approve stays available in the workout sheet.

Schema: `plans.coach_reviewed_block INTEGER`, `plans.coach_reviewed_at TIMESTAMPTZ`, `plans.coach_reviewed_by INTEGER REFERENCES users(id)`.

Access: every new endpoint uses `require_athlete_access` (or `require_coach` for roster), like the existing `/api/coaching/athletes/{id}/…` routes.

---

## Calls I made (check these)

- Existing coach–athlete links default to **Review**.
- The signal thresholds in the table above (130% overload, 5 days no sync, 3 misses, 0.6 adherence, and so on).
- Encouragement lives in the Highlights strip, not in a separate inbox section, so a runner isn't listed twice.
- A Review runner's new plan goes live immediately; review never blocks the runner.
- "Message" is a one-way coach note; the mockup's "Reply to runner note" is dropped because runners can't write notes.
- The overall view uses each runner's **own plan week**, not a calendar week, because workouts carry `week_number` rather than dates.
- The old roster-wide charts are removed from iOS.
- `plan_to_review` keys on **who created the plan**, not on the plan type, so a Coached runner who builds their own plan still shows up for review.
- Plan-check issues get one fixed sentence per code on the device; `plan_lint` isn't touched.
- `next_block_due` means the end of the generated weeks (the current block), not the race.
- A block the coach generated counts as already reviewed.

## Left to the builder

- Exact SwiftUI composition, view-model split, and which existing views to extract for reuse.
- Query shape for the batched signal inputs, as long as it meets the 500 ms target.
- Sparkline drawing (Swift Charts is fine).
- Exact EN/VI wording, within the copy skill's rules.

## Testing

- **Backend:**
  - pytest per signal rule (pure function, fixed `today`)
  - the overview additive-fields contract (old keys still present)
  - `plan_type` PATCH auth
  - review and publish endpoints (auth, idempotency, draft → active)
  - the Phase 1 #3 approval-count fix
- **iOS:**
  - unit tests for filter and aggregation math
  - signal → sentence mapping (EN + VI)
  - Phase 1 #1 / #4 / #6
- **Screenshots:**
  - re-record the coach fixtures (`scripts/record_fixtures.sh`) with a seeded roster covering every status
  - update `Phase6CoachScreenshots` to the new screens in light, dark and VI

## Rollout

Three PRs in order: Phase 1 → Phase 2 → Phase 3. Each one can be released on its own (Phase 1's iOS fixes need a TestFlight build). Both migrations (`plan_type` and `coach_reviewed_*`) ship with Phase 2, because the `plan_to_review` signal reads the review columns.

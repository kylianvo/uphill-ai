# Beginner goals and milestones: First 5K → First 10K

Date: 2026-10-20
Status: approved design; implementation plan to follow (`superpowers:writing-plans`).

## Why

A `start_running` plan today is open-ended. It has no target, no milestones and no event. The plan prompt's goal text only says "learn to run" (`plan_generator.py:1435`). The web header shows "Block ends {date}", iOS `goalText` returns nil, and the GoalPill is hidden because these plans have no `course_distance_km`. The one progress number the beginner rules care about, `users.max_continuous_jog_min`, is written only by adapt week, and the web never sends it.

The research behind this spec points the other way:

- **Goals help.** Goal-setting interventions have a medium effect on physical activity (McEwan et al. 2016, 45 trials, d = 0.55). In beginner running groups, reaching "30 min continuous" was predicted by self-efficacy and attendance (Loughborough prospective study). Autonomy-supportive coaching raised attendance (Frontiers in Psychology 2015).
- **Beginners drop out early and feel behind.** In a UK Couch to 5K cohort only 27% finished, most dropouts left before halfway, and they blamed injury (mostly lower leg and knee), progression that felt too fast, and guilt after missed sessions. The authors ask for slower, tailored progression, a flexible structure and injury-prevention advice from day one (IJERPH 2023).
- **The proven 0 → 5K shape** is NHS Couch to 5K: 9 weeks, 3 runs a week with rest days between, run/walk from 1 min / 1.5 min up to 30 min continuous. Weeks can be repeated, and graduates get a certificate and a pointer to parkrun.
- **5K → 10K is a second stage of about 8–12 weeks** (Higdon 10K Novice: 8 weeks, 3 runs, longest 6 mi; coach-written bridges about 12 weeks). This is weaker evidence: coach and vendor guides, not trials.
- **The 10% rule isn't backed by evidence.** A graded 13-week plan with a 10% cap had the same ~20% injury rate as an 8-week plan (Buist, BJSM). In the Nielsen GPS cohort of 874 novices, only progression above 30% a week was a weak warning sign. The bigger risk is a single session much longer than the longest run of the past month (BJSM, 5,000+ runners).

So a beginner picks **First 5K** or **First 10K** (with an optional event date), sees a milestone path during onboarding, and watches it tick off in the plan, either automatically from synced runs or by tapping "I did it". The plan prompt, the week brief and Coach Uphill all know the target.

## Decisions (from the athlete-owner)

- Ladder: **5K, then 10K**. The athlete picks which one the plan ends at.
- Tracking: **auto-tick from synced runs, with a manual fallback**.
- Event date: **optional, the plan flexes**, with a soft warning when it is too soon.
- v1 surfaces: **iOS onboarding, iOS plan view, web (same features), Coach Uphill chat**.

## Goals, non-goals, anti-goals

**Goals:** a visible finish line and short steps toward it. Progress that never punishes a repeated week. Milestones the athlete can trust: never ticked on weak evidence, and always correctable.

**Non-goals (v1):** a trail-race target, jog detection from laps or HR streams (COROS laps aren't stored), auto-advancing plan weeks when a milestone is reached, badges or social sharing, making `plans.race_date` nullable.

**Anti-goals:** turning typical-week ranges into deadlines ("you're behind"), letting the LLM decide whether a milestone is reached, or pushing an athlete to cut walk breaks to tick a box. The beginner rules' "the walk is prescribed, never a failure" still holds.

## Milestone ladder

The ladder is deterministic and lives in code in a new `backend/services/beginner_milestones.py`, alongside pure detection functions. The LLM never decides achievement.

| key | kind | threshold | stage | typical weeks |
|---|---|---|---|---|
| `first_session` | sessions | 1 | A | 1 |
| `jog_5` | jog_min | 5 | A | 3–5 |
| `jog_10` | jog_min | 10 | A | 4–6 |
| `jog_20` | jog_min | 20 | A | 5–8 |
| `jog_30` | jog_min | 30 | A | 7–10 |
| `first_5k` | distance_km | 5 | A, where a 5K target ends | 9–12 |
| `jog_45` | jog_min | 45 | B | 13–17 |
| `jog_60` | jog_min | 60 | B | 16–21 |
| `first_10k` | distance_km | 10 | B, where a 10K target ends | 18–24 |

- The typical-week ranges come from the C25K timeline and the bridge plans. They are shown as "usually around week X–Y" and are never compared against the current week to say "late". Exact numbers are the builder's call within these ranges.
- **Baseline:** onboarding asks for the current longest unbroken jog. Every jog milestone at or below it is stored as achieved with `source='baseline'`. `first_session` stays open.
- A 5K target shows rows `first_session` through `first_5k`. A 10K target shows all nine.

## Data

Follow the `db-migration` skill: every change goes in both `db.py:init_db()` and an Alembic migration.

- `plans.milestone_target TEXT NULL`: `'5k'` or `'10k'`. Set only for `start_running` plans. NULL means a legacy open-ended plan, which keeps today's behaviour and shows no milestone UI.
- `plans.has_target_event BOOLEAN NOT NULL DEFAULT FALSE`.
  - When true, the existing `race_name` and `race_date` hold the athlete's event name and date.
  - When false, `race_date` keeps its current meaning, a synthetic block end. This avoids changing a NOT NULL column and avoids making the required iOS `raceDate` optional across about 10 call sites.
- New table `plan_milestones`:
  - Columns: `plan_id`, `milestone_key`, `achieved_at TIMESTAMPTZ NULL`, `source TEXT` (`auto`, `manual`, `baseline` or `revoked`), `activity_id NULL`, `workout_id NULL` (the evidence).
  - Primary key `(plan_id, milestone_key)`, with an FK to plans that cascades on delete.
- When a jog milestone is achieved, by any source, also call `db.set_max_continuous_jog_min` (`db.py:2158`, which only ever goes up). The existing beginner rules, tier logic and adapt week then see the progress with no extra wiring.

## Plan length and event date

- **No event:** a 5K target defaults to 12 weeks, which is today's `start_running` default (`main.py:1418`). A 10K target defaults to 22 weeks.
- **With an event:** the plan length runs to the event date.
  - Minimum sensible lengths are 9 weeks for a 5K and 17 weeks for a 10K.
  - The minimum shrinks with the baseline: count the remaining milestones' typical weeks from the first one not yet achieved. For example, a baseline of `jog_30` gives about 8 weeks to a 10K.
- **Too-soon date:** this gets a soft warning in onboarding and the planner, and is never blocked. The warning reads roughly "Most beginners need about N weeks. Pick a later date, or plan to run/walk the event."
- **Event handling (my call):**
  - The event's distance is assumed to equal the target (5 or 10 km).
  - Its week is a light week with the event as the last session, and the event itself is a "run/walk is fine" session. There's no taper block and no race-path `+2` weeks.
  - The plan stays on the non-race `start_running` path. `has_target_event` only makes the length and the end date real.
- **Upgrading 5K → 10K (owner decision):**
  - The `first_5k` celebration, and a link in the path card, offers "Next: First 10K".
  - Accepting `PATCH`es `milestone_target` to `'10k'`. Existing rows carry over, and the stage B rows appear.
  - If there's no event, `total_weeks` is extended to the 10K default, counted from the plan start. The extra weeks are generated by the normal next-block flow.
  - With an event, the athlete is asked whether to keep the event or clear it.
- **Request fields:** onboarding (`OnboardingRequest`) and generate-plan (`PlanGenerateRequest`) gain `milestone_target`, `current_jog_min`, `event_name` and `event_date`.
  - `current_jog_min` writes `max_continuous_jog_min` and seeds the baseline.
  - The coach endpoint currently ignores dates for non-event goals (`main.py:2151`). For `start_running` with an event, it must use `event_date`.

## Auto-detection

`activities` stores no laps or splits (`db.py:410`). The watch matcher also runs in shadow mode by default (`MATCHING_SHADOW_MODE`, `config.py:194`): it records matches but doesn't mark workouts complete. So jog credit hangs off **completed workouts**, not raw matches.

- **jog_min (owner decision):** credit comes from a run workout in the plan becoming `is_completed`, whether the athlete ticked it or the live matcher did once shadow mode is off.
  - If the workout is continuous (no `walk_interval_value`), the credit is its planned run duration in minutes.
  - If it is run/walk, the credit is the planned `interval_rep_value`, the longest jog segment in it.
  - This works with or without a watch.
- **distance_km:** any synced running activity (any provider, matched or not) with `distance_km ≥ threshold` (5.0 or 10.0), dated within the plan. Run/walk counts: "first 5 km" means covering it, which matches parkrun.
- **sessions:** the first completed run workout in the plan.
- **When it runs:**
  - Jog and session milestones are checked when a workout's completion flips to true (the workout-log update path).
  - Distance milestones are checked when an activity is stored (COROS sync and Apple Health sync; the builder finds the call sites).
  - Both checks only run for the active `start_running` plan with a non-null `milestone_target`.
  - Both are idempotent (`INSERT … ON CONFLICT DO NOTHING`), and an existing row of any source is never overwritten.
- **Un-ticking a workout** doesn't remove an achieved milestone. That's my call: celebrations shouldn't vanish because of a stray tap, and the athlete can undo the milestone directly.
- **Manual routes:**
  - `POST /api/plans/{plan_id}/milestones/{key}` marks a milestone achieved (`source='manual'`), replacing a `revoked` row if there is one.
  - `DELETE` on the same path turns the row into `source='revoked'` with `achieved_at` NULL, rather than deleting it. Detection then can't bring it back on the next sync. A revoked milestone shows as not achieved.
  - `DELETE` doesn't lower `max_continuous_jog_min`, which only goes up.
  - The routes are athlete-only in v1 (my call), with the ownership check used by the other plan routes. Coach-scoped mirrors can come later.
  - Order isn't enforced, but clients suggest the next open milestone.

## API

The active-plan response gains a `milestones` object, or null when `milestone_target` is null:

```json
{
  "target": "10k",
  "has_event": true,
  "items": [
    {"key": "jog_5", "kind": "jog_min", "threshold": 5, "stage": "A",
     "typical_weeks": [3, 5], "achieved_at": "2026-11-02T07:10:00Z", "source": "auto"}
  ],
  "next_key": "jog_10"
}
```

`PATCH /api/plans/{plan_id}/milestone-target` with `{"target": "10k"}` performs the upgrade.

The server sends keys only. Clients localize the labels (en/vi).

## LLM touchpoints

These follow `.claude/skills/llm-change-process/SKILL.md`: Langfuse prompt versions, a golden-set eval, then staging → production labels. Put the checklist in the PR.

- **Plan prompt:** the `start_running` `goal_description` names the target, the next milestone and the event when there is one.
  - `_beginner_rules` (`plan_rules.py:38`) gains a **stage B** clause for a 10K target once `jog_30` is reached. Run/walk is done. Add one long run a week that grows measured against the longest run of the past 30 days, not just 10% weekly time. There is still no intensity.
  - Whether stage B moves the athlete out of the BEGINNER tier is the builder's call: check `athlete_tier.explain_tier`, where a beginner goal currently forces BEGINNER.
  - Stage B takes effect at the **next generated block** (my call). Adapt week already reads the raised `max_continuous_jog_min`, so no `week_rebuild` change is needed beyond the brief fact below.
- **Week brief:** add a fact to the decision log (`main.py:2606`, `week_rebuild.py`): "Milestone: next = jog_20 (usually wk 5–8), best so far = 12 min".
- **Coach Uphill:** add a milestone block to `build_chat_context` (target, achieved list, next, event). This lets the coach answer "how am I doing?" and celebrate.

## UI: iOS (`ios-native/UphillAI/`)

**Onboarding** (`Core/Plan/PlanSetupDraft.swift`; `SetupStep.steps` has `questions = []` for `.startRunning` today):

1. **Target:** First 5K / First 10K, two tiles in the existing goal-tile style.
2. **Today:** "How long can you jog without stopping?" The options are: not yet, 1–5 min, about 10 min, 20+ min. This maps to `current_jog_min` 0, 3, 10 or 20, which is the builder's call.
3. **Event (optional):** a toggle, then a name and date, with the soft warning inline.
4. **Review** (`SetupReviewStep`): a **"Your path"** preview.
   - It shows the ladder with typical-week ranges and the baseline milestones pre-ticked.
   - It carries one line of tone: "Repeating a week is normal. You move on when you're ready."

**Plan view** (`Features/Plan/PlanView.swift`, `SummaryCarousel.swift`), for start_running plans with a target:

- **Header:** "First 5K · 3 of 6 milestones", plus "N weeks to {event}" when there is one.
- **`MilestonePathCard`** replaces `raceCard` in the carousel.
  - It is a vertical ladder: checkmarks for achieved milestones, and the next one highlighted with its typical-week range and an **"I did it"** button that asks for confirmation.
  - Tapping it opens a full list with undo.
- **Celebration** when a milestone is newly achieved, by any source except baseline.
  - It is a sheet with a SwiftUI animation, `.sensoryFeedback(.success)` and a teaser for the next milestone.
  - `first_5k` and `first_10k` get a certificate-style card.
  - Seen-state is stored locally, keyed by plan and milestone, so a celebration shows once per device.
- Reuse the `UH` tokens, `.uhCard()` and `PrimaryButtonStyle`.

**Models:** add optional `milestones`, `milestoneTarget` and `hasTargetEvent` to `Plan`, decoded snake_case with nil defaults. Add a test in `PlanDecodingTests`.

**Copy:** vi strings go in `Localizable.xcstrings` via the `uphill-ai-vietnamese-copy` skill.

## UI: web (`frontend/src`)

The web is also the Android build (Capacitor).

- **`views/OnboardingWizard.tsx`:** the `fitness_start` step for start_running gains the target, current jog and optional event, matching iOS.
- **`views/PlannerView.tsx`:** the start-running block replaces the bare "Duration (weeks)" select with target and event fields. The duration is derived.
- **New `components/MilestonePath.tsx`:** it goes in the `PlanSummaryCarousel` goal slot and replaces the "Block ends" header text for these plans. It carries the same ladder, the "I did it" control and a celebration toast.
- **Plan labels** (`hooks/usePlanner.ts:455`, `app/app/page.tsx:2050`): "First 5K plan" or "First 10K plan" replaces "(Ends date) | Start running".
- **Copy:** vi via the Vietnamese copy skill.

## Delivery

This ships as stacked PRs, the same pattern as #145 → #148:

1. **Backend:** columns, table, ladder module, detection hook, API fields, manual endpoints, tests.
2. **LLM:** plan prompt, week brief and coach context, via the LLM change process.
3. **Web UI**, with screenshots (`ui-screenshot-evidence`).
4. **iOS UI**, with simulator screenshots and a TestFlight build.

PRs 3 and 4 depend only on PR 1 and can run in parallel.

## Verification

- **Backend:** unit tests for `beginner_milestones`:
  - baseline seeding;
  - distance rule;
  - jog credit for continuous and run/walk workouts on completion;
  - un-ticking keeps the milestone;
  - revoked rows survive re-detection;
  - idempotency;
  - a 5K target ending at `first_5k`;
  - the 5K → 10K upgrade carrying rows over.

  Also API tests for the plan response and manual tick/undo, and a check that `init_db` and Alembic agree. Integration tests run only against a scratch DB (they TRUNCATE).
- **LLM:** `golden_eval.py compare` for the plan service, with no regression on beginner cases.
- **Web:** vitest for `MilestonePath`. Screenshots of onboarding (5K, 10K, event warning) and of the plan view (path card, after "I did it", celebration).
- **iOS:** unit and decoding tests. A simulator walkthrough with en and vi screenshots: onboarding → "Your path" → plan card → "I did it" → celebration.
- **End to end:**
  1. Create a start_running 10K plan with a baseline of 3 min.
  2. Tick a continuous 10-minute workout complete, and check that `jog_5` and `jog_10` tick and `max_continuous_jog_min` rises to 10.
  3. Sync a 5.2 km run, and check that `first_5k` auto-ticks.
  4. Check that the next week brief and a coach reply both mention the milestone.

## Sources

- NHS Couch to 5K running plan: https://www.nhs.uk/better-health/get-active/get-running-with-couch-to-5k/couch-to-5k-running-plan/
- "Couch-to-5k or Couch to Ouch to Couch!?" (IJERPH 2023): https://pmc.ncbi.nlm.nih.gov/articles/PMC10487403/
- Buist et al., graded training programme RCT (BJSM): https://bjsm.bmj.com/content/43/2/155
- Nielsen et al., progression in weekly running distance: https://vbn.aau.dk/da/publications/excessive-progression-in-weekly-running-distance-and-risk-of-runn
- McEwan et al. 2016, goal-setting meta-analysis: https://researchportal.bath.ac.uk/en/publications/the-effectiveness-of-multi-component-goal-setting-interventions-f/
- Beginner running groups, prospective study (Loughborough): https://repository.lboro.ac.uk/articles/journal_contribution/Prospective_study_of_beginner_running_groups_psychological_predictors_and_outcomes_of_participation/20480781
- Autonomy support in a beginners' running programme (Frontiers 2015): https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00648/full
- Hal Higdon 10K Novice: https://www.trainingpeaks.com/training-plans/running/10km/tp-139211/hal-higdon-10k-novice
- Couch to 10K bridge plans: https://www.runstreet.com/blog/couch-to-10k, https://marathonhandbook.com/couch-to-10k-training-plan/

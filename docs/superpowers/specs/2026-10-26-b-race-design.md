# B-races: tune-up races inside a training block

Date: 2026-10-26
Status: draft for the owner's review
Mockups: https://claude.ai/artifact/XHSuX1qZMixkVMDZHZzJzj (private canvas, five phone screens)

## Why

Runners often enter a smaller race while they train for their goal race: a friend's 25K, a local trail race, a race chosen
as a rehearsal. Today the app has no idea these exist. The plan keeps its long run on race day, has no mini-taper and no
recovery afterwards, and nobody tells the runner whether the race helps or hurts the goal. The only trace in the code is
that a mid-plan workout of type `Race` is left alone by `rows_after_race` (R-G2 in `docs/plan-rules.md`).

A good coach handles this in three moments. Before the race, they give an honest opinion: is this a good test or a risk
to the goal, which distance, and how hard to run it. During race week, they trim the days before and protect the days
after. After the race, they debrief: what the result says about the goal, what the rehearsal taught, how long to recover.

## Doctrine (from the KB, Scott Johnston / Evoke Endurance)

- A B-race is a **training session** and a **systems check** (fuel, gear, poles, pacing), not a goal event.
- Best placed in the **Specific / Build** period. For 50–100 km B-races, **4–8 weeks** before the A-race.
- **Never within the final 10–14 days** before the A-race.
- **Mini-taper only**: 2–4 days, volume down about 30–50%, 2–3 short strides. No full taper.
- **Re-entry**: 3–7 days of easy Zone 1 (or rest, light cycling) before structured intensity returns. Heavy or flat legs:
  keep runs to 45–60 min Zone 1 until the bounce is back.
- Races take "money out of the fitness bank". **Don't stack** races; don't chase an all-out result if it costs the A-race.

## Decisions

**The owner's:**

1. The app knows about B-races and puts them in the plan. They show as **next races** beside the A-race.
2. The app gives an **opinion**: a good test or a risk. The runner can **cancel** a B-race at any time.
3. B-races get a **taper and race-week advice**, the same way the A-race does.
4. B-races can be added **while creating a plan** or **at any point during it**.
5. B-races use the **A-race lookup**: match the name against the race list for the course, distances, climb and past results.
6. The debrief covers **both**: the time against a prediction and what it means for the A-race, **and** how the
   rehearsal went (fuel, pacing, gear).
7. The five mockups are the agreed direction.

**Mine (the owner can overrule any of these):**

- **Four verdict levels**, set by rules in code. The coach only words them.
- **The runner always has the final say.** Every level can be kept. The app never refuses; it plans honestly around the choice.
- **The safer option is one tap**: a shorter distance from the race's own options, or "run it as a training race"
  (long-run effort). It is the primary button whenever the level is not "good test".
- **Inside the final 14 days** the runner can still enter the race, but the plan treats it as a training race: no
  mini-taper of its own, and the A-race taper and race week are never cut. The coach says plainly that racing it
  all-out risks the goal.
- **B-races fall after the plan start and before the A-race.** A race after the A-race belongs to the next plan.
- Platforms: **iOS and web** (both web shells), plus **Coach Uphill chat** can propose adding a race.
- **v1 is for race plans only** (`goal_type` finish / time / optimal). Start-running, return and recovery plans don't offer B-races.
- **At most 3 planned B-races per plan.**

## Goals, non-goals, anti-goals

**Goals:** honest, consistent advice the runner can trust; a plan that bends around the race without losing the
goal's key sessions; a debrief that turns the race into lessons for the A-race.

**Non-goals (v1):** B-races on non-race plans; changing which race is the A-race; course-specific pacing for the B-race
(Pace Strategy already exists for that); social or results sharing; lap or split analysis (activities store no laps).

**Anti-goals:**
- The model deciding the verdict, the taper or the recovery length.
- A verdict that changes from one tap to the next with no new facts.
- Lecturing, or blocking a runner who has made up their mind.
- A B-race that silently eats the A-race taper or the peak week.

## The verdict engine

A new pure module, `backend/services/b_race.py`, the same shape as `beginner_milestones.py`: dataclasses, no DB access
in the rules, one impure wrapper.

**Inputs:**
- A-race: date, distance, climb.
- The B-race: date, distance, climb, effort (`race` or `training`).
- The plan's phase for the B-race week (from `plan_journey` phases).
- The runner's longest run of the last 6 weeks, in minutes and km (`fitness_snapshot`, else completed workouts).
- The other planned B-races.

**Derived:**
- `days_before_a`.
- `load_ratio`: B-race distance (climb-adjusted, as `effort_km` in `athlete_tier`) over the longest recent run.
- `size_ratio`: B over A, same adjustment.
- `recovery_days` and `taper_days` (below).

**Levels, first match wins** (thresholds are a starting point; the builder tunes them in tests):

| Level | When |
|---|---|
| `not_recommended` | `days_before_a < 14` |
| `risky` | the recovery window overlaps the A-race taper or the peak week; **or** another B-race (race effort) within 21 days, 28 if either is ≥ 42 km; **or** `load_ratio > 1.5` at race effort |
| `conditions` | `load_ratio` 1.2–1.5 at race effort; **or** `days_before_a` 14–27 at race effort; **or** base phase with `size_ratio > 0.6` |
| `good` | everything else |

`training` effort lowers the cost. Its recovery is about half, and it skips the `load_ratio` and `days_before_a` race-effort rules.

**Taper and recovery** (from the doctrine):

| B-race (effort-km) | Mini-taper | Recovery before intensity returns |
|---|---|---|
| ≤ 21 | 2 days | 3 days |
| 22–42 | 3 days | 5 days |
| 43–70 | 3 days | 7 days |
| > 70 | 4 days | 10 days (discouraged before an A-race; usually `risky`) |

Training effort: taper 1–2 days, recovery about half.

**The safer suggestion.** If the level is not `good`, try the alternatives and keep the first one that scores `good`:
1. Each shorter distance the matched race offers, at race effort.
2. Then the same distance at training effort.
3. Then shorter distances at training effort.

If none is `good`, suggest training effort at the shortest distance.

**What the verdict returns:**
- `level`;
- reason codes (`too_close`, `overlaps_taper`, `overlaps_peak`, `stacked`, `longer_than_trained`, `base_phase`);
- the numbers behind them;
- `cost`: which planned sessions change and what happens to peak-week volume;
- the suggestion.

**Cost and goal confidence.** `cost` comes from a dry run of the taper and recovery placement over the plan's current
workouts. The goal-confidence line on the risky screen comes from re-running `a_gate` / `goal_service.path_for` with that
cost. If that is too heavy, drop the line in v1 (builder's call).

## Data

Follow the `db-migration` skill: `db.py:init_db()` and an Alembic migration that agree.

New table **`plan_races`** (the A-race stays on `plans.race_*`; this table holds only B-races):

| Group | Columns |
|---|---|
| Keys | `id`; `plan_id` (FK → plans, cascade on delete) |
| Race | `race_name`; `course_ref` (the matched race-list entry); `race_date`; `distance_km`; `elevation_gain_m` |
| Plan | `effort` (`race` / `training`); `status` (`planned` / `cancelled` / `done`) |
| Advice | `verdict` JSONB (level, reasons, numbers, suggestion, cost); `verdict_text` JSONB (the worded opinion, en/vi); `predicted` JSONB (low/high seconds) |
| Result | `result_seconds`; `activity_id` (FK → activities, set null) |
| Debrief | `debrief` JSONB (answers, coach text) |
| Times | `created_at`; `cancelled_at` |

**The race in the calendar** is a normal workout row with `type = "Race"`, `title` = the race name, on its date, linked
by `plan_race_id` (a new nullable column on `workouts`). Existing code already treats `Race` correctly:
- `plan_lint` skips it for session caps;
- `rows_after_race` only acts on the last race, which is the A-race;
- `coros_plan_window` already handles race rows.

## Placing the race in the plan

**The rule that makes it reliable:** the model may write the sessions around the race, but code owns the race row, the
taper days and the recovery window. After any generation or rebuild that touches a B-race week, a guard runs, like
`apply_priority_guard`, and enforces:

- **The race row exists**, on its day, and nothing else is scheduled that day.
- **Taper days are capped**: each is easy and at most 50% of that week's normal easy-session minutes, and no hard
  session falls in the taper window. The last taper day may carry 2–3 strides.
- **The recovery window is easy**: every session is Zone 1, 45–60 min at most. No intensity and no long run.
- **The race replaces that week's long run**: if the race week still has a separate long run, it is removed.
- **The A-race taper and race week are untouched.**

Lint findings for these rules join `plan_lint`, so the existing corrective retry also covers them.

**When a race is added or cancelled:**
- **Weeks already generated:** rebuild the race week and the recovery week through the existing `week_rebuild` pipeline.
  The race goes in as a fixed row with a `B-RACE` rule block in the prompt that spells out the days.
  - I'd apply the rebuild automatically: the runner already confirmed the race. The runner sees a short "what changed"
    summary built from `build_diff`.
  - History rows are never touched; `week_rebuild` already protects them.
- **Weeks not generated yet:** stored on the plan. The next-block flow reads `plan_races` and builds around it.
- **Cancel:** set `status='cancelled'`, delete the race row, and rebuild the same weeks back to normal. Logged sessions stay.
- **Fallback:** if the model fails, the rule-based layout (`week_layout`) has to honour the race and the guard too.

**At plan creation**, B-races go in the setup flow as an optional step after the race date: "Any other races before
your goal?". The first generation then builds around them. Each gets its verdict in the review step.

## Prediction and debrief

**Prediction:** `goal_service.run` with the B-race course and the plan's context, using its rules tier, or Gemini when
`GOAL_LLM_ENABLED`. Store the B-band as `predicted`. If the course has no distance, there's no prediction; say so.

**Finding the result:**
- **Automatic:** a running activity on the race date (±1 day) whose distance is within 15% of the B-race distance. It
  links by `activity_id` and fills `result_seconds`.
- **Manual:** otherwise, a "How did it go?" entry with a typed finish time.
- **Race history:** the result is also written to `race_results` as a manual entry, so it feeds the goal anchors.

**The debrief has two parts:**

1. **Time against prediction**, and what it means for the A-race.
   - Re-run the goal assessment with the new result.
   - If the suggested Time Target changes, the runner confirms it, as the Goal pill already works. The app never changes the target silently.
2. **The rehearsal**: three one-tap questions.
   - Fuel: went to plan / stomach trouble / skipped some.
   - Pacing: even / too fast early / held back.
   - Gear: all good / something to change.
   - An optional note.

**Coach text and recovery:** the coach's debrief is model-worded from the facts and grounded the same way as `coach_nudge`
(every number must appear in the facts), with a rule-written fallback in en and vi. The recovery days come from the table
above. For a race kept against a `risky` verdict, add 2 days.

## LLM touchpoints

These follow `.claude/skills/llm-change-process/SKILL.md`: Langfuse text prompts with in-code fallbacks, a golden check,
and staging → production labels.

| Prompt | What it words | Inputs |
|---|---|---|
| `b_race_opinion` | the verdict | level, reasons, numbers, suggestion; 2–4 sentences, grounded |
| `b_race_debrief` | the debrief | time vs band, goal effect, answers, recovery |
| plan prompts | the `B-RACE` rule block for `plan_generation` and the rebuild | the fixed days, as a new variable or appended to the existing rules variable |

- **Week brief and coach review:** add race-week facts (B-race date, taper days, the rehearsal focus).
- **Coach Uphill chat:**
  - add the next races to `build_chat_context`;
  - add a `propose_b_race` tool on the pattern of `propose_rebuild_week`, which shows a card the runner confirms.

## UI

**iOS** (`ios-native/UphillAI/`), following the mockups:

- **Add a race sheet:**
  - race search (the same matcher as setup), distance chips, date and effort;
  - the verdict card, coloured by level with the coach's text;
  - primary and secondary buttons.
- **Risky and not recommended:** the "what it would cost" list; the safer option first; "Keep it anyway" in red.
- **Plan screen:**
  - a **Next races** card in the summary carousel: B-races and the A-race with date, badge and "+ Add race";
  - tapping a race opens it: verdict, prediction, change effort or distance, cancel.
- **Race week:** the existing week brief and coach review, carrying race-week facts; taper days marked.
- **Debrief:** a sheet that opens the day after the race (a push notification, plus a card on the plan screen until it is done).
- **Copy:** vi through the Vietnamese copy skill.

**Web** (`frontend/src`): the same flows. The Next races card shows in both shells (v1 is what production runs). The
add and debrief flows are modals.

## API (sketch, the builder finalises)

- `GET /api/plans/{id}/races`: the B-races with verdict, prediction and status.
- `POST /api/plans/{id}/races/assess`: assess without saving. It drives the live verdict as the runner changes distance or effort.
- `POST /api/plans/{id}/races`: add a race. It returns the race and a rebuild job when weeks change.
- `PATCH /api/plans/{id}/races/{race_id}`: change distance, effort or date. It re-assesses and rebuilds.
- `DELETE /api/plans/{id}/races/{race_id}`: cancel.
- `POST /api/plans/{id}/races/{race_id}/result` and `.../debrief`: the time, and the answers.
- The plan setup bodies (`OnboardingRequest`, `PlanGenerateRequest`) gain an optional `b_races` list.

Ownership checks follow `_verify_plan_ownership`. Coach-scoped mirrors can come later.

## Delivery (stacked PRs, as #145 → #148)

1. **Engine and data:** `b_race.py`, the table, the API, the guard and lint rules, unit tests. No UI.
2. **Plan integration:**
   - generation, rebuild, cancel and the `week_layout` fallback;
   - the `B-RACE` prompt block.
3. **Words:**
   - the opinion and debrief prompts, the week-brief facts, the coach chat tool;
   - the LLM change process.
4. **Web UI**, with screenshots (`ui-screenshot-evidence`).
5. **iOS UI**, with simulator screenshots in en and vi, then a TestFlight build.

PRs 4 and 5 depend on 1–3 and can run in parallel.

## Verification

- **Engine unit tests:**
  - each level and each reason;
  - the 14-day hard line;
  - stacking;
  - training effort lowering the cost;
  - the suggestion search;
  - taper and recovery lengths by distance.
- **Guard tests:** a model draft that keeps a long run on race day, puts intervals in the recovery window, or touches
  the A-race taper is corrected.
- **Rebuild tests:**
  - add, then cancel, returns the weeks to normal;
  - logged history is untouched;
  - a race in an ungenerated week is honoured by the next block.
- **`scripts/plan_reliability.py`:** add B-race scenarios (25K at 6 weeks, 50K at 3 weeks, 25K at 10 days, two races
  stacked) to the rule-based scorecard.
- **Real model:** one paid `plan_live_check` run with a B-race, only when the owner OKs it.
- **UI:** screenshots of each mockup state on web and iOS, en and vi.

## Left to the builder

- Exact thresholds, inside the doctrine above.
- How `cost` is computed.
- Whether the goal-confidence line ships in v1.
- Push notification copy and timing.
- How the "what changed" summary looks.
- Whether the add flow's live assessment is debounced or explicit.

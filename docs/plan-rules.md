# Plan rules: create, next block, adapt week

Every number in a plan should trace back to a rule on this page. Use the rule IDs when you
answer an athlete ("why is my long run only 180 min?") or a coach review. Each rule names its
source (the book is *Training for the Uphill Athlete*, "UA") and where it lives in code.

How a plan is made, in one line: **Gemini drafts each week, then code enforces the rules below,
then the lint checks the result (one retry) and the quality bar scores it.** When Gemini
fails, the rules-only fallback builds the week and the same enforcement runs on it. So the rules
hold whichever engine wrote the week.

Paths are under `backend/services/` unless stated.

---

## 0. Where the rules come from (read this before changing plan code)

**Order of authority** when two sources disagree:
1. **Coach Quang Tran** for ultras (45 km+) trained on a weekly mountain day: the target user is a HCMC runner on
   flat roads on weekdays with Núi Dinh (60 m D+/km) at the weekend. His rules, as he gave them on 2026-10-22/23:
   - Long run on the mountain day, in hours: weeks 1–2 3 h, weeks 3–5 4 h, weeks 6–8 5 h, peak 6–7 h (30–35 km
     at Dinh); recovery weeks 4 h. 50 km: 3 h ×4 → 4 h → 4.5 h → 5 h peak, recovery 3 h.
   - Weekday easy runs 1 h–1 h 30 for 100 km+ (45 min is too little).
   - Quality (hill repeats or intervals, ≤1 h 30 each): finishers 1 a week, advanced/elite 2 a week.
   - +20% volume, all of it on the weekdays, never on the long run.
   - A runner at 50–60 km/week stays at 50–60 km for the first 2 weeks.
   - A back-to-back weekend is allowed as the athlete's choice (owner, 2026-10-27).
2. **Uphill Athlete** (*Training for the Uphill Athlete*, the KB in `kb_seed/scheduler.json`) for everything else:
   aerobic base first (80/20, Zone 1–2), the AeT gate for aerobic deficiency, 3:1 loading, growth of about 10% a
   week, ME on top of the running and not in the last 10–14 days, a 2–3 week taper, specificity (climbing, descents,
   time on feet) in the last 8 weeks, and no making up missed sessions.
3. **Code defaults** fill the gaps and must not contradict 1 or 2.

Where Quang and the book disagree (session cap, long-run share, ladder growth, weekday minimum, start hold) the
table in `docs/superpowers/specs/2026-10-23-ultra-rules-design.md` records the decision and why.

**Where code differs from what Quang said, decided with the book** (NotebookLM on the KB sources, 2026-10-28):
- **Quality only in the last 8 weeks before the taper**, 0 in Base (firm rule). Short plans open with up to 3 ME
  weeks, then Zone 3 replaces ME for the rest of the Specific weeks (firm rule). The exception, Zone 3 in Base for a
  tested runner with an AeT–AnT gap ≤10%, is not built (owner: too few such runners).
- **Advanced runners get 1 Zone 3 session a week**, not 2: two need tested thresholds, an elite engine and 15–20 h+
  weeks (`quality_dose`, `ultra_gated` in `plan_generator.py`). Estimated thresholds keep the Base gate on, which
  holds every week to one session.
- **Estimated thresholds are treated as aerobic deficiency** (firm rule): Base in Zones 1–2. No scheduled AeT drift
  test (owner, 2026-10-22 and 2026-10-28).
- **Recovery weeks stay at ≤80% of the week before** (book: cut 30–50%), because Quang's recovery long run (3–4 h)
  and the weekday minimums leave no room for less; recorded as C9 in the spec.
- **Never 4 loading weeks into the peak** (firm rule, modulation): when the peak lands on a 4th week, the week
  before it is the recovery week (R-P2). Long plans hold 5 h for many weeks and reach 6 h and 7 h once each, a
  recovery week apart.
- **Taper**: 50 km keeps one taper week plus race week (= the book's 2 weeks; the 5 h run is 14 days out); 100 km+
  tapers two weeks plus race week (R-P3).

**Before you change plan generation, next block or adapt week:**
1. Find the rule ID below that covers the change. A new behaviour gets a new rule ID here, with its source
   (Quang, the book, or the owner) and the code that enforces it.
2. Enforce it in code after the model (post-processing), and add a `plan_lint` check when the model could break it.
   A rule that only lives in the prompt is not a rule.
3. Write the failing test first; keep `python backend/scripts/plan_reliability.py` at all scenarios passing.
4. Update this page in the same PR. If the change departs from Quang or the book, add it to the spec's deviation
   table and to the list above.
5. For a bigger change, run the persona plans (`scripts/plan_live_personas.py`, Quang personas `q_*`) and judge them
   against this page before shipping.

---

## 1. Inputs and who decides what

| Input | Where it comes from | Used for |
|---|---|---|
| Race: distance, D+, cut-off, target time, date, terrain | plan wizard; cut-off saved on `plans.cutoff_time_hours` | race demands (R-D) |
| Recent load: weekly km (and vert) | watch (≥3 full weeks, `fitness_snapshot`: the **median** of the last 4, so one down week doesn't pull it under), else typed `current_weekly_km` | week 1, ramp, tier |
| Readiness flag | watch (`fitness_snapshot.readiness`) | R-V1 hold while fatigued |
| Zone 2 pace, AeT/AnT HR, `threshold_source` | profile; COROS threshold pace if synced | zones, AeT gate (R-I1) |
| Days, long-run day, gym, treadmill (max incline), stairs, training mountain, mountain days | wizard / adapt form | layout, climbing venues |
| Long-day format: one long mountain day or a back-to-back weekend (`plans.long_day_format`) | wizard / next block (web, iOS) | R-U1 |
| Tier (beginner … elite) | `athlete_tier.explain_tier`: load, performance, measured physiology, experience | every cap below |

---

## 2. Rules for every week (create, next block and adapt)

### Race demands and feasibility
- **R-D1 Race demands.** `goal_demands.compute` turns the race into: longest session, peak-week
  km, climb rate. Finish-only goals use the cut-off, with a safety margin. *Source: UA long-run
  and specificity chapters.*
- **R-D2 Feasibility.** `goal_feasibility.assess` says supported / stretch / unsupported and
  names the levers (more days, more weeks, steeper venue, mountain access). A stretch goal keeps
  the plan; it doesn't hide the gap.
- **R-D3 Road marathon.** A flat course (<12 m D+/km, 30–48 km) gets a long run up to 180 min
  (or 75% of race time) and marathon-pace long runs in Build.

### Phases
- **R-P1 Phases set by code**, not by the model (`PlanGenerator.phase_for_week`): Base → Build →
  Peak → Taper → Race week → Recovery.
- **R-P2 Deload every 4th week**, never the last build week (`is_deload_week`). When the last build week is itself
  a 4th week, the week before it is the deload, so no plan loads 4 weeks in a row into its peak (2026-10-28; e.g. a
  10-week 50 km: 4 h, 4 h 30, recovery, 5 h peak). A deload week is
  **at most 80% of the week before**, cut from easy runs (`_ramp_volume`), checked again against the week
  before as it finally stands (`_cap_growth`). On a mountain-day ultra the deload's easy minutes go into runs of
  at least 30 min, not runs too short to keep. *UA: 3:1 loading.*
- **R-P3 Two-step taper** for plans of 12+ weeks and for every 100 km+ race (`taper_weeks(total, km)`; a 10-week
  100 km plan puts its 7 h long run 3 weeks out, not 13 days) (code: about 70%, then 50% of the peak week; one step
  at 50% for shorter plans; the lint holds each taper week to ≤85% of the week before). Taper weeks
  are built by code from the real peak (`TAPER_BY_RULES`), with no new hard work. *UA taper.*

### Volume
- **R-V1 Week 1 from recent load.** Week 1 is at most **10% above** what the athlete runs now
  (`recent_weekly_minutes` = weekly km × own Zone 2 pace; `RECENT_LOAD_GROWTH`). The cut comes off
  easy runs; the long run, ME and quality sessions stay. With no data: 180 min. A mountain-day
  minimum can still push week 1 higher; that's the athlete's choice. While the watch says the athlete is
  fatigued (`readiness_flag` fatigued/overreaching) weeks 1–2 **hold** at recent load, no +10%
  (`start_load_growth`). A mid-week start gets its **share** of week 1 (Thursday: 4/7 of the load and of the
  4 kept run days, `first_week_share`); the lint asks for that many days, not the full week's.
- **R-V4 Over the limit with every easy run at its minimum** (`_fit_week`, for R-V1, R-V2 and R-P2): whole
  easy runs go (a second run on a double day first, then a run on an ME day, then the shortest) while the
  week is over by at least half a run, keeping at least **4 run days** (fewer only when the athlete trains
  fewer). A week held this way may use fewer days than the athlete chose; the lint's `DAYS_SHORT` accepts
  it (start load in weeks 1–2; growth on mountain-day ultras). *Plan 131 (2026-10-26): seven 60-min
  weekday runs plus doubles gave a 49 km runner an 89 km week 2.*
- **R-V2 Weekly growth cap.** No week goes above the week before × (1 + tier
  `max_weekly_progression`); the excess is trimmed from easy runs. Return from a deload is
  measured against the larger of the last two weeks. On a mountain-day ultra it runs again after the
  week shape (`_cap_growth`, which lifts weekday runs to their minimum), on the rest of the week: the
  long run's ladder step (and its back-to-back day) is R-U1's. No extra cap on the whole week: it would use up
  the room Quang gives the weekdays (a 15% cap was tried on 2026-10-27 and cut plan 131's peak from 109 to 77 km).
  After a recovery week both the generator and the lint measure against the week before it.
- **R-V3 Ramp toward the goal.** Build weeks grow toward the race's peak-week volume
  (`_ramp_volume`), within R-V2 and the tier's weekday maximum.

### Long run
- **R-L1 Long run grows toward the race's time on feet**, asked at most +20%/week (the lint allows +25%,
  `LONG_RUN_JUMP`), capped by the session cap (300 min; 480 min sub-elite 100-mile) and the long-run share
  (tier cap ±5%, `LONG_SHARE_SOFT`). Mountain-day ultras follow R-U instead.
- **R-L2 Back-to-back weekend** for ultras in the last build weeks (mountain-day ultras: only by the athlete's
  choice, R-U1).
- **R-L3 Taper long run** about 60%, then 40% of the peak, and inside the long-run share even when
  short taper runs are dropped (`_fit_taper_long_share`).
- **R-L4 Mountain minimum.** On a mountain day the long run is at least the athlete's chosen
  minimum (default 180 min), except in recovery/taper/deload weeks ("chill" mode).
- **R-L5 Race rehearsal.** On an ultra, Build/Peak long runs of 5 h+ carry the race pack, 60–90 g carbs per hour
  and, once, a pre-dawn start with a headlamp (set in code, `_race_specifics`, and in the ladder prompt).

### Ultras with a mountain day (R-U, coach Quang 2026-10-22)
Races of 45 km+ with `mountain_days` set (`services/ultra_rules.py`; spec
`docs/superpowers/specs/2026-10-23-ultra-rules-design.md`, which records where this departs from the book).
- **R-U1 Long-run ladder** in hours, read back from the peak week: 100 km 3, 3, 4, 4, 5 … 6, 7 h; 50 km
  3 h ×4 → 4 → 4.5 → 5 h; 100 mi as 100 km, 8 h peak for sub-elite/elite; a short plan drops its earliest
  rungs and keeps one filler step, so no rung is 2 h above the last (a 13-week 100 km: 3, 3, 4, (3), 4, 5, 6, (4),
  7 h; a 10-week 100 km: 3, 4, 4, (3), 5, 6, 7 h, then two taper weeks). A recovery week's long run is **a rung below the last
  build week**, 4 h at most (3 h at the first one). Never more than 60 min above the last two weeks'
  longest. Session cap 300 / 420 / 420–480 min, long-run share 60%; ladder steps are exempt from
  `LONG_RUN_JUMP` and the weekly growth checks measure the rest of the week.
  **Back-to-back (athlete's choice, `long_day_format`; owner 2026-10-27: Quang allows both):** the 6 h and 7 h
  rungs become the mountain day 2 h shorter plus an easy Zone 2 run on the other weekend day (flat is fine),
  about 10% longer in all: 6 h → 4 h + 2 h 30, 7 h → 5 h + 2 h 45 (`b2b_split`). Only on a day the athlete runs
  and never over ME or quality; the pair holds the rung for `ULTRA_LADDER` and the step cap. The default is
  one long day.
- **R-U2 Week shape.** Weekday easy runs 45–90 min (50 km) or 60–90 min (100 km+; 150 for advanced 100 mi);
  the other weekend day at most 90 / 60 / 45 min after a ≤4 h / 5 h / 6 h+ mountain day; no back-to-back
  unless the athlete chose one (R-U1);
  no ME in a week with a 6 h+ long run; deload weeks ≤80% of the week before; first 2 weeks at current load
  (Quang: a 50–60 km runner stays at 50–60 km), so the weekday minimum sets each run's length, not the
  number of runs: a short week has fewer 60-min runs (R-V4), never shorter ones.
- **R-U3 Quality sessions** only in the 8 weeks up to the peak (deloads excluded): Zone 3 uphill or
  rolling intervals, ≤90 min, 1 a week (2 only for an ungated elite on 15 h+ weeks, `ELITE_DOSE_WEEK_MIN`; Quang
  asked 2 for advanced runners, see section 0), none before or in the taper; no Zone 4. Gated runners (R-I1) still get one at 20–30 min of work. `QUALITY_COUNT`, `_add_tempo`,
  `_gate_hard`.

### All plans (2026-10-23)
- **R-G1 ME is not volume.** `plan_lint.week_minutes` leaves ME out (volume growth, recovery detection,
  start load); the long-run share and back-to-back checks still use all training time. `ME_LOAD` (R-U plans only): one ME
  session a week (two for sub-elite/elite in Base/Build), and what goes beyond one stays under 10%.
- **R-G2 Rest after the race.** Sessions after the goal race in its week become rest (`rows_after_race`); tune-up races are left alone.

### Run days (2026-10-28)
The days the athlete picks are run days (iOS ties "Runs per week" to them; the prompt makes every other day rest).
- **R-W1 Seven-day runners recover on Monday.** When all 7 days are picked, the Monday after a weekend long run is a
  30–40 min Zone 1 flat recovery run (30 after a 5 h+ weekend), exempt from the R-U2 weekday minimum
  (`_seven_day_monday`). Week 1 keeps its Monday (no weekend before it). *UA: no weekly day off is required; the
  day after a hammering long run stays easy.*
- **R-W2 Rest instead.** That Monday is rest after a 6 h+ long day (or back-to-back weekend), and always for a
  beginner or novice who picked 7 days: seven run days is too many at that level. The rest day says why.
- **R-W3 Too few run days for an ultra.** Setup (web plan form and onboarding, iOS setup) warns when a race of 45 km+
  has fewer than 4 run days, or 90 km+ fewer than 5, and asks the runner to confirm before creating the plan. It never
  blocks. The feasibility verdict (R-D2) stays the measure after creation; a mountain-day ultra counts every picked day
  as run time (ME goes on top of the runs, R-G1), so a fourth day adds capacity (`week_capacity_parts(strength_day=)`).

### Intensity
- **R-I1 AeT gate.** *UA: aerobic deficiency.*
  - Measured gap (`threshold_source` lab/field) **>10%**: no Zone 3–5 work in any phase.
  - Thresholds only estimated: the **Base** phase stays in Zones 1–2.
  - Hill sprints and strides always stay (neuromuscular, not endurance intensity).
  - Code: `athlete_tier.hard_work_banned_phases`, `_gate_hard`.
- **R-I2 (removed 2026-10-22).** Plans no longer schedule an AeT drift test. R-I1 uses a measured
  gap once the athlete enters lab or field thresholds in Profile → Thresholds.
- **R-I3 Dose per session.** At most ~60 min of Zone 3 (session ≤75 min) or ~30 min of Zone 4
  (≤70 min). Longer ones become easy runs (`_cap_hard_dose`).
- **R-I4 Dose per week.** Zone 3 ≤120 min and Zone 4 ≤40 min of work (scored by the quality bar).
- **R-I5 Sub-elite tempo.** A sub-elite athlete with no Zone 3/4 in a Build/Peak week gets one
  30–40 min tempo (`_add_tempo`), unless R-I1 bans it.
- **R-I6 No three hard days in a row.** A tempo or interval stays a day clear of the long run, ME,
  hill sprints, mountain days and any session of 120+ min (`_space_hard_days`, `_add_tempo`).
- **R-I7 Recovery runs ≤60 min.** A longer "recovery" becomes an easy Zone 1 run of the same
  length.
- **R-I8 Finish-only race pace** is Zone 2 slowed for the climbing, never faster.

### Strength / ME
- **R-M1 ME block** (`plan_rules.py`):
  - With 16+ weeks to go: 8–14 weeks of ME starting in Base.
  - With under 16 weeks: a short 6–8-session block.
  - Soft start for the first 2 sessions.
  - 48 h clear of the long run and hard work.
  - No ME in the last 10–14 days.
  - *UA ME chapter.*
- **R-M2 Climbing ME for flat athletes.** On a steep race with no hills, Build/Peak ME is climbing
  work (incline treadmill, stairs, weighted step-ups) (`CLIMB_SPECIFICITY`).
- **R-M3 Eccentric finisher.** On a course of 40+ m D+/km every ME session ends with eccentric work for the
  descents: 3 × 10 slow step-downs per leg, or walking down the stairs with the pack on (`_race_specifics`).

### Climbing (vert)
- **R-C1 Climb session.** For races ≥20 m D+/km, an athlete with a treadmill or stairs gets a
  Zone 2 climb session in every Base/Build/Peak week without climbing (`_add_climb_session`).
- **R-C2 Second climb session** in Build/Peak (not deload) weeks while the week is under its R-C8 target (40% of
  race D+ without one). Taper weeks keep one short session (≤45 min).
- **R-C3 Incline long runs.** A treadmill-only athlete (no hills, no mountain) gets three incline
  blocks inside the Base/Build/Peak long run, filled up to the cap in R-C4 (`_incline_long_run`).
- **R-C4 Weekly cap.** No week carries more than **80% of race D+** (`_cap_week_vert`).
- **R-C5 Honest vert.** Treadmill gain = belt speed × time × grade, only at ≥3% incline; sprints
  claim no vert. Stairs are credited at 600 m/h. A flat-only athlete never gets invented outdoor
  climbing.
- **R-C6 Trail pace.** Runs of ≥15 m D+/km get a climb-adjusted pace (flat × (1 + 0.012 × D+/km));
  mountain runs use the venue's climb rate (`trail_pace.py`, `training_mountains.py`).
- **R-C7 Descents.** On a course of 40+ m D+/km, the last 6 build weeks train descents: the mountain-day long run
  runs 2–3 of them at controlled race effort; an athlete with no mountain day ends one easy run a week with
  4–6 × 1 min controlled downhill on a ramp, bridge or overpass (`_race_specifics`). With R-M3 this is the
  downhill rule.
- **R-C8 Weekly D+ target.** For courses of 20+ m D+/km, each build week has a D+ target: from the athlete's recent
  weekly vert (watch; else 10% of race D+) toward **40% of race D+** by the last build week (25% when only a
  treadmill or stairs can deliver it), at most +20% a week, none in recovery weeks (`goal_demands.vert_targets`).
  Only where a venue can deliver it: hills at home, a mountain day on a mountain at least 60% as steep as the
  course, a treadmill or stairs. The prompt states the block's targets; R-C2's second climb session is added
  while a week is under its target; the lint's `VERT_SHORT` flags a week under 70% of it (not a back-to-back
  weekend the athlete chose: it moves about 2 h off the mountain, and the choice's help text says so).
  The plan views show each week's planned D+ against its target (web calendar week row, iOS week card;
  `goal_service.vert_targets_for` in the plan payload).
- **R-C9 Gentle mountain.** On a mountain under 60% of the course's steepness (e.g. Châu Thới, 28 m D+/km, for
  VHT at 53), Build/Peak mountain long runs spend their middle on repeats of its steepest climb; the vert credited
  is still the mountain's own rate. The setup screens (web and iOS) warn when such a mountain is the only climbing
  and ask for stairs (a building or an overpass) or a treadmill.

### Session text
- **R-T1** Step minutes add up to the session; a session whose steps disagree by >15% is
  rewritten.
- **R-T2** Titles match the session: no "Deload" outside deload weeks, no "Incline" at 0%, the
  zone in the title is the session's zone.
- **R-T3** Runs under 20 min become rest. Road paces are removed from climbing sessions. Treadmill
  sprints never say "jump onto the belt".
- **R-T4 Vietnamese** (`vi_style.py`, `kb_seed/vi_lexicon.json`):
  - Banned words are replaced.
  - Technical terms stay in English.
  - Titles use sentence case; place names keep their capitals.
  - Text that still reads unnatural is swapped for a reviewed template.

---

## 3. Create plan (`POST /api/coach/generate-plan`)

1. Resolve tier, zones, demands, feasibility (sections 1–2).
2. Week by week (`WEEKS_PER_BLOCK = 1`):
   - Gemini drafts the week from the prompt (KB doctrine, ADS status, demands, ME status, venues).
   - **Section 2 is enforced by code.**
   - `plan_lint` runs, with one retry on hard-rule failures.
3. Taper weeks skip Gemini (R-P3).
4. If Gemini fails twice, the rules-only fallback builds the week; section 2 still applies.

**To justify a result:** quote the tier and its caps, the demands and feasibility verdict, then
the R-rules that set the number in question.

## 4. Next block (`POST /api/coach/generate-next-block`)

- **R-N1 Completion gate.** The previous block must be ≥70% complete by training time, unless the
  athlete confirms the override.
- **R-N2 Block review.** RPE and notes from the athlete are saved and passed into the prompt with
  a per-session summary of the block (`block_history.build_history_lines`), plus any coach notes.
- **R-N3 Same demands.** The saved cut-off and race keep the demands identical across blocks.
  Terrain is read from the course (D+/km), not the profile.
- **R-N4 Progression from real weeks.** R-V2 compares against the weeks already saved, so a block
  never jumps over what the athlete was actually given.
- **R-N5 Goal check in the brief.** A stretch or unsupported goal (R-D2) is a fact in the week brief, with what
  would help (`goal_feasibility.brief_line`); the coach nudge and the Goal screen already say it. A new plan's
  week 1 gets a brief too (`main._week_one_brief`, `week_brief.week_one_facts`): current volume and the fatigue
  hold, a mid-week start, run days left out (R-V4) and the goal check.
- Section 2 applies unchanged.

## 5. Adapt week (`POST /api/coach/adapt-week`, chat `propose_rebuild_week`)

Code: `week_rebuild.py`, `plan_rules.missed_reason_rules`.

- **R-A1 What is kept.** Past days, completed and GPS-matched sessions, and coach-edited sessions
  are never changed. Only the rest of the week is rebuilt; past weeks are refused.
- **R-A2 Reference volume.**
  - The reference is the week as planned. If that's missing, use the prior week as planned. If
    that's missing too, use current volume (weekly km × the athlete's own easy pace, as R-V1).
  - If the prior week was **<80% complete**, the week **holds** at 95–102% of the reference: a
    repeat, not progression and not a punishment.
- **R-A3 Feeling band.** Reported effort sets the allowed range of the reference:

  | Feeling | Range |
  |---|---|
  | very light / light | 102–108% |
  | moderate | 98–105% |
  | hard | 85–90% |
  | max / exhausted | 70–80% |

  High fatigue overrides the R-A2 hold.
- **R-A4 Missed-session reasons.** The lowest cap wins:

  | Reason | Rule | Cap | Source |
  |---|---|---|---|
  | any miss | never make up missed sessions or volume | — | UA-R1 |
  | busy | resume as planned | — | UA-R2 |
  | sick | first days back Zone 1–2 only, first 2 sessions at ~50% | no progression (1.0) | UA-R3–R7 |
  | pain | don't run through pain; short, easy, flat, pain-free only; first sessions ~50% | no progression (1.0) | UA-R6–R7 |
  | tired | drop the long run, intensity and ME until fresh | 0.90 | UA-R10 |
  | weather | swap to treadmill or stairs, keep the volume | — | UA-R12 |
  | resting HR ≥10% above baseline | first session of the week is easy | — | UA-R9 |
  | 1–4 weeks off | start at ~80% | 0.80 | UA-R15 |
  | >4 weeks off | start at 50% | 0.50 | UA-R14 |
  | last 14 days before the race | never add missed or extra quality work | — | UA-R17 |
  | same weekday missed 2 of the last 3 weeks | plan around the real schedule | — | UA-R24 |

- **R-A5 Warnings shown before saving:**
  - W1: two hard sessions on one day, or a hard session the day before the long run.
  - W2: the week total moves by more than 20%.
- **R-A6 Explanation.** Every volume decision is written to a `decision_log` that the week brief
  uses, so the athlete sees the real reason (e.g. "Under 80% complete, so this week holds").
- Section 2 applies to the rebuilt days.

---

## 6. Quality bar (`plan_quality.assess`)

Run on finished plans by `scripts/plan_quality_report.py` (persona runs) to score whether the rules
held:
1. Climbing prep: peak week ≥40% of race D+, or ≥25% with treadmill/stairs only.
2. Long day (or back-to-back) ≥40% of race time, capped.
3. No Zone 3 session >75 min and no Zone 4 session >70 min.
4. Weekly Zone 3 ≤120 min and Zone 4 ≤40 min.
5. Two-step taper.
6. Finish-only race pace not faster than Zone 2.
7. Trail pace on runs of ≥15 m D+/km.
8. Step minutes add up.
9. Natural Vietnamese.
10. No week >80% of race D+.
11. AeT gate respected.
12. Week 1 within 10% of recent load (weeks 1–2 on a mountain-day ultra), at four run days or more.

## 7. Known gaps (say so when asked)

- Capacity-bound plans (3 days a week, low volume, long race) can't reach the long-day target; the verdict says
  so on the Goal screen, in the coach nudge and in the week brief.
- Gentle mountains (R-C9) have no measured repeat-climb rates, so their repeats earn no extra vert credit and
  get no D+ target.

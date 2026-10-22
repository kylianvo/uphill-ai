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

## 1. Inputs and who decides what

| Input | Where it comes from | Used for |
|---|---|---|
| Race: distance, D+, cut-off, target time, date, terrain | plan wizard; cut-off saved on `plans.cutoff_time_hours` | race demands (R-D) |
| Recent load: weekly km (and vert) | watch (≥3 full weeks, `fitness_snapshot`), else typed `current_weekly_km` | week 1, ramp, tier |
| Zone 2 pace, AeT/AnT HR, `threshold_source` | profile; COROS threshold pace if synced | zones, AeT gate (R-I1) |
| Days, long-run day, gym, treadmill (max incline), stairs, training mountain, mountain days | wizard / adapt form | layout, climbing venues |
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
- **R-P2 Deload every 4th week**, never the last build week (`is_deload_week`). A deload week is
  **at most 80% of the week before**, cut from easy runs (`_ramp_volume`). *UA: 3:1 loading.*
- **R-P3 Two-step taper** for plans of 12+ weeks (code: about 70%, then 50% of the peak week; one step at 50%
  for shorter plans; the lint holds each taper week to ≤85% of the week before). Taper weeks
  are built by code from the real peak (`TAPER_BY_RULES`), with no new hard work. *UA taper.*

### Volume
- **R-V1 Week 1 from recent load.** Week 1 is at most **10% above** what the athlete runs now
  (`recent_weekly_minutes` = weekly km × own Zone 2 pace; `RECENT_LOAD_GROWTH`). The cut comes off
  easy runs; the long run, ME and quality sessions stay. With no data: 180 min. A mountain-day
  minimum can still push week 1 higher; that's the athlete's choice.
- **R-V2 Weekly growth cap.** No week goes above the week before × (1 + tier
  `max_weekly_progression`); the excess is trimmed from easy runs. Return from a deload is
  measured against the larger of the last two weeks.
- **R-V3 Ramp toward the goal.** Build weeks grow toward the race's peak-week volume
  (`_ramp_volume`), within R-V2 and the tier's weekday maximum.

### Long run
- **R-L1 Long run grows toward the race's time on feet**, asked at most +20%/week (the lint allows +25%,
  `LONG_RUN_JUMP`), capped by the session cap (300 min; 480 min sub-elite 100-mile) and the long-run share
  (tier cap ±5%, `LONG_SHARE_SOFT`). Mountain-day ultras follow R-U instead.
- **R-L2 Back-to-back weekend** for ultras in the last build weeks (not for mountain-day ultras: R-U).
- **R-L3 Taper long run** about 60%, then 40% of the peak, and inside the long-run share even when
  short taper runs are dropped (`_fit_taper_long_share`).
- **R-L4 Mountain minimum.** On a mountain day the long run is at least the athlete's chosen
  minimum (default 180 min), except in recovery/taper/deload weeks ("chill" mode).

### Ultras with a mountain day (R-U, coach Quang 2026-10-22)
Races of 45 km+ with `mountain_days` set (`services/ultra_rules.py`; spec
`docs/superpowers/specs/2026-10-23-ultra-rules-design.md`, which records where this departs from the book).
- **R-U1 Long-run ladder** in hours, read back from the peak week: 100 km 3, 3, 4, 4, 5 … 6, 7 h; 50 km
  3 h ×4 → 4 → 4.5 → 5 h; 100 mi as 100 km, 8 h peak for sub-elite/elite. Deload weeks 3 h (50 km) or 4 h.
  Never more than 60 min above the last two weeks' longest. Session cap 300 / 420 / 420–480 min, long-run
  share 60%; ladder steps are exempt from `LONG_RUN_JUMP` and the weekly growth checks measure the rest of
  the week.
- **R-U2 Week shape.** Weekday easy runs 45–90 min (50 km) or 60–90 min (100 km+; 150 for advanced 100 mi);
  the other weekend day at most 90 / 60 / 45 min after a ≤4 h / 5 h / 6 h+ mountain day; no back-to-back;
  no ME in a week with a 6 h+ long run; deload weeks ≤80% of the week before; first 2 weeks at current load.
- **R-U3 Quality sessions** only in the 8 weeks up to the peak (deloads excluded): Zone 3 uphill or
  rolling intervals, ≤90 min, 1 a week (2 for ungated sub-elite/elite), none before or in the taper; no
  Zone 4. Gated runners (R-I1) still get one at 20–30 min of work. `QUALITY_COUNT`, `_add_tempo`,
  `_gate_hard`.

### All plans (2026-10-23)
- **R-G1 ME is not volume.** `plan_lint.week_minutes` leaves ME out (volume growth, recovery detection,
  start load); the long-run share and back-to-back checks still use all training time. `ME_LOAD` (R-U plans only): one ME
  session a week (two for sub-elite/elite in Base/Build), and what goes beyond one stays under 10%.
- **R-G2 Rest after the race.** Sessions after the goal race in its week become rest (`rows_after_race`); tune-up races are left alone.

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

### Climbing (vert)
- **R-C1 Climb session.** For races ≥20 m D+/km, an athlete with a treadmill or stairs gets a
  Zone 2 climb session in every Base/Build/Peak week without climbing (`_add_climb_session`).
- **R-C2 Second climb session** in Build/Peak (not deload) weeks while the week is under 40% of
  race D+. Taper weeks keep one short session (≤45 min).
- **R-C3 Incline long runs.** A treadmill-only athlete (no hills, no mountain) gets three incline
  blocks inside the Base/Build/Peak long run, filled up to the cap in R-C4 (`_incline_long_run`).
- **R-C4 Weekly cap.** No week carries more than **80% of race D+** (`_cap_week_vert`).
- **R-C5 Honest vert.** Treadmill gain = belt speed × time × grade, only at ≥3% incline; sprints
  claim no vert. Stairs are credited at 600 m/h. A flat-only athlete never gets invented outdoor
  climbing.
- **R-C6 Trail pace.** Runs of ≥15 m D+/km get a climb-adjusted pace (flat × (1 + 0.012 × D+/km));
  mountain runs use the venue's climb rate (`trail_pace.py`, `training_mountains.py`).

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
- Section 2 applies unchanged.

## 5. Adapt week (`POST /api/coach/adapt-week`, chat `propose_rebuild_week`)

Code: `week_rebuild.py`, `plan_rules.missed_reason_rules`.

- **R-A1 What is kept.** Past days, completed and GPS-matched sessions, and coach-edited sessions
  are never changed. Only the rest of the week is rebuilt; past weeks are refused.
- **R-A2 Reference volume.**
  - The reference is the week as planned. If that's missing, use the prior week as planned. If
    that's missing too, use current volume.
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
12. Week 1 within 10% of recent load.

## 7. Known gaps (say so when asked)

- Mountain athletes without a treadmill or stairs (e.g. Hà Nội + Hàm Lợn at weekends) can peak
  below the climbing a coach wants; repeat-climb rates per mountain are not set yet.
- No downhill/eccentric conditioning rule yet.
- Adapt week still converts km to minutes at 6.0 min/km (R-A2); create and next block use the
  athlete's own pace (R-V1).
- Capacity-bound plans (3 days a week, low volume, long race) can't reach the long-day target.
  The feasibility verdict says "stretch", but the plan text doesn't explain it yet.

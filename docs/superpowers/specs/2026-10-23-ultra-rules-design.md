# Ultra rules: one rule set for 50 km, 100 km and 100 miles

Status: draft, 2026-10-23. Source: coach Quang Tran (two chats, 2026-10-22) plus the decisions in the brainstorm `~/.claude/plans/help-me-inspect-my-wild-nova.md`. Replaces the earlier 100 km-only plan and the uncommitted `athlete_tier.py` edit on `feat/quang-100k-mountain-rules`.

## Job

Ultra plans with a mountain day are too light. A 3–4 h long run at Núi Dinh covers about 20 km; a 100 km runner needs 5–7 h (30–35 km) at peak, and 45 min weekday runs (7–8 km) are too short. The plan must follow a fixed long-run ladder, longer weekday runs and a set number of quality sessions, by race distance band.

## Who gets these rules

- **Band** from `course_distance_km`. Bands start about 10% below the round number, so a 98 km "100K" is in the 100 km band.
  - 50 km band: 45–89 km
  - 100 km band: 90–139 km
  - 100 miles band: 140 km and up
- **Mountain day:** the ladder applies only when the plan has a mountain day (`mountain_days` non-empty, see `services/training_venues.py`). Without one, the current rules stay.
- **Finisher vs advanced:** finishers are `BEGINNER`, `NOVICE`, `RECREATIONAL`; advanced are `SUB_ELITE`, `ELITE` (`services/athlete_tier.py`), after `graduated_profile`.

## Rules

| Rule | 50 km band | 100 km band | 100 miles band |
|---|---|---|---|
| Long run on the mountain day | 3 h weeks 1–4 → 4 h → 4.5 h → 5 h peak; recovery week 3 h (**open: Quang to confirm**) | 3 h, 3 h, 4 h, 4 h, then 5 h; 6 h → 7 h at peak; recovery week 4 h | 100 km ladder, peak 7 h (finishers) or 8 h (advanced) |
| Other weekend day | 45–90 min easy, shorter after a longer mountain day: long run ≤ 4 h → 90, 5 h → 60, ≥ 6 h → 45 (Zone 1) | same | same |
| Weekday easy runs | 45–90 min | 60–90 min | 60–90 min (advanced up to 150) |
| Quality per week, final 8 weeks before taper only (uphill/rolling intervals, Zone 3, ≤ 90 min each) | finishers 1, advanced 2; gated 1 | same | same |
| First 2 weeks | at the athlete's current weekly km | same | same |
| Extra volume | on weekdays, never on the long run | same | same |

- The ladder is in hours, not km; km follows from the venue.
- Taper weeks keep the current taper rules; the ladder covers base, build and peak.
- Short plans (fewer weeks than the ladder) enter the ladder at the step that fits the weeks left, never above the athlete's recent longest run + one step.
- **Quality sessions** (book + Quang, decided 2026-10-23):
  - Only in the 8 weeks up to and including the peak week (not deload weeks, never in the taper). Base and the weeks before get hill sprints and ME instead.
  - Zone 3 only; no Zone 4 for 50 km–100 mi.
  - Work: finishers 20–30 min (4–5 × 5 min or 3 × 8–10 min, 2–3 min walk); advanced 40–60 min. Whole session ≤ 90 min with warm-up and cool-down.
  - **Gated runners** (measured AeT–AnT gap > 10%, or estimated thresholds) still get **1** Zone 3 session a week in those 8 weeks, at the finisher dose, whatever their level (book: "within about eight weeks of your event you better start adding specific training in").
- **Hill repeats for city runners:** treadmill at 8–12% incline, stairs or an overpass. They are a quality session (breathing is the limit), never ME (leg burn is the limit, often with a pack).

### Muscular endurance (all plans, Johnston)

- ME is added on top of the running, never in its place, and is ≤ 10% of the week.
- 1 a week; advanced up to 2 in Base and Build. Easy day after.
- No ME in a week with a long run of 6 h or more.
- ME minutes do **not** count toward the weekly volume target: `plan_lint.week_minutes` drops ME (`_is_me` exists), matching `race_readiness`.

### Day after the race

Rest. No recovery run.

## What changes against the current rules

| # | Current | New | Where |
|---|---|---|---|
| C1/C11 | Single session ≤ 300 min (`athlete_tier.MAX_SESSION_MIN`, `plan_generator.py:601-603` hard-coded 300) | Ladder cap per band: 300 (50 km), 420 (100 km), 420/480 (100 miles) | `athlete_tier`, `plan_generator` (use the constant, not 300) |
| C2 | Long run ≤ 28–40% of the week (`long_run_share_cap`) | Share cap does not apply to the ladder long run in the mountain-day bands | `athlete_tier.long_run_share_cap` callers, `plan_lint` |
| C3 | Long run growth ≤ +20%/week (code), lint +25% (`plan_lint.MAX_LONG_RUN_GROWTH`) | Ladder steps are exempt; growth rule still applies off the ladder | `plan_lint`, generator post-processing |
| C4 | Base long run ≈ 25% of the week (prompt) | Ladder step wins; week 1 at ~50% is accepted | plan prompt rule text |
| C5 | Weekday minimum 45 min, not enforced | Band minimum enforced in post-processing and lint | `plan_generator`, `plan_lint` |
| C6 | AeT gate: no Zone 3+ with a gap > 10% (all phases) or estimated thresholds (Base) | Gate stays on outside the final 8 weeks. Inside them, gated runners get 1 Zone 3 session at the finisher dose; ungated get Quang's count. No switch | `_gate_hard`, prompt |
| C7 | Back-to-back weekend in the last build weeks for races ≥ 80 km | For mountain-day bands: one ladder long run + one 60–90 min easy day. Back-to-back stays for plans without a mountain day | `plan_generator` back-to-back block (~line 1766, 2144) |
| C8 | ME counts toward weekly minutes in lint | ME excluded | `plan_lint.week_minutes` |
| C9 | Recovery week 80% of the week before | Unchanged; the long run follows the ladder's recovery step | — |
| C10 | No rule after race day | Rest | post-processing |
| C12 | `docs/plan-rules.md` R-L1 says +20% (lint +25%); R-P3 taper says 85/70% (code −30/−50%) | Fix the doc to match code and these rules | `docs/plan-rules.md` |

## Stated deviation from the book

C1, C2 and C3 follow Quang, not Johnston. NotebookLM answers (2026-10-23, six prompts). "Firm rule" / "guideline" labels below are NotebookLM's own reading; the quotes are what the sources say.

| Topic | Book / Evoke (source) | Quang / this spec | Verdict |
|---|---|---|---|
| Longest session | Recreational 3–5 h; 6–8 h only for elites, sparingly (Tom Evans: one 8 h day before UTMB). "We never do anything that approaches that duration" (Book Club, Ch. 3) | 5 h (50 km), 7 h (100 km), 7–8 h (100 mi) for all levels | **Deviation** (C1) |
| Long-run share | 25% of weekly volume, once a week, Zone 1 (Ch. 10). A run that leaves legs hammered 2–3 days is uncounted ME: keep the following days to ~1 h on moderate terrain | Up to 60% on ladder weeks | **Deviation** (C2) |
| Long-run growth | 7–10% a week (Ch. 9); connective tissue adapts at ~1/7 the rate of muscle | 3 h → 4 h (+33%) ladder steps | **Deviation** (C3) |
| One long day vs back-to-back | One long run a week; back-to-back only as 2-day overreaching blocks, 2–3 times in the Specific period, followed by easy days (Book Club #4) | One ladder day, no back-to-back | Agrees (C7) |
| Other weekend day | Zone 1 recovery jog or 45–60 min walk/hike, or rest; ~1 h easy if legs are hammered | 45–90 min, shorter after a longer mountain day | Decided 2026-10-23 (between the two) |
| Weekday easy minimum | 20–30 min is useful; Zone 2 continuous 30–90 min; 45 min "is definitely enough" | 60 min (100 km+), 45 min (50 km) | **Deviation** (C5) |
| Zone 3 sessions | Base: 0 for everyone; mountain runners use ME in Base, then uphill/rolling intervals in the final 8 weeks before taper. Recreational 1/week, sub-elite/elite 1–2/week. Zone 4: 0 for 50 km–100 mi. No extra quality in the taper | 1 finisher / 2 advanced, final 8 weeks only | Decided 2026-10-23: follows the book |
| Open AeT–AnT gap | Wait for gap ≤ 10%, but "once you get within about eight weeks of your event you better start adding specific training in": 1 Zone 3 or ME session a week, high intensity < 10% of weekly time | 1 Zone 3 a week in the final 8 weeks | Decided 2026-10-23: follows the book |
| Quality session dose | 60–90 min total. Recreational 20–30 min Zone 3 work (4–5 × 5 min or 3 × 8–10 min, 2–3 min walk); elite 40–60 min (10 × 1 km, 1 min rest). Weekly Zone 3: recreational 30–60 min (5–8%), elite 2–3 h (8–10%). Zone 4 ≤ 30–40 min/week | ≤ 90 min | Agrees. `_cap_hard_dose` (75 min Zone 3) must allow 90 for ultra quality |
| Uphill intervals vs ME | Unweighted 8–12% intervals limited by breathing = Zone 3/4; weighted carries (10–15% BW, 20–30%+ grade) limited by leg burn = ME | Same split | Agrees |
| Hill sprints, strides | Hill sprints are neuromuscular, year-round, ~1/week, no global fatigue; strides are not quality sessions | Not counted as quality | Agrees |
| ME | 1/week (elite 1–2 in specific blocks); mountain runners in early Base; ≤ 10% of training; **on top of** Zone 1–2 volume, never replacing it; skip when the long run already hammers the legs; 1–2 recovery days after | Same | Agrees (C8 confirmed) |
| Recovery weeks | 3:1; volume and long run cut 30–50% | 80% of the week before; ladder recovery long run (240 after 300 = −20%) | Shallower than the book (C9) — not changed here |
| Plan start | Hold current volume 3–4 weeks; first long run 25% of the week (NotebookLM's arithmetic: 12.5–15 km at 50–60 km/week) | Hold 2 weeks; 3–4 h trail long run | **Deviation** |
| Taper | 40–60% less volume over 2–3 weeks (Ch. 12); NotebookLM suggests ~75–80% → ~60% → 40–50% of peak for 100 km | Code: −30% / −50% (C12) | Code is within the book's range |

**Why we deviate:** Quang coaches the runners this plan is for (HCMC, one mountain day a week at Núi Dinh, weekdays on flat roads). The mountain day is the only place they can train the race's terrain, so it carries more of the week than the book's 25%. The risks the book names (connective tissue, multi-day fatigue) are handled by: ladder steps capped at +60 min over the last two weeks, a recovery long run every 4th week, ME skipped in 6 h+ weeks, and the lint still checking everything off the ladder.

## Open

1. 50 km ladder: Quang to confirm the scaled ladder.

## Checks

- `python scripts/plan_reliability.py` scorecard: new rows for each band × finisher/advanced × mountain day yes/no.
- Unit tests: band lookup (44.9 / 45 / 89 / 90 / 139 / 140 km), ladder per week incl. recovery and short plans, weekday minimum, ME excluded from `week_minutes`, share cap and growth exemptions only on ladder long runs, rest after race day.
- Rule-based fallback (`week_layout.py`) produces the ladder too, so a plan is right without the model.
- HCMC persona pack (`scripts/render_persona_pack.py`) re-rendered and sent to Quang for review.
- Prompt changes go through `.claude/skills/llm-change-process/SKILL.md`.

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
| Other weekend day | 60–90 min easy | 60–90 min easy | 60–90 min easy |
| Weekday easy runs | 45–90 min | 60–90 min | 60–90 min (advanced up to 150) |
| Quality per week (hill repeat or interval, ≤ 90 min each) | finishers 1, advanced 2 | finishers 1, advanced 2 | finishers 1, advanced 2 |
| First 2 weeks | at the athlete's current weekly km | same | same |
| Extra volume | on weekdays, never on the long run | same | same |

- The ladder is in hours, not km; km follows from the venue.
- Taper weeks keep the current taper rules; the ladder covers base, build and peak.
- Short plans (fewer weeks than the ladder) enter the ladder at the step that fits the weeks left, never above the athlete's recent longest run + one step.
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
| C6 | AeT gate: no Zone 3+ with a gap > 10% or estimated thresholds | **Default: gate stays on.** Gated runners get the quality slots as Zone 2 steep hill repeats; ungated runners get Quang's Zone 3 sessions. One switch (`ULTRA_QUALITY_IGNORES_AET_GATE`, default false) flips it if NotebookLM Q5 backs Quang | intensity rules in prompt + post-processing |
| C7 | Back-to-back weekend in the last build weeks for races ≥ 80 km | For mountain-day bands: one ladder long run + one 60–90 min easy day. Back-to-back stays for plans without a mountain day | `plan_generator` back-to-back block (~line 1766, 2144) |
| C8 | ME counts toward weekly minutes in lint | ME excluded | `plan_lint.week_minutes` |
| C9 | Recovery week 80% of the week before | Unchanged; the long run follows the ladder's recovery step | — |
| C10 | No rule after race day | Rest | post-processing |
| C12 | `docs/plan-rules.md` R-L1 says +20% (lint +25%); R-P3 taper says 85/70% (code −30/−50%) | Fix the doc to match code and these rules | `docs/plan-rules.md` |

## Stated deviation from the book

C1, C2 and C3 follow Quang, not Johnston's 4–5 h session ceiling and long-run share guidance. The NotebookLM answers to questions 1–3 (prompt in the brainstorm) go here when run:

- Q1 session ceiling: _pending_
- Q2 long-run share: _pending_
- Q3 progression: _pending_
- Q5 intensity / AeT gate: _pending_ (decides C6's switch)

## Open

1. 50 km ladder: Quang to confirm the scaled ladder.
2. C6 switch: NotebookLM Q5.

## Checks

- `python scripts/plan_reliability.py` scorecard: new rows for each band × finisher/advanced × mountain day yes/no.
- Unit tests: band lookup (44.9 / 45 / 89 / 90 / 139 / 140 km), ladder per week incl. recovery and short plans, weekday minimum, ME excluded from `week_minutes`, share cap and growth exemptions only on ladder long runs, rest after race day.
- Rule-based fallback (`week_layout.py`) produces the ladder too, so a plan is right without the model.
- HCMC persona pack (`scripts/render_persona_pack.py`) re-rendered and sent to Quang for review.
- Prompt changes go through `.claude/skills/llm-change-process/SKILL.md`.

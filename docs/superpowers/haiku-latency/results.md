# Haiku latency: results log

Running record for `docs/superpowers/plans/2026-10-24-haiku-latency.md`. Each task appends its numbers here; PR descriptions quote them.

## Prod settings

Reading the prod `backend/.env` was not permitted from this session, so prod's flags are inferred from Langfuse
(generation spans on `claude-haiku-5-5`, 2026-10-17 → 2026-10-24):

| Environment | Feature (trace) | Haiku calls |
|---|---|---|
| production | goal_estimate | 7 |
| production | plan_generation | 3 |
| production | gear_finder | 3 |
| production | nutrition_lab | 1 |
| development | generation (chat), plan_generation, nutrition_lab, goal_estimate, gear_finder | 53, 26, 25, 14, 14 |

So Goal, Plan, Gear and Nutrition run on Haiku in prod; chat runs on Haiku only in development. Prod's
`PLAN_LLM_EFFORT` is unknown; the baseline uses the code default `medium`, which matches the ~9.6k output tokens per
plan call seen in Langfuse. Confirm both on the server before flipping any `.env` switch.

## Baseline (Task 2) and thinking off (Tasks 3, 6)

Golden sets run locally against the scratch DB with the KB seeds loaded (2026-10-24). "Gemini" is the stored
`.ref.json` latency of each fixture. Latency is the per-fixture wall clock; p50 over the fixtures.

| Feature | Gemini p50 | Haiku today p50 | Haiku thinking off p50 (p95) | Quality: today → thinking off | Verdict |
|---|---|---|---|---|---|
| Gear (12) | 6.5 s | 15.2 s | 8.8 s (9.9 s) | gate PASS, 12/12 in catalog → PASS, 12/12 | keep off |
| Nutrition (12) | 5.9 s | 13.8 s | 8.5 s (11.5 s) | gate PASS, 12/12 in catalog → PASS, 12/12 | keep off |
| Goal judge (12) | 3.1 s | 10.5 s | 6.6 s (8.0 s) | gate PASS, 1 reduced-prompt retry → PASS, 0 retries | keep off |
| Week brief (10 synthetic) | — | 4.8 s | 2.0 s | 10/10 usable → 10/10 | keep off |
| Coach nudge (10 synthetic, 8 with a tone) | — | 2.4 s | 1.4 s | 8/8 grounded → 7/8 | **revert** (keeps thinking) |
| LLM judge (calibration) | — | — | — | 100% on all 4 criteria → 100% | keep off |
| Chat (4 + benchmark) | 4.8 s | 9.7 s | (Task 7) | gate FAIL: `chat_vi_recovery_short_sleep` safety violation already on today's Haiku | — |

Not measurable here: `goal_backtest.py` found 0 cases (the scratch DB has no race history), so Goal's bar is the
goal_judge golden gate only. Gemini week brief/nudge baselines were not run (Gemini paid runs declined to save the
key's time window; these two features run on Gemini in prod anyway).

Gear and Nutrition are now under the 10 s target at p50; Goal judge is 6.6 s against Gemini's 4.5 s prod p50 — faster
than today but still above target. Reports: `docs/superpowers/haiku-latency/reports/`.

## Plan tail (Task 4)

Langfuse, `plan_generation` on Haiku, 2026-10-10 → 2026-10-24, 29 traces. Every successful call runs at roughly
220 output tokens/s (9.6k tokens ≈ 44 s, 23k ≈ 104 s), so ordinary latency is output length. The p95 of ~400 s comes
from two traces (57be5f38…, fcfe887c…) whose primary Claude call ended in `status=error` with no usage after 631 s and
602 s: a stalled stream that only failed at the Anthropic SDK's default 10-minute timeout. The reduced-prompt retry then
finished in 53 s and 32 s. No call hit the 32000 `max_tokens` cap (max seen 23,090) and no trace stacked more than one
retry.

Finding: (c)-type stall, not runaway output or stacked retries. Fix added as Task 4b: give the Plan stream a read
timeout so a stall fails within a minute and the existing retry tier takes over. Effort/thinking (Task 5) addresses the
ordinary 44 s.

## Caching decision (Task 8 step 1)

Production, 2026-10-10 → 2026-10-24: Gear had 6 calls, 2 of them within 5 minutes of the one before (pairs 44 s and
94 s apart); Nutrition had 1 call. Gear's catalog block (`render_catalog_context(filter_catalog(chunks, surface,
preferred_brands))`) sits right after the opening line, but it changes whenever surface or preferred brands change,
so even the quick repeats only hit if the athlete kept both. Plan bursts (block after block for one athlete within
minutes), but its prompt is per-athlete before the first fixed block.

Verdict: not worth it yet. With ~2 cacheable Gear calls in two weeks, the saving is about a second of time to first
token on a handful of calls, against new code on the request path. Revisit if Gear/Nutrition traffic grows, or after
Task 3 if Gear is still above its 10 s target.

## Plan effort / thinking sweep (Task 5)

Scheduler golden set (20 plans with a Gemini ref), local scratch stack, 2026-10-24:

| Config | p50 | p95 | Gate | Reduced-prompt retries |
|---|---|---|---|---|
| Gemini (stored refs) | 13.1 s | — | — | — |
| Today: `medium` + adaptive | 67.0 s | 233.7 s | PASS | 2 |
| `low` + adaptive | 44.0 s | 74.5 s | PASS | 0 |
| `low` + thinking off | 13.2 s | 28.0 s | **FAIL** (6: ME sessions missing, week-2 volume out of range) | 1 |
| `medium` + thinking off | 14.1 s | 25.9 s | **FAIL** (3: ME sessions, week-2 volume) | 2 |

Thinking off is what would reach Gemini's speed, but at both efforts it drops strength (ME) sessions and breaks the
week-2 volume ramp, so it fails the bar. `low` + adaptive passes with fewer retries than today. Persona check below.

## Chat thinking (Task 7)

| Config | p50 | Gate | Judge (tool fixture) |
|---|---|---|---|
| adaptive (today) | 8.9 s | PASS: 0 safety violations, EN 23/23, VI 22/22 | grounded 1.00; called `get_week` |
| thinking off | 6.7 s | **FAIL**: safety violation on `chat_vi_17_dangerous_dehydration`, VI 21/22 | grounded 0.50; called `get_week` |

Verdict: chat keeps adaptive thinking (`CLAUDE_COACH_THINKING` stays `adaptive`). Note the Task 2 baseline run failed
once on `chat_vi_recovery_short_sleep` and this adaptive run passed it: that case is flaky on Haiku, not a regression.

### Personas (2 of 21, chosen to fit the key's time window; Gemini personas declined)

| Persona | `medium` + adaptive (today) | `low` + adaptive |
|---|---|---|
| recreational_50k (11 blocks) | 0 fails; block p50 124.9 s, p95 314.2 s; $0.21 | 0 fails; block p50 72.9 s, p95 136.8 s; $0.12 |
| hcm_rec_100k_dinh (15 blocks) | 1 fail (week 4 `WEEKDAY_SHORT`); 177.6 s / 338.6 s; $0.50 | 1 fail (week 9 `QUALITY_COUNT`); 96.6 s / 153.1 s; $0.30 |

Same number of failed checks on both personas (the ultra-ladder check fails once in each, on a different week), same
engine mix (two rules-tier blocks in both, in the same weeks). Verdict: Plan moves to `PLAN_LLM_EFFORT=low` with
adaptive thinking; `config.py` default changed from `medium` to `low` so prod picks it up even without a `.env` entry.

For scale against the app: production `plan_generation` spans (mostly Gemini) are p50 23.9 s, p95 48.3 s per job;
Haiku `low` is about 1.5–1.8× that, down from about 3×. Closing the rest needs shorter output (Task 10, Claude-only
prompt wording), since thinking off fails the quality bar.

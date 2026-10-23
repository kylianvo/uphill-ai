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

## Baseline

(Task 2)

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

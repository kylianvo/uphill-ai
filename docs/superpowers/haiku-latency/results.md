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

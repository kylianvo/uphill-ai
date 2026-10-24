# Haiku 5.5 latency without losing quality

Status: design, awaiting approval. Date: 2026-10-24.

## Why

Haiku 5.5 was meant to be the fast, cheap engine. In production it is slower than the Gemini setup it
replaced on every feature we can compare, and Plan's tail is close to the app's 7-minute give-up point.
The cause is on our side: Haiku spends output tokens on adaptive thinking we neither need nor see
(`output_tokens` includes thinking, and `Usage.from_anthropic` records `thinking_tokens=0`), and Plan runs
at `effort: medium`. Time to first token is close to Gemini's, so this is not an Anthropic outage.

Langfuse, 2026-10-10 → 2026-10-24, generation spans:

| Feature | Haiku p50 / p95 | Haiku output tok p50 | Gemini p50 / p95 | Gemini output tok p50 |
|---|---|---|---|---|
| Plan (`plan_generation`) | 44.6 s / 402 s | 9,612 | 19.0 s / 31.8 s | 2,280 |
| Goal (`goal_estimate`) | 6.1 s / 9.1 s | 1,018 | 4.5 s / 5.8 s | 312 |
| Gear (`gear_finder`) | 12.5 s / 42.8 s | 2,593 | 10.0 s / 10.9 s (6 calls) | 1,079 |
| Nutrition (`nutrition_lab`) | 12.1 s / 21.0 s | 2,219 | no Gemini calls in window | — |
| Chat (untagged `generation` trace, our guess) | 3.5 s, first token 2.8 s | 576 | 3.9 s, first token 2.2 s | 156 |

Haiku's tokenizer counts the same text as about 30% more tokens, so roughly a third of the gap is
counting, not writing.

## Goals

1. Every feature that runs on Haiku is at least as fast as Gemini was, and faster where it can be:
   - Plan (plan generation, next block, adapt week): p50 ≤ 19 s, p95 ≤ 32 s.
   - Goal: p50 ≤ 4.5 s. Gear: p50 ≤ 10 s.
   - Nutrition: p50 ≤ 10 s (no Gemini baseline; Gear's target, since the two calls have the same shape —
     our call).
   - Chat: time to first token ≤ today's 2.8 s; total turn time no worse than today.
   - Small features: no target of their own; they take whatever the shared lever gives them.
2. Quality holds: on every check below, the faster setup scores **at least as well as today's Haiku
   and at least as well as Gemini wherever a Gemini baseline exists** (the athlete's bar).
3. We can see where Haiku's output tokens go (answer versus thinking) per feature in Langfuse, so the
   next slowdown is diagnosed from data rather than guessed.

## Non-goals

- Switching models (no Sonnet/Opus), or moving features back to Gemini.
- Changing any Gemini path, prompt or setting.
- Frontend or iOS changes (the 7-minute poll window stays).

## Anti-goals

- A feature that gets faster but drops below either quality bar ships anyway. It does not: it keeps its
  current settings, and the result is reported.
- Capping `max_tokens` so tightly that answers get cut off (`stop_reason == "max_tokens"` is treated as a
  failed call and falls to the retry/rules tiers, which is slower and worse).
- Overwriting the Gemini baselines (`tests/golden/<service>/*.ref.json`) while measuring Haiku.

## Scope: every Haiku call site

| Feature | Call site | Today |
|---|---|---|
| Plan: generation, next block, adapt week | `plan_generator._claude_generate`, streamed, used from `_generate_plan_workouts` | `PLAN_LLM_EFFORT` (default `medium`), thinking on, `max_tokens=32000` |
| Goal | `goal_judge._call_claude` → `claude_llm.generate` | `CLAUDE_TEXT_EFFORT=low` |
| Gear | `gear_planner` → `claude_llm.generate(schema=GearResponse)` | low |
| Nutrition | `nutrition_planner` → `claude_llm.generate(schema=NutritionResponse)` | low |
| Chat | `coach_model.ClaudeCoachModel.stream` (tools, streamed) | `CLAUDE_COACH_EFFORT=low`, thinking on |
| Chat via `routers/coach_chat.py:484` and copilot `main.py:2025` | `claude_llm.generate` | low |
| Small features: week brief, coach nudge, LLM judge, knowledge extractor, KB distiller | `claude_llm.call` | low, thinking on |

Each feature only reaches Haiku when its `<FEATURE>_LLM_PROVIDER=claude` in that environment's `.env`.
Which flags are on in prod (and prod's `PLAN_LLM_EFFORT`) is read from the prod `.env` before measuring.

## Quality bar per feature

"Pass" means: no new release-gate failure, and every score at least today's Haiku and at least Gemini's
where Gemini has a baseline.

| Feature | Checks (existing tools) | Gemini baseline |
|---|---|---|
| Plan | `golden_eval.py compare --service scheduler --provider claude` gate (no rules fall-through, tier, week-2 volume, ME count, venues); `plan_live_personas.py --provider claude --effort …` (plan-quality score, lint failures, readiness, rules-fallback rate, JSON parse failures, p50/p95, cost; $5 cap) | personas run with `--provider gemini`; scheduler `.ref.json` |
| Goal | `goal_backtest.py` with `GOAL_JUDGE_LLM_PROVIDER=claude` (must still beat the anchors' median and today's Haiku); `golden_eval.py compare --service goal_judge --provider claude` gate (ordered, B within anchors) | backtest on Gemini; `.ref.json` |
| Gear | `golden_eval.py compare --service gear --provider claude` gate (no off-catalog pick) plus the report's field diff against the Gemini ref; 5 recommendations, brand constraint kept | `.ref.json` |
| Nutrition | same as Gear with `--service nutrition` | `.ref.json` |
| Chat | `golden_eval.py compare --service chat --provider claude` gate (safety, acceptable ≥ 90% per language, `judge_safe` ≥ 0.9) | `.ref.json` (4 of 5) |
| LLM judge | `scripts/judge_calibration.py` with `LLM_JUDGE_PROVIDER=claude`: every criterion ≥ 85% agreement | calibration set |
| Other small features | sampled side-by-side of ~10 synthetic inputs each: nudge `grounded()` pass rate, brief/card JSON validity, KB rows passing `validate_domain_rows` | same inputs on Gemini |

"Today's Haiku" is measured first, before any change, with the same commands, and its reports are kept
under a distinct name so later runs compare against it. The Gemini `.ref.json` files are never
re-captured in this work.

Paid runs are cheap on Haiku ($0.10 / $0.50 per M tokens) but each batch still gets the user's go-ahead
first, per the llm-change-process skill. Plan personas keep their $5 cap.

## Levers, cheapest first

Each lever is measured against the bar before it ships, feature by feature. A lever that fails the bar
for a feature is not applied to that feature.

1. **Make thinking visible (measurement, no behaviour change).** Record, per generation, how much of
   `output_tokens` was the visible answer versus thinking, so Langfuse shows the split as it does for
   Gemini. Also record the Anthropic `request-id` on each span, so any genuine Anthropic slowness can be
   reported with evidence. (Every generation span already carries `metadata.feature`, so per-feature
   queries group by that instead of renaming traces.)
2. **Thinking off where the task is pick-from-a-list or fill-a-form.** Gear, Nutrition, goal judge
   (already uncommitted in this worktree: `claude_llm.generate(..., thinking=False)` sends
   `thinking: {"type": "disabled"}`), then week brief, nudge and LLM judge. The knowledge extractor and
   KB distiller are admin batch jobs nobody waits on, and copilot is conversational, so they keep their
   settings. Haiku 5.5 accepts `disabled` at effort `low`/`medium`/`high`. Anthropic's guidance is
   to prefer lower effort over `disabled`; we are already at `low`, so `disabled` is the remaining step,
   and the bar decides per feature.
3. **Plan effort and thinking.** Measure Plan at `low` versus `medium` (#172 found `low` beat `medium`;
   `medium` hit `max_tokens` on 5 replies), and `low` with thinking off. Plan's thinking setting must be
   switchable from the prod `.env` like `PLAN_LLM_EFFORT`, so a regression is reverted without a deploy.
4. **Plan's tail.** Find what makes p95 400 s before tuning further: count model calls per plan job (lint
   retry and reduced-prompt retry each add a full call), output tokens per call, and calls ending at
   `max_tokens`. Fix what the data shows (for example a retry that regenerates the whole block).
5. **Prompt caching for stable prefixes.** Gear and Nutrition send the same ~24k-token catalog on every
   call with no cache reads; Plan and chat have large fixed instruction blocks. Caching cuts time to first
   token and input cost, not output time, so it comes after the output levers. It needs the cached part
   byte-stable and ahead of the per-request part. Only where the prefix is actually stable (main's #182
   changed how Gear grounds in the catalog, so this is checked on current main).
6. **Shorter output through prompt wording (last).** Claude-tuned prompt versions asking for less output
   (Plan session descriptions first, then Gear pros/cons), only if levers 2–5 miss a target. Published
   under the Langfuse `claude-staging` label, gated by the same checks, promoted to `claude-production`,
   following `.claude/skills/llm-change-process/SKILL.md`. Gemini's labels are untouched.
7. **Chat.** Chat streams, so the athlete feels time to first token. Try thinking off for chat only after
   the chat gate passes on it; Anthropic notes thinking-off models can skip a needed tool call, so the
   gate's tool-use fixtures matter here.

## Rollout

- Work starts from current `main` (this worktree is 5 commits behind, including #182's Gear grounding
  change); the uncommitted `thinking=False` change is carried over and kept only if it passes the bar.
- One PR per group, each with the llm-change-process checklist and its before/after numbers: (a)
  measurement, (b) thinking off for Gear/Nutrition/Goal, (c) Plan effort/thinking and tail, (d) small
  features, (e) chat, (f) caching, (g) prompt wording if still needed.
- Staging is stopped, so each PR is deployed to prod by hand as usual (diff the prod `.env` keys after
  every deploy). After each deploy, a Langfuse check one or two days later confirms the latency moved and
  error/fallback rates did not.

## Builder's calls

- How the visible-versus-thinking split is computed (for example `output_tokens` minus a token count of
  the returned text, or the presence of thinking blocks), as long as it is metadata-only.
- Naming of any new env var for Plan's thinking setting, following the existing `PLAN_LLM_*` pattern.
- Where in each prompt the cache breakpoint goes, and the order of PRs (d)–(f).

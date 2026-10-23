# Claude for all text generation (design)

Date: 2026-10-23. Follows PR #172 (plan generation on Claude behind `PLAN_LLM_PROVIDER`, report
`docs/superpowers/reports/2026-10-23-haiku-plan-generation.md`).

## Goal

Every Gemini text-generation call in `backend/` can run on Claude, switched per feature, so each
feature flips only after its own paid check passes. Nothing changes in production while the flags
stay at their default.

Out of scope: embeddings. Anthropic has no embedding model, so `gemini-embedding-2` stays for KB
search (`services/kb_retrieval.py`, Qdrant `uphill_kb_scheduler`). That is the only Gemini call left
once every flag is `claude`, and the server `GEMINI_API_KEY` stays for it.

## Flags

One flag per feature, `gemini` (default) or `claude`, in `config.py` next to `PLAN_LLM_PROVIDER`:

| Flag | Feature | Code |
|---|---|---|
| `GEAR_LLM_PROVIDER` | Gear Finder | `services/gear_planner.py` |
| `NUTRITION_LLM_PROVIDER` | Nutrition Lab | `services/nutrition_planner.py` |
| `GOAL_JUDGE_LLM_PROVIDER` | Goal judge (only runs when `GOAL_LLM_ENABLED=true`) | `services/goal_judge.py` |
| `WEEK_BRIEF_LLM_PROVIDER` | Week brief | `services/week_brief.py` |
| `COACH_NUDGE_LLM_PROVIDER` | Coach nudge | `services/coach_nudge.py` |
| `LLM_JUDGE_PROVIDER` | Live judge of coach turns | `services/llm_judge.py` |
| `KNOWLEDGE_LLM_PROVIDER` | Podcast cards + VI translation | `services/knowledge_extractor.py` |
| `KB_DISTILL_LLM_PROVIDER` | Gear/nutrition/race-result web distillation | `services/kb_distiller.py` |
| `COACH_COPILOT_LLM_PROVIDER` | Coach-side athlete copilot | `main.py` (`/api/coaching/.../copilot`) |
| `COACH_CHAT_LLM_PROVIDER` | Coach Uphill chat (tool calling), chat summary, legacy chat route | `services/coach_model.py`, `services/coach_chat.py`, `routers/coach_chat.py` |

`GOAL_JUDGE_LLM_PROVIDER` is named after the module, not `GOAL_LLM_PROVIDER`, so it is not confused
with the existing `GOAL_LLM_ENABLED` gate. The two compose: `GOAL_LLM_ENABLED` decides whether a model
judges at all, `GOAL_JUDGE_LLM_PROVIDER` decides which.

`scripts/` and `translate_cards.py` are operator tools, not request paths; they stay on Gemini. The
NotebookLM sweep (`scripts/distill_principles.py`) is untouched.

## Shared helper: `services/claude_llm.py`

Every feature except plan generation and coach chat is one blocking prompt → one answer, mostly
JSON against a Pydantic schema. One helper covers all of them:

- `generate(prompt, *, schema=None, system=None, model=None, max_tokens=16000)` → the `Message`.
  With `schema`, it uses `client.messages.parse(output_format=schema)` (structured outputs), which
  replaces Gemini's `response_schema`. Haiku 5.5 rejects `temperature` and prefill, so the
  Gemini `temperature=0.2` has no Claude counterpart; effort is the only knob.
- `text(message)` → the answer text; raises on `refusal` or `max_tokens`, so callers treat it like any
  failed model call (each caller already has a fallback or an error path for that).
- `is_claude(provider)`, `prompt_label(provider)`.

Callers keep their own parsing (`json.loads`) and Pydantic validation, so the Gemini and Claude paths
share everything after the text comes back. Plan generation keeps its own streamed call
(`plan_generator._claude_generate`, 32k output); it is not moved onto the helper here to keep #172's
measured behaviour unchanged.

Coach chat is a streaming tool-calling loop, so it gets its own class, `ClaudeCoachModel`, beside
`GeminiCoachModel` in `services/coach_model.py`, implementing the same `CoachModel` protocol
(`count_tokens`, `stream`, `close`) on `anthropic.AsyncAnthropic().messages.stream`. The tools in
`services/coach_tools/` are LangChain tools; the adapter converts their argument schemas to Anthropic
tool definitions and emits the same `ModelEvent("tool_call", ...)` the graph already handles. No
`langchain-anthropic` dependency.

## Keys and billing

Claude always runs on the server `ANTHROPIC_API_KEY`. Per-user Gemini keys (`users.gemini_api_key`)
stop paying for any feature whose flag is `claude`; that usage moves to the server key. Each caller
checks for the Anthropic key when its flag is `claude` and takes its existing no-key path (mock reply,
rule-based fallback, or "key missing" error) when it is empty. KB retrieval inside a feature (coach
chat, copilot, plan generation) still needs a Gemini key for the query embedding.

## Models

| Setting | Default | Used by |
|---|---|---|
| `CLAUDE_TEXT_MODEL` | `claude-haiku-5-5` | every `claude_llm.generate` caller |
| `CLAUDE_TEXT_EFFORT` | `low` | same |
| `CLAUDE_COACH_MODEL` | `claude-haiku-5-5` | `ClaudeCoachModel` |
| `CLAUDE_COACH_EFFORT` | `low` | same |
| `CLAUDE_PLAN_MODEL` / `PLAN_LLM_EFFORT` | unchanged from #172 | plan generation |

Haiku 5.5 at `low` effort is the default everywhere. #172 found `low` beat `medium` for plan
generation (medium ran into `max_tokens` on 5 replies); the one-shot features here are shorter and
simpler, so `low` is the starting point and the golden runs confirm it.

Where a bigger model may earn its price (only on evidence from the paid check):

- **Coach chat** — multi-turn, tool choice, safety-sensitive, the most user-visible text. If Haiku
  misses the chat gate (safety, `judge_safe` ≥ 0.9, acceptable rate ≥ 90 % per language), try
  `claude-sonnet-5-5` via `CLAUDE_COACH_MODEL` before touching the prompt. The coach chat PR adds
  Sonnet 5.5 to the price table and the model allowlist so that override is traced and costed.
- **Goal judge** — numeric reasoning over anchors; if the hold-out backtest does not beat the anchors'
  median on Haiku, Sonnet 5.5 is the next candidate.
- Gear, nutrition, week brief, nudge, knowledge cards, KB distillation and the live judge are
  extraction, ranking from a supplied catalog, or short wording: Haiku. Opus is not justified for any
  of them.

## Prompt labels

Same rule as #172: when a feature's flag is `claude`, `observability.load_prompt` asks Langfuse for
the label `claude-<COACH_CHAT_PROMPT_LABEL>` (`claude-production`, `claude-staging`). With no version
under that label, it serves the in-code fallback, which is the same text Gemini uses. So:

1. Flip-ready means the in-code prompt passes the paid check on Claude, or a Claude-tuned version
   exists in Langfuse under `claude-staging` and passes it.
2. Promote that version to `claude-production` before flipping the flag in prod.
3. Gemini keeps reading `production` / `staging`; the two never share a version by accident.

Prompts without Langfuse management today (the copilot system prompt in `main.py`, the KB distiller
asks, the VI translation prompt) stay in-code.

## Observability

- **Generation spans:** each Claude branch uses the same `observability.generation(...)` scope as its
  Gemini branch, with `model=` set to the Claude model, and records
  `observability.Usage.from_anthropic(message.usage)` (input includes cache read/write tokens; output
  includes thinking).
- **Allowlist** (`services/observability_policy.py`): `anthropic` provider/system and
  `claude-haiku-5-5` are already allowed (#172). The `claude` / `claude_retry` span names were not
  (plan generation's Claude spans exported as `operation`); the goal judge PR adds them. The coach chat PR adds `claude-sonnet-5-5`. No new
  span names, features or metadata keys: the existing ones carry over, and the `engine` metadata value
  is `claude` instead of `gemini`.
- **Prices** (`config.DEFAULT_LLM_PRICES_USD_PER_M`): Haiku 5.5 is present; Sonnet 5.5 is added with
  the coach chat PR ($2 input, $0.20 cached, $10 output per M). Langfuse needs matching model
  definitions before the first flip.
- **Telemetry:** `rag_attempts_total` / `rag_latency_seconds` use `engine="claude"` on the Claude path,
  so the Gemini and Claude hit rates are visible side by side, as `gemini_retry` is today.
- Export stays metadata-only (`LANGFUSE_EXPORT_CONTENT=false`): nothing about the Claude path sends
  prompts or replies to Langfuse.

## Rollout

One PR per feature, in this order, each with the `llm-change-process` checklist:

1. Gear + Nutrition (this spec ships with it).
2. Goal judge.
3. Small callers: week brief, coach nudge, live judge, knowledge extractor, KB distiller, copilot.
4. Coach chat.

Each PR leaves its flag at `gemini` and wires its service into `scripts/golden_eval.py --provider claude` (sets that service's flag; `--model` then picks the Claude model and the run name records both). Before flipping a flag, run the paid check named in its PR
(asked for and approved separately):

| Feature | Paid check before the flip |
|---|---|
| Gear | `golden_eval.py compare --service gear --provider claude --push-langfuse --synthetic-only` (no off-catalog picks) |
| Nutrition | `golden_eval.py compare --service nutrition --provider claude --push-langfuse --synthetic-only` |
| Goal judge | `scripts/goal_backtest.py` with `GOAL_JUDGE_LLM_PROVIDER=claude` must beat the anchors' median, then `golden_eval.py compare --service goal_judge --provider claude` |
| Live judge | `LLM_JUDGE_PROVIDER=claude python scripts/judge_calibration.py`: every criterion ≥ 85 % agreement (llm-change-process § C) |
| Other small callers | no golden set exists; a sampled side-by-side of ~10 synthetic inputs per feature (nudge `grounded()` pass rate, brief/card JSON validity, KB distiller rows passing `validate_domain_rows`) |
| Coach chat | `golden_eval.py compare --service chat --provider claude` (chat gate incl. LLM judge) |

Prod also needs `anthropic==1.17.0` installed in the container (still missing per #172) and
`ANTHROPIC_API_KEY` in `backend/.env` before any flag flips.

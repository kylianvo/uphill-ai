# Claude Haiku 5.5 for plan generation

Status: draft, 2026-10-23. Source: brainstorm `~/.claude/plans/help-me-inspect-my-wild-nova.md`, topic B. Builds on the unimplemented `docs/superpowers/plans/2026-10-09-haiku-benchmark.md`.

## Job

Let plan generation run on Claude Haiku 5.5 behind one env switch, prove it is at least as good as Gemini 3.8 Flash on our personas, then flip. Only plan generation; the other 18 Gemini call sites and embeddings stay on Gemini.

## Facts

- Model `claude-haiku-5-5`, $0.10 / $0.50 per MTok in/out (prompts ≤ 100K). One block ≈ $0.005; a 15-call persona run ≈ $0.05–0.15.
- Adaptive thinking with `output_config.effort` (low … max, default medium). `temperature` returns a 400. No prefill. No server-side refusal fallback: check `stop_reason == "refusal"`.
- Plan generation already parses JSON from free text, so Haiku text drops in.
- Embeddings stay on Gemini (no Anthropic embeddings; Qdrant holds 3072-dim vectors).
- `anthropic` is not installed.

## Design

### Switch
- `config.py`: `PLAN_LLM_PROVIDER = gemini|claude` (default `gemini`), `PLAN_LLM_EFFORT = low|medium|high` (default `medium`), `ANTHROPIC_API_KEY`, `CLAUDE_PLAN_MODEL = claude-haiku-5-5`.
- `plan_generator.py`: a small `_plan_llm_generate(prompt) -> (text, Usage)` used by the `_try_gemini` path and its reduced-prompt retry. Gemini branch is the current code moved, not changed.
- Claude branch: `anthropic.Anthropic().messages.create(model, max_tokens, messages, output_config={"effort": ...})`, text from the `text` blocks, refusal → treated like an unparseable response (falls to the retry, then rules).
- Per-user Gemini keys (`users.gemini_api_key`) are ignored on the Claude branch.
- `anthropic` added to `requirements.txt`.

### Observability (silent traps; all required before any prod run)
- `Usage.from_anthropic` (input, output, cache tokens).
- `observability_policy.py`: add `anthropic` to `_PROVIDERS`/`_SYSTEMS`, `claude-haiku-5-5` to `_MODELS`, `claude`/`claude_retry` to `_ENGINES`; the Anthropic instrumentation scope if one is used.
- `observability.py`: `plan_engine` scores allow `claude`, `claude_retry`.
- `config.DEFAULT_LLM_PRICES_USD_PER_M` + `METRIC_MODELS`: price row for `claude-haiku-5-5`.
- Langfuse model definition for `claude-haiku-5-5`.
- Test: a Claude span and cost survive the policy filter (not labelled `other`).

### Prompt
- Copy Langfuse `plan_generation` to a Claude variant, label `claude-staging`; same variables.
- Run the claude-api prompt audit on it: soften Gemini-era "IMPORTANT / NEVER" shouting, keep rules.
- `load_prompt` picks the label by provider.

## Evaluation

1. **Free baseline:** replay saved Gemini persona rows, score with `scripts/plan_quality_report.py`.
2. **Prompt iteration (free):** dump the built prompt to a file; a Claude Code subagent on `model: haiku` returns rows; replay + score. Good for "does it follow the rules and return valid rows", not a gate (own system prompt, no effort setting, no cost/latency).
3. **Gate (paid, cap $5):** `scripts/plan_live_personas.py` with new `--provider claude --effort low|medium|high` flags, ~10 personas. Script stops at the budget cap. Compare per effort: plan-quality score, lint failures, rules-fallback rate, JSON parse failures, latency p50/p95, cost per plan.
4. **Release gate:** no fall-through to rules on the golden set (`golden_eval` rule) and plan-quality score ≥ Gemini's, at the cheapest effort that passes.
5. **Shadow (optional, 1 week):** new plans stay on Gemini; a background Haiku call on the same prompt is scored and logged, never shown.
6. **Flip:** `PLAN_LLM_PROVIDER=claude` in prod `backend/.env`. Rollback = one env value.

## Out of scope

Coach chat, goal judge, gear, nutrition, KB distiller, knowledge cards, embeddings. Each gets its own swap later.

## Checks

- Unit: provider switch picks the branch; refusal → retry path; usage mapping; policy allowlist.
- Langfuse checklist from `.claude/skills/llm-change-process/SKILL.md` in the PR.
- Every paid run needs the user's go-ahead first.

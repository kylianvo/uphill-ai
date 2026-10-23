# Haiku 5.5 Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every Haiku-backed feature at least as fast as Gemini was, without any quality check scoring below today's Haiku or Gemini.

**Architecture:** First make Haiku's thinking tokens and request ids visible in Langfuse, then measure a quality and latency baseline, then apply one lever at a time (thinking off, Plan effort/thinking, chat thinking, caching, prompt wording), each gated by the existing golden sets, persona runs and backtests before it ships. Levers are code constants for one-shot features and `.env` switches for Plan and chat, so a regression there is reverted without a deploy.

**Tech Stack:** Python 3 / FastAPI backend, `anthropic` SDK (Haiku 5.5 `claude-haiku-5-5`), Langfuse (metadata-only), pytest, `scripts/golden_eval.py`, `scripts/plan_live_personas.py`, `scripts/goal_backtest.py`, `scripts/judge_calibration.py`.

**Spec:** `docs/superpowers/specs/2026-10-24-haiku-latency-design.md`

## Global Constraints

- Model stays `claude-haiku-5-5` everywhere; no Gemini path, prompt or label changes.
- `thinking: {"type": "disabled"}` is only ever sent with effort `low`, `medium` or `high` (Haiku 5.5 returns 400 with `xhigh`/`max`).
- `max_tokens` is never lowered below today's values (16000 for `claude_llm.generate`, 32000 for Plan, `max_output_tokens + 4096` for chat).
- Never re-capture `tests/golden/<service>/*.ref.json` (no `golden_eval.py capture --overwrite`); those are the Gemini baselines.
- Every paid run (golden `compare`, personas, backtest, calibration) is listed with a cost estimate and approved by the user before it runs; personas keep `--budget-usd 5`.
- Paid runs and integration tests use the local Docker stack (Postgres on host port 5433, local Qdrant with `scripts/load_kb.py`), never the prod database.
- `LANGFUSE_EXPORT_CONTENT` stays `false`; the only new exported metadata key is `request_id`.
- A lever ships for a feature only if, on every check in the spec's "Quality bar per feature" table, the result is at least today's Haiku and at least Gemini where a Gemini baseline exists.
- Each PR carries the `.claude/skills/llm-change-process/SKILL.md` checklist plus its before/after numbers from `docs/haiku-latency/results.md`.
- Prod deploys are by hand (staging is stopped); diff the prod `backend/.env` keys after every deploy.

## Review Focus

- A Claude reply with thinking blocks and very little text (refusal, `max_tokens` cut-off): the answer/thinking split must never go negative and output + thinking must equal Anthropic's `output_tokens`. Test in Task 1.
- Vietnamese or other long-character text: the visible-token estimate must be clamped to `output_tokens`. Test in Task 1.
- `PLAN_LLM_THINKING=disabled` with `PLAN_LLM_EFFORT` set to something other than low/medium/high in a `.env`: the request must not 400; Plan falls back to adaptive thinking. Test in Task 5.
- A Langfuse-managed prompt whose variable order changed, so the stable prefix no longer starts the compiled prompt: the call must go out uncached with the full prompt, never a wrong or split prompt. Test in Task 8.
- Chat with thinking off when a turn needs a tool: the model must still call the tool rather than write it as text. The chat gate in Task 7 must include a tool-using fixture.

---

### Task 0: Start from current main and record what prod runs

**Files:**
- Create: `docs/haiku-latency/results.md`

**Interfaces:**
- Produces: `docs/haiku-latency/results.md` with a "Prod settings" section and a "Baseline" table every later task appends to.

- [ ] **Step 1: Commit the uncommitted thinking-off change as its own commit**

The worktree holds an unmeasured change (`claude_llm.generate(..., thinking=False)` used by `gear_planner`, `nutrition_planner`, `goal_judge`, plus a test). Keep it, unshipped until Task 3 measures it.

```bash
git add backend/services/claude_llm.py backend/services/gear_planner.py backend/services/nutrition_planner.py backend/services/goal_judge.py backend/tests/unit/test_claude_llm.py
git commit -m "WIP: thinking off for gear, nutrition, goal judge (unmeasured)"
```

- [ ] **Step 2: Bring the branch up to date with main**

Call the ccd_host `sync_with_base_branch` tool; resolve conflicts (main's #182 changed `gear_planner.py`).
Run: `cd backend && pytest tests/unit/test_claude_llm.py tests/unit/test_plan_llm_provider.py tests/unit/test_coach_model.py -q`
Expected: all pass.

- [ ] **Step 3: Read prod's Claude settings (read-only)**

Run: `ssh root@45.119.215.120 "grep -E '_LLM_PROVIDER|_EFFORT|CLAUDE_|PLAN_LLM' /opt/uphill-ai-backend/backend/.env"`
Write the values into `docs/haiku-latency/results.md` under "Prod settings". Features whose provider is `gemini` in prod are measured but their prod check in Task 9 is skipped.

- [ ] **Step 4: Commit**

```bash
git add docs/haiku-latency/results.md
git commit -m "docs: record prod Claude settings for the Haiku latency work"
```

### Task 1: Thinking split and request id in Langfuse

**Files:**
- Modify: `backend/services/observability.py` (`Usage.from_anthropic`)
- Modify: `backend/services/observability_policy.py` (`METADATA_KEYS`)
- Modify: `backend/services/claude_llm.py` (new `record`, used by `call`)
- Modify: `backend/services/gear_planner.py`, `backend/services/nutrition_planner.py`, `backend/services/goal_judge.py`, `backend/services/plan_generator.py` (the `set_usage(Usage.from_anthropic(...))` lines), `backend/services/coach_model.py` (`ClaudeCoachModel.stream`)
- Test: `backend/tests/unit/test_anthropic_usage_split.py` (new), `backend/tests/unit/test_claude_llm.py`, `backend/tests/unit/test_observability_policy.py`

**Interfaces:**
- Produces: `Usage.from_anthropic(usage: Any, content: list[Any] | None = None) -> Usage`. With a `thinking` block in `content`, `output_tokens` is the estimated visible answer and `thinking_tokens` the rest; without one, unchanged behaviour (`thinking_tokens=0`). `output_tokens + thinking_tokens` always equals Anthropic's `usage.output_tokens`, so cost is unchanged.
- Produces: `claude_llm.record(generation: observability.GenerationRecorder, message: Any) -> None`, which sets the split usage and `request_id` (from `message._request_id`, skipped when missing).
- Produces: metadata key `request_id` in `observability_policy.METADATA_KEYS`.

- [ ] **Step 1: Write the failing tests** in `tests/unit/test_anthropic_usage_split.py`

```python
def _usage(out=1000):  # SimpleNamespace(input_tokens=10, output_tokens=out, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    ...

def test_split_moves_non_answer_tokens_to_thinking():
    u = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "x" * 300)])
    assert (u.output_tokens, u.thinking_tokens) == (100, 900)

def test_no_thinking_block_keeps_everything_as_output():
    u = Usage.from_anthropic(_usage(1000), [block("text", "x" * 300)])
    assert (u.output_tokens, u.thinking_tokens) == (1000, 0)

def test_estimate_is_clamped_to_output_tokens():  # long VI text
    u = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "ạ" * 6000)])
    assert (u.output_tokens, u.thinking_tokens) == (1000, 0)

def test_refusal_with_empty_text_is_all_thinking():
    u = Usage.from_anthropic(_usage(500), [block("thinking", "")])
    assert (u.output_tokens, u.thinking_tokens) == (0, 500)

def test_split_does_not_change_cost():
    raw = Usage.from_anthropic(_usage(1000))
    split = Usage.from_anthropic(_usage(1000), [block("thinking", ""), block("text", "x" * 300)])
    assert _cost_details_usd("claude-haiku-5-5", split)["total"] == _cost_details_usd("claude-haiku-5-5", raw)["total"]
```

In `test_claude_llm.py`: `test_record_sets_split_usage_and_request_id` (fake recorder captures `set_usage` and `set` calls; message with `_request_id="req_1"` → `set(request_id="req_1")`; message without it → no `set` call). In `test_observability_policy.py`: `filter_metadata({"request_id": "req_1"}) == {"request_id": "req_1"}`.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && pytest tests/unit/test_anthropic_usage_split.py tests/unit/test_claude_llm.py tests/unit/test_observability_policy.py -q`
Expected: FAIL (`from_anthropic` takes no `content`, `record` undefined, `request_id` filtered out).

- [ ] **Step 3: Implement**

Visible answer estimate is `ceil(len(text) / 3)` over the joined `text` blocks, clamped to `output_tokens`, with the comment `# shortcut: chars/3 approximates Haiku 5.5's tokenizer; replace with count_tokens if the split needs to be exact`. Add `request_id` to `METADATA_KEYS`. `claude_llm.call` uses `record`. Replace each direct `generation.set_usage(observability.Usage.from_anthropic(message.usage))` in gear, nutrition, goal judge and plan with `claude_llm.record(generation, message)`. In `ClaudeCoachModel.stream`, pass `final.content` to `Usage.from_anthropic` and `gen.set(request_id=...)` when `getattr(final, "_request_id", None)` is set.

- [ ] **Step 4: Run tests to verify they pass, plus the observability suite**

Run: `cd backend && pytest tests/unit -q -k "observability or claude or coach_model or plan_llm_provider or usage_split"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services backend/tests/unit
git commit -m "Observability: split Haiku output into answer vs thinking, record Anthropic request id"
```

Open PR (a). No behaviour change, so it deploys first and gives Task 2 the thinking split in Langfuse.

### Task 2: Baseline of today's Haiku (paid, approval first)

**Files:**
- Create: `docs/haiku-latency/baseline/` (copied reports and persona JSONs)
- Modify: `docs/haiku-latency/results.md` ("Baseline" table)

**Interfaces:**
- Consumes: prod settings from Task 0 (Plan effort to reproduce).
- Produces: per feature, the baseline numbers later tasks compare against: gate result, scores, latency p50/p95, output tokens.

- [ ] **Step 1: Make a clean checkout of today's behaviour**

The branch now has thinking off for three features, so the baseline runs from main. `git worktree add ../haiku-baseline origin/main`, copy `backend/.env` into it, point `DATABASE_URL` at the local scratch database and `QDRANT_URL` at local Qdrant, and run `python scripts/load_kb.py --domain scheduler` once.

- [ ] **Step 2: Ask the user to approve the batch**

List the commands below with an estimate (Haiku: cents per golden service; personas capped at $5 per provider; Gemini personas are the costliest item) and wait for a yes.

- [ ] **Step 3: Run the baseline in `../haiku-baseline/backend`**

```bash
python scripts/golden_eval.py compare --service gear --provider claude
python scripts/golden_eval.py compare --service nutrition --provider claude
python scripts/golden_eval.py compare --service goal_judge --provider claude
python scripts/golden_eval.py compare --service scheduler --provider claude
python scripts/golden_eval.py compare --service chat --provider claude
GOAL_JUDGE_LLM_PROVIDER=claude python scripts/goal_backtest.py
LLM_JUDGE_PROVIDER=claude python scripts/judge_calibration.py
python scripts/plan_live_personas.py --provider claude --effort <prod PLAN_LLM_EFFORT> --out <scratch>/personas-haiku --budget-usd 5
python scripts/plan_live_personas.py --provider gemini --out <scratch>/personas-gemini --budget-usd 5
```

After each `compare`, copy `tests/golden/report_<service>.md` to `docs/haiku-latency/baseline/report_<service>_haiku.md` (the next run overwrites it). Copy the persona JSONs to `docs/haiku-latency/baseline/personas-{haiku,gemini}/`.

Expected: every command finishes; `[gate]` lines are recorded as they are (a baseline failure is a fact to record, not to fix here).

- [ ] **Step 4: Add Langfuse latency for the same features**

Query generation spans, last 14 days, grouped by `metadata.feature` and model: count, latency p50/p95, output tokens p50, and, from Task 1 onward, thinking tokens. Add these to the "Baseline" table.

- [ ] **Step 5: Remove the baseline worktree and commit**

```bash
git worktree remove ../haiku-baseline
git add docs/haiku-latency
git commit -m "docs: Haiku baseline (quality and latency) before latency levers"
```

### Task 3: Thinking off for Gear, Nutrition and Goal judge (measure the WIP change)

**Files:**
- Already changed in Task 0's WIP commit: `backend/services/{gear_planner,nutrition_planner,goal_judge}.py`, `backend/services/claude_llm.py`
- Modify: `docs/haiku-latency/results.md`

**Interfaces:**
- Consumes: `claude_llm.generate(..., thinking: bool = True)` (WIP commit); baseline from Task 2.

- [ ] **Step 1: Ask for approval, then run on the branch**

```bash
python scripts/golden_eval.py compare --service gear --provider claude
python scripts/golden_eval.py compare --service nutrition --provider claude
python scripts/golden_eval.py compare --service goal_judge --provider claude
GOAL_JUDGE_LLM_PROVIDER=claude python scripts/goal_backtest.py
```

Copy reports to `docs/haiku-latency/thinking-off/`.

- [ ] **Step 2: Decide per feature**

Each feature keeps `thinking=False` only if its gate passes, its scores are ≥ the Haiku baseline and ≥ the Gemini ref, and its latency p50 drops. Otherwise remove `thinking=False` from that call site. Record the verdict and numbers in `results.md`.

- [ ] **Step 3: Run unit tests and commit**

Run: `cd backend && pytest tests/unit/test_claude_llm.py -q -k "gear or nutrition or goal or claude"`
Expected: PASS.

```bash
git add backend/services docs/haiku-latency
git commit -m "Gear, Nutrition, Goal judge: Haiku without thinking (measured against Haiku and Gemini baselines)"
```

Open PR (b) with the llm-change-process checklist and the before/after table.

### Task 4: Find what makes Plan's slowest 5% take ~400 s

**Files:**
- Modify: `docs/haiku-latency/results.md` ("Plan tail" section)

**Interfaces:**
- Produces: a finding that decides whether Task 5 is enough or a targeted fix task is added after it.

- [ ] **Step 1: Query Langfuse (no cost)**

For `metadata.feature = plan_generation`, model `claude-haiku-5-5`, last 14 days:
- generation spans with `output_tokens + thinking_tokens ≥ 30000` (runs into the 32000 cap),
- spans per trace (a plan job with primary + reduced retry + lint retry has 3+),
- share of spans with `tier = retry`,
- latency against output tokens (is the tail long output, or slow tokens/second?).

- [ ] **Step 2: Write the finding**

One paragraph in `results.md`: which of (a) runaway output hitting the cap, (b) retries stacking, (c) slow throughput explains the calls over 60 s, with counts. If (a) or (b) dominates and Task 5's effort/thinking change does not remove it, add a task after Task 5 that fixes that specific cause, using the same gate.

- [ ] **Step 3: Commit**

```bash
git add docs/haiku-latency/results.md
git commit -m "docs: what drives Plan's slow tail on Haiku"
```

### Task 5: Plan effort and thinking switch

**Files:**
- Modify: `backend/config.py` (`PLAN_LLM_THINKING`)
- Modify: `backend/services/plan_generator.py` (`_claude_generate`)
- Modify: `backend/scripts/plan_live_personas.py` (`--thinking`)
- Test: `backend/tests/unit/test_plan_llm_provider.py`

**Interfaces:**
- Produces: `settings.PLAN_LLM_THINKING: str = os.getenv("PLAN_LLM_THINKING", "adaptive")`, values `adaptive` | `disabled`.
- Produces: `_claude_generate(prompt: str) -> Any` sends `thinking={"type": "disabled"}` only when `PLAN_LLM_THINKING == "disabled"` and `PLAN_LLM_EFFORT in ("low", "medium", "high")`; otherwise no `thinking` key.
- Produces: `plan_live_personas.py --thinking {adaptive,disabled}` setting `settings.PLAN_LLM_THINKING`.

- [ ] **Step 1: Write the failing tests**

```python
def test_claude_plan_call_disables_thinking_when_configured(monkeypatch):
    # PLAN_LLM_THINKING="disabled", PLAN_LLM_EFFORT="low" -> stream kwargs["thinking"] == {"type": "disabled"}

def test_claude_plan_call_keeps_adaptive_by_default(monkeypatch):
    # PLAN_LLM_THINKING="adaptive" -> "thinking" not in stream kwargs

def test_claude_plan_call_never_disables_thinking_above_high(monkeypatch):
    # PLAN_LLM_THINKING="disabled", PLAN_LLM_EFFORT="xhigh" -> "thinking" not in stream kwargs
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && pytest tests/unit/test_plan_llm_provider.py -q`
Expected: the first test FAILs (no `thinking` sent); the other two pass trivially.

- [ ] **Step 3: Implement the setting, the `_claude_generate` change and the `--thinking` flag**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/test_plan_llm_provider.py -q`
Expected: PASS.

- [ ] **Step 5: Ask for approval, then sweep (paid)**

Three configurations, each with personas (`--budget-usd 5`) and `golden_eval.py compare --service scheduler --provider claude` (set the env vars for the scheduler run): `low`+`adaptive`, `low`+`disabled`, and `medium`+`disabled` only if `low` fails the bar. Save outputs under `docs/haiku-latency/plan-<effort>-<thinking>/`.

- [ ] **Step 6: Pick the setting**

The fastest configuration whose persona checks (plan-quality score, lint failures, readiness, rules-fallback rate, JSON parse failures) and scheduler gate are all ≥ both the Haiku and the Gemini baselines. Record the comparison table and the chosen `PLAN_LLM_EFFORT` / `PLAN_LLM_THINKING` in `results.md`. If none passes, keep prod's current values and say so.

- [ ] **Step 7: Commit**

```bash
git add backend/config.py backend/services/plan_generator.py backend/scripts/plan_live_personas.py backend/tests/unit/test_plan_llm_provider.py docs/haiku-latency
git commit -m "Plan: PLAN_LLM_THINKING switch for Haiku, measured effort/thinking sweep"
```

Open PR (c). Prod rollout is an `.env` change (`PLAN_LLM_EFFORT`, `PLAN_LLM_THINKING`) after deploy.

### Task 6: Thinking off for week brief, coach nudge and LLM judge

**Files:**
- Modify: `backend/services/week_brief.py`, `backend/services/coach_nudge.py`, `backend/services/llm_judge.py` (their `claude_llm.call(...)` gets `thinking=False`)
- Create: `backend/scripts/small_callers_check.py`
- Test: `backend/tests/unit/test_claude_small_callers.py`

**Interfaces:**
- Consumes: `claude_llm.call(prompt, generation, **kwargs)` forwarding `thinking` to `generate`.
- Produces: `small_callers_check.py --feature {week_brief,coach_nudge} --thinking {on,off} --n 10`, which builds 10 synthetic inputs, runs the feature on Claude and prints per run: valid output (brief JSON parses / nudge passes `grounded()`), latency, and a summary line `valid=<k>/10 p50=<s>`.

The knowledge extractor and KB distiller are left unchanged: they are admin batch jobs nobody waits on. Copilot and the legacy chat router are conversational and don't record generations, so they're also left alone.

- [ ] **Step 1: Write the failing tests**

In `test_claude_small_callers.py`, one test per feature asserting the Claude branch passes `thinking=False` to `claude_llm.call` (patch `claude_llm.call`, assert `kwargs["thinking"] is False`).

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && pytest tests/unit/test_claude_small_callers.py -q`
Expected: FAIL (`thinking` not passed).

- [ ] **Step 3: Implement the three call-site changes and the check script**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/test_claude_small_callers.py -q`
Expected: PASS.

- [ ] **Step 5: Ask for approval, then measure (paid, cents)**

Run `small_callers_check.py` for both features with `--thinking on` (baseline) and `--thinking off`, and once with the Gemini provider for the Gemini baseline. Run `LLM_JUDGE_PROVIDER=claude python scripts/judge_calibration.py` on the branch (every criterion ≥ 85% and ≥ the Task 2 baseline). Keep `thinking=False` per feature only where valid counts are ≥ both baselines; revert the others. Record in `results.md`.

- [ ] **Step 6: Commit**

```bash
git add backend/services backend/scripts/small_callers_check.py backend/tests/unit/test_claude_small_callers.py docs/haiku-latency
git commit -m "Week brief, coach nudge, LLM judge: Haiku without thinking where quality holds"
```

Open PR (d).

### Task 7: Chat thinking switch

**Files:**
- Modify: `backend/config.py` (`CLAUDE_COACH_THINKING`)
- Modify: `backend/services/coach_model.py` (`ClaudeCoachModel.stream`)
- Possibly create: `backend/tests/golden/chat/fixture_en_tool_week_lookup.json` (only if no existing chat fixture needs a tool)
- Test: `backend/tests/unit/test_coach_model.py`

**Interfaces:**
- Produces: `settings.CLAUDE_COACH_THINKING: str = os.getenv("CLAUDE_COACH_THINKING", "adaptive")`, values `adaptive` | `disabled`; `stream` sends `thinking={"type": "disabled"}` only when `disabled` and `CLAUDE_COACH_EFFORT in ("low", "medium", "high")`.

- [ ] **Step 1: Write the failing test**

`test_claude_coach_model_disables_thinking_when_configured`: with `CLAUDE_COACH_THINKING="disabled"`, the fake client's `messages.stream` kwargs contain `thinking == {"type": "disabled"}`; with the default, no `thinking` key.

- [ ] **Step 2: Run it to verify it fails**

Run: `cd backend && pytest tests/unit/test_coach_model.py -q -k thinking`
Expected: FAIL.

- [ ] **Step 3: Implement the setting and the `stream` change**

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/test_coach_model.py -q`
Expected: PASS.

- [ ] **Step 5: Make sure the chat gate exercises a tool call**

Check whether any `tests/golden/chat/fixture_*.json` needs a coach tool to answer (for example a question about this week's sessions). If none does, add one synthetic fixture (`"synthetic": true`, EN) whose correct answer needs `get_week`, with a `safety_invariants.must_not_contain` entry for a raw tool-call string such as `"get_week("`.

- [ ] **Step 6: Ask for approval, then run the chat gate twice (paid)**

`golden_eval.py compare --service chat --provider claude` with `CLAUDE_COACH_THINKING=adaptive` and with `disabled`. Keep `disabled` only if the gate passes, acceptable rate and `judge_safe` are ≥ the Task 2 baseline, and the tool fixture passes. Record in `results.md`.

- [ ] **Step 7: Commit**

```bash
git add backend/config.py backend/services/coach_model.py backend/tests docs/haiku-latency
git commit -m "Chat: CLAUDE_COACH_THINKING switch, measured against the chat gate"
```

Open PR (e). Prod rollout is an `.env` change, then check time to first token in Langfuse (Task 9).

### Task 8: Cache stable prompt prefixes, only where traffic repeats

**Files:**
- Modify: `backend/services/claude_llm.py` (`generate` gains `cached_prefix`)
- Modify: `backend/services/gear_planner.py`, `backend/services/nutrition_planner.py`
- Test: `backend/tests/unit/test_claude_llm.py`

**Interfaces:**
- Produces: `claude_llm.generate(prompt, *, ..., cached_prefix: str | None = None)`. When `prompt` is a string that starts with `cached_prefix`, the user content is two text blocks, `[{"type": "text", "text": cached_prefix, "cache_control": {"type": "ephemeral"}}, {"type": "text", "text": rest}]`; otherwise it sends `prompt` unchanged.

- [ ] **Step 1: Decide whether caching would ever hit (no cost)**

From Langfuse, per feature (gear, nutrition, plan): the share of calls with another call of the same feature less than 5 minutes earlier. Also confirm on current main whether the Gear/Nutrition catalog block is byte-identical across two different criteria (compile the prompt twice locally). Continue only for features with a stable prefix ≥ 512 tokens and a repeat share of at least 30%; otherwise record "not worth it" in `results.md` with the numbers, commit, and stop this task.

- [ ] **Step 2: Write the failing tests**

```python
def test_generate_caches_a_matching_prefix(monkeypatch):
    # generate("CATALOG...criteria", cached_prefix="CATALOG...") -> messages[0]["content"] ==
    #   [{"type":"text","text":"CATALOG...","cache_control":{"type":"ephemeral"}}, {"type":"text","text":"criteria"}]

def test_generate_sends_prompt_unchanged_when_prefix_does_not_match(monkeypatch):
    # generate("criteria first, CATALOG later", cached_prefix="CATALOG") -> content == "criteria first, CATALOG later"
```

- [ ] **Step 3: Run them to verify they fail**

Run: `cd backend && pytest tests/unit/test_claude_llm.py -q -k cache`
Expected: FAIL.

- [ ] **Step 4: Implement `cached_prefix`, and pass it from the qualifying features**

The prefix is the prompt compiled with its trailing per-request variables (`criteria_block`, `course_context_block` for Gear; the equivalents for Nutrition) set to empty strings.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/unit/test_claude_llm.py -q`
Expected: PASS.

- [ ] **Step 6: Ask for approval, then confirm quality is unchanged (paid)**

Rerun `compare` for each feature that now caches. Pass means gate and scores equal to Task 3's results, and a second identical run shows `cached_tokens > 0` in Langfuse.

- [ ] **Step 7: Commit**

```bash
git add backend/services/claude_llm.py backend/services/gear_planner.py backend/services/nutrition_planner.py backend/tests/unit/test_claude_llm.py docs/haiku-latency
git commit -m "Gear/Nutrition: cache the catalog prefix on Haiku"
```

Open PR (f).

### Task 9: Deploy each PR and confirm in production

**Files:**
- Modify: `docs/haiku-latency/results.md` ("Production" section)

- [ ] **Step 1: After each PR merges, deploy by hand**

Follow the `deploy-backend` skill / `deploy_main_prod.sh` with `LANGFUSE_RELEASE=$(git rev-parse --short HEAD)`. Apply any `.env` value the PR chose (`PLAN_LLM_EFFORT`, `PLAN_LLM_THINKING`, `CLAUDE_COACH_THINKING`), then diff prod `.env` keys against the pre-deploy backup.

- [ ] **Step 2: One to two days later, check Langfuse**

Per feature on Haiku since the deploy: latency p50/p95, output and thinking tokens, time to first token for chat, `tier = retry` share for Plan, and error-level spans. Pass means p50 at or under the spec's target and retry and error shares no higher than the baseline. Record in `results.md`. If a feature regressed, revert its `.env` switch, or revert its PR for code constants.

- [ ] **Step 3: Commit**

```bash
git add docs/haiku-latency/results.md
git commit -m "docs: Haiku latency in production after <PR>"
```

### Task 10: Shorter output through Claude-only prompt wording (only if a target is still missed)

**Files:**
- Langfuse prompts only (`plan_generation`, then `gear_finder`), label `claude-staging` → `claude-production`
- Modify: `docs/haiku-latency/results.md`

Run this task only for a feature that still misses its latency target in Task 9 with every other lever applied.

- [ ] **Step 1: Write the Claude-tuned version**

Start from the current `claude-production` (or in-code fallback) text. Change only output-length instructions; for Plan, cap each session description (for example "description: at most 2 sentences"). Publish it under `claude-staging`, following `.claude/skills/llm-change-process/SKILL.md`. Gemini's `production`/`staging` labels are untouched.

- [ ] **Step 2: Ask for approval, then gate it (paid)**

The same checks as the feature's lever task (Plan: personas + scheduler gate; Gear: gear `compare`), run with `--prompt-label claude-staging`. Pass means ≥ both baselines and output tokens p50 lower.

- [ ] **Step 3: Promote and record**

Move `claude-production` to the new version, record before/after in `results.md`, and confirm in production as in Task 9 Step 2.

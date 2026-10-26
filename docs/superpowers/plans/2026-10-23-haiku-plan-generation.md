# Haiku Plan Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Plan generation can run on Claude Haiku 5.5 behind `PLAN_LLM_PROVIDER`. A persona matrix (10 existing personas plus 5 new ones) shows whether Haiku is at least as good as Gemini 3.8 Flash, and the plans come out as coach review packs.

**Architecture:** One function, `_plan_llm_generate`, inside `PlanGenerator.generate_plan_workouts`, sends the compiled prompt to Gemini (today's code, moved) or Claude, and returns the text. Everything after it (JSON extraction, post-processing, retry, rules fallback) stays shared. Observability learns the new provider, model and engine names, so Claude spans and costs are not dropped or labelled `other`. `plan_live_personas.py` gains `--provider/--effort/--budget-usd` flags, records engine, cost and latency per week, and gets 5 new personas aimed at what #171 changed.

**Tech Stack:** Python 3.12, `anthropic==1.17.0` (sync client, streaming + `get_final_message()`), `google-genai` (unchanged), pytest, Prometheus counters, Langfuse.

**Spec:** `docs/superpowers/specs/2026-10-23-haiku-plan-generation-design.md`

## Global Constraints

- The default stays `PLAN_LLM_PROVIDER=gemini`, so production behaviour is unchanged until the flip. Only plan generation (`plan_generation` prompt, `_try_gemini` path) switches. `plan_single_workout`, `block_narrative`, embeddings and the KB retrieval stay on Gemini.
- Claude call: model `settings.CLAUDE_PLAN_MODEL` (default `claude-haiku-5-5`), `max_tokens=32000`, streamed (`client.messages.stream(...)` → `get_final_message()`), `output_config={"effort": settings.PLAN_LLM_EFFORT}`.
  - Never send `temperature`, `top_p`, `top_k`, a `thinking` budget or an assistant prefill: each returns a 400 on Haiku 5.5.
  - Text = join of the `text` blocks.
  - `stop_reason == "refusal"` or `"max_tokens"` → treat as an unparseable response (go to the retry tier, then rules).
- Pin `anthropic==1.17.0` in `backend/requirements.txt`. 2.x is a new major that our tooling hasn't been checked against; moving to it is a separate change.
- Claude prices (USD per 1M tokens): input 0.10, cached_input 0.01, output 0.50. Anthropic `output_tokens` already include thinking, so `thinking_tokens=0`. Anthropic `input_tokens` exclude cache reads and writes; our `Usage.input_tokens` includes them.
- Engine names: `claude` and `claude_retry`. They go into the `rag_attempts_total` labels, the `plan_engine` score and the span metadata.
- Keys:
  - The Claude branch needs `settings.ANTHROPIC_API_KEY` and ignores the per-user Gemini key. The Gemini `api_key` is still passed to KB retrieval; with no Gemini key, retrieval is skipped and the call still goes to Claude.
  - Keys live only in the environment or `backend/.env`. Never commit a key, and never print one in logs, ledgers or PR text.
- Paid runs (Gemini or Claude): get the user's go-ahead before each one. The Claude persona gate has a hard cap of $5, enforced by the script.
- New personas are invented (synthetic). They never copy a real athlete's data.

## Review Focus

1. **A refusal or a `max_tokens` stop** must fall to `claude_retry` and then to rules, never raise out of `generate_plan_workouts`. Task 2 tests both.
2. **A Gemini-only user under `PLAN_LLM_PROVIDER=claude`** (user key set, server Anthropic key missing): rules fallback with a log line, no crash. Task 2 tests this.
3. **A Langfuse version without a `claude-` label** (`claude-production` not created yet) must fall back to the in-code `PLAN_GENERATION_PROMPT`, not to the Gemini-labelled text. Task 3 tests this.
4. **Cost accounting on a cache-hit response:** `Usage.from_anthropic` must add cache reads and writes into `input_tokens`. Otherwise cost is under-counted. Task 1 tests this.
5. **Budget cap mid-persona:** the gate script must stop before the next block once cumulative cost reaches the cap, and still write what it has. Task 4 tests the cap function.

---

### Task 1: Settings, usage mapping, prices and the observability allowlist

**Files:**
- Modify: `backend/config.py` (settings plus a `DEFAULT_LLM_PRICES_USD_PER_M` row)
- Modify: `backend/services/observability.py` (`Usage.from_anthropic`, `METRIC_MODELS`, `_SCORE_SPECS["plan_engine"]`)
- Modify: `backend/services/observability_policy.py` (`_PROVIDERS`, `_SYSTEMS`, `_MODELS`, `_ENGINES`)
- Modify: `backend/requirements.txt` (`anthropic==1.17.0`)
- Test: `backend/tests/unit/test_observability_contract.py`, `backend/tests/unit/test_observability_policy.py`, `backend/tests/unit/test_observability_cost.py`

**Interfaces:**
- Produces:
  - `settings.PLAN_LLM_PROVIDER: str` (env, default `"gemini"`)
  - `settings.PLAN_LLM_EFFORT: str` (env, default `"medium"`)
  - `settings.ANTHROPIC_API_KEY: str` (env, default `""`)
  - `settings.CLAUDE_PLAN_MODEL: str` (env, default `"claude-haiku-5-5"`)
  - `observability.Usage.from_anthropic(usage) -> Usage`

- [ ] **Step 1: Write the failing tests**

```python
# test_observability_contract.py
def test_usage_from_anthropic_folds_cache_into_input():
    u = SimpleNamespace(input_tokens=100, output_tokens=40, cache_read_input_tokens=1000, cache_creation_input_tokens=50)
    assert obs.Usage.from_anthropic(u) == obs.Usage(input_tokens=1150, output_tokens=40, thinking_tokens=0, cached_tokens=1000)

def test_usage_from_anthropic_handles_missing_cache_fields():
    assert obs.Usage.from_anthropic(SimpleNamespace(input_tokens=7, output_tokens=3)) == obs.Usage(input_tokens=7, output_tokens=3)
    assert obs.Usage.from_anthropic(None) == obs.Usage()

# test_observability_cost.py
def test_haiku_is_priced():
    cost = obs.cost_usd("claude-haiku-5-5", obs.Usage(input_tokens=1_000_000, output_tokens=1_000_000))
    assert cost == pytest.approx(0.60)

# test_observability_policy.py: follow the file's existing sanitize-call style
# - metadata {"engine": "claude"}, {"engine": "claude_retry"}, {"model": "claude-haiku-5-5"} survive
# - attribute llm.provider="anthropic" and gen_ai.system="anthropic" survive
# - observability.score(..., name="plan_engine", value="claude_retry") is exported (see test_llm_judge.py:74 for the pattern)
```

- [ ] **Step 2: Run them and watch them fail**

Run: `cd backend && .venv/bin/pytest tests/unit/test_observability_contract.py tests/unit/test_observability_cost.py tests/unit/test_observability_policy.py -q`
Expected: FAIL (`from_anthropic` missing, Haiku unpriced, values dropped by the policy).

- [ ] **Step 3: Implement**

Make the additions listed under Files.
- `Usage.from_anthropic`: getattr with `or 0` for each field, the same way `from_genai` does it.
- Policy sets:
  - `_PROVIDERS` += `"anthropic"`
  - `_SYSTEMS` += `"anthropic"`
  - `_MODELS` += `"claude-haiku-5-5"`
  - `_ENGINES` += `"claude"`, `"claude_retry"`
- Score spec: `plan_engine` adds `"claude"` and `"claude_retry"`.
- Run `pip install anthropic==1.17.0` in `backend/.venv`.

- [ ] **Step 4: Run the tests and the whole observability suite**

Run: `cd backend && .venv/bin/pytest tests/unit -q -k observability`
Expected: PASS

- [ ] **Step 5: Commit** — `feat(llm): Anthropic usage, Haiku price and policy allowlist for plan generation`

---

### Task 2: Provider switch in plan generation

**Files:**
- Modify: `backend/services/plan_generator.py` (`_try_gemini` at about line 3286 and the loop at about line 3500)
- Modify: `backend/scripts/golden_eval.py` (`_scheduler_counters`, `_scheduler_engine_used`, `gate_failures`)
- Create: `backend/tests/unit/test_plan_llm_provider.py`

**Interfaces:**
- Consumes: Task 1's settings and `Usage.from_anthropic`.
- Produces:
  - Module-level `plan_generator._claude_text(message) -> str | None`: returns `None` when `stop_reason` is `"refusal"` or `"max_tokens"`, otherwise the joined `text` blocks.
  - Inside `generate_plan_workouts`: `_try_gemini(reduced)` keeps its name and its callers, and picks the engine from `settings.PLAN_LLM_PROVIDER`. Engine names: `gemini`/`gemini_retry` or `claude`/`claude_retry`.
  - `golden_eval` counts a `claude`/`claude_retry` "used" as a model-made plan.

- [ ] **Step 1: Write the failing tests** (`test_plan_llm_provider.py`)

Build the call the way `test_model_prompt_carries_the_ladder_block` in `tests/unit/test_ultra_plan_generation.py` does: same race_info, `weeks_per_block=4`, `PLAN_LINT_ENABLED=False`.
- Patch `anthropic.Anthropic` with a fake whose `messages.stream(**kw)` is a context manager returning an object with `get_final_message()`.
- Patch `google.genai.Client` so embeddings return one vector, and so any `generate_content` call raises.

```python
def test_claude_provider_uses_haiku_with_effort_and_no_sampling(...):
    # PLAN_LLM_PROVIDER=claude, PLAN_LLM_EFFORT=low, ANTHROPIC_API_KEY=x; fake returns one valid week-1 row JSON
    kw = fake.calls[0]
    assert kw["model"] == "claude-haiku-5-5" and kw["output_config"] == {"effort": "low"}
    assert not {"temperature", "top_p", "top_k", "thinking"} & set(kw)
    assert "MOUNTAIN-DAY ULTRA RULES" in kw["messages"][0]["content"]
    assert workouts and gemini_generate_not_called

def test_refusal_goes_to_claude_retry_then_rules(...):
    # fake answers stop_reason="refusal" twice -> two calls, second prompt starts with "RETRY:", result is rule-based
    assert len(fake.calls) == 2 and fake.calls[1]["messages"][0]["content"].startswith("RETRY:")

def test_max_tokens_stop_is_unparseable(...):
    assert plan_generator._claude_text(SimpleNamespace(stop_reason="max_tokens", content=[...])) is None

def test_claude_without_server_key_falls_to_rules(...):
    # ANTHROPIC_API_KEY="" with a Gemini api_key passed: no Anthropic client built, rule-based plan returned, no exception

def test_gemini_default_unchanged(...):
    # PLAN_LLM_PROVIDER unset: google.genai generate_content called once, anthropic never constructed
```

- [ ] **Step 2: Run them and watch them fail**

Run: `cd backend && .venv/bin/pytest tests/unit/test_plan_llm_provider.py -q`
Expected: FAIL (anthropic never called).

- [ ] **Step 3: Implement**

- Inside `_try_gemini`, compute `_claude = settings.PLAN_LLM_PROVIDER == "claude"`. Then:
  - `_engine = ("claude" if _claude else "gemini") + ("_retry" if reduced else "")`
  - The guard becomes `if not (_ai_prompt and (settings.ANTHROPIC_API_KEY if _claude else api_key)): return None`.
  - KB retrieval runs only when `api_key` is set.
- Replace the body of the `observability.generation(...)` block with a branch:
  - **Gemini:** today's code, unchanged.
  - **Claude:** `anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)`. Inside `asyncio.to_thread`, a nested function streams with the Global Constraints parameters and returns `get_final_message()`. `generation.set_usage(Usage.from_anthropic(msg.usage))`, `model=settings.CLAUDE_PLAN_MODEL`. Text comes from `_claude_text(msg)`; `None` → log `event="refusal"` or `"truncated"` and take the existing empty-result path (`return None`).
- Keep the log lines and metrics. Their `engine` field already comes from `_engine`.
- In the loop, `_engine_used` comes from the same rule.
- In `golden_eval`, add `claude_ok` and `claude_retry_ok` samples, and accept `claude`/`claude_retry` wherever `gemini`/`gemini_retry` is accepted (`claude_retry` is a warning, like `gemini_retry`).

- [ ] **Step 4: Run the new tests, the plan-generation suites and the golden_eval tests**

Run: `cd backend && .venv/bin/pytest tests/unit/test_plan_llm_provider.py tests/unit/test_plan_generation_observability.py tests/unit/test_ultra_plan_generation.py tests/unit/test_plan_generator_snapshot.py -q && .venv/bin/pytest tests/unit -q -k golden`
Expected: PASS (the snapshot test proves the Gemini branch moved without changing).

- [ ] **Step 5: Commit** — `feat(plan): PLAN_LLM_PROVIDER switch, Claude Haiku branch with refusal/truncation fallback`

---

### Task 3: Prompt label per provider

**Files:**
- Modify: `backend/services/observability.py` (`load_prompt`)
- Modify: `backend/services/plan_generator.py` (the `load_prompt("plan_generation", ...)` call at about line 3259)
- Test: `backend/tests/unit/test_observability_langfuse.py`

**Interfaces:**
- Produces: `observability.load_prompt(name, fallback, label: str | None = None) -> PromptTemplate`. `label=None` keeps `settings.COACH_CHAT_PROMPT_LABEL`.
- Plan generation passes `label=f"claude-{settings.COACH_CHAT_PROMPT_LABEL}"` when the provider is `claude`.

- [ ] **Step 1: Write the failing tests**

```python
def test_load_prompt_uses_explicit_label(monkeypatch):
    seen = {}
    monkeypatch.setattr(obs, "get_prompt_template", lambda name, label, fallback, cache_ttl_seconds: seen.setdefault("label", label) and obs.PromptTemplate(name, "local", fallback, "local_fallback"))
    obs.load_prompt("plan_generation", "x {{a}}", label="claude-staging")
    assert seen["label"] == "claude-staging"

def test_missing_claude_label_falls_back_to_in_code_prompt():
    # with Langfuse disabled (tests), load_prompt("plan_generation", PLAN_GENERATION_PROMPT, label="claude-production").template == PLAN_GENERATION_PROMPT
```

- [ ] **Step 2: Run them and watch them fail** — `pytest tests/unit/test_observability_langfuse.py -q`. Expected: FAIL (unexpected keyword `label`).
- [ ] **Step 3: Implement** — add the parameter; make the one call site in plan_generator pick the label by provider.
- [ ] **Step 4: Run** — `pytest tests/unit -q -k "observability or plan_llm"`. Expected: PASS.
- [ ] **Step 5: Commit** — `feat(llm): plan_generation prompt label follows the provider`

---

### Task 4: Persona pack: provider flags, cost cap, 5 new personas

**Files:**
- Modify: `backend/scripts/plan_live_personas.py`
- Modify: `backend/scripts/plan_quality_report.py` (print engine, cost and latency columns when present)
- Create: `backend/tests/unit/test_plan_live_personas.py`

**Interfaces:**
- Consumes: Task 2's engine names (counter labels `rag_attempts_total{service="plan_generator",engine=…,status="used"}`) and `llm_cost_usd_total{feature="plan_generation",model=…}`.
- Produces:
  - CLI flags `--provider gemini|claude` (sets `settings.PLAN_LLM_PROVIDER`), `--effort low|medium|high`, `--budget-usd 5.0`.
  - Each result JSON gains `"runs": {week: {"engine": str, "cost_usd": float, "seconds": float}}` and `"provider"`/`"effort"` keys.
  - `over_budget(spent: float, cap: float) -> bool` (true when `spent >= cap`).
  - `engine_for(before: dict, after: dict) -> str`: the engine whose "used" counter moved, else `"rules"`.
  - `install_replay` also patches `anthropic.Anthropic` with the same saved-row source, so `--replay` works under `--provider claude`.

- [ ] **Step 1: Write the failing tests** (`test_plan_live_personas.py`, import the script as `plan_quality_report.py` does)

```python
def test_over_budget():
    assert P.over_budget(5.0, 5.0) and not P.over_budget(4.99, 5.0)

def test_engine_for_picks_the_moved_counter():
    assert P.engine_for({"claude": 1, "claude_retry": 0}, {"claude": 1, "claude_retry": 1}) == "claude_retry"
    assert P.engine_for({"gemini": 2}, {"gemini": 2}) == "rules"

def test_new_personas_are_synthetic_and_well_formed():
    new = ["vn_masters_100k_gated_vi", "sub_elite_100mi_mountain", "low_base_50k_mountain_10wk",
           "short_8wk_100k_mountain", "vi_beginner_10k_road"]
    for n in new:
        p = P.PERSONAS[n]
        assert {"user", "plan", "weeks", "expect"} <= set(p)
        assert p["plan"]["course_distance_km"] > 0 and p["weeks"] >= 8

def test_ladder_personas_no_longer_expect_back_to_back():
    for n, p in P.PERSONAS.items():
        if p["plan"].get("mountain_days") and p["plan"]["course_distance_km"] >= 45:
            assert not p["expect"].get("b2b"), n
```

- [ ] **Step 2: Run them and watch them fail** — `pytest tests/unit/test_plan_live_personas.py -q`. Expected: FAIL.

- [ ] **Step 3: Implement**

- Add `threshold_source` to `USER_COLUMNS`.
- Add `expect=dict(ladder=True)` handling in `evaluate`: one row, "ultra ladder rules hold", ok when the lint issues carry no `ULTRA_LADDER`, `WEEKDAY_SHORT` or `QUALITY_COUNT` before the taper.
- Drop `b2b=True` from `ultra_100_miles` and `vn_hanoi_ham_lon_100k_vi`, and give them, `quang_aptrc80` and `vn_hcmc_chau_thoi_50k_vi` `ladder=True`. #171 removed back-to-back weekends on ladder plans.
- In `run_persona`, sample the counters around each `poll` for engine, cost and wall-clock seconds, and check `over_budget` before each block. Over the cap → write the partial result with `"stopped": "budget"` and stop the whole run.

New personas, all invented:

| Name | User | Plan | Weeks | Expect | Covers |
|---|---|---|---|---|---|
| `vn_masters_100k_gated_vi` | age 52, aet 132, ant 160, max 178, resting 58, `threshold_source="lab"`, z2 7:00–6:20 | 100 km / 5200 m, finish, 55 km/wk, 6 days Tue–Sun, long run Sat, `mountain_days=["Saturday"]`, `training_mountain="nui_dinh"`, flat home, `lang="vi"` | 20 | `ladder`, `mountain`, `min_mountain_long_run=180`, `vietnamese` | ADS gate: 1 Zone 3 session a week in the window, Vietnamese copy |
| `sub_elite_100mi_mountain` | aet 155, ant 168, max 188, resting 42, `threshold_source="lab"`, z2 5:10–4:40, threshold 3:50 | 165 km / 9500 m, time 26 h, cutoff 46 h, 130 km/wk, 6 days, long run Sat, `mountain_days=["Saturday"]`, `training_mountain="nui_dinh"` | 20 | `ladder`, `min_longest_session=420` | 8 h peak, 60–150 min weekdays, 2 quality sessions a week |
| `low_base_50k_mountain_10wk` | aet 145, ant 165, max 185, resting 60, z2 7:10–6:30 | 55 km / 2800 m, finish, cutoff 14 h, 25 km/wk, 5 days, long run Sun, `mountain_days=["Sunday"]`, `training_mountain="chau_thoi"` | 10 | `ladder`, `max_long_run_min=300` | step cap (+60 min) from a low base, short ladder |
| `short_8wk_100k_mountain` | aet 150, ant 168, max 186, resting 50, z2 6:00–5:25 | 100 km / 4500 m, finish, cutoff 28 h, 75 km/wk, 6 days, long run Sat, `mountain_days=["Saturday"]`, `training_mountain="ham_lon"` | 8 | `ladder` | compressed plan enters the ladder late |
| `vi_beginner_10k_road` | aet 138, ant 158, max 192, resting 66, z2 8:00–7:20 | 10 km / 50 m road, finish, 12 km/wk, 3 days Tue/Thu/Sun, long run Sun, `lang="vi"` | 8 | `no_intensity`, `zero_vert`, `vietnamese`, `max_long_run_min=75` | non-ultra control in Vietnamese; ultra rules must not leak |

- [ ] **Step 4: Run** — `pytest tests/unit/test_plan_live_personas.py -q && python scripts/plan_live_personas.py --list`. Expected: PASS; 15 names listed.
- [ ] **Step 5: Commit** — `feat(scripts): persona pack runs on either provider with a cost cap; 5 personas for the ultra rules`

---

### Task 5: Free evaluation (no model spend)

Operational. Write the results to `docs/superpowers/reports/2026-10-23-haiku-plan-generation.md`.

- [ ] **Step 1: Gemini baseline through today's post-processing.** Use a scratch DB and local Qdrant as in `plan_live_check.py`'s docstring (integration tests truncate tables: scratch DB only).
  Run: `python scripts/plan_live_personas.py --replay /tmp/personas --out /tmp/personas_gemini_replay`, then `python scripts/plan_quality_report.py /tmp/personas_gemini_replay`.
  Expected: the 10 old personas scored; the 5 new ones show `rules` (no saved rows).
- [ ] **Step 2: Haiku prompt check without the API.** Add `--dump-prompts DIR` to `plan_live_personas.py`. It installs a fake client that writes each prompt to `DIR/<persona>_w<N>.txt` and raises, so each week continues on rules. Dump week 1 for `quang_aptrc80`, `vn_masters_100k_gated_vi` and `vi_beginner_10k_road`. Give each file to an `Agent` with `model: "haiku"`, asking for the JSON array only. Save its rows as a replay dir and score them as in Step 1.
  Expected: valid JSON from all 3; record the rule breaks you see. This is not the gate.
- [ ] **Step 3: Prompt audit.** Run `/claude-api prompt-audit` on `PLAN_GENERATION_PROMPT`. Write the proposed Claude-variant text to `backend/prompts/plan_generation.claude.txt`, with the same `{{variables}}` (`load_prompt` rejects a template that drops one). It is pushed to Langfuse in Task 6 Step 1, never into the in-code constant.
- [ ] **Step 4: Commit** — `docs: free Haiku evaluation and Claude prompt draft`

---

### Task 6: Paid gate (ask first: each run needs the user's go-ahead)

- [ ] **Step 1: Langfuse.**
  - Create a `plan_generation` version from `backend/prompts/plan_generation.claude.txt` with label `claude-development`.
  - Add the model definition `claude-haiku-5-5` with Task 1's prices (`mcp__langfuse__createModel`).
- [ ] **Step 2: Gemini baseline for the 5 new personas** ( about 15 calls each, a few dollars).
  Run: `python scripts/plan_live_personas.py --provider gemini --only <names> --out /tmp/personas_gemini_new`
- [ ] **Step 3: Claude gate, $5 cap shared across efforts.**
  Run `--provider claude --effort low` on all 15 personas, then `medium`, then `high` only if budget remains:
  `ANTHROPIC_API_KEY=… python scripts/plan_live_personas.py --provider claude --effort low --budget-usd 5 --out /tmp/personas_claude_low`
  Expected per run: printed checks, plus `runs` engine, cost and seconds per week.
- [ ] **Step 4: Golden gate.**
  Run: `PLAN_LLM_PROVIDER=claude PLAN_LLM_EFFORT=<cheapest passing> COACH_CHAT_PROMPT_LABEL=development python scripts/golden_eval.py compare --service scheduler --push-langfuse --synthetic-only --fail-on-regression`
  Expected: no `rule-based-or-unknown` case.
- [ ] **Step 5: Report and review packs.**
  - Fill the report with a per-effort table: plan-quality score vs Gemini, hard-lint failures, `rules` share, `*_retry` share, p50/p95 seconds per block, cost per plan, plus a verdict (flip or not, at which effort).
  - Render a coach pack per persona: `python scripts/render_persona_pack.py <run>.json > docs/persona-packs/2026-10-haiku/<provider>-<effort>/<persona>.md`, for Gemini and the chosen effort, so Quang can compare the two side by side.
- [ ] **Step 6: Commit and open the PR.**
  - Put the llm-change-process checklist in the PR body.
  - The flip (`PLAN_LLM_PROVIDER=claude` in prod `.env`, plus `claude-production` and `claude-staging` labels on the promoted prompt) happens after merge, with the user's go-ahead. Rollback is setting the env value back to `gemini`.

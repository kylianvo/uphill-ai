---
name: llm-change-process
description: Use whenever a change touches an LLM prompt (coach chat, chat summary, plan generation, single workout, block narrative, gear finder, nutrition planner, goal judge), adds or changes a Gemini call, or adds a new LLM-powered service. Covers Langfuse prompt versioning, tracing/allowlist wiring, golden-set evals, and the staging → production promotion that every such change must go through.
---

# LLM change process (prompts and LLM services)

Every prompt change and every new LLM call ships through the same gates:
**trace it → version the prompt in Langfuse → eval it on the golden set → promote by label.**
A change is not done until the eval ran and its Langfuse run is linked in the PR.

## Ground rules (never break these)

- `services/observability.py` is the only module that imports `langfuse` / `opentelemetry`.
  Everything else goes through `observability.trace/span/generation/get_prompt_template`.
- Export is metadata-only (`LANGFUSE_EXPORT_CONTENT=false`). Prompts are fetched from Langfuse,
  but variables are compiled **locally** — athlete data never goes to the prompt API or into spans.
- `services/observability_policy.py` is a default-deny allowlist. A new span name, feature,
  metadata key, prompt name or tool name that isn't listed there is silently dropped at export.
  Add it there and add a test in `tests/unit/test_observability_policy.py`.
- Golden fixtures are invented, never copied from real athletes: `"synthetic": true` plus a
  `"provenance"` listed in `observability._SYNTHETIC_PROVENANCES`.
- The in-code prompt text is the fallback used when Langfuse is unreachable. It must stay a
  working prompt, and must be kept in sync once a Langfuse version is promoted.

## A. Changing an existing prompt

No code deploy needed when only the template text changes.

1. **Draft** a new version in Langfuse (Prompts → name). It gets only `latest`; no environment
   serves it yet. Keep every `{{variable}}` the code fills — a template that drops one is rejected
   by the code and it falls back to the local text.
2. **Staging:** move the `staging` label to the new version. Staging picks it up within
   `COACH_CHAT_PROMPT_CACHE_TTL_SECONDS` (300 s). Smoke-test on staging.
3. **Eval gate** (from `backend/`, with Langfuse keys + `LANGFUSE_ENVIRONMENT=development`):
   ```bash
   COACH_CHAT_PROMPT_LABEL=staging python scripts/golden_eval.py compare --service <svc> --push-langfuse --synthetic-only
   ```
   `<svc>` ∈ gear | nutrition | scheduler | chat | goal_judge. Add `--fail-on-regression` to get
   a non-zero exit, `--prompt-label <label>` / `--model <id>` to evaluate a candidate (the run
   name records the variant). Compare the new run with the previous one in Langfuse
   (Datasets → `uphill_<svc>_golden` → Runs). The gate (`golden_eval.gate_failures`) fails on:
   - chat: any critical safety violation, < 90% acceptable per language, mean `judge_safe` < 0.9
     (chat cases are also graded by the LLM judge: `judge_grounded/safe/actionable/language`)
   - scheduler / goal_judge: any case falling through to the rule-based tier (a
     `gemini_retry` is reported as a warning, not a failure)
   - gear/nutrition: any recommendation outside the catalog
   - goal_judge: goals not ordered a < b < c, or b outside the anchors' range
   No regression versus the last run. Read `tests/golden/report_<svc>.md` for the diffs.
   CI runs this automatically (`.github/workflows/llm-evals.yml`) on PRs touching LLM code,
   prompts' fallbacks, fixtures or KB seeds; `workflow_dispatch` accepts a `prompt_label` to
   evaluate a Langfuse-only prompt change before promoting it.
4. **Promote:** move the `production` label to the new version. Live within 300 s.
5. **Watch** the "Uphill AI – LLM Ops" dashboard (cost, p95 latency, errors per feature) and the
   "Uphill AI – Quality" dashboard (thumbs, proposal apply rate, live judge scores, quality by
   release), and filter traces by prompt version to compare old vs new.
6. **Rollback:** move `production` back to the previous version. No deploy.
7. **Sync the fallback:** open a small PR copying the promoted text into the in-code constant.

If the change also needs new variables or different parsing, it is a code change — do B's
steps 3–6 as well and ship the code before promoting the template.

## B. Adding a new LLM-powered service (or a new Gemini call)

1. **Trace:** wrap the request in `observability.trace("<trace_name>", feature=...)` and every
   model call in `observability.generation("generation", feature=..., model=settings.GEMINI_MODEL, prompt=<PromptTemplate>)`,
   and call `generation.set_usage(observability.Usage.from_genai(...))`.
2. **Allowlist:** add the trace name, feature and any metadata keys to `observability_policy.py`
   (plus a policy test).
3. **Prompt in Langfuse:** keep the template as a module constant with `{{variables}}`, fetch it
   with `observability.get_prompt_template(name, label=settings.COACH_CHAT_PROMPT_LABEL, fallback=CONSTANT)`,
   compile locally, and pass the `PromptTemplate` to `generation(prompt=...)` so traces carry the
   prompt version. Add the name to `_PROMPT_NAMES` in `observability_policy.py`.
   Create the prompt in Langfuse with the **same text as the constant** and labels `staging` +
   `production` **before** the production deploy — otherwise prod silently runs the fallback.
4. **Cost:** the model string must exist in `DEFAULT_LLM_PRICES_USD_PER_M` (`config.py`) and have
   a Langfuse model definition (Settings → Models) with matching prices.
5. **Golden set:** add `backend/tests/golden/<svc>/` with ≥ 12 synthetic fixtures covering normal,
   edge and Vietnamese cases; wire the service into `scripts/golden_eval.py` (`_run`, scoring in
   `compare`, `--service` choices) and add the provenance to `_SYNTHETIC_PROVENANCES`.
6. **Baselines:** `python scripts/golden_eval.py capture --service <svc>` and commit the
   `*.ref.json` files with the PR.
7. **Staging:** deploy, check the traces appear in Langfuse with the right trace name, cost and
   prompt version, then run the eval gate (A.3).
8. **Production:** deploy, confirm on the LLM Ops dashboard; add an alert if the feature is costly.

## C. Changing the LLM judge (`llm_judge` prompt or `services/llm_judge.py`)

The judge grades both live turns and experiments, so a bad judge corrupts every quality signal.
Run `python scripts/judge_calibration.py` (hand-labelled cases in
`tests/golden/judge_calibration/cases.json`); every criterion must stay at ≥ 85% agreement.
Traces reviewers mark `judge_wrong` in the triage queue are new calibration cases — add a
*synthetic* look-alike to `cases.json`.

## D. The feedback loop (weekly)

- Live signals on each coach turn's trace (`coach_chat.turn`, trace id stored on the message):
  `thumbs` (UI), `proposal_applied` (Apply/Discard), `judge_*` (in-process judge on
  `LLM_JUDGE_SAMPLE_RATE` of turns; only scores leave the server). Plans get `plan_engine`.
- `python scripts/triage_traces.py` queues low-scored traces into the `uphill-triage`
  annotation queue and prints the chat message id for each. Review, set `triage_verdict`, and for
  `needs_fixture` write a synthetic look-alike golden case — never copy the athlete's words.
- New score names must be added to `_SCORE_SPECS` in `observability.py` (and a Langfuse score
  config) or they are dropped.
- Deploys set `LANGFUSE_RELEASE=$(git rev-parse --short HEAD)` in the backend env so every trace
  carries its release and the Quality dashboard can compare releases.

## Before calling it done — checklist for the PR description

- [ ] Prompt name + version (or "fallback only") and which labels point where
- [ ] Langfuse eval run name(s) and the pass criteria result
- [ ] Policy allowlist updated + test (new names/keys only)
- [ ] Unit tests pass (`python -m pytest tests/unit -q`)
- [ ] Fallback constant matches the promoted Langfuse version
- [ ] No real athlete data in fixtures, prompts in Langfuse, or span metadata

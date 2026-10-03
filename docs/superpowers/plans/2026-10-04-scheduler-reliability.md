# Scheduler Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate consistent, feasible plans for urban Vietnamese recreational and sub-elite runners, with training load and progression grounded in verified Uphill Athlete principles.

**Architecture:** Preserve the existing scheduler and public workout fields. Add a small internal prescription helper, carry explicit progression/access context through existing generation paths, and validate resolved output before storage. Correct arithmetic deterministically; preserve coaching intent and use the existing bounded retry/fallback for invalid prescriptions.

**Tech Stack:** Python, FastAPI, pytest, existing Gemini/Langfuse integration, PostgreSQL, existing Next.js workout views for screenshot evidence.

**Spec:** `docs/superpowers/specs/2026-10-03-scheduler-reliability-design.md`.

**Status:** Proposed implementation plan for owner review. Writing this plan does not authorize code execution, paid experiments, prompt publication or staging deployment. Native execution is recommended because the tasks share prescription and context interfaces.

## Global Constraints

- Production remains on HOLD. Do not deploy production, move its prompt label, merge, or mark the PR ready.
- Do not change requirements, deploy scripts, environment files or dashboards.
- Integration tests may run only against the verified scratch database `uphill_ai_test`.
- All pushes use `--synthetic-only`; Langfuse remains metadata-only.
- Keep existing tier/volume bands and +20% latency gate.
- Keep public workout fields compatible; no schema migration in this release.
- Preserve historical references. Never overwrite a failed run to make the report appear green.
- Never add mileage to rest days or raise intensity just to satisfy a test.
- One logical commit per task, ending with `Co-Authored-By: Codex <noreply@openai.com>`.
- Scan the complete diff and external text against the existing private denylist without reproducing it in files.
- Source claims must distinguish verified book excerpts, author supplements, and app policy. Captions are approximate; do not invent book pages or numerical prescriptions.

## Review Focus

1. A complete calendar week with unlogged sessions must not become a partial week or confirmed inactivity (Task 2).
2. Flat weekday access with unknown stairs or unknown treadmill capability must not acquire equipment through inference (Tasks 3–5).
3. Mixed ME with running warm-up/cool-down must count each movement once; passive recovery must not inflate running load (Task 3).
4. A legacy workout or malformed candidate must not bypass validation or crash an otherwise readable historical plan (Tasks 3–5).
5. Interval recovery, planned down weeks and missing intermediate weeks must not produce misleading easy-share or progression scores (Task 5).

## Decisions to approve before execution

The following are proposed policy choices, not claims from the book:

- Report long-run **locomotion-time share** (running plus hiking, including moving warm-up/cool-down), excluding strength and passive rest; report distance share separately. Do not add a new hard percentage gate in this release. Preserve existing app limits until the owner approves a sourced replacement or explicitly accepts them as app policy.
- Unknown terrain/equipment permits a conservative accessible workout; it does not authorize stairs, weights or an incline machine. Day-specific availability in current notes can constrain selection, but uncertainty must remain explicit.
- Experiment budget: **one candidate plus at most one refinement**. Each candidate receives one complete paired suite and three repeats of each urban case plus the sequential blocker. Stop after a failed refinement; do not create a third version. Record actual API usage and cost. This is a new proposed budget, not reuse of the exhausted earlier experiment allowance.
- Separate approval checkpoints: source/policy register before affected coaching changes; offline result before staging. Production remains owner-controlled.

## File map

| File | Responsibility |
|---|---|
| `docs/research/2026-10-04-scheduler-rule-register.md` (new) | Rule, evidence, applicability, units, disposition and owner decisions |
| `backend/services/plan_generator.py` | Initial, next-block, single-workout, retry and fallback integration |
| `backend/services/workout_prescription.py` (new) | Internal segments, totals and EN/VI numerical instructions |
| `backend/services/plan_checks.py` | Context-aware checks; preserve existing legacy entry point |
| `backend/services/plan_rules.py` | Scoped, sourced rule corrections; explicit app-policy attribution |
| `backend/main.py` | `_generate_next_block_for_athlete` context, preserving access gate and readiness distinctions |
| `backend/kb_seed/scheduler.json` | Only reviewed corrections to conflicting affected chunks |
| `backend/scripts/golden_eval.py` | Fixed dates, sequential cases, versioned artifacts and per-case gates |
| `backend/tests/unit/test_scheduler_progression_context.py` (new) | Mocked next-block regression matrix, no database |
| `backend/tests/unit/test_workout_prescription.py` (new) | Pure accounting and rendering tests |
| `backend/tests/unit/test_plan_checks_context.py` (new) | Context-aware quality checks |
| Existing `test_plan_generator_helpers.py`, `test_plan_generator_snapshot.py`, `test_golden_eval.py` | Generation, compatibility, evaluation wiring |
| `backend/tests/golden/scheduler/fixture_sequence_*.json` (new) | Invented sequential scenarios |
| `docs/runbooks/2026-10-scheduler-reliability-release.md` (new) | Frozen gates, run identities, decisions, staged deployment log |
| `docs/superpowers/evidence/scheduler-reliability/` (new) | Synthetic results and EN/VI screenshots |

Read before execution: the spec; both October 3/4 research notes; `CLAUDE.md`; `.claude/skills/llm-change-process/SKILL.md`; `.claude/skills/ui-screenshot-evidence/SKILL.md`; existing fitness release runbook. Verify branch/worktree and preserve unrelated changes. Recheck function locations, not line numbers, against the execution commit.

### Task 1: Freeze the rule register and experiment contract

**Files:** Create the rule register and release runbook; inspect `plan_rules.py`, `plan_generator.py`, `athlete_tier.py`, and affected scheduler seed chunks.

**Interfaces:** Produces a reviewed register consumed by Tasks 3–7. Each row has `rule_id`, source URL/location, population/event, prerequisites, phase, units/denominator, code/seed location, disposition, and implementation decision.

- [ ] Record continuity, gradualness, modulation, individual recovery, AeT/AnT terminology, ME set order, strength prerequisites and treadmill stimulus distinctions from the research notes.
- [ ] Mark 30%/33% long-run and 50% weekend caps as existing app policy with unresolved source attribution. Record the proposed reporting units above; do not label them book prescriptions.
- [ ] Document exact planned corrections: remove the universal ban on straight sets; do not let short race runway imply strength readiness; do not treat hill power, sustained climbing and gym ME as interchangeable. Defer disputed intensity percentages until definitions and denominator are verified.
- [ ] Freeze candidate budget, acceptance matrix, code SHA, model, production prompt version, KB seed hash and retrieval source. Separate fixed date from live clock.
- [ ] Stop for owner adjudication of disputed coaching changes and approval of the proposed experiment budget. Arithmetic reproduction may continue independently; no disputed rule is silently adopted.
- [ ] Commit the register/runbook with message `docs: define scheduler coaching rules and release gates` plus the required trailer.

### Task 2: Reproduce and correct next-block context loss

**Files:** Modify `backend/main.py` at `_generate_next_block_for_athlete` and only the implicated generator context code; create `test_scheduler_progression_context.py`.

**Interfaces:** Keep `GenerateNextBlockRequest.override_gate` as access permission only. Existing `block_context: str | None` carries separately labeled calendar coverage, completed evidence, explicitly missed evidence, unknown logs and reported readiness. Do not introduce a persisted completion model.

- [ ] Add a mocked-data test matrix for completed, unknown, explicitly missed, reported fatigue/illness and overridden weeks. Exercise the real next-block core with DB helpers and background generation mocked; capture the exact generator arguments.
- [ ] Pin the key invariant with a local test helper returning captured context:

```python
@pytest.mark.parametrize("override", [False, True])
def test_override_does_not_invent_completed_training(override):
    context = capture_next_block_context(status="unknown", override=override)
    assert context["completed_minutes"] == 0
    assert context["unknown_sessions"] > 0
    assert context["calendar_days"] == 7
```

`capture_next_block_context` is a test-only adapter over the captured arguments, not a new production API. For the locked/no-override case, assert HTTP 403 instead of invoking generation; use an already-unlocked mixed-status block to exercise both override values above. Assert fatigue text survives an authorized override.

- [ ] Run `cd backend && pytest tests/unit/test_scheduler_progression_context.py -q`; confirm each real regression fails for its intended reason before changing implementation. Do not force a failure where current behavior is correct.
- [ ] Save synthetic prompt/raw/normalized diagnostics locally to distinguish context adaptation from arithmetic loss. Reproduce the historical 110.2 km result's scenario without requiring an LLM to reproduce the same random number.
- [ ] Correct only the demonstrated context error. Keep healthy full-week volume bands unchanged; no unconditional distance clamp. Add partial-calendar and missing-log tests separately.
- [ ] Rerun the matrix and existing `test_block_window_helpers.py`, `test_plan_generator_snapshot.py`. Record cause and before/after evidence in the runbook.
- [ ] Commit `fix: preserve training evidence in next-block context` plus trailer; if no context defect exists, commit regression tests/evidence without a speculative fix.

### Task 3: Define and test internal workout accounting

**Files:** Create `workout_prescription.py`, `test_workout_prescription.py`.

**Interfaces:** New pure functions:

```python
def resolve_prescription(segments: list[dict], *, lang: str) -> dict: ...
def render_prescription(resolved: dict, *, lang: str) -> str: ...
```

The resolver returns plain dictionaries; validation errors use `ValueError`.

Input segment keys: `kind` (`run`, `hike`, `strength`, `recovery`, `rest`), `duration_minutes`, `zone`, `setting` (`flat_outdoor`, `mountain`, `treadmill`, `indoor`, `unknown`), optional `pace_min_per_km`, `incline_pct`. Recovery locomotion must be explicit as run/hike; `recovery` means passive recovery. All numeric inputs must be finite and nonnegative; movement pace must be positive. Reject contradictory segment fields with `ValueError`. Return validated `segments`, `run_km`, `hike_km`, `aerobic_minutes`, `strength_minutes`, `passive_minutes`, `duration_minutes`, `estimated_indoor_ascent_m`, and `description`. No database calls or LLM calls.

- [ ] Write exact arithmetic tests first:

```python
def test_me_counts_moving_warmup_and_cooldown_once():
    segments = [
        {"kind": "run", "duration_minutes": 12, "zone": "Zone 1",
         "setting": "flat_outdoor", "pace_min_per_km": 6},
        {"kind": "strength", "duration_minutes": 24, "zone": None,
         "setting": "indoor"},
        {"kind": "run", "duration_minutes": 6, "zone": "Zone 1",
         "setting": "flat_outdoor", "pace_min_per_km": 6},
    ]
    result = resolve_prescription(segments, lang="en")
    assert result["run_km"] == 3
    assert result["strength_minutes"] == 24
    assert result["aerobic_minutes"] == 18
    assert result["duration_minutes"] == 42
```

- [ ] Add pure-strength zero-km, hiking separate from running, passive-rest exclusion, empty/rest, negative/NaN/infinite input and duplicate accounting tests. Specify total rounding only at output: distance 0.1 km, time 0.1 min, ascent 1 m. Test tolerance at those boundaries.
- [ ] Run `pytest tests/unit/test_workout_prescription.py -q` from `backend/`, confirm the failing assertions.
- [ ] Implement sums without parsing descriptions. Reuse verified existing pace/grade conventions; explicitly document whether treadmill distance is belt-path or horizontal distance before computing ascent. Test a known geometry case and mark indoor ascent estimated.
- [ ] Generate EN/VI numeric lines from resolved values, with exercise rationale separate. Test identical quantities and range endpoints in both languages. Read the Vietnamese-copy skill before writing VI output.
- [ ] Rerun the test file, then commit `feat: resolve mixed workout accounting from segments` plus trailer.

### Task 4: Integrate one prescription across generation paths

**Files:** Modify `plan_generator.py`, scoped `plan_rules.py` and scheduler seed entries; extend existing generator unit tests.

**Interfaces:** Consume Task 3 functions. Initial and next-block generation use `generate_plan_workouts`; single edits use `generate_single_workout`. All newly generated outputs derive public totals and numerical descriptions from the resolved prescription. Existing persisted legacy records remain readable without reconstruction.

- [ ] Mock LLM responses for mixed ME, treadmill, pure circuits and malformed segments. Assert raw contradictory numerical prose never becomes a second prescription; assert both EN and VI public fields match the resolver.
- [ ] Add path tests for normal generation, reduced retry, rule-based fallback and single-workout generation. Assert no more model attempts than the existing original-plus-one-retry budget. An invalid fallback must fail generation before persistence.
- [ ] Run targeted generator tests to expose the conflicts before implementing.
- [ ] Extend the local response contract with segments and nonnumerical coaching rationale; integrate Task 3 at the common normalization boundary and equivalent single-workout/fallback boundaries. Retain a clearly tested compatibility path for existing prompt versions; record unavailable segment precision rather than inventing it from prose.
- [ ] Apply only Task 1-approved rule/seed corrections. Never replace the whole KB. Keep candidate template and in-code fallback compatible; preserve every required template variable. Record any old-production incompatibility as a gate failure, not a silent switch of tested prompt.
- [ ] Run the generator/helper/snapshot and prescription tests. Commit `fix: unify generated workout totals and instructions` plus trailer.

### Task 5: Add contextual validation before storage

**Files:** Modify `plan_checks.py`, generator call sites and `main.py` context plumbing; create `test_plan_checks_context.py`.

**Interfaces:** Preserve `run_checks(workouts)` for legacy callers. Add `run_context_checks(workouts: list[dict], *, context: dict) -> dict[str, bool | None]`. Context has calendar coverage by week, phase, tier, explicit day access, and resolved prescriptions. `None` means unavailable/not applicable, never a pass. Checks report arithmetic, access, intensity-accounting and comparable-week progression independently. Long-run time/distance shares are diagnostics until policy approval.

- [ ] Add test cases asserting: partial first week skips only the full-week growth ratio; missing intermediate week is not adjacent progression; an unlogged full week is still calendar-complete; interval work/recovery is counted by segments; a down week does not create an automatic unrestricted rebound exemption.
- [ ] Add access cases for flat weekdays, treadmill Tuesday/Thursday only, weekend mountains, unknown stairs and unknown equipment. Structured fixture context may assert access; runtime notes may constrain it, but unsupported assumptions cannot grant access.
- [ ] Run `pytest tests/unit/test_plan_checks_context.py -q`, then implement the smallest context checks. Keep existing easy-share/growth constants labeled app policy and do not silently change thresholds.
- [ ] Wire structural/access failures into Task 4's bounded validation path before storage. Verify a violated fallback cannot be saved. Preserve independent reasons locally; export only approved metadata keys through observability.
- [ ] Add one test for legacy context absence: unavailable checks are omitted from pass-share denominator and explicitly reported as unavailable in evaluation.
- [ ] Rerun check/generator tests. Commit `feat: validate scheduler output with explicit week and access context` plus trailer.

### Task 6: Make the experiment reproducible

**Files:** Modify `golden_eval.py`, `test_golden_eval.py`; add sequential fixtures and versioned evidence.

**Interfaces:** Add CLI `--as-of YYYY-MM-DD`, `--fixture ID` (repeatable), and `--output-dir PATH`. Plumb `as_of` as an optional date through generation date calculations, defaulting to the live date for normal app calls. Do not patch the global clock. Sequential fixture field `sequence` contains ordered block requests and synthetic completion/readiness states; the runner invokes the same context construction verified in Task 2 with stubbed persistence.

- [ ] Add tests showing identical dates produce identical calendar windows; a Saturday-start fixture remains partial; an invalid fixture ID fails rather than silently running no cases; output directories cannot overwrite previous run artifacts.
- [ ] Add sequential cases for healthy completed, unknown with override, explicitly missed, fatigue/illness, recovery and taper. Preserve the healthy blocker's existing 115–150 km expectation. Define exact adaptation expectations in the approved register before running; recovery scenarios are not judged against healthy volume floors.
- [ ] Run `pytest tests/unit/test_golden_eval.py tests/unit/test_scheduler_progression_context.py -q`; implement date/filter/artifact support and sequential runner. Keep all 19 existing fixture IDs and references.
- [ ] Report each case's tier, full-week km, component minutes, long-run shares with units, access/structure results, unavailable checks, engine, prompt version, latency and failure reason. Version new metrics rather than presenting them as directly comparable historical scores.
- [ ] Run `cd backend && pytest tests/unit -q -m "not kafka"` until green. No integration run is necessary unless persistence behavior changed; then verify the scratch DB name before invoking any truncating test.
- [ ] Commit `test: add reproducible sequential scheduler evaluation` plus trailer.

### Task 7: Run the bounded candidate experiment and capture UI evidence

**Files:** Release runbook and evidence directory; local fallback template if candidate changes are necessary. Remote prompt changes only after approved budget.

**Interfaces:** Candidate label `scheduler-reliability-exp`; never move staging/production here. Record prompt version, content hash, code SHA, KB/retrieval snapshot and model for every run. New trace names or score keys require observability allowlist/spec tests; prefer existing fields.

- [ ] Verify production still references the expected version; if it has changed, report and refresh the baseline contract before paid runs. Create one reviewed candidate preserving template variables, labeled only with the experiment label (and service-managed latest).
- [ ] Run the paired complete suite on identical code/date/KB. These commands use options implemented in Task 6:

```bash
COACH_CHAT_PROMPT_LABEL=production python scripts/golden_eval.py compare --service scheduler --as-of 2026-10-05 --output-dir tests/golden/runs/reliability-production-1 --push-langfuse --synthetic-only --fail-on-regression
COACH_CHAT_PROMPT_LABEL=scheduler-reliability-exp python scripts/golden_eval.py compare --service scheduler --as-of 2026-10-05 --output-dir tests/golden/runs/reliability-candidate-1 --push-langfuse --synthetic-only --fail-on-regression
```

- [ ] Repeat each of the four Vietnam fixtures and the healthy sequential blocker three times per arm, using `--fixture` and unique output directories. Report all failures, even if later repeats pass. Do not selectively recapture failing references.
- [ ] Gate: unchanged healthy tier/volume bands; compare identical fixture sets and report both full-suite and repeated-subset paired mean latency; no rule-based fallback in golden results; retries reported; zero structural/access failures in new output; no regression in existing applicable checks; paired mean latency increase at most 20%. Preserve explicit missing-data counts. Report policy diagnostics separately from gates.
- [ ] If the candidate fails, explain the defect before the single permitted refinement. Re-run the full gate for the refinement. If it still fails, stop with HOLD and retain all evidence.
- [ ] Use the screenshot-evidence skill to run the local UI and capture EN/VI mixed ME and treadmill workout details using synthetic accounts. Verify displayed totals, instructions, ranges and locale. Remove temporary accounts/plans by their exact synthetic IDs.
- [ ] Record run names, results, costs, source-rule coverage and decision. Run privacy scan before publishing evidence. Commit `docs: record scheduler reliability experiment and UI evidence` plus trailer.
- [ ] **CHECKPOINT:** push, update the draft PR with completed tasks and run names; link evidence in an authorized PR comment. Stop and report offline gates, deviations and recommendation. Wait for explicit staging go-ahead.

### Task 8: Staging validation only after go-ahead

**Files:** Release runbook; follow existing staging deployment guide and fitness release runbook without changing deploy scripts.

- [ ] Record UTC timestamps, current staging code/prompt versions and rollback reference. Verify every target is `/opt/uphill-ai-backend-staging`, port 8001, with its isolated database/vector services.
- [ ] Perform checksum dry-run; inspect exclusions including `.env*`; stop staging; rsync; start; check health; perform the existing runbook's `alembic stamp head` only after confirming schema compatibility (this plan adds no migration). Log each result.
- [ ] Only after offline PASS and explicit staging authorization, move the staging label to the tested candidate. Confirm actual prompt version on smoke traces after cache refresh; never move production.
- [ ] Smoke initial and ordinary completed-week next-block generation separately from override generation. Include all four Vietnam profiles, unknown logs, missed sessions and reported fatigue; verify access, arithmetic and instructions.
- [ ] Capture EN/VI staged-result screenshots locally, remove exact synthetic accounts/plans and record cleanup. If any release gate fails, restore previous staging code/prompt and keep HOLD.
- [ ] Commit timestamped results, push, update the draft PR, and stop at **production HOLD** with owner handoff. No production action is included.

## Plan self-review

Coverage: source audit → Task 1; sequential volume diagnosis → Task 2; accounting and bilingual instructions → Tasks 3–4; context/partial weeks/access → Task 5; repeatable comparisons → Task 6; bounded prompt experiment/screenshots → Task 7; staged verification → Task 8. No public API redesign, automatic KB sweep, new dashboard, schema migration or production promotion is included.

Pending owner decisions are explicit checkpoints, not implementation placeholders. Exact physiological adaptations for disputed scenarios must be approved in the source register before those gates run. Ordinary arithmetic/context regressions can be reproduced without deciding a new coaching policy.

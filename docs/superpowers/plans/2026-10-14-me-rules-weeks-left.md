# Plan: ME scheduling rules keyed to weeks left, with ME history

## Context

Dylan (plan 105, 17 weeks) has had no ME session, and under the current prompt he will not get one:

- **Tier gate.** He is Novice, and ME is switched off below Recreational. That part is intended and not changed here.
- **Even at Recreational, nothing places ME.** The prompt keys ME timing to *total plan length*. A plan of 10 weeks or less gets the short-runway override. Longer plans get "ME block in early Base, 8–14 weeks", then Build = "After the ME block … ME is no longer the focus."
  - An 11–15-week plan can't fit a full ME block plus ~8 weeks of intervals, and nothing says what to cut.
  - An athlete who reaches Build with zero ME stays with zero.
  - A Novice → Recreational promotion mid-plan starts from zero ME, and the prompt never mentions it.
- **Gemini can't see ME history.** The next-block context sends volume and feedback, but never "ME sessions done so far".
- **No soft start.** Nothing tells the model to go easy on the first sessions. The rule-based fallback prescribes 6 sets from plan week 3 on, even for a runner's first ME session.

Intended outcome: the rule the user stated becomes explicit and is driven by data the prompt can see.

- **16+ weeks before the taper:** a full 8-week ME block, then 8 weeks of intervals.
- **Fewer weeks:** a short ME block now, at least 6–8 sessions, once or twice a week on top of easy volume. Then intervals in the weeks that remain, with ME stopping 10–14 days out.
- **Either way:** keep the 48-hour gap from the long run and hard sessions, and go easy on the first sessions.

## Approach

Everything below applies only when `tier_profile.allows_me_blocks` is true. Beginner and Novice prompts stay byte-identical, and `test_prompt_tier_isolation.py` guards that.

### 1. Pure helpers in `backend/services/plan_rules.py`

- `count_me_sessions(workouts, before_week) -> tuple[int, int]` returns (completed, scheduled) ME sessions before `before_week`.
  - A session counts as ME when `type == "Muscular Endurance"` or its title contains "Muscular Endurance".
  - Reuse the matching already used by the missed-ME check at `week_rebuild.py:402-410`, and move it here so both callers share it.
- `me_runway(block_start_week, race_week_num) -> int` returns the weeks left before the ME cutoff, which is race week − 2 (10–14 days out). `race_week_num = total_weeks - 1`, as computed at `plan_generator.py:1288`.
- `me_status_block(done, scheduled, weeks_left, tier_changed_from) -> str` builds a short prompt section:

  ```
  ME HISTORY: 0 ME sessions completed so far (0 scheduled) before week 11.
  Weeks left before the ME cutoff (10-14 days out): 4.
  [TIER CHANGE: athlete moved up from novice this block — ME starts from zero.]
  ```

### 2. Rewrite rule 4 (`me_periodization`, `plan_rules.py:157-165`)

Replace the "≤ 10 weeks total plan" override with branches on **weeks before the taper, read from ME HISTORY**. When there is no history (block 1), the plan's total length is used.

- **16 or more weeks before the taper:** a full ME block in early Base (8–14 weeks, up to 16, at least 8 sessions), then about 8 weeks of uphill and rolling intervals.
- **Fewer than 16:** a short ME block starting now, at least 6–8 sessions, once or twice a week on top of Zone 1–2 volume. Intervals fill the weeks that remain.
- **Catch-up:** if ME HISTORY shows fewer than 6 completed sessions and 3 or more weeks remain before the cutoff, schedule ME this block **even in Build**. That's 2 sessions a week when the remaining runway is short, 1 when load is high. The "ME is no longer the focus" line applies only once the block is done.
- Fewer than 3 weeks before the cutoff: don't start ME. Stopping it 10–14 days out still applies in every case.

Rule 12 (ME directives, `plan_rules.py:178-190`) gets one new bullet:
- **Soft start:** the first 2 ME sessions of a block, or the first ever, use reduced volume. That means about 4 sets of gym ME, or 20–30 minutes of weighted climbing at the low end of the 5–15% body-weight load, to limit DOMS. Then progress.

Keep the 48-hour buffer bullet as is.

### 3. Feed ME history into the prompt

- **`plan_generator.py`, `generate_plan_block`:** read `race_info["me_history"]` (dict: `done`, `scheduled`), compute `weeks_left` with `me_runway`, and work out the tier change from `race_info["previous_tier"]` against the resolved `athlete_tier`.
  - Append `me_status_block(...)` to `block_scope_instruction` (code-filled, so **no new Langfuse template variable**), and only when `allows_me_blocks`.
  - On block 1 with no history, emit only the weeks-left line.
- **`main.py` next-block path (around 2474–2700):** `all_workouts` is already loaded. Set `race_info["me_history"]` from `count_me_sessions(all_workouts, block_start_week)`. `previous_tier` is already passed (line 2696).
- **`services/week_rebuild.py` (around 600–620):** same as the next-block path, using its `all_workouts`. Replace the inline missed-ME matching (lines 402–410) with the shared helper.
- **Plan creation (`main.py` ~1279, ~2140):** nothing to pass. No history means block 1 behaviour.

### 4. Rule-based fallback (`plan_generator.py:2078-2132`)

- Base gym ME: compute sets from the ME sessions done (from `race_info["me_history"]`) plus the ME weeks already emitted in this run. Use 4 sets for the first 2 sessions and 6 after, instead of `week <= 2`.
- Build step-ups: start at the low end for the first 2 sessions. Begin at 400 steps and 10% body weight whatever the week, so a promoted or late-starting athlete doesn't open at full dose.
- Peak: unchanged (hill sprints, no ME).

### 5. Golden set (`scripts/golden_eval.py`, `tests/golden/scheduler/`)

- Let `_run_scheduler` read optional `block_number` from the fixture (default 1). `race_info` already passes `me_history` / `previous_tier` through.
- Add synthetic fixtures (`"synthetic": true`, `"provenance": "scheduler"`, invented values):
  - `fixture_rec_17wk_build_no_me.json`: Recreational, 17 weeks, block in week 11, `me_history {done: 0}`. **Expect at least 1 ME session** in the block.
  - `fixture_rec_13wk_short_runway.json`: Recreational, 13 weeks, block 1. Expect ME in week 1 or 2.
  - `fixture_promoted_novice_week5.json`: `previous_tier: novice`, resolves to Recreational, 20 weeks, block 5. Expect ME, soft-start dose.
  - `fixture_rec_late_no_me_cutoff.json`: 2 weeks before the cutoff, no ME. **Expect no ME.**
- Add an `expect.me_sessions_min` / `me_sessions_max` check in `compare` scoring next to the existing `week2_km` expectation. Capture `.ref.json` baselines.

## Files

- `backend/services/plan_rules.py`: helpers, rule 4 rewrite, rule 12 soft-start bullet
- `backend/services/plan_generator.py`: ME status injection, fallback dose ramp
- `backend/main.py`: pass `me_history` on next-block generation
- `backend/services/week_rebuild.py`: pass `me_history`, use the shared ME matcher
- `backend/scripts/golden_eval.py`, `backend/tests/golden/scheduler/fixture_*.json`
- Tests: `tests/unit/test_plan_rules_me.py` (new), `tests/integration/test_prompt_tier_isolation.py`, `tests/unit/test_plan_generator_helpers.py`

No DB schema change, and no Langfuse template change (`rules_block` and `block_scope_instruction` are already code-filled variables).

## Verification

1. **Unit tests:**
   - `count_me_sessions`: type and title matching, `before_week` boundary.
   - `me_runway`: 17-week plan at week 11 gives 4.
   - Rule 4 text for the ≥16, <16, catch-up and <3 branches.
   - Novice and Beginner prompts unchanged (tier isolation).
   - Fallback: first ME session gets 4 sets.

   Run `cd backend && pytest tests/unit tests/integration -q` and `ruff check`.
2. **Prompt snapshot:** render the prompt for the 17-week fixture at week 11 and confirm the ME HISTORY block and catch-up rule appear.
3. **Golden eval (llm-change-process A.3):** `python scripts/golden_eval.py compare --service scheduler --push-langfuse --synthetic-only --fail-on-regression`. No rule-based fall-through, new ME expectations pass, no regressions on existing fixtures. Link the Langfuse run in the PR along with the skill's checklist.
4. **Staging:** deploy, generate the next block for a synthetic Recreational account set up like Dylan's (17 weeks, no ME, week 11). Confirm ME sessions appear, 48 h clear of the long run, and that the first one is a reduced dose.
5. **Production:** deploy, then watch the `plan_checks` and `plan_engine` scores on the LLM Ops dashboard.

## Out of scope

- Dylan's own tier (Novice from a self-reported 6:10/km threshold pace) and the Threshold Pace field hint. The user declined these.
- Any change to tier thresholds.

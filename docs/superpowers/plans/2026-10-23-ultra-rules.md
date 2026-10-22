# Ultra Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ultra plans that have a mountain day follow Quang's long-run ladder, weekday minimums and quality count for each distance band (50 km / 100 km / 100 miles), and the lint, the rule-based fallback and the prompt all agree with them.

**Architecture:** One new pure module, `services/ultra_rules.py`, holds the bands, the ladder and the per-band numbers. `athlete_tier.for_race` and `session_cap_minutes` gain a `mountain_day` flag, so the session cap, weekday range and long-run share cap reach every existing caller (generator, lint, feasibility, fallback) through the profile they already use. The generator's post-processing sets the ladder long run and the week shape, so the Gemini path and the rule-based fallback both go through it. The lint learns the exemptions, plus a few new checks so the corrective retry can explain them.

**Tech Stack:** Python 3.12, FastAPI backend, pytest (unit tests only: no DB, no network).

**Spec:** `docs/superpowers/specs/2026-10-23-ultra-rules-design.md`

## Global Constraints

- **Band** from `course_distance_km`:
  - `"50k"` for 45 ≤ km < 90
  - `"100k"` for 90 ≤ km < 140
  - `"100mi"` for km ≥ 140
  - `None` below 45 km
- Ultra rules apply only when the band is set **and** `Venues.mountain_days` is non-empty. Every other plan keeps today's behaviour, except the all-plan rules listed below.
- **Advanced** means tier key `sub_elite` or `elite`. Every other tier is a finisher.
- **Ladder (minutes; recovery is the deload-week value):**
  - 50k: 180 ×4, filler 240, then 270 → 300 peak. Recovery 180.
  - 100k: 180, 180, 240, 240, filler 300, then 360 → 420 peak. Recovery 240.
  - 100mi finisher: same as 100k.
  - 100mi advanced: 100k ladder with 480 as the new peak (…360, 420, 480). Recovery 240.
- **Short plans** enter the ladder at the step that fits the weeks left (the ladder is read back from the peak). A week is never above the athlete's recent longest long run + 60 min.
- **Session cap:**
  - 50k: 300
  - 100k: 420
  - 100mi: 420 finisher, 480 advanced
- **Weekday easy runs:**
  - 50k: 45–90 min
  - 100k: 60–90 min
  - 100mi: 60–90 min, advanced up to 150
- **Other weekend day:** 45–90 min easy, shorter after a longer mountain day: long run ≤ 240 → 90, ≤ 300 → 60, longer → 45 (Zone 1).
- **Quality** (uphill/rolling intervals, Zone 3 only, never Zone 4; whole session ≤ 90 min):
  - only in the **quality window**: the 8 weeks up to and including `peak_week`, deload weeks excluded; none before it and none in the taper (hill sprints and strides stay everywhere and never count)
  - count: finishers 1, advanced 2; **gated** runners 1 whatever their level (gated = the generator's `hard_banned` is non-empty: measured gap > 10% or estimated thresholds)
  - work: finishers and gated 20–30 min, advanced 40–60 min
- **First 2 weeks:** at the athlete's current weekly volume (× `RECENT_LOAD_GROWTH`).
- **Long-run share cap** for ladder plans: 0.60. **Growth rule:** ladder steps are exempt from `LONG_RUN_JUMP`.
- **Back-to-back:** off for ladder plans, unchanged for every other plan.
- **ME (all plans):**
  - not counted in `week_minutes`
  - ≤ 10% of the week's run minutes
  - at most 1 a week; advanced up to 2 in Base and Build
  - none in a week with a long run ≥ 360 min (ladder plans)
- **All plans:** every session after the race, in race week, becomes Rest.
- **AeT gate for ladder plans:** the window's quality sessions are allowed even for gated runners (book: "within about eight weeks of your event you better start adding specific training in"). Outside the window, ladder plans have no Zone 3+ at all. No config switch.
- Prompt wording changes follow `.claude/skills/llm-change-process/SKILL.md`. The new text goes into the `goal_description` variable, not the Langfuse template, but the golden-set eval and checklist still apply.

## Review Focus

1. **A 98 km "100K" or a 44.9 km "45K".** Band edges are exact (`band_for(89.99) == "50k"`, `band_for(90) == "100k"`, `band_for(44.9) is None`). Task 1 tests these.
2. **An 8-week 100K plan.** It must enter the ladder late (no 7 h run after two 3 h weeks): each week ≤ the previous long run + 60. Task 1 (`long_run_target`) and Task 4 test this.
3. **A deload week that falls on a ladder step.** It runs the recovery value. The following week returns to the ladder and is not blocked by `LONG_RUN_JUMP` (240 → 300 after a 240 recovery). Task 3 tests this.
4. **A race on a Saturday.** The Sunday row becomes Rest, not a 30-minute recovery run. A race on Sunday leaves the week untouched. Task 5 tests this.
5. **A 100K plan with no `mountain_days`.** It gets none of this: 300 cap, tier share cap, and back-to-back still on. Task 2 and Task 4 test this.

---

### Task 1: `services/ultra_rules.py` — bands, ladder, numbers

**Files:**
- Create: `backend/services/ultra_rules.py`
- Test: `backend/tests/unit/test_ultra_rules.py`

**Interfaces:**
- Produces:
  - `Band = Literal["50k", "100k", "100mi"]`
  - `band_for(km: float | None) -> Band | None`
  - `applies(km: float | None, mountain_days: Sequence[str]) -> Band | None`: the band, only when `mountain_days` is non-empty
  - `is_advanced(tier_key: str) -> bool`
  - `session_cap(band: Band, advanced: bool) -> int`
  - `weekday_minutes(band: Band, advanced: bool) -> tuple[int, int]`
  - `quality_weeks(total_weeks: int) -> frozenset[int]`: weeks `peak_week - 7` … `peak_week`, minus deload weeks
  - `quality_per_week(advanced: bool, gated: bool) -> int`
  - `quality_work_minutes(advanced: bool, gated: bool) -> tuple[int, int]`: (20, 30) or (40, 60)
  - `other_day_minutes(long_run_min: float) -> int`: 90 / 60 / 45
  - `peak_week(total_weeks: int) -> int`: `total_weeks - 3 - taper_shift(total_weeks)`, the same "last build" as `goal_demands.long_run_ask`
  - `is_deload(week: int, total_weeks: int) -> bool`: the same rule as `PlanGenerator.is_deload_week`, kept here to avoid an import cycle
  - `ladder(band: Band, advanced: bool, total_weeks: int) -> dict[int, int]`: minutes for each week from 1 to `peak_week`, with the recovery value on deload weeks
  - `long_run_target(band, advanced, week, total_weeks, recent_longest: float | None) -> int | None`: `None` after the peak week. Otherwise `min(ladder[week], recent_longest + STEP_CAP_MIN)` when `recent_longest` is set.
  - Constants: `LONG_SHARE_CAP = 0.60`, `STEP_CAP_MIN = 60`, `QUALITY_MAX_MIN = 90`, `ME_FREE_LONG_RUN_MIN = 360`, `ME_MAX_SHARE = 0.10`

- [ ] **Step 1: Write the failing tests**

```python
from services import ultra_rules as u
from services.plan_generator import PlanGenerator

def test_band_edges():
    assert u.band_for(44.9) is None
    assert u.band_for(45) == "50k" and u.band_for(89.99) == "50k"
    assert u.band_for(90) == "100k" and u.band_for(98) == "100k" and u.band_for(139.9) == "100k"
    assert u.band_for(140) == "100mi" and u.band_for(None) is None

def test_applies_needs_a_mountain_day():
    assert u.applies(100, ()) is None
    assert u.applies(100, ("Saturday",)) == "100k"

def test_100k_ladder_20_weeks():
    lad = u.ladder("100k", False, 20)  # peak_week = 20 - 3 - 1 = 16; deloads 4, 8, 12
    assert [lad[w] for w in (1, 2, 3, 5)] == [180, 180, 240, 240]
    assert lad[4] == lad[8] == lad[12] == 240
    assert lad[15] == 360 and lad[16] == 420
    assert set(lad) == set(range(1, 17))

def test_100mi_advanced_peaks_at_8h_and_50k_at_5h():
    assert u.ladder("100mi", True, 20)[16] == 480
    assert u.ladder("100mi", False, 20)[16] == 420
    lad = u.ladder("50k", False, 16)  # peak 12
    assert lad[12] == 300 and lad[11] == 270 and lad[1] == 180 and lad[4] == 180

def test_short_plan_enters_late_and_never_jumps_more_than_an_hour():
    lad = u.ladder("100k", False, 8)  # peak_week 5
    assert lad[5] == 420 and lad[1] >= 180
    assert u.long_run_target("100k", False, 5, 8, recent_longest=240) == 300

def test_deload_matches_plan_generator():
    for total in range(6, 30):
        for w in range(1, total + 1):
            assert u.is_deload(w, total) == PlanGenerator.is_deload_week(w, total)

def test_numbers():
    assert u.session_cap("50k", True) == 300 and u.session_cap("100k", False) == 420
    assert u.session_cap("100mi", False) == 420 and u.session_cap("100mi", True) == 480
    assert u.weekday_minutes("50k", False) == (45, 90)
    assert u.weekday_minutes("100k", True) == (60, 90)
    assert u.weekday_minutes("100mi", True) == (60, 150)
    assert u.quality_per_week(False, False) == 1 and u.quality_per_week(True, False) == 2
    assert u.quality_per_week(True, True) == 1
    assert u.quality_work_minutes(True, False) == (40, 60) and u.quality_work_minutes(True, True) == (20, 30)
    assert [u.other_day_minutes(m) for m in (180, 240, 300, 360, 420)] == [90, 90, 60, 45, 45]

def test_quality_window_is_8_weeks_to_peak_without_deloads():
    assert u.quality_weeks(20) == frozenset({9, 10, 11, 13, 14, 15, 16})  # peak 16, deload 12
    assert u.quality_weeks(8) == frozenset({1, 2, 3, 5})  # short plan: the whole build, deload 4
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run `cd backend && pytest tests/unit/test_ultra_rules.py -v`. Expected: ImportError.
- [ ] **Step 3: Implement the module.** Build the non-deload sequence for `n` = the number of non-deload weeks up to `peak_week`:
  - Long enough: `start + [filler] * (n - len(start) - len(end)) + end`.
  - Shorter: keep the tail of `start + end` (`seq[-n:]`).
  - Then walk weeks 1..`peak_week`, giving deload weeks the recovery value and the other weeks the next step of the sequence.
- [ ] **Step 4: Run the tests and confirm they pass.** Same command. Expected: all pass.
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): ultra_rules — bands and Quang's long-run ladder"`

---

### Task 2: Caps reach the profile — `for_race` / `session_cap_minutes` take `mountain_day`

**Files:**
- Modify: `backend/services/athlete_tier.py:355-371` (`for_race`, `session_cap_minutes`)
- Modify callers so they pass `mountain_day=bool(venues.mountain_days)`:
  - `backend/services/plan_generator.py:1109, 1381, 1774, 3512, 3733`
  - `backend/services/plan_lint.py:391, 474`, reading the new `Prefs.mountain_day`
  - `backend/services/goal_feasibility.py:40, 63`
  - `backend/scripts/plan_live_personas.py:305`
- Modify: `backend/services/plan_lint.py` `Prefs`: add `mountain_day: bool = False`, set at `plan_generator.py:1116` from `venues.mountain_days`
- Test: `backend/tests/unit/test_athlete_tier.py`

**Interfaces:**
- Consumes: `ultra_rules.applies`, `is_advanced`, `session_cap`, `weekday_minutes`, `LONG_SHARE_CAP`
- Produces:
  - `for_race(profile, race_km, mountain_day: bool = False) -> TierProfile`: for a band, `weekday_minutes = ultra_rules.weekday_minutes(...)` and `long_run_share_cap = max(cap, 0.60)`. The sub-elite 100-mile branch still runs first.
  - `session_cap_minutes(profile, race_km, mountain_day: bool = False) -> int`: `ultra_rules.session_cap(...)` for a band. The existing branches apply otherwise.
  - `plan_lint.Prefs.mountain_day: bool`

- [ ] **Step 1: Write the failing tests** in `test_athlete_tier.py`:

```python
def test_mountain_ultra_caps():
    rec = TIER_PROFILES["recreational"]
    p = for_race(rec, 104, mountain_day=True)
    assert p.weekday_minutes == (60, 90) and p.long_run_share_cap == 0.60
    assert session_cap_minutes(rec, 104, mountain_day=True) == 420
    assert session_cap_minutes(TIER_PROFILES["elite"], 170, mountain_day=True) == 480

def test_no_mountain_day_keeps_book_caps():
    rec = TIER_PROFILES["recreational"]
    assert for_race(rec, 104) == rec
    assert session_cap_minutes(rec, 104) == 300
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run `pytest tests/unit/test_athlete_tier.py -k mountain -v`. Expected: TypeError (unexpected keyword).
- [ ] **Step 3: Implement both functions and update every caller listed above.** In `plan_generator.py`, `venues` already exists at 1315 and 1112. In `plan_lint.py`, the call at 391 passes `prefs.mountain_day if prefs else False`.
- [ ] **Step 4: Run the tests.** Run `pytest tests/unit -q -x -k "tier or lint or feasib or plan_generator"`. Expected: all pass, with no change for plans that have no mountain day.
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): mountain-day ultra caps flow through for_race and session_cap_minutes"`

---

### Task 3: Lint — ME, ladder exemptions, weekday minimum, quality, ME load

**Files:**
- Modify: `backend/services/plan_lint.py`
- Test: `backend/tests/unit/test_plan_lint.py`

**Interfaces:**
- Consumes:
  - `Prefs.mountain_day`, `Prefs.total_weeks`, `Prefs.demands.distance_km`
  - `ultra_rules.applies`, `ladder`, `weekday_minutes`, `quality_weeks`, `quality_per_week`, `is_advanced`, `ME_MAX_SHARE`
  - new `Prefs.quality_gated: bool = False`, set at `plan_generator.py:1116` from `bool(hard_banned)`
- Produces:
  - `week_minutes(ws)` now leaves out ME rows (C8). Callers in the generator keep the same signature.
  - `_ultra(prefs, profile) -> tuple[Band, bool] | None`: the band and whether the athlete is advanced, or `None` when ultra rules don't apply.
  - New issue codes:
    - `WEEKDAY_SHORT`: a non-down week, ultra only. An Easy/Aerobic Capacity row that isn't on the long-run day is under the band minimum. The message names the row and the minimum.
    - `ULTRA_LADDER`: a non-down build week, ultra only. The longest Long Run is below 90% of `ladder[week]`. The message says "make the Long Run about N min".
    - `QUALITY_COUNT`: ultra only. In a `quality_weeks` week, the number of `is_hard` rows (titles containing "sprint" or "stride" excluded) is ≠ `quality_per_week(advanced, prefs.quality_gated)`. Outside the window, any such row is flagged. Zone 4/5 rows are always flagged for ultras.
    - `ME_LOAD` (all plans): more ME rows than allowed (1; advanced 2 in Base/Build), or ME minutes > 10% of `week_minutes`.
  - `LONG_RUN_JUMP` is skipped when ultra applies and `longest_now <= ladder[week]`.
  - `B2B_MISSING` and the back-to-back window are skipped when ultra applies (C7).

- [ ] **Step 1: Write the failing tests.** Reuse the file's `s()` / `filler()` helpers. Define `ULTRA_PREFS = Prefs(long_run_day="Saturday", mountain_day=True, total_weeks=20, demands=D100)`, reusing the file's existing `D100 = goal_demands.compute(104.2, 5533, 14.67, 29)`:

```python
def test_me_not_counted_in_week_minutes():
    assert week_minutes([s(1, "Tuesday", "Easy", 60), s(1, "Thursday", "Muscular Endurance", 45)]) == 60

def test_ladder_step_is_not_a_long_run_jump():
    # 180 -> 240 is +33% (over MAX_LONG_RUN_GROWTH 25%, step 60 > 20), and ladder("100k", False, 20)[3] == 240
    wk = filler(2, 300) + [s(2, "Saturday", "Long Run", 180)]
    wk += [s(3, "Tuesday", "Easy", 60), s(3, "Saturday", "Long Run", 240)]
    assert "LONG_RUN_JUMP" not in codes(lint_week(wk, 3, REC, ULTRA_PREFS))

def test_same_jump_without_mountain_day_is_flagged():
    wk = filler(2, 300) + [s(2, "Saturday", "Long Run", 180)]
    wk += [s(3, "Tuesday", "Easy", 60), s(3, "Saturday", "Long Run", 240)]
    assert "LONG_RUN_JUMP" in codes(lint_week(wk, 3, REC, replace(ULTRA_PREFS, mountain_day=False)))

def test_weekday_short_and_ladder_short():
    wk = [s(9, "Tuesday", "Easy", 45, phase="Build"), s(9, "Saturday", "Long Run", 200, phase="Build")]
    got = codes(lint_week(wk, 9, REC, ULTRA_PREFS))
    assert "WEEKDAY_SHORT" in got and "ULTRA_LADDER" in got

def test_no_b2b_missing_for_ladder_plans():
    # week 16 of 20 is total - 4 - taper_shift: today's B2B_MISSING ask week
    wk = [s(16, "Tuesday", "Easy", 60, phase="Peak"), s(16, "Saturday", "Long Run", 420, phase="Peak")]
    assert "B2B_MISSING" not in codes(lint_week(wk, 16, REC, ULTRA_PREFS))

def test_me_load_all_plans():
    wk = [s(3, "Monday", "Muscular Endurance", 40), s(3, "Thursday", "Muscular Endurance", 40),
          s(3, "Saturday", "Long Run", 120)]
    assert "ME_LOAD" in codes(lint_week(wk, 3, REC, Prefs()))
```

- [ ] **Step 2: Run the tests and confirm they fail.** Run `pytest tests/unit/test_plan_lint.py -v`. Expected: the new tests fail.
- [ ] **Step 3: Implement the checks.** Add each new code to the retry text map if `plan_lint_retry` keys messages by code (check `tests/unit/test_plan_lint_retry.py`). Add `WEEKDAY_SHORT`, `ULTRA_LADDER` and `QUALITY_COUNT` to `scripts/plan_reliability.py` `DEMAND_CODES`.
- [ ] **Step 4: Run the tests.** Run `pytest tests/unit -q -k "lint or readiness or reliability"`. Expected: pass. Existing fixtures whose totals included ME may need their expected minutes updated. Update the numbers and leave the assertions as they are.
- [ ] **Step 5: Commit.** `git commit -m "feat(lint): ultra ladder exemptions, weekday minimum, quality count; ME off the volume"`

---

### Task 4: Generator post-processing — ladder long run and week shape

**Files:**
- Modify: `backend/services/plan_generator.py`:
  - `_progress_long_runs` (1764)
  - `_cap_start_load` (1550)
  - the post-process call order (2523-2533)
  - new closure `_ultra_week_shape`
- Test: `backend/tests/unit/test_ultra_plan_generation.py`. It runs the rule-based path the way `scripts/plan_reliability.py` does: no Gemini, `settings.PLAN_DEMANDS_ENABLED` patched on.

**Interfaces:**
- Consumes: Task 1 functions, Task 2 profile, `plan_lint.week_minutes` (ME-free)
- Produces, in `generate_plan` scope:
  - `ultra = ultra_rules.applies(course_distance_km, venues.mountain_days)`
  - `advanced = ultra_rules.is_advanced(tier_profile.key)`
  - `_progress_long_runs`: when `ultra` is set, for each week ≤ `peak_week` (deload weeks included), the Long Run becomes `long_run_target(ultra, advanced, week, total_weeks, recent_longest)`, raised or lowered with `_resize`. `recent_longest` is the max Long Run of the two prior weeks (prior blocks included). The `long_run_ask` / share-limit path and the back-to-back block are skipped. Taper handling is unchanged.
  - `_ultra_week_shape(wos)`, called right after `_progress_long_runs` and only when `ultra` is set:
    - Easy/Aerobic Capacity rows on non-long-run days are clamped into `weekday_minutes(ultra, advanced)` with `_resize`.
    - The other weekend day (Saturday/Sunday, whichever isn't the long-run day), when it's a run, becomes an easy run of `other_day_minutes(long run minutes)`; Zone 1 when that is 45.
    - In weeks where the Long Run is ≥ `ME_FREE_LONG_RUN_MIN`, ME rows become easy runs (`_to_easy`).
    - Quality rows are capped at `QUALITY_MAX_MIN` (90). In `_cap_hard_dose`, a Zone 3 row of an ultra plan in a quality week may run to 90 min instead of 75. (Which rows stay hard is Task 6.)
  - `_cap_start_load(wos, weeks: tuple[int, ...] = (1,), floor: int = 30)`: the existing call is unchanged. When `ultra` is set, a second call runs after `_ultra_week_shape` with `weeks=(1, 2)` and `floor=weekday_minutes(ultra, advanced)[0]`. The long run is never cut (it already isn't).

- [ ] **Step 1: Write the failing tests.** They cover the 100K race from `plan_reliability.RACES`, `mountain_days=["Saturday"]`, long-run day Saturday and 6 days a week:

```python
def test_100k_mountain_plan_follows_ladder(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    longs = {w["week_number"]: w["duration_minutes"] for w in wos if w["type"] == "Long Run"}
    assert longs[1] == 180 and longs[4] == 240 and longs[16] == 420
    assert max(longs.values()) <= 420
    weekday = [w for w in wos if w["type"] == "Easy" and w["day_of_week"] not in ("Saturday", "Sunday")
               and w["phase"] in ("Base", "Build", "Peak")]
    assert all(60 <= w["duration_minutes"] <= 90 for w in weekday)
    assert not any(plan_lint.is_b2b_week([w for w in wos if w["week_number"] == n]) for n in longs)

def test_short_plan_never_jumps_more_than_an_hour(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=8, mountain_days=["Saturday"], tier="recreational")
    longs = [w["duration_minutes"] for w in sorted(wos, key=lambda w: w["week_number"]) if w["type"] == "Long Run"]
    assert all(b - a <= 60 for a, b in zip(longs, longs[1:]))

def test_no_mountain_day_unchanged(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=[], tier="recreational")
    assert max(w["duration_minutes"] for w in wos if w["type"] == "Long Run") <= 300

def test_no_me_in_6h_weeks(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="recreational")
    big = {w["week_number"] for w in wos if w["type"] == "Long Run" and w["duration_minutes"] >= 360}
    assert not [w for w in wos if w["week_number"] in big and w["type"] == "Muscular Endurance"]
```

  Write `rule_based_plan` as a fixture in the test file. It builds `race_info` the way `plan_reliability.py` does, with `mountain_days` added, calls the generator with no API key, and returns the workouts.
- [ ] **Step 2: Run the tests and confirm they fail.** Run `pytest tests/unit/test_ultra_plan_generation.py -v`. Expected: the ladder assertions fail.
- [ ] **Step 3: Implement the changes listed above.**
- [ ] **Step 4: Run the checks.** Run `pytest tests/unit -q`, then `python scripts/plan_reliability.py`. Expected:
  - all unit tests pass
  - the scorecard has no new failures for the existing (no mountain-day) rows
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): ladder long run and ultra week shape in post-processing"`

---

### Task 5: Rest after the race (all plans)

**Files:**
- Modify: `backend/services/plan_generator.py`: add a new closure `_rest_after_race(wos)` and call it at the end of `post_process_workouts`, just before it returns.
- Test: `backend/tests/unit/test_ultra_plan_generation.py`

**Interfaces:**
- Produces: `_rest_after_race(wos)`. In each week that holds a `type == "Race"` row, every row on a later weekday is passed to `_make_rest`.

- [ ] **Step 1: Write the failing tests:** a Saturday race → the Sunday row is `Rest` with 0 minutes; a Sunday race → no row changes.
- [ ] **Step 2: Run the tests and confirm they fail.** Run `pytest tests/unit/test_ultra_plan_generation.py -k race -v`.
- [ ] **Step 3: Implement `_rest_after_race`.**
- [ ] **Step 4: Run the tests and confirm they pass.** Same command, then `pytest tests/unit -q`.
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): the day after the race is rest"`

---

### Task 6: Quality window and the AeT gate for ladder plans (C6)

**Files:**
- Modify: `backend/services/plan_generator.py`: `_gate_hard` (1527) gets an ultra branch; `ultra`, `advanced` and `aet_gated = bool(hard_banned)` must be computed before 1299, so move the `venues` line (1315) up if needed.
- Test: `backend/tests/unit/test_ultra_plan_generation.py`

**Interfaces:**
- Consumes: `ultra_rules.quality_weeks`, `quality_per_week`, `quality_work_minutes`; the `rule_based_plan` fixture from Task 4, extended with optional `aet_hr`, `ant_hr`, `threshold_source` keyword arguments passed into the user profile (`threshold_source="lab"` must be in `MEASURED_THRESHOLD_SOURCES`; check and use a listed value).
- Produces: when `ultra` is set, `_gate_hard` ignores `hard_banned` and applies one rule to every non-Race row with `is_hard` true (hill sprints / strides by `HILL_SPRINT_TITLE_KEYWORDS` untouched):
  - Zone 4/5 rows → `_to_easy`.
  - Week not in `quality_weeks(total_weeks)` → `_to_easy`.
  - Week in the window → keep the first `quality_per_week(advanced, aet_gated)` Zone 3 rows by day; the rest → `_to_easy`.

- [ ] **Step 1: Write the failing tests**

```python
def test_ultra_quality_only_in_the_window(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="sub_elite")
    window = ultra_rules.quality_weeks(20)
    hard = [w for w in wos if plan_lint.is_hard(w) and w["type"] != "Race"
            and not any(k in w["title"].lower() for k in ("sprint", "stride"))]
    assert all(w["week_number"] in window for w in hard)
    assert all(w["target_zone"] == "Zone 3" for w in hard)
    per_week = Counter(w["week_number"] for w in hard)
    assert max(per_week.values()) <= 2

def test_gated_runner_gets_one_zone3_in_the_window(rule_based_plan):
    wos = rule_based_plan(km=104.2, weeks=20, mountain_days=["Saturday"], tier="sub_elite",
                          aet_hr=140, ant_hr=170, threshold_source="lab")  # 18% gap: ADS
    hard = [w for w in wos if plan_lint.is_hard(w) and w["type"] != "Race"
            and not any(k in w["title"].lower() for k in ("sprint", "stride"))]
    assert hard and max(Counter(w["week_number"] for w in hard).values()) == 1
```

  If the rule-based template has no Zone 3 session in some window week, the generator does not invent one; the lint's `QUALITY_COUNT` (Task 3) asks the model for it on the Gemini path. The tests therefore check the upper bounds and that gated runners keep at least one.
- [ ] **Step 2: Run the tests and confirm they fail.** Run `pytest tests/unit/test_ultra_plan_generation.py -k "window or gated" -v`.
- [ ] **Step 3: Implement the ultra branch of `_gate_hard`.**
- [ ] **Step 4: Run the tests.** Run `pytest tests/unit -q`. Expected: pass.
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): ultra quality sessions only in the final 8 weeks, gated runners get one"`

---

### Task 7: Prompt block for the model

**Files:**
- Modify: `backend/services/ultra_rules.py`. Add `prompt_block(band: Band, advanced: bool, weeks: dict[int, int], total_weeks: int, aet_gated: bool, lang: str) -> str`.
- Modify: `backend/services/plan_generator.py:2797`. Next to `goal_demands.prompt_block`, append `ultra_rules.prompt_block(ultra, advanced, {w: target for the block's weeks}, total_weeks, aet_gated=aet_gated, lang=lang)` when `ultra` is set.
- Test: `backend/tests/unit/test_ultra_rules.py`

**Interfaces:**
- Produces: a rule block that handles `lang` the same way `goal_demands.prompt_block` does. It says:
  - this week's Long Run minutes for each week of the block, on the mountain day
  - the other weekend day's minutes for each week (`other_day_minutes`)
  - the weekday easy range
  - for each block week in `quality_weeks`: the count and work minutes, as "uphill or rolling intervals in Zone 3 (8–12% treadmill, stairs or an overpass where there are no hills), breathing-limited, never ME, no Zone 4, whole session ≤ 90 min"; for block weeks outside the window: "no Zone 3+; hill sprints, strides and ME only"
  - extra volume goes on weekdays
  - no back-to-back weekend
  - this ladder overrides the long-run share and growth rules

- [ ] **Step 1: Write the failing tests:**
  - `"420" in prompt_block("100k", False, {16: 420}, 20, False, "en")`
  - week 16 block, `aet_gated=True`: the text holds "1" session and "20-30" min, and not "Zone 4" as an instruction to do Zone 4
  - week 5 block (outside the window): "no Zone 3" in the lowered text
  - `"back-to-back" in ...lower()`
- [ ] **Step 2: Run the tests and confirm they fail.**
- [ ] **Step 3: Implement `prompt_block` and wire it into `plan_generator.py`.**
- [ ] **Step 4: Run the tests.** Run `pytest tests/unit -q`. Expected: pass. If `test_plan_generator_snapshot.py` snapshots change for mountain-day ultra fixtures only, update them. Any other snapshot change is a bug.
- [ ] **Step 5: Commit.** `git commit -m "feat(plan): ultra ladder prompt block"`

---

### Task 8: Docs, scorecard rows, persona pack

**Files:**
- Modify: `docs/plan-rules.md`:
  - R-L1: the lint allows +25%; ladder plans are exempt.
  - R-P3: match the code's taper (−30% / −50%).
  - Add a new "R-U Ultra ladder" section that points to the spec.
- Modify: `backend/scripts/plan_reliability.py`:
  - add `mountain_days` to scenarios
  - add rows for 50K / 100K × finisher (`65km 6d`) / advanced (`100km 6d`) × mountain day yes/no
  - for mountain-day rows, ladder plans may show `LONG_SHARE`-free, `LONG_RUN_JUMP`-free weeks; no new exemptions needed
- Modify: `CLAUDE.md` (Goal-reliable plans paragraph): one sentence on `services/ultra_rules.py` (ladder, quality window).

- [ ] **Step 1: Run the scorecard.** Run `python scripts/plan_reliability.py`. Expected: exit 0 with the new rows.
- [ ] **Step 2: Re-render the HCMC persona pack.** Run `python scripts/render_persona_pack.py` and hand the output to the user for Quang's review. This is a manual step; don't send it to anyone.
- [ ] **Step 3: Commit.** `git commit -m "docs: ultra ladder rules; scorecard rows for mountain-day ultras"`

---

## Out of this plan

- The uncommitted `athlete_tier.py` edit on `feat/quang-100k-mountain-rules` (in `~/.codex/worktrees/inferred-missed`) is replaced by Tasks 1–2. Discard it when this branch lands.
- Langfuse prompt versioning and promotion: the PR carries the `llm-change-process` checklist. The template itself is unchanged.
- The open questions still stand: Quang to confirm the 50 km ladder, and NotebookLM Q5 to decide the C6 default.

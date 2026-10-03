# Vietnam urban scheduler fixtures

Four fully invented profiles cover recreational and sub-elite runners, each with
and without weekday gym access. No-gym cases live in Hanoi; treadmill cases live
in HCM. Outdoor weekday runs are flat; mountains are available on Saturday and
Sunday; the long run is Sunday. Gym cases allow incline treadmills on Tuesday and
Thursday only. Plans request Vietnamese output. City and equipment are coupled
in this small matrix; it tests the access constraint, not a city-specific effect.

The application exposes one global `mixed` terrain setting. Day-specific access
is therefore expressed in `athlete_notes`, alongside structured gym/treadmill
flags in both the profile and race input. Availability is manually reviewed; it
is not a new automated terrain gate.

Invented recreational anchors: 66 km + 900 m = 75 effort-km, marathon predictor
13,860 s, measured AeT/AnT 146/166. The spec's interpolation and weights resolve
recreational (approximately 2.724). Sub-elite anchors: 108 km + 1,800 m = 126
effort-km, predictor 11,640 s, AeT/AnT 154/171, resolving sub-elite (approximately
3.307). Existing tier-resolution tests now exercise all four fixtures through
the actual golden runner. The matrix test checks access flags, language and notes.
No tier or volume gate was loosened.

## 2026-10-03 targeted evaluation

Production references use `plan_generation` v1, all Gemini, two weeks per case.
The candidate is existing v4 at `snapshot-exp`. Targeted Langfuse run:
`eval_scheduler_snapshot-exp_1791031783`, pushed with `--synthetic-only`; all four
score sets were read back through Scores API v3. This is four-case coverage,
not a new full 19-case scheduler run. No prompt or label was changed.

| Case | Snapshot km | Expected week-2 km | Production v1 km | Candidate v4 km | Tier / volume |
|---|---:|---:|---:|---:|---|
| Recreational, no gym | 66 | 55–73 | 61.5 | 60.7 | PASS / PASS |
| Recreational, treadmill | 66 | 55–73 | 45.1 | 58.3 | PASS / PASS |
| Sub-elite, no gym | 108 | 92–119 | 97.8 | 106.0 | PASS / PASS |
| Sub-elite, treadmill | 108 | 92–119 | 88.0 | 102.9 | PASS / PASS |

All four candidate cases use Gemini without fallback. Production passes two of
four volume bands; v4 passes four. In both versions, `easy_share` and
`complete_sessions` pass; `progression` fails because the current-date first
week starts on Saturday and is compared with a full second week. The score is
2/3 in every case, with no regression. This partial-week effect is retained,
not waived or rewritten.

One production response failed the literal privacy scan before saving or
exporting. The two remaining missing references were then captured once more;
all four committed references are clean Gemini output. The candidate ran while
the last two references were missing; the final comparison above and check parity
were computed from the completed references afterward.

## Access and output review

The inspected v4 outputs respect the requested terrain timing: outdoor weekday
runs have zero ascent; hills and mountain runs occur on weekends; gym incline
sessions are on Tuesday/Thursday; every long run is Sunday. No-gym weekday ME
uses bodyweight circuits, without treadmills, weights or machines. Step-ups need
a household bench/step; no-gym does not imply no household objects.

There are output consistency issues despite the passing tier/volume gates:

- Recreational treadmill Thursday describes 12.3 km of incline running but has
  zero recorded ascent. Tuesday ME describes running/walking but records zero
  distance. Sub-elite treadmill Tuesday ME also records zero distance/ascent.
- Some deterministic treadmill fields differ from generated instructions:
  recreational Tuesday's displayed incline range is 10–15%, broader than the
  text's exact 12%; sub-elite Thursday's field is 10–15% while its text specifies
  8–10%. These are independent of terrain availability and warrant follow-up.
- Week-2 long-run distance shares are 42.8%, 37.2%, 38.0% and 31.3%, versus
  configured recreational/sub-elite share caps of 33%/30%, included in the prompt
  through `plan_rules`. The prompt calls this weekly volume without a unit;
  these comparisons use recorded distance, not minutes. Those caps are not
  checked by the current golden quality checks; this is a distribution concern,
  not an additional automated gate result.
- Both no-gym plans explicitly mention "snapshot" in athlete-facing descriptions,
  contrary to v4's instruction to avoid disclosing the snapshot block.
- No-gym ME includes running warm-ups/cool-downs with zero recorded distance,
  so the passing sum of `distance_km` does not prove that every described running
  segment is accounted for.

[Candidate scores and generated workouts](vietnam-urban-v4-samples.json) preserve
these observations for review. Production references live beside their fixtures
under `backend/tests/golden/scheduler/`.

Validation: `pytest tests/unit -q -m "not kafka"` — **1,138 passed**, 23 warnings.
No integration suite ran. The entire committed diff passes the owner literal
privacy scan. Existing production HOLD remains: the separate staging no-COROS
sequential path missed its volume band. These four offline passes do not clear
that failure or establish repeatability for the new access cases.

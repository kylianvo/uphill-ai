"""COROS course sections built from the description's Process chain.

Fixtures are the three workouts from the 2026-09-25 staging live check, whose
COROS copies had a fixed 10/5 min warm-up/cool-down and -- for the tempo -- a
single 55-minute block at tempo heart rate.
"""

import datetime as dt

from services.coros_workouts import (
    MAX_DESCRIPTION,
    SECTION_COOLDOWN,
    SECTION_RECOVERY,
    SECTION_TRAINING,
    SECTION_WARMUP,
    build_course,
    parse_process_steps,
    validate_course,
)
from services.training_rules import TrainingRules

ZONES = TrainingRules.calculate_heart_rate_zones(185, 60, 150, 170)
# Zone 1 120-135, Zone 2 135-150, Zone 3 150-170, Zone 4 170-177, Zone 5 177-185

FLUSH = {
    "title": "Pre-Weekend Recovery Flush Run",
    "type": "Recovery",
    "duration_minutes": 45,
    "target_zone": "Zone 1",
    "target_hr_range": "125-140 bpm",
    "approved_at": dt.datetime(2026, 9, 1, tzinfo=dt.UTC),
    "description": (
        "Process: Warm up 10 min light jog @ 6:15 /km in Zone 1 → Main run 25 min relaxed recovery cruising "
        "@ 6:00 /km in Zone 1 → Cool down 10 min walk and gentle jog @ 6:20 /km in Zone 1. "
        "Overall: A very light, regenerative run. Reason: Placed on Friday. Benefit: Recovery. Warning: Stay easy."
    ),
}
LONG = {
    **FLUSH,
    "title": "Run Club Flat Aerobic Long Run",
    "type": "Long Run",
    "duration_minutes": 120,
    "target_zone": "Zone 2",
    "target_hr_range": "140-155 bpm",
    "description": (
        "Process: Warm up 15 min easy conversational jogging @ 5:50 /km in Zone 1 → Main run 90 min continuous "
        "steady aerobic running with run club @ 5:35 /km in Zone 2 → Cool down 15 min easy jogging @ 6:05 /km "
        "in Zone 1. Overall: A steady two-hour aerobic long run. Reason: Weekend. Benefit: Aerobic base."
    ),
}
TEMPO = {
    **FLUSH,
    "title": "Flat Aerobic Sub-Threshold Tempo",
    "type": "Tempo",
    "duration_minutes": 70,
    "target_zone": "Zone 3",
    "target_hr_range": "160-172 bpm",
    "description": (
        "Process: Warm up 15 min progressive aerobic jogging @ 5:45 /km in Zone 2 → 10 min sustained tempo "
        "@ 5:00 /km in Zone 3 → 3 min easy jog recovery @ 5:45 /km in Zone 2 → 10 min sustained tempo @ 5:00 /km "
        "in Zone 3 → 3 min easy jog recovery @ 5:45 /km in Zone 2 → 10 min sustained tempo @ 5:00 /km in Zone 3 "
        "→ 3 min easy jog recovery @ 5:45 /km in Zone 2 → Cool down 16 min easy running @ 5:50 /km in Zone 1. "
        "Overall: Three 10-minute tempo repeats. Reason: Saturday. Benefit: Lactate clearance."
    ),
}


def _hr(section):
    return section.get("intensityValueStart"), section.get("intensityValueEnd")


def test_parse_process_steps_reads_minutes_zones_and_roles():
    steps = parse_process_steps(TEMPO["description"])
    assert [(s.minutes, s.zone) for s in steps] == [(15, 2), (10, 3), (3, 2), (10, 3), (3, 2), (10, 3), (3, 2), (16, 1)]
    assert steps[0].role == "warmup" and steps[-1].role == "cooldown"
    assert [s.role for s in steps[1:-1]] == ["training", "recovery"] * 3


def test_parse_process_steps_without_process_or_minutes_is_none():
    assert parse_process_steps("Overall: just run.") is None
    assert parse_process_steps("Process: Run easy → Run hard. Overall: x") is None
    assert parse_process_steps(None) is None


def test_flush_run_keeps_its_real_warmup_and_cooldown():
    c = build_course(FLUSH, "en", ZONES)
    assert [(s["sectionType"], s["targetValue"]) for s in c["sections"]] == [
        (SECTION_WARMUP, 600),
        (SECTION_TRAINING, 1500),
        (SECTION_COOLDOWN, 600),
    ]
    assert all(_hr(s) == (125, 140) for s in c["sections"])  # every step is the workout's own zone
    assert validate_course(c) == []


def test_long_run_uses_zone_table_for_warmup_and_cooldown():
    c = build_course(LONG, "en", ZONES)
    warm, main, cool = c["sections"]
    assert (warm["targetValue"], main["targetValue"], cool["targetValue"]) == (900, 5400, 900)
    assert _hr(main) == (140, 155) and _hr(warm) == (120, 135) and _hr(cool) == (120, 135)


def test_tempo_becomes_a_repeat_group_not_one_long_tempo_block():
    c = build_course(TEMPO, "en", ZONES)
    warm, group, cool = c["sections"]
    assert (warm["sectionType"], warm["targetValue"], _hr(warm)) == (SECTION_WARMUP, 900, (135, 150))
    assert group["intervalGroup"] is True and group["repeats"] == 3
    work, rec = group["sets"]
    assert (work["sectionType"], work["targetValue"], _hr(work)) == (SECTION_TRAINING, 600, (160, 172))
    assert (rec["sectionType"], rec["targetValue"], _hr(rec)) == (SECTION_RECOVERY, 180, (135, 150))
    assert (cool["sectionType"], cool["targetValue"], _hr(cool)) == (SECTION_COOLDOWN, 960, (120, 135))
    assert validate_course(c) == []


def test_trailing_rep_without_recovery_stays_outside_the_group():
    w = {
        **TEMPO,
        "duration_minutes": 67,
        "description": TEMPO["description"].replace(
            "→ 3 min easy jog recovery @ 5:45 /km in Zone 2 → Cool down", "→ Cool down"
        ),
    }
    _, group, last, _ = build_course(w, "en", ZONES)["sections"]
    assert group["repeats"] == 2 and (last["sectionType"], last["targetValue"]) == (SECTION_TRAINING, 600)


def test_without_profile_zones_other_steps_use_coros_zone_numbers():
    c = build_course(TEMPO, "en", None)
    warm, group, _ = c["sections"]
    assert warm["sectionIntensity"] == 2 and "intensityValueStart" not in warm
    assert _hr(group["sets"][0]) == (160, 172)


def test_minutes_that_do_not_add_up_fall_back_safely_for_quality_sessions():
    w = {**TEMPO, "duration_minutes": 90}  # Process sums to 70
    (only,) = build_course(w, "en", ZONES)["sections"]
    assert (only["sectionType"], only["targetValue"]) == (SECTION_TRAINING, 5400)
    assert "intensityType" not in only  # never a whole session at tempo heart rate


def test_minutes_that_do_not_add_up_keep_easy_run_shape():
    w = {**LONG, "duration_minutes": 100}
    warm, main, cool = build_course(w, "en", ZONES)["sections"]
    assert _hr(main) == (140, 155) and warm["sectionType"] == SECTION_WARMUP


def test_long_description_is_cut_at_a_word_boundary():
    w = {**FLUSH, "description": FLUSH["description"] + " " + "recovery " * 200}
    desc = build_course(w, "en", ZONES)["courseDescription"]
    assert len(desc) <= MAX_DESCRIPTION and desc.endswith("…")
    assert desc[:-1].rstrip().split()[-1] == "recovery"

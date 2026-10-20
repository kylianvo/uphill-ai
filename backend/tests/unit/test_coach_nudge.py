from datetime import date

from services import coach_nudge


def w(week, day, minutes, **kw):
    return {"week_number": week, "day_of_week": day, "type": kw.pop("type", "Easy"), "duration_minutes": minutes,
            "phase": kw.pop("phase", "Base"), "title": kw.pop("title", "Easy run"), **kw}  # fmt: skip


def _week(week, done, missed=0, reason=None, **kw):
    days = ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    out = []
    for i, d in enumerate(days):
        completed = 1 if i < done else 0
        is_missed = 1 if completed == 0 and i < done + missed else 0
        out.append(w(week, d, 60, is_completed=completed, is_missed=is_missed,
                     missed_reason=reason if is_missed else None, **kw))  # fmt: skip
    return out


PLAN = {"start_date": "2026-10-05", "total_weeks": 12, "race_date": "2027-01-02", "id": 1}
TODAY = date(2026, 10, 21)  # week 3 of the plan (starts 2026-10-05)


def facts(workouts, **kw):
    args = {"readiness_flag": None, "feasibility_verdict": None, "plan_supported": True}
    return coach_nudge.facts_for(PLAN, workouts, TODAY, **{**args, **kw})


def test_facts_describe_last_completed_week_and_the_consistent_run():
    ws = _week(1, 5) + _week(2, 4, missed=1, reason="busy")
    f = facts(ws)
    assert f["current_week"] == 3
    assert f["last_week"] == {
        "planned": 5,
        "completed": 4,
        "missed": 1,
        "adherence": 0.8,
        "missed_reasons": {"busy": 1},
    }
    assert f["consistent_weeks"] == 2


def test_tone_encourages_after_a_consistent_week():
    assert coach_nudge.tone_for(facts(_week(1, 5) + _week(2, 5))) == "encourage"


def test_tone_pushes_gently_after_a_slipped_week():
    assert coach_nudge.tone_for(facts(_week(1, 5) + _week(2, 1, missed=2, reason="tired"))) == "push"


def test_heads_up_wins_for_a_risky_goal_or_a_fatigued_body():
    ws = _week(1, 5) + _week(2, 1, missed=2)
    assert coach_nudge.tone_for(facts(ws, feasibility_verdict="unsupported")) == "heads_up"
    assert coach_nudge.tone_for(facts(ws, readiness_flag="overreaching")) == "heads_up"
    assert coach_nudge.tone_for(facts(_week(1, 5) + _week(2, 5), plan_supported=False)) == "heads_up"


def test_silence_when_there_is_nothing_worth_saying():
    assert coach_nudge.tone_for(facts(_week(1, 3, missed=0) + _week(2, 3))) is None
    assert coach_nudge.tone_for(facts([])) is None


def test_the_milestone_just_passed_is_a_fact_and_a_reason_to_encourage():
    ws = _week(1, 5) + _week(2, 3) + [w(2, "Sunday", 190, type="Long Run", is_completed=1)]
    f = facts(ws)
    assert [m["key"] for m in f["milestones_just_done"]] == ["long_run_3h"]
    assert coach_nudge.tone_for(f) == "encourage"


def test_fallback_text_uses_only_fact_numbers_in_both_languages():
    f = facts(_week(1, 5) + _week(2, 1, missed=2, reason="tired"))
    for lang in ("en", "vi"):
        text = coach_nudge.fallback_text(f, "push", lang)
        assert text and coach_nudge.grounded(text, f)
        assert not any(b in text.lower() for b in ("thể tích", "kiến tạo", "tối ưu hóa"))


def test_grounding_rejects_invented_numbers():
    f = facts(_week(1, 5) + _week(2, 5))
    assert coach_nudge.grounded("Two solid weeks in a row.", f)
    assert not coach_nudge.grounded("You ran 87% of the plan.", f)


def test_hash_changes_with_facts_tone_and_language():
    a = facts(_week(1, 5) + _week(2, 5))
    b = facts(_week(1, 5) + _week(2, 4, missed=1))
    assert coach_nudge.facts_hash(a, "encourage", "en") != coach_nudge.facts_hash(b, "encourage", "en")
    assert coach_nudge.facts_hash(a, "encourage", "en") != coach_nudge.facts_hash(a, "encourage", "vi")


def test_a_vietnamese_push_names_the_reason_in_vietnamese():
    f = facts(_week(1, 5) + _week(2, 1, missed=2, reason="busy"))
    assert "(bận)" in coach_nudge.fallback_text(f, "push", "vi") and "(busy)" in coach_nudge.fallback_text(
        f, "push", "en"
    )

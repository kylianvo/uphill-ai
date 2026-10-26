from datetime import UTC, date, datetime

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


def test_training_behind_the_b_path_is_a_plain_heads_up_and_ahead_is_encouraged():
    behind = {"b": "behind", "a": "behind", "measured_pct": 0.1, "weeks": 6, "confidence": "medium"}
    ahead = {"b": "ahead", "a": "on", "measured_pct": 3.0, "weeks": 6, "confidence": "medium"}
    ws = _week(1, 3) + _week(2, 3)
    assert coach_nudge.tone_for(facts(ws, path=behind)) == "heads_up"
    assert coach_nudge.tone_for(facts(ws, path={**behind, "confidence": "low"})) is None
    f = facts(ws, path=ahead)
    assert coach_nudge.tone_for(f) == "encourage"
    assert coach_nudge.grounded(coach_nudge.fallback_text(f, "encourage", "en"), f)


def test_zone_labels_are_not_invented_numbers():
    f = facts(_week(1, 5) + _week(2, 5))
    assert coach_nudge.grounded("Keep the Zone 2 sessions steady.", f)
    assert not coach_nudge.grounded("Keep Zone 2 for 87 minutes.", f)


def test_facts_include_beginner_milestone_reached_this_week():
    rows = [{"milestone_key": "jog_10", "source": "auto", "achieved_at": datetime(2026, 10, 19, 7, tzinfo=UTC)}]
    f = facts(_week(1, 3) + _week(2, 3), beginner_rows=rows)
    assert {"key": "jog_10", "week": 2} in f["milestones_just_done"]
    assert coach_nudge.tone_for(f) == "encourage"


def test_baseline_and_revoked_not_in_just_done():
    rows = [
        {"milestone_key": "jog_5", "source": "baseline", "achieved_at": datetime(2026, 10, 19, tzinfo=UTC)},
        {"milestone_key": "jog_10", "source": "revoked", "achieved_at": None},
    ]
    assert facts(_week(1, 3), beginner_rows=rows)["milestones_just_done"] == []


def test_fallback_text_names_first_5k_en_vi():
    f = {"milestones_just_done": [{"key": "first_5k", "week": 2}], "last_week": {}}
    assert "5 km" in coach_nudge.fallback_text(f, "encourage", "en")
    assert "5 km" in coach_nudge.fallback_text(f, "encourage", "vi")


def test_grounded_accepts_milestone_numbers():
    f = {"milestones_just_done": [{"key": "jog_20", "week": 2}]}
    assert coach_nudge.grounded("You just ran 20 minutes without stopping.", f)


def test_next_session_never_points_to_a_day_already_past():
    ws = _week(1, 5) + _week(2, 5) + [w(3, "Monday", 60, title="Past run"), w(3, "Thursday", 60, title="Next run")]
    assert facts(ws)["next_session"]["title"] == "Next run"


def _legs_week():
    return [
        w(3, "Tuesday", 50, type="Muscular Endurance", title="Muscular Endurance (ME)"),
        w(3, "Wednesday", 60),
        w(3, "Thursday", 50, type="Muscular Endurance", title="Muscular Endurance (ME)"),
        w(3, "Saturday", 180, type="Long Run", title="Mountain Long Run"),
    ]


def test_this_week_names_the_focus_and_the_session_to_nail():
    f = facts(_week(1, 5) + _week(2, 5) + _legs_week())
    week = f["this_week"]
    assert week["focus"] == "leg_strength"
    assert [s["day"] for s in week["key_sessions"]] == ["Tuesday", "Thursday", "Saturday"]
    assert week["nail"] == {"day": "Saturday", "title": "Mountain Long Run", "minutes": 180}


def test_a_quiet_week_still_gets_a_steady_review():
    f = facts(_week(1, 3) + _week(2, 3) + _legs_week())  # 60% last week: neither slip nor solid
    assert coach_nudge.tone_for(f) == "steady"


def test_fallback_review_has_three_grounded_messages_and_a_nail():
    f = facts(_week(1, 5) + _week(2, 5) + _legs_week())
    for lang in ("en", "vi"):
        review = coach_nudge.fallback_review(f, coach_nudge.tone_for(f), lang)
        assert len(review["messages"]) == 3 and review["nail"].startswith("Saturday: Mountain Long Run, 180")
        assert coach_nudge.acceptable(review, f)


def test_a_model_review_with_an_invented_number_is_rejected():
    f = facts(_week(1, 5) + _week(2, 5) + _legs_week())
    review = {"messages": ["5 for 5.", "Legs week.", "You will climb 4321 m this week."], "nail": "Saturday, 180 min."}
    assert not coach_nudge.acceptable(review, f)

"""apply_priority_guard: the server-side rules for the AI-set `is_priority` flag."""

from services.plan_generator import MAX_PRIORITY_PER_WEEK, apply_priority_guard


def _wo(day="Monday", week=1, type_="Tempo", **kw):
    return {"week_number": week, "day_of_week": day, "type": type_, **kw}


def test_missing_field_defaults_to_false():
    assert apply_priority_guard([_wo()])[0]["is_priority"] is False


def test_non_bool_values_coerce_to_false():
    wos = [
        _wo(day=d, is_priority=v)
        for d, v in zip(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ["true", 1, "yes", None, [True]], strict=True
        )
    ]
    assert [w["is_priority"] for w in apply_priority_guard(wos)] == [False] * 5


def test_true_is_kept():
    assert apply_priority_guard([_wo(type_="Long Run", is_priority=True)])[0]["is_priority"] is True


def test_rest_is_never_priority():
    assert apply_priority_guard([_wo(type_="Rest", is_priority=True)])[0]["is_priority"] is False


def test_easy_and_recovery_are_never_priority():
    # The prompt says so, but the model still flagged an Easy run in the golden eval.
    for t in ("Easy", "Recovery"):
        assert apply_priority_guard([_wo(type_=t, is_priority=True)])[0]["is_priority"] is False


def test_walk_run_can_be_priority():
    # Beginner and return-to-run plans are all Walk/Run, so their key session is one.
    assert apply_priority_guard([_wo(type_="Walk/Run", is_priority=True)])[0]["is_priority"] is True


def test_cap_keeps_first_two_by_day_order_not_list_order():
    wos = [
        _wo(day="Sunday", type_="Long Run", is_priority=True),
        _wo(day="Wednesday", type_="Interval", is_priority=True),
        _wo(day="Tuesday", type_="Tempo", is_priority=True),
    ]
    apply_priority_guard(wos)
    assert [w["is_priority"] for w in wos] == [False, True, True]
    assert MAX_PRIORITY_PER_WEEK == 2


def test_cap_is_per_week_and_rest_does_not_use_a_slot():
    wos = [
        _wo(day="Monday", type_="Rest", is_priority=True),
        _wo(day="Tuesday", is_priority=True),
        _wo(day="Wednesday", is_priority=True),
        _wo(day="Thursday", is_priority=True),
        _wo(day="Monday", week=2, is_priority=True),
    ]
    apply_priority_guard(wos)
    assert [w["is_priority"] for w in wos] == [False, True, True, False, True]

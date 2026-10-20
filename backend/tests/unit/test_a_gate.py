from services import a_gate
from services.aerobic_speed import PathStatus


def p(a="on", b="on", conf="medium"):
    return PathStatus(b=b, a=a, measured_pct=2.0, expected_pct=1.5, weeks=6, confidence=conf)


def w(week, done, planned=4):
    return [{"week_number": week, "type": "Easy", "is_completed": 1 if i < done else 0} for i in range(planned)]


GOOD = w(1, 4) + w(2, 4)


def test_open_when_every_condition_holds():
    g = a_gate.evaluate(p(), readiness_flag="optimal", workouts=GOOD, before_week=3, plan_supported=True)
    assert g.open and g.reasons == []


def test_each_condition_can_close_it_and_says_why():
    ok = {"readiness_flag": "optimal", "workouts": GOOD, "before_week": 3, "plan_supported": True}
    assert not a_gate.evaluate(p(a="behind"), **ok).open
    assert not a_gate.evaluate(None, **ok).open
    assert not a_gate.evaluate(p(conf="low"), **ok).open
    assert not a_gate.evaluate(p(), **{**ok, "readiness_flag": "overreaching"}).open
    assert not a_gate.evaluate(p(), **{**ok, "plan_supported": False}).open
    assert not a_gate.evaluate(p(), **{**ok, "workouts": w(1, 2) + w(2, 2)}).open
    reasons = a_gate.evaluate(p(a="behind"), **{**ok, "readiness_flag": "fatigued"}).reasons
    assert len(reasons) == 2


def test_no_history_is_closed_not_open():
    g = a_gate.evaluate(p(), readiness_flag=None, workouts=[], before_week=1, plan_supported=True)
    assert not g.open and any("sessions" in r for r in g.reasons)


def test_prompt_and_log_lines():
    open_ = a_gate.evaluate(p(), readiness_flag="optimal", workouts=GOOD, before_week=3, plan_supported=True)
    shut = a_gate.evaluate(p(a="behind"), readiness_flag="optimal", workouts=GOOD, before_week=3, plan_supported=True)
    assert "allowed" in a_gate.prompt_line(open_) and "B goal only" in a_gate.prompt_line(shut)
    assert a_gate.log_line(shut).startswith("A-goal extras are on hold")

import datetime as dt

from services.coros_push import created_plan_id, parse_plan_library

LIBRARY = (
    "Training Plan Library\n========================\nStatus filter: in progress\nPlans on this page: 2\n\n"
    "1. Uphill AI · UTMB 50K [In progress] [mcp]\n   Plan ID: 500000000000000001\n   Record role: execution\n"
    "   Editable via MCP: yes\n   Dates: 2027-04-07 to 2027-05-02\n   Weeks: 4\n"
    "   Created: 2027-04-07 08:00:00 | Updated: 2027-04-07 08:00:00\n\n"
    "2. 100km (24/4-28/5) [Not started] [custom]\n   Plan ID: 451902540550946816\n   Record role: library\n"
    "   Editable via MCP: no\n   Weeks: 5\n   Overview: line one\nline two\n\n"
    "Only use a Plan ID with recordRole=execution and editable=true for updateTrainingPlan."
)


def test_parse_plan_library():
    recs = parse_plan_library(LIBRARY)
    assert [r.plan_id for r in recs] == ["500000000000000001", "451902540550946816"]
    a, b = recs
    assert (a.name, a.role, a.editable, a.start, a.weeks) == (
        "Uphill AI · UTMB 50K",
        "execution",
        True,
        dt.date(2027, 4, 7),
        4,
    )
    assert (b.name, b.role, b.editable, b.start, b.weeks) == ("100km (24/4-28/5)", "library", False, None, 5)


def test_parse_plan_library_empty_and_garbage():
    assert parse_plan_library("No training plans found.") == []
    assert parse_plan_library("") == []


def test_created_plan_id_prefers_explicit_id_then_name_match():
    recs = parse_plan_library(LIBRARY)
    assert created_plan_id("Created plan. Plan ID: 42", recs, "whatever") == "42"
    assert created_plan_id("Created.", recs, "Uphill AI · UTMB 50K") == "500000000000000001"
    assert created_plan_id("Created.", recs, "Other") is None


def test_unapplied_days_reads_coros_update_summary():
    from services.coros_push import unapplied_days

    reply = (
        "Training plan updated successfully.\nUpdated days (dayNo): 8, 10\n"
        "Cleared to rest (dayNo): none\nSkipped executed days (dayNo): 9\nPlan length: 13 weeks"
    )
    sent = [{"dayNo": d} for d in (8, 9, 10, 11)]
    assert unapplied_days(reply, sent) == [11]
    assert unapplied_days(reply, sent[:3]) == []
    assert unapplied_days("Plan updated.", sent) == []  # no summary: nothing to check


def test_unapplied_days_expands_coros_ranges():
    from services.coros_push import unapplied_days

    reply = "Training plan updated successfully.\nUpdated days (dayNo): 9-11, 87\nCleared to rest (dayNo): none"
    assert unapplied_days(reply, [{"dayNo": d} for d in (9, 10, 11, 87)]) == []


def test_coros_error_text_is_a_failure():
    import pytest

    from services.coros_push import _ok
    from services.mcp_client import McpToolError

    with pytest.raises(McpToolError):
        _ok("COROS API error: 1 validation error(s): [dayNo=87, course=1] The training distance is too long.")
    assert _ok("Training plan updated successfully.") == "Training plan updated successfully."


def test_race_placeholder_over_80km_is_free_mode():
    from services.coros_workouts import race_day_course

    assert race_day_course("UTMB", 104.2, "en")["sections"][0]["targetType"] == 4
    assert race_day_course("VMM", 70, "en")["sections"][0]["targetValue"] == 70000

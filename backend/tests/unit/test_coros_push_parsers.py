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

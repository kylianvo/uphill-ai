"""Gemini attempt -> reduced-prompt retry -> rule-based, inside generate_plan_workouts.

Successor to test_plan_generator_engines.py, which tested RAG_ENGINE's gemini/notebooklm
ordering. NotebookLM is gone; the cases that outlived it (Gemini succeeds and is grounded
with KB context, engine attribution on the "used" counter, course-context injection, and
the fall-through when Gemini fails) live on here alongside the new retry tier.
"""

import json
from unittest.mock import MagicMock, patch

from services.plan_generator import PlanGenerator

WORKOUT_JSON = json.dumps(
    [
        {
            "week_number": 1,
            "day_of_week": "Tue",
            "phase": "Base",
            "title": "Easy Aerobic Run",
            "type": "Easy",
            "duration_minutes": 45,
            "target_zone": "Zone 2",
            "target_hr_range": "125-140 bpm",
            "target_pace": "6:30 /km",
            "distance_km": 7.0,
            "elevation_gain_m": 0,
            "grade_percent": 0,
            "description": "Warm up 10min → run 30min Zone 2 → cool down 5min. Overall: aerobic base.",
            "fueling_tip": "Water only.",
        }
    ]
)

USER_PROFILE = {"age": 34, "max_hr": 188, "resting_hr": 52}
RACE_INFO = {"lang": "en", "terrain": "trail"}


def _fake_gemini_client(*texts: str):
    """A client whose successive generate_content calls return `texts` in order.
    With one text it behaves as a always-succeeds client."""
    responses = []
    for t in texts or (WORKOUT_JSON,):
        r = MagicMock()
        r.text = t
        responses.append(r)
    fake_client = MagicMock()
    if len(responses) == 1:
        fake_client.models.generate_content.return_value = responses[0]
    else:
        fake_client.models.generate_content.side_effect = responses
    return fake_client


async def _generate(race_info=RACE_INFO):
    return await PlanGenerator.generate_plan_workouts(
        plan_id=999999,
        user_profile=USER_PROFILE,
        race_info=race_info,
        total_weeks=8,
        api_key="test-key",
        block_number=1,
    )


def test_gemini_is_grounded_with_retrieved_kb_context():
    import asyncio

    fake_client = _fake_gemini_client()
    chunks = [{"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds, short rests."}]
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        workouts = asyncio.run(_generate())

    assert workouts and workouts[0]["title"] == "Easy Aerobic Run"
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "UPHILL ATHLETE PHILOSOPHY" in prompt_sent
    assert "6-8 rounds" in prompt_sent


def _used_count(engine: str) -> float:
    from prometheus_client import REGISTRY

    return (
        REGISTRY.get_sample_value(
            "rag_attempts_total", {"service": "plan_generator", "engine": engine, "status": "used"}
        )
        or 0.0
    )


def test_used_counter_attributes_the_returned_plan_to_the_attempt_that_produced_it():
    """An answer that fails JSON parsing must NOT count as "used" — only the attempt
    whose parsed output is actually returned increments it (golden_eval.py relies on
    this for attribution). Here the first attempt is unparseable and the retry wins."""
    import asyncio

    before = {"gemini": _used_count("gemini"), "gemini_retry": _used_count("gemini_retry")}
    fake_client = _fake_gemini_client("Sorry, I could not produce a plan.", WORKOUT_JSON)
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake_client),
    ):
        workouts = asyncio.run(_generate())

    assert workouts and workouts[0]["title"] == "Easy Aerobic Run"
    assert _used_count("gemini") == before["gemini"]  # parse-failed answer never "used"
    assert _used_count("gemini_retry") == before["gemini_retry"] + 1


def test_unparseable_first_attempt_triggers_a_reduced_retry():
    """The retry exists to recover from length-driven failures, so it must drop the KB
    grounding block and ask for shorter output rather than resend the identical prompt."""
    import asyncio

    chunks = [{"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds."}]
    fake_client = _fake_gemini_client("not json at all", WORKOUT_JSON)
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=chunks),
        patch("google.genai.Client", return_value=fake_client),
    ):
        workouts = asyncio.run(_generate())

    assert workouts and workouts[0]["title"] == "Easy Aerobic Run"
    assert fake_client.models.generate_content.call_count == 2
    first, second = (c.kwargs["contents"] for c in fake_client.models.generate_content.call_args_list)
    assert "UPHILL ATHLETE PHILOSOPHY" in first
    assert "UPHILL ATHLETE PHILOSOPHY" not in second  # retry drops grounding to shorten
    assert second.startswith("RETRY:")


def test_gemini_failure_falls_back_to_the_rule_based_schedule():
    """Both attempts failing must still yield a usable plan, not an error."""
    import asyncio

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = Exception("Gemini down")
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake_client),
    ):
        workouts = asyncio.run(_generate())

    assert fake_client.models.generate_content.call_count == 2  # first attempt + retry
    assert workouts, "rule-based fallback must still produce a schedule"
    # Block 1 with the default weeks_per_block=2 covers weeks 1-2, so the fallback must
    # stay inside that window rather than laying out all 8 weeks of the plan.
    assert {w["week_number"] for w in workouts} == {1, 2}
    assert all(w.get("title") for w in workouts)


RACE_INFO_WITH_COURSE_CONTEXT = {
    "lang": "en",
    "terrain": "trail",
    "name": "Vietnam Mountain Marathon",
    "goal_type": "finish",
    "course_context": "Highly technical hand-and-knees scrambles on the final climbs.",
}


def test_course_context_is_injected_into_the_prompt_when_present():
    import asyncio

    fake_client = _fake_gemini_client()
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake_client),
    ):
        asyncio.run(_generate(RACE_INFO_WITH_COURSE_CONTEXT))
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "COURSE INTELLIGENCE" in prompt_sent or "COURSE PROFILE" in prompt_sent
    assert "hand-and-knees scrambles" in prompt_sent


def test_no_course_context_key_omits_the_section():
    import asyncio

    fake_client = _fake_gemini_client()
    with (
        patch("services.kb_retrieval.search_scheduler_chunks", return_value=[]),
        patch("google.genai.Client", return_value=fake_client),
    ):
        asyncio.run(_generate())  # RACE_INFO has no course_context key
    prompt_sent = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "COURSE PROFILE" not in prompt_sent

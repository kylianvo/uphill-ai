"""Fixtures that require a live Postgres (uphill_ai_test) -- scoped to
tests/integration/ only. See the root conftest.py for why DATABASE_URL/
ENVIRONMENT must already be set by the time this module is imported (they
are: root conftest.py always loads first for the whole pytest session).
"""

import pytest
from sqlalchemy import text

from db import engine, init_db

# Truncated in child-first order isn't strictly required (CASCADE handles FK
# dependencies), but listed here for readability of the dependency graph.
ALL_TABLES = [
    "race_results",
    "race_profile_claims",
    "vbm_athletes",
    "chat_proposals",
    "chat_llm_calls",
    "chat_turns",
    "chat_messages",
    "chat_threads",
    "chat_daily_usage",
    "kb_chunks",
    "block_reviews",
    "knowledge_cards",
    "workout_types",
    "shoes",
    "analytics_events",
    "nutrition_products",
    "coros_plan_links",
    "coros_push_usage",
    "workouts",
    "plans",
    "sessions",
    "sources",
    "coach_notes",
    "coach_athletes",
    # activities self-references itself via duplicate_of, which TRUNCATE
    # tolerates as long as the table is truncated in the same statement --
    # it and daily_metrics/athlete_connections also FK to users, so all three
    # must precede "users" in this list (CASCADE would pull them in anyway,
    # but listing them keeps the truncation from depending on that).
    "activities",
    "daily_metrics",
    "athlete_connections",
    "users",
]


@pytest.fixture(scope="session", autouse=True)
def _init_test_database():
    """Creates the schema once per test session against uphill_ai_test.

    Also truncates once here, since init_db() seeds default rows (e.g. two
    default users) that would otherwise leak into whichever test happens to
    run first in the session.
    """
    init_db()
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))
        conn.commit()
    yield


@pytest.fixture(autouse=True)
def _truncate_tables():
    """Truncates all tables between tests for isolation.

    db.py opens a fresh engine.connect() + explicit conn.commit() per call
    (not one connection/transaction per request), so per-test transaction
    rollback isn't viable here -- truncate-between-tests is the pragmatic
    equivalent. Consequence: tests must not depend on execution order or on
    rows left behind by another test.

    Also clears main.plan_jobs: it's process-global, in-memory state that
    outlives any single test's TestClient, unlike the DB rows above. A test
    that fires a background generation job via asyncio.create_task without
    polling it to completion (e.g. one that only checks the 200/job_id on
    the initiating response) leaves that job stuck at status "generating"
    forever. Because RESTART IDENTITY above resets plan_id back to the same
    small integers for every test, a later test's freshly-created plan can
    reuse that same plan_id -- and generate-next-block's double-submission
    guard matches on plan_id across the whole process lifetime, so it
    silently hands back the stale leaked job instead of running the new
    request, skipping the 70% completion gate entirely.
    """
    yield
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))
        conn.commit()
    from main import plan_jobs

    plan_jobs.clear()


@pytest.fixture
def client():
    """FastAPI TestClient. Imports main.app lazily so the DATABASE_URL/
    ENVIRONMENT env vars set by the root conftest.py are always in place
    before main.py -- and everything it imports -- gets loaded."""
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Authenticates via /api/auth/mock-login (only registered when
    ENVIRONMENT != production, which the root conftest.py guarantees) and
    returns both the Authorization header and the created user's id."""
    resp = client.post("/api/auth/mock-login", json={"email": "test-runner@uphill.ai"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['session_token']}"},
        "user_id": data["user"]["id"],
    }


@pytest.fixture
def mock_gemini():
    """Patches the real, shared google.genai module object.

    Gemini is imported as `from google import genai` locally in multiple
    files (main.py, services/plan_generator.py, services/knowledge_extractor.py).
    All of those bindings resolve to the
    same sys.modules entry, so patching the attribute on the real module is
    the one mock target that's reliable regardless of which file does the
    importing.
    """
    from unittest.mock import MagicMock, patch

    fake_response = MagicMock()
    fake_response.text = "[]"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("google.genai.Client", return_value=fake_client) as mock_cls:
        yield mock_cls, fake_client


@pytest.fixture
def mock_plan_generation():
    """Neutralizes PlanGenerator.generate_plan_workouts for the ENTIRE test,
    not just the initiating POST request.

    Both /api/auth/onboarding and /api/coach/generate-plan commit the plans
    row synchronously, then fire actual workout generation via
    asyncio.create_task -- a fire-and-forget background task that is not
    awaited by the endpoint. A TestClient request returns as soon as the
    response is ready, which does not guarantee the background task has run
    yet. If a test only patches generate_plan_workouts inside a `with`
    block scoped to the POST call (and exits that block right after), the
    background task can end up executing AFTER the patch has already been
    undone -- silently falling through to a real Gemini network call. Scoping the patch to this fixture's full lifetime (active for the
    whole test function, including any later polling calls) avoids that.
    """
    from unittest.mock import AsyncMock, patch

    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=([], "recreational"),
    ) as mock_fn:
        yield mock_fn


@pytest.fixture
def mock_single_workout_generation():
    """Neutralizes PlanGenerator.generate_single_workout (the AI co-create
    path) -- unlike generate_plan_workouts, this one is awaited directly in
    the request handler, so no fire-and-forget background-task concern."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "services.plan_generator.PlanGenerator.generate_single_workout",
        new_callable=AsyncMock,
        return_value={
            "week_number": 1,
            "day_of_week": "Wednesday",
            "phase": "Training",
            "title": "Rolling Tempo",
            "type": "Tempo",
            "duration_minutes": 40,
            "distance_km": 7.0,
            "target_zone": "Zone 3",
            "target_hr_range": "150-160 bpm",
            "target_pace": "5:30 - 5:10 /km",
            "description": "Warm up, then 25 min steady at Zone 3, cool down.",
            "fueling_tip": None,
            "session_slot": "main",
        },
    ) as mock_fn:
        yield mock_fn

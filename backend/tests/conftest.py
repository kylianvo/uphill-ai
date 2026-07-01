"""Shared fixtures for the backend test suite.

IMPORTANT ORDERING CONSTRAINT: backend/config.py builds its `settings`
singleton at import time by reading os.getenv(...), and backend/db.py
builds its SQLAlchemy `engine` at import time from settings.DATABASE_URL.
backend/main.py also computes `_is_prod` (which gates whether
POST /api/auth/mock-login is even registered) at import time from
os.getenv("ENVIRONMENT"). So the env vars below MUST be set before
anything imports `db` or `main` -- which is why this happens at module
scope, at the very top of conftest.py, before any project import.
"""

import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test",
)
os.environ.setdefault("ENVIRONMENT", "development")  # required for /api/auth/mock-login to be registered
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod")

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from db import engine, init_db  # noqa: E402

# Truncated in child-first order isn't strictly required (CASCADE handles FK
# dependencies), but listed here for readability of the dependency graph.
ALL_TABLES = [
    "block_reviews",
    "knowledge_cards",
    "workout_types",
    "shoes",
    "analytics_events",
    "nutrition_products",
    "workouts",
    "plans",
    "sessions",
    "sources",
    "users",
]


@pytest.fixture(scope="session", autouse=True)
def _init_test_database():
    """Creates the schema once per test session against uphill_ai_test."""
    init_db()
    yield


@pytest.fixture(autouse=True)
def _truncate_tables():
    """Truncates all tables between tests for isolation.

    db.py opens a fresh engine.connect() + explicit conn.commit() per call
    (not one connection/transaction per request), so per-test transaction
    rollback isn't viable here -- truncate-between-tests is the pragmatic
    equivalent. Consequence: tests must not depend on execution order or on
    rows left behind by another test.
    """
    yield
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {', '.join(ALL_TABLES)} RESTART IDENTITY CASCADE"))
        conn.commit()


@pytest.fixture
def client():
    """FastAPI TestClient. Imports main.app lazily so the DATABASE_URL/
    ENVIRONMENT env vars set above are always in place before main.py --
    and everything it imports -- gets loaded."""
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Authenticates via /api/auth/mock-login (only registered when
    ENVIRONMENT != production, which conftest guarantees above) and returns
    both the Authorization header and the created user's id."""
    resp = client.post("/api/auth/mock-login", json={"email": "test-runner@uphill.ai"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['session_token']}"},
        "user_id": data["user"]["id"],
    }


@pytest.fixture
def mock_gemini():
    """Patches the real, shared google.generativeai module object.

    Gemini is imported as `import google.generativeai as genai` locally in
    multiple files (main.py, services/plan_generator.py,
    services/knowledge_extractor.py, services/workout_type_extractor.py).
    All of those bindings resolve to the same sys.modules entry, so patching
    the attribute on the real module is the one mock target that's reliable
    regardless of which file does the importing.
    """
    from unittest.mock import MagicMock, patch

    fake_response = MagicMock()
    fake_response.text = "[]"
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    with (
        patch("google.generativeai.GenerativeModel", return_value=fake_model) as mock_cls,
        patch("google.generativeai.configure"),
    ):
        yield mock_cls, fake_model


@pytest.fixture
def mock_notebooklm():
    """Forces PlanGenerator's NotebookLM call to fail, which sends it down
    the Gemini fallback path deterministically (see
    services/plan_generator.py's NotebookLM-then-Gemini flow)."""
    from unittest.mock import patch

    with patch(
        "services.notebooklm_service.NotebookLmService.query_notebook",
        side_effect=Exception("NotebookLM disabled in tests"),
    ) as mock_query:
        yield mock_query


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
    undone -- silently falling through to a real Gemini/NotebookLM network
    call. Scoping the patch to this fixture's full lifetime (active for the
    whole test function, including any later polling calls) avoids that.
    """
    from unittest.mock import AsyncMock, patch

    with patch(
        "services.plan_generator.PlanGenerator.generate_plan_workouts",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fn:
        yield mock_fn

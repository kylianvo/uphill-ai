"""Session-wide setup shared by unit AND integration tests.

IMPORTANT ORDERING CONSTRAINT: backend/config.py builds its `settings`
singleton at import time by reading os.getenv(...), and backend/db.py
builds its SQLAlchemy `engine` at import time from settings.DATABASE_URL.
backend/main.py also computes `_is_prod` (which gates whether
POST /api/auth/mock-login is even registered) at import time from
os.getenv("ENVIRONMENT"). So the env vars below MUST be set before
anything imports `db` or `main` -- which is why this happens at module
scope, at the very top of the ROOT conftest.py (root conftest.py always
loads before any test module in the session is collected, regardless of
whether pytest collects tests/unit/ or tests/integration/ first).

Deliberately does NOT define DB-touching fixtures here (schema creation,
truncation, TestClient, auth) -- those live in tests/integration/conftest.py
only, so tests/unit/ never needs a live Postgres connection. That's what
makes tests/unit/ safe to run in the pre-commit hook with no DB available.
"""

import os

# setdefault (not a plain assignment): if something already exported
# DATABASE_URL before pytest started -- CI's backend-tests.yml, or
# deploy_server.sh's preflight step -- that value must win. Only fall back
# to this default for a bare local `pytest` invocation with nothing set.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://uphill:uphill_secret@localhost:5433/uphill_ai_test",
)
os.environ.setdefault("ENVIRONMENT", "development")  # required for /api/auth/mock-login to be registered
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod")

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
os.environ.setdefault("RACE_HISTORY_WORKER_ENABLED", "false")
os.environ.setdefault("GOAL_ASSESS_ON_PLAN_CREATE", "false")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-prod")

import logging
import uuid

import pytest

import log_utils

_orig_get_logger = log_utils.get_logger


def _test_get_logger(name: str) -> logging.Logger:
    logger = _orig_get_logger(name)
    logger.propagate = True
    return logger


log_utils.get_logger = _test_get_logger


@pytest.fixture
def langfuse_spans(monkeypatch):
    """Enables services.observability against an in-memory OTel exporter -- no network.
    Yields the exporter; call observability.flush() before reading get_finished_spans().

    Each test gets a fresh public key: Langfuse caches its resource manager per key, so
    reusing one would silently keep the previous test's exporter."""
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from config import settings
    from services import observability

    previous_client, observability._client = observability._client, None
    previous_init_failed, observability._init_failed = observability._init_failed, False
    fixture_client = None
    try:
        exporter = InMemorySpanExporter()
        monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", f"pk-lf-test-{uuid.uuid4().hex}")
        monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-test")
        monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "test-salt")
        monkeypatch.setattr(settings, "LANGFUSE_BASE_URL", "http://127.0.0.1:9")
        try:
            observability.init(span_exporter=exporter)
        finally:
            fixture_client = observability._client
        assert observability.enabled(), "observability.init() did not enable with test keys"
        yield exporter
    finally:
        try:
            try:
                GoogleGenAIInstrumentor().uninstrument()
            finally:
                LangChainInstrumentor().uninstrument()
        finally:
            try:
                if fixture_client is not None and fixture_client is not previous_client:
                    fixture_client.shutdown()
            finally:
                observability._client = previous_client
                observability._init_failed = previous_init_failed

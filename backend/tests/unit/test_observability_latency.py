"""A Langfuse endpoint that accepts connections and never answers must not slow traced
work down, and flush() must return within the export timeout. A blocking export would
take at least LANGFUSE_TIMEOUT (2 s here) per batch."""

import socket
import time
import uuid

import pytest

from config import settings
from services import observability as obs


@pytest.fixture
def silent_endpoint():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(64)
    yield f"http://127.0.0.1:{server.getsockname()[1]}"
    server.close()


def test_unresponsive_exporter_adds_no_request_latency(monkeypatch, silent_endpoint):
    from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

    monkeypatch.setattr(settings, "LANGFUSE_PUBLIC_KEY", f"pk-lf-latency-{uuid.uuid4().hex}")
    monkeypatch.setattr(settings, "LANGFUSE_SECRET_KEY", "sk-lf-latency")
    monkeypatch.setattr(settings, "OBSERVABILITY_ID_SALT", "latency-salt")
    monkeypatch.setattr(settings, "LANGFUSE_BASE_URL", silent_endpoint)
    monkeypatch.setattr(settings, "LANGFUSE_TIMEOUT", 2)
    obs._client = None
    obs.init()
    assert obs.enabled()
    try:
        started = time.perf_counter()
        for turn in range(50):
            with obs.trace("latency.turn", feature="coach_chat", user_id=turn):
                with obs.span("inner") as inner:
                    inner.set(retrieval_k=turn)
        traced_seconds = time.perf_counter() - started

        flush_started = time.perf_counter()
        obs.flush()
        flush_seconds = time.perf_counter() - flush_started
    finally:
        GoogleGenAIInstrumentor().uninstrument()
        client, obs._client = obs._client, None
        client.shutdown()

    assert traced_seconds < 0.5, f"50 traced turns took {traced_seconds:.2f}s: export is on the request path"
    assert flush_seconds < settings.LANGFUSE_TIMEOUT + 1, f"flush blocked {flush_seconds:.2f}s"

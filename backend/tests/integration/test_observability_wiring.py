"""The app lifecycle is the contract here: init() once at startup, flush() once at
shutdown -- otherwise traces are never enabled, or the last batch is lost on deploy."""

from fastapi.testclient import TestClient

from services import observability


def test_startup_initialises_and_shutdown_flushes(monkeypatch):
    calls = []
    monkeypatch.setattr(observability, "init", lambda **kwargs: calls.append("init"))
    monkeypatch.setattr(observability, "flush", lambda: calls.append("flush"))
    from main import app

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert calls == ["init"]

    assert calls == ["init", "flush"]

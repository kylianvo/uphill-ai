import pytest

from dev import studio_factory as sf


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://u:p@localhost:5432/uphill_ai",
        "postgresql://u:p@127.0.0.1:15433/uphill_ai",
        "postgresql://u:p@db:5432/uphill_ai",
    ],
)
def test_local_database_passes(url):
    sf.assert_local_dev("development", url)


def test_production_environment_is_refused():
    with pytest.raises(RuntimeError, match="production"):
        sf.assert_local_dev("production", "postgresql://u:p@localhost:5432/x")


@pytest.mark.parametrize(
    "url",
    ["postgresql://u:p@45.119.215.120:5434/uphill_ai", "postgresql://u:p@staging-db.internal/uphill_ai"],
)
def test_remote_database_is_refused(url):
    with pytest.raises(RuntimeError, match="local"):
        sf.assert_local_dev("development", url)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://u:p@localhost/db?host=45.119.215.120",
        "postgresql://u:p@localhost/db?hostaddr=45.119.215.120",
        "postgresql://u:p@localhost/db?service=x",
    ],
)
def test_query_param_host_bypass_is_refused(url):
    with pytest.raises(RuntimeError):
        sf.assert_local_dev("development", url)


def test_staging_environment_is_refused():
    with pytest.raises(RuntimeError, match="ENVIRONMENT"):
        sf.assert_local_dev("staging", "postgresql://u:p@localhost:5432/uphill_ai")


def test_empty_environment_is_refused():
    with pytest.raises(RuntimeError, match="ENVIRONMENT"):
        sf.assert_local_dev("", "postgresql://u:p@localhost:5432/uphill_ai")


def test_studio_user_id_is_required():
    with pytest.raises(RuntimeError, match="STUDIO_USER_ID"):
        sf.load_studio_user_id({})


def test_studio_user_id_must_exist(monkeypatch):
    monkeypatch.setattr(sf.db, "get_user_by_id", lambda uid: None)
    with pytest.raises(RuntimeError, match="does not exist"):
        sf.load_studio_user_id({"STUDIO_USER_ID": "42"})


def test_studio_user_id_parses(monkeypatch):
    monkeypatch.setattr(sf.db, "get_user_by_id", lambda uid: {"id": uid})
    assert sf.load_studio_user_id({"STUDIO_USER_ID": "42"}) == 42


def test_graph_has_prepare_and_coach_subgraph():
    graph = sf.build_studio_graph(1, real_model=False)
    nodes = set(graph.get_graph().nodes)
    assert {"prepare", "coach"} <= nodes
    xray_nodes = set(graph.get_graph(xray=True).nodes)
    # the embedded coach graph's own nodes are visible when expanded
    assert any(n.endswith("generate") for n in xray_nodes)
    assert any(n.endswith("tools") for n in xray_nodes)


@pytest.mark.asyncio
async def test_fake_run_executes_one_tool_then_replies(monkeypatch):
    monkeypatch.setattr(sf.db, "get_or_create_chat_thread", lambda uid: {"id": 7, "summary": None})
    monkeypatch.setattr(sf.coach_context, "build_chat_context", lambda **kw: {"athlete": {}, "history": []})
    # get_week runs for real against db.get_active_plan -- stub it to "no plan"
    monkeypatch.setattr("db.get_active_plan", lambda uid: None)

    graph = sf.build_studio_graph(1, real_model=False)
    for _ in range(2):  # the cycling fake model must work on repeated Studio runs
        out = await graph.ainvoke({"question": "What's my week?", "lang": "en"})
        assert out["reply_text"]
        assert len(out["tool_history"]) == 1
        assert out["tool_history"][0]["name"] == "get_week"


@pytest.mark.asyncio
async def test_cancelled_run_does_not_desync_cycling_fake_model(monkeypatch):
    """A run cancelled after only the tool-call round leaves the fake model's
    _cursor at 1, not 0 or back-to-len(responses). The prepare node must reset
    it to 0 so the next run still starts with the tool call instead of jumping
    straight to the reply round."""
    monkeypatch.setattr(sf.db, "get_or_create_chat_thread", lambda uid: {"id": 7, "summary": None})
    monkeypatch.setattr(sf.coach_context, "build_chat_context", lambda **kw: {"athlete": {}, "history": []})
    monkeypatch.setattr("db.get_active_plan", lambda uid: None)

    created = {}
    orig_init = sf.CyclingFakeCoachModel.__init__

    def capturing_init(self):
        orig_init(self)
        created["model"] = self

    monkeypatch.setattr(sf.CyclingFakeCoachModel, "__init__", capturing_init)

    graph = sf.build_studio_graph(1, real_model=False)
    # Simulate a cancelled run that consumed only round 1 (the tool call).
    created["model"]._cursor = 1

    out = await graph.ainvoke({"question": "What's my week?", "lang": "en"})
    assert out["reply_text"]
    assert len(out["tool_history"]) == 1
    assert out["tool_history"][0]["name"] == "get_week"

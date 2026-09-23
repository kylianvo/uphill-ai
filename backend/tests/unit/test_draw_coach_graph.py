from scripts.draw_coach_graph import render_mermaid


def test_diagram_with_tools_has_every_node_and_the_tool_loop():
    out = render_mermaid(with_tools=True)
    for node in ("retrieve", "generate", "tools", "final_generate"):
        assert node in out
    # conditional edges out of generate are drawn dotted in LangGraph's mermaid
    assert "generate -.->" in out


def test_diagram_without_tools_is_linear():
    out = render_mermaid(with_tools=False)
    assert "retrieve" in out and "generate" in out
    assert "tools" not in out
    assert "final_generate" not in out


def test_render_touches_no_database(monkeypatch):
    import db

    def _boom(*a, **k):
        raise AssertionError("diagram rendering must not hit the DB")

    monkeypatch.setattr(db.engine, "connect", _boom)
    assert "generate" in render_mermaid(with_tools=True)

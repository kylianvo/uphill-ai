import json

from services.kb_context import render_catalog_context, render_principles_context


def test_render_catalog_context_embeds_payload_and_title():
    chunks = [
        {"title": "Speedgoat 7", "payload": {"brand": "Hoka", "price": "$155"}},
        {"title": "Genesis", "payload": '{"brand": "Salomon"}'},  # payload may arrive as JSON string
    ]
    block = render_catalog_context(chunks, "gear")
    assert "GEAR KNOWLEDGE BASE" in block
    assert "recommend ONLY from these" in block
    # Every item is present as one JSON entry with name + payload merged
    payload_lines = [line for line in block.splitlines() if line.startswith("{")]
    items = [json.loads(line) for line in payload_lines]
    assert {"name": "Speedgoat 7", "brand": "Hoka", "price": "$155"} in items
    assert {"name": "Genesis", "brand": "Salomon"} in items


def test_render_catalog_context_empty():
    assert render_catalog_context([], "gear") == ""


def test_render_principles_context():
    chunks = [{"title": "ME circuits", "content": "One pass per exercise, 6-8 rounds."}]
    block = render_principles_context(chunks, heading="UPHILL ATHLETE PHILOSOPHY")
    assert "UPHILL ATHLETE PHILOSOPHY" in block
    assert "[ME circuits]" in block
    assert "6-8 rounds" in block
    assert render_principles_context([]) == ""


def test_find_uncatalogued_flags_unknown_products():
    from services.kb_context import find_uncatalogued

    catalog = ["Hoka Speedgoat 7", "Salomon Genesis"]
    recs = [
        {"brand": "Hoka", "model": "Speedgoat 7"},  # exact — ok
        {"brand": "Salomon", "name": "Genesis"},  # name key variant — ok
        {"brand": "Nike", "model": "Imaginary Trail 9"},  # hallucinated
    ]
    missing = find_uncatalogued(recs, catalog)
    assert missing == ["nike imaginary trail 9"]
    assert find_uncatalogued([], catalog) == []

from sqlalchemy import text

from db import engine


def test_exact_card_does_not_substitute_language(client, auth_headers):
    with engine.begin() as conn:
        card = conn.execute(
            text(
                "INSERT INTO knowledge_cards(chapter_title,summary,lang,key_points,tags,topic) VALUES('Original','Text','en','[]','[]','Training') RETURNING id"
            )
        ).scalar()
    assert client.get(f"/api/knowledge/cards/{card}?lang=vi", headers=auth_headers["headers"]).status_code == 404
    assert (
        client.get(f"/api/knowledge/cards/{card}?lang=en", headers=auth_headers["headers"]).json()["chapter_title"]
        == "Original"
    )
    path = f"/api/knowledge/cards/{card}/opened?lang=en"
    assert client.post(path, headers=auth_headers["headers"]).status_code == 200
    assert client.post(path, headers=auth_headers["headers"]).status_code == 200
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM notification_knowledge_opens")).scalar() == 1

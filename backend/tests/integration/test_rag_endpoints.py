"""Integration tests for RAG source endpoints.

Network calls (RagService.scrape_web_url / get_youtube_transcript) are
mocked at the service-method level rather than mocking httpx globally, to
keep these tests fast and decoupled from RagService's internals.
"""

from unittest.mock import patch


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


class TestListSources:
    def test_returns_empty_list_when_no_sources_exist(self, client, auth_headers):
        resp = client.get("/api/rag/sources", headers=auth_headers["headers"])
        assert resp.status_code == 200
        assert resp.json() == []

    def test_non_admin_can_still_list_sources(self, client, auth_headers):
        # Reading sources doesn't require admin -- only mutating them does.
        resp = client.get("/api/rag/sources", headers=auth_headers["headers"])
        assert resp.status_code == 200


class TestIngestLink:
    def test_admin_can_ingest_a_web_url(self, client):
        admin_headers = _admin_headers(client)
        with patch(
            "services.rag_service.RagService.scrape_web_url",
            return_value={
                "title": "Example Article",
                "content": "some scraped text",
                "url_path": "https://example.com",
            },
        ):
            resp = client.post("/api/rag/link", headers=admin_headers, json={"url": "https://example.com/article"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["type"] == "url"
        assert resp.json()["title"] == "Example Article"

    def test_admin_can_ingest_a_youtube_link(self, client):
        admin_headers = _admin_headers(client)
        with patch(
            "services.rag_service.RagService.get_youtube_transcript",
            return_value={
                "title": "A Talk",
                "content": "transcript text",
                "url_path": "https://youtube.com/watch?v=abc",
            },
        ):
            resp = client.post("/api/rag/link", headers=admin_headers, json={"url": "https://youtube.com/watch?v=abc"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["type"] == "youtube"

    def test_non_admin_cannot_ingest_a_link(self, client, auth_headers):
        resp = client.post(
            "/api/rag/link", headers=auth_headers["headers"], json={"url": "https://example.com/article"}
        )
        assert resp.status_code == 403

    def test_scrape_failure_returns_400(self, client):
        admin_headers = _admin_headers(client)
        with patch(
            "services.rag_service.RagService.scrape_web_url",
            side_effect=ValueError("could not fetch that page"),
        ):
            resp = client.post("/api/rag/link", headers=admin_headers, json={"url": "https://example.com/unreachable"})
        assert resp.status_code == 400


class TestDeleteSource:
    def test_non_admin_cannot_delete_a_source(self, client, auth_headers):
        resp = client.delete("/api/rag/sources/1", headers=auth_headers["headers"])
        assert resp.status_code == 403

    def test_deleting_a_nonexistent_source_returns_404(self, client):
        admin_headers = _admin_headers(client)
        resp = client.delete("/api/rag/sources/999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_admin_can_delete_an_ingested_source(self, client):
        admin_headers = _admin_headers(client)
        with patch(
            "services.rag_service.RagService.scrape_web_url",
            return_value={"title": "To Delete", "content": "text", "url_path": "https://example.com"},
        ):
            create_resp = client.post(
                "/api/rag/link", headers=admin_headers, json={"url": "https://example.com/to-delete"}
            )
        source_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/rag/sources/{source_id}", headers=admin_headers)
        assert delete_resp.status_code == 200

        sources = client.get("/api/rag/sources", headers=admin_headers).json()
        assert all(s["id"] != source_id for s in sources)

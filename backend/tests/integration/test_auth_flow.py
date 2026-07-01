"""Integration tests for register/login/mock-login/me/logout.

Playwright e2e tests will depend on mock-login working exactly like this, so
covering it here is cheap insurance against a regression surfacing first in
a much slower e2e run.
"""


class TestRegister:
    def test_register_creates_a_session_and_user(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"name": "Ada Athlete", "email": "ada@uphill.ai", "password": "correcthorse"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["user"]["email"] == "ada@uphill.ai"
        assert data["user"]["name"] == "Ada Athlete"
        assert data["session_token"]

    def test_duplicate_email_is_rejected(self, client):
        payload = {"name": "Ada Athlete", "email": "dupe@uphill.ai", "password": "correcthorse"}
        first = client.post("/api/auth/register", json=payload)
        assert first.status_code == 200

        second = client.post("/api/auth/register", json=payload)
        assert second.status_code == 409

    def test_short_password_is_rejected(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"name": "Ada Athlete", "email": "shortpw@uphill.ai", "password": "short"},
        )
        assert resp.status_code == 400


class TestLogin:
    def test_correct_credentials_log_in(self, client):
        client.post(
            "/api/auth/register",
            json={"name": "Login Tester", "email": "login-test@uphill.ai", "password": "correcthorse"},
        )
        resp = client.post("/api/auth/login", json={"email": "login-test@uphill.ai", "password": "correcthorse"})
        assert resp.status_code == 200
        assert resp.json()["session_token"]

    def test_wrong_password_is_rejected(self, client):
        client.post(
            "/api/auth/register",
            json={"name": "Login Tester", "email": "wrong-pw@uphill.ai", "password": "correcthorse"},
        )
        resp = client.post("/api/auth/login", json={"email": "wrong-pw@uphill.ai", "password": "wrong-password"})
        assert resp.status_code == 401

    def test_unknown_email_is_rejected(self, client):
        resp = client.post("/api/auth/login", json={"email": "nobody@uphill.ai", "password": "whatever123"})
        assert resp.status_code == 401


class TestMockLogin:
    def test_creates_a_new_user_on_first_call(self, client):
        resp = client.post("/api/auth/mock-login", json={"email": "fresh-mock@uphill.ai"})
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "fresh-mock@uphill.ai"

    def test_reuses_the_same_user_on_second_call(self, client):
        first = client.post("/api/auth/mock-login", json={"email": "repeat-mock@uphill.ai"})
        second = client.post("/api/auth/mock-login", json={"email": "repeat-mock@uphill.ai"})
        assert first.json()["user"]["id"] == second.json()["user"]["id"]


class TestMeAndLogout:
    def test_me_returns_the_authenticated_user(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"] == auth_headers["user_id"]

    def test_me_without_a_token_is_rejected(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    def test_logout_invalidates_the_session(self, client, auth_headers):
        logout_resp = client.post("/api/auth/logout", headers=auth_headers["headers"])
        assert logout_resp.status_code == 200

        me_resp = client.get("/api/auth/me", headers=auth_headers["headers"])
        assert me_resp.status_code in (401, 403)

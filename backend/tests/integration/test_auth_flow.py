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


class TestSessionLifetime:
    """Sessions slide: a returning athlete stays logged in as long as they
    open the app within JWT_EXPIRE_DAYS of their last visit."""

    def _expires_at(self, token):
        from sqlalchemy import text

        from db import engine

        with engine.connect() as conn:
            return conn.execute(
                text("SELECT expires_at FROM sessions WHERE session_token = :t"), {"t": token}
            ).scalar_one()

    def _set_expires_in(self, token, days):
        from sqlalchemy import text

        from db import engine

        with engine.connect() as conn:
            conn.execute(
                text("UPDATE sessions SET expires_at = NOW() + make_interval(days => :d) WHERE session_token = :t"),
                {"d": days, "t": token},
            )
            conn.commit()

    def test_new_session_lasts_jwt_expire_days(self, client, auth_headers):
        import datetime

        from config import settings

        token = auth_headers["headers"]["Authorization"].split(" ", 1)[1]
        remaining = self._expires_at(token) - datetime.datetime.now(datetime.UTC)
        assert remaining > datetime.timedelta(days=settings.JWT_EXPIRE_DAYS - 1)

    def test_using_an_aging_session_extends_it(self, client, auth_headers):
        import datetime

        from config import settings

        token = auth_headers["headers"]["Authorization"].split(" ", 1)[1]
        self._set_expires_in(token, 1)

        resp = client.get("/api/auth/me", headers=auth_headers["headers"])
        assert resp.status_code == 200

        remaining = self._expires_at(token) - datetime.datetime.now(datetime.UTC)
        assert remaining > datetime.timedelta(days=settings.JWT_EXPIRE_DAYS - 1)

    def test_a_session_past_its_jwt_exp_still_works_while_the_db_row_is_live(self, client):
        """Tokens minted before sliding sessions carry a 7-day JWT exp; the DB
        row is the source of truth, so extending it must keep them valid."""
        import datetime

        import jwt

        from config import settings
        from db import verify_session

        resp = client.post("/api/auth/mock-login", json={"email": "old-token@uphill.ai"})
        user_id = resp.json()["user"]["id"]
        past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
        old_token = jwt.encode(
            {"sub": str(user_id), "exp": past, "iat": past - datetime.timedelta(days=7), "jti": "old"},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        from sqlalchemy import text

        from db import engine

        with engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO sessions (session_token, user_id, expires_at) VALUES (:t, :u, NOW() + interval '1 day')"
                ),
                {"t": old_token, "u": user_id},
            )
            conn.commit()

        assert verify_session(old_token)["id"] == user_id

    def test_an_expired_db_row_is_rejected(self, client, auth_headers):
        token = auth_headers["headers"]["Authorization"].split(" ", 1)[1]
        self._set_expires_in(token, -1)
        resp = client.get("/api/auth/me", headers=auth_headers["headers"])
        assert resp.status_code == 401

    def test_a_forged_token_is_rejected(self, client, auth_headers):
        import jwt

        forged = jwt.encode({"sub": str(auth_headers["user_id"])}, "wrong-secret", algorithm="HS256")
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert resp.status_code == 401

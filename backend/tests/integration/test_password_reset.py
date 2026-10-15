"""Forgot-password / reset-password end to end against the scratch DB.

The email background task is replaced by a recorder, so each test can read
the code that would have been mailed."""

import pytest
from sqlalchemy import text

from db import engine

FORGOT = "/api/auth/forgot-password"
RESET = "/api/auth/reset-password"
GENERIC = "If an account exists for this email, we sent a code."


@pytest.fixture
def sent(client, monkeypatch):
    mails = []
    monkeypatch.setattr("main.send_password_reset_code", lambda to, code, lang: mails.append((to, code, lang)))
    return mails


def register(client, email, password="correcthorse"):
    resp = client.post("/api/auth/register", json={"name": "Reset Tester", "email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["session_token"]


def run_sql(sql):
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


def age_codes(minutes=2):
    run_sql(f"UPDATE password_reset_codes SET created_at = created_at - INTERVAL '{minutes} minutes'")


def test_unknown_email_gets_the_same_answer_and_no_mail(client, sent):
    resp = client.post(FORGOT, json={"email": "nobody@uphill.ai"})
    assert resp.status_code == 200
    assert resp.json() == {"message": GENERIC}
    assert sent == []


def test_known_email_gets_a_six_digit_code(client, sent):
    register(client, "known@uphill.ai")
    resp = client.post(FORGOT, json={"email": "known@uphill.ai", "lang": "vi"})
    assert resp.json() == {"message": GENERIC}
    [(to, code, lang)] = sent
    assert to == "known@uphill.ai" and lang == "vi"
    assert len(code) == 6 and code.isdigit()


def test_email_case_and_spaces_are_ignored(client, sent):
    register(client, "casey@uphill.ai")
    client.post(FORGOT, json={"email": "  CASEY@Uphill.ai "})
    [(to, code, _)] = sent
    assert to == "casey@uphill.ai"
    resp = client.post(RESET, json={"email": " Casey@UPHILL.ai", "code": code, "new_password": "newpassword1"})
    assert resp.status_code == 200, resp.text


def test_second_request_within_a_minute_sends_nothing(client, sent):
    register(client, "fast@uphill.ai")
    client.post(FORGOT, json={"email": "fast@uphill.ai"})
    resp = client.post(FORGOT, json={"email": "fast@uphill.ai"})
    assert resp.json() == {"message": GENERIC}
    assert len(sent) == 1


def test_sixth_request_in_an_hour_sends_nothing(client, sent):
    register(client, "many@uphill.ai")
    for _ in range(6):
        client.post(FORGOT, json={"email": "many@uphill.ai"})
        age_codes(2)
    assert len(sent) == 5


def test_new_request_keeps_the_earlier_code_valid(client, sent):
    # A stranger requesting codes for this email must not invalidate the one the owner is typing.
    register(client, "twice@uphill.ai")
    client.post(FORGOT, json={"email": "twice@uphill.ai"})
    age_codes(2)
    client.post(FORGOT, json={"email": "twice@uphill.ai"})
    old, new = sent[0][1], sent[1][1]
    good = client.post(RESET, json={"email": "twice@uphill.ai", "code": old, "new_password": "newpassword1"})
    assert good.status_code == 200
    if old != new:
        used = client.post(RESET, json={"email": "twice@uphill.ai", "code": new, "new_password": "newpassword2"})
        assert used.status_code == 400


def test_wrong_guesses_count_across_all_live_codes(client, sent):
    register(client, "budget@uphill.ai")
    client.post(FORGOT, json={"email": "budget@uphill.ai"})
    age_codes(2)
    client.post(FORGOT, json={"email": "budget@uphill.ai"})
    codes = {c for _, c, _ in sent}
    wrong = next(w for w in ("000000", "111111", "222222") if w not in codes)
    for _ in range(5):
        client.post(RESET, json={"email": "budget@uphill.ai", "code": wrong, "new_password": "newpassword1"})
    for code in codes:
        r = client.post(RESET, json={"email": "budget@uphill.ai", "code": code, "new_password": "newpassword1"})
        assert r.status_code == 400


def test_reset_signs_in_and_kills_old_sessions(client, sent):
    old_token = register(client, "reset@uphill.ai")
    client.post(FORGOT, json={"email": "reset@uphill.ai"})
    code = sent[0][1]

    resp = client.post(RESET, json={"email": "reset@uphill.ai", "code": code, "new_password": "brandnewpass"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["session_token"] and data["expires_at"]
    assert data["user"]["email"] == "reset@uphill.ai"

    old = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old.status_code == 401
    new = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['session_token']}"})
    assert new.status_code == 200

    assert (
        client.post("/api/auth/login", json={"email": "reset@uphill.ai", "password": "correcthorse"}).status_code == 401
    )
    assert (
        client.post("/api/auth/login", json={"email": "reset@uphill.ai", "password": "brandnewpass"}).status_code == 200
    )

    again = client.post(RESET, json={"email": "reset@uphill.ai", "code": code, "new_password": "anotherpass1"})
    assert again.status_code == 400
    assert again.json()["detail"] == "Invalid or expired code."


def test_five_wrong_guesses_kill_the_code(client, sent):
    register(client, "guess@uphill.ai")
    client.post(FORGOT, json={"email": "guess@uphill.ai"})
    code = sent[0][1]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        r = client.post(RESET, json={"email": "guess@uphill.ai", "code": wrong, "new_password": "newpassword1"})
        assert r.status_code == 400
    r = client.post(RESET, json={"email": "guess@uphill.ai", "code": code, "new_password": "newpassword1"})
    assert r.status_code == 400


def test_expired_code_is_rejected(client, sent):
    register(client, "late@uphill.ai")
    client.post(FORGOT, json={"email": "late@uphill.ai"})
    run_sql("UPDATE password_reset_codes SET expires_at = NOW() - INTERVAL '1 second'")
    r = client.post(RESET, json={"email": "late@uphill.ai", "code": sent[0][1], "new_password": "newpassword1"})
    assert r.status_code == 400


def test_short_password_is_rejected_without_using_the_code(client, sent):
    register(client, "short@uphill.ai")
    client.post(FORGOT, json={"email": "short@uphill.ai"})
    code = sent[0][1]
    r = client.post(RESET, json={"email": "short@uphill.ai", "code": code, "new_password": "short"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Password must be at least 8 characters."
    ok = client.post(RESET, json={"email": "short@uphill.ai", "code": code, "new_password": "longenough1"})
    assert ok.status_code == 200


def test_code_with_whitespace_works(client, sent):
    register(client, "space@uphill.ai")
    client.post(FORGOT, json={"email": "space@uphill.ai"})
    r = client.post(RESET, json={"email": "space@uphill.ai", "code": f" {sent[0][1]} ", "new_password": "newpassword1"})
    assert r.status_code == 200


def test_oauth_only_user_can_set_a_password(client, sent):
    register(client, "oauth@uphill.ai")
    run_sql("UPDATE users SET password_hash = NULL WHERE email = 'oauth@uphill.ai'")
    client.post(FORGOT, json={"email": "oauth@uphill.ai"})
    r = client.post(RESET, json={"email": "oauth@uphill.ai", "code": sent[0][1], "new_password": "firstpass1"})
    assert r.status_code == 200
    assert r.json()["user"]["has_password"] is True
    login = client.post("/api/auth/login", json={"email": "oauth@uphill.ai", "password": "firstpass1"})
    assert login.status_code == 200


def test_reset_for_unknown_email_is_generic(client):
    r = client.post(RESET, json={"email": "ghost@uphill.ai", "code": "123456", "new_password": "newpassword1"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid or expired code."

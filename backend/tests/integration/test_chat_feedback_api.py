"""Thumbs feedback on coach replies and the proposal-outcome score."""

import db
from services import observability
from tests.integration.test_proposal_apply_api import _apply, _proposal, _setup

TRACE_ID = "b" * 32


def _assistant_message(uid, trace_id=TRACE_ID):
    thread = db.get_or_create_chat_thread(uid)
    mid = db.append_chat_message(thread["id"], "assistant", "Easy run today.")
    db.update_chat_message(mid, trace_id=trace_id)
    return mid


def _record_scores(monkeypatch):
    calls = []
    monkeypatch.setattr(observability, "score", lambda **kw: calls.append(kw))
    return calls


def test_feedback_is_stored_and_mirrored_as_one_idempotent_score(client, auth_headers, monkeypatch):
    calls = _record_scores(monkeypatch)
    mid = _assistant_message(auth_headers["user_id"])

    for value in (1, -1):
        res = client.post(
            f"/api/coach/chat/messages/{mid}/feedback", headers=auth_headers["headers"], json={"value": value}
        )
        assert res.status_code == 200, res.text
        assert res.json() == {"message_id": mid, "feedback": value}

    assert db.get_chat_message(mid)["feedback"] == -1
    assert [c["value"] for c in calls] == [1, -1]
    assert {c["score_id"] for c in calls} == {f"thumbs-{mid}"}
    assert calls[0]["trace_id"] == TRACE_ID and calls[0]["name"] == "thumbs"


def test_feedback_rejects_invalid_values_and_other_users_messages(client, auth_headers, monkeypatch):
    _record_scores(monkeypatch)
    mid = _assistant_message(auth_headers["user_id"])
    bad = client.post(f"/api/coach/chat/messages/{mid}/feedback", headers=auth_headers["headers"], json={"value": 3})
    assert bad.status_code == 422

    other = db.create_user_with_password("other-feedback@example.com", "Other", "x")["id"]
    foreign = _assistant_message(other)
    res = client.post(
        f"/api/coach/chat/messages/{foreign}/feedback", headers=auth_headers["headers"], json={"value": 1}
    )
    assert res.status_code == 404
    assert db.get_chat_message(foreign)["feedback"] is None


def test_applying_a_proposal_scores_the_turn_that_proposed_it(client, auth_headers, monkeypatch):
    calls = _record_scores(monkeypatch)
    uid, plan_id, wid = _setup(auth_headers)
    pid = _proposal(uid, plan_id, wid)
    message_id = db.get_chat_proposal(pid)["message_id"]
    db.update_chat_message(message_id, trace_id=TRACE_ID)

    assert _apply(client, auth_headers, pid).status_code == 200

    assert calls == [{"trace_id": TRACE_ID, "name": "proposal_applied", "value": 1, "score_id": f"proposal-{pid}"}]

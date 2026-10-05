"""UTMB index from the athlete's own claim, with the runner mirror as fallback.
Scratch DB only; every runner here is synthetic."""

from sqlalchemy import text

import db
from db import engine


def _claim(uid, meta, external_id="https://utmb.world/runner/0000001.synthetic"):
    with engine.connect() as conn:
        conn.execute(
            text("""INSERT INTO race_profile_claims (user_id, source, external_id, display_name, meta)
                    VALUES (:u, 'utmb', :e, 'Synthetic Runner', CAST(:m AS jsonb))"""),
            {"u": uid, "e": external_id, "m": meta},
        )
        conn.commit()


def _user(email):
    with engine.connect() as conn:
        uid = conn.execute(
            text("INSERT INTO users (email, name) VALUES (:e, 'S') RETURNING id"), {"e": email}
        ).scalar_one()
        conn.commit()
    return uid


def test_general_index_comes_from_the_claim_meta():
    uid = _user("utmb1@test.io")
    _claim(uid, '{"indexes": [{"index": 610, "piCategory": "general"}, {"index": 620, "piCategory": "50k"}]}')
    assert db.get_utmb_index(uid) == 610


def test_falls_back_to_the_mirror_when_meta_has_no_general_index():
    uid = _user("utmb2@test.io")
    uri = "https://utmb.world/runner/0000002.synthetic"
    with engine.connect() as conn:
        conn.execute(
            text("""INSERT INTO utmb_runners (uri, full_name, name_norm, utmb_index)
                    VALUES (:u, 'Synthetic', 'synthetic', 480)"""),
            {"u": uri},
        )
        conn.commit()
    _claim(uid, '{"indexes": [{"index": null, "piCategory": "general"}]}', external_id=uri)
    assert db.get_utmb_index(uid) == 480


def test_a_malformed_meta_index_is_ignored_not_raised():
    uid = _user("utmb4@test.io")
    _claim(uid, '{"indexes": [{"index": "n/a", "piCategory": "general"}]}')
    assert db.get_utmb_index(uid) is None


def test_none_without_a_claim():
    assert db.get_utmb_index(_user("utmb3@test.io")) is None

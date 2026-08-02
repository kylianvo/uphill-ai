"""Unit tests for simulate_clickstream -- HTTP calls and the Postgres user pool
lookup are mocked, no live backend/DB needed."""

from unittest.mock import MagicMock, patch

from scripts.simulate_clickstream import _generate_event, run


def test_generate_event_produces_valid_event_shape():
    event, session_id, user_id, email = _generate_event(
        user_pool=[(1, "a@x.com"), (2, "b@x.com"), (3, "c@x.com")], session_ids={}
    )

    assert "event_name" in event
    assert "properties" in event
    assert "url" in event
    assert session_id
    assert user_id is None or user_id in [1, 2, 3]
    assert (user_id is None) == (email is None)


def test_run_sends_exactly_count_events():
    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {"session_token": "tok"}
    with (
        patch("scripts.simulate_clickstream.httpx.post", return_value=fake_response) as mock_post,
        patch(
            "scripts.simulate_clickstream._load_user_pool",
            return_value=[(1, "a@x.com"), (2, "b@x.com"), (3, "c@x.com")],
        ),
        patch("scripts.simulate_clickstream.time.sleep"),
    ):
        sent = run(rate=1000, duration=None, count=10, burst=True)

    assert sent == 10
    track_batch_calls = [c for c in mock_post.call_args_list if "track_batch" in c.args[0]]
    assert len(track_batch_calls) == 10


def test_run_counts_failures_separately_from_sent():
    fake_response = MagicMock(status_code=500, text="server error")
    with (
        patch("scripts.simulate_clickstream.httpx.post", return_value=fake_response) as mock_post,
        patch(
            "scripts.simulate_clickstream._load_user_pool",
            return_value=[(1, "a@x.com"), (2, "b@x.com"), (3, "c@x.com")],
        ),
        patch("scripts.simulate_clickstream.time.sleep"),
    ):
        sent = run(rate=1000, duration=None, count=5, burst=True)

    # every request "failed" (500), so nothing counted as sent, and the loop
    # must still terminate rather than retrying forever -- it terminates because
    # `count` bounds total attempts (sent + failed), not `sent` alone.
    assert sent == 0
    track_batch_calls = [c for c in mock_post.call_args_list if "track_batch" in c.args[0]]
    assert len(track_batch_calls) == 5


def test_run_attaches_authorization_header_for_attributed_events():
    login_response = MagicMock(status_code=200)
    login_response.json.return_value = {"session_token": "tok-123"}
    track_response = MagicMock(status_code=200)

    def fake_post(url, *args, **kwargs):
        if "mock-login" in url:
            return login_response
        return track_response

    with (
        patch("scripts.simulate_clickstream.httpx.post", side_effect=fake_post) as mock_post,
        patch("scripts.simulate_clickstream._load_user_pool", return_value=[(1, "a@x.com")]),
        patch("scripts.simulate_clickstream.random.random", return_value=0.9),  # force attributed (not anonymous)
        patch("scripts.simulate_clickstream.time.sleep"),
    ):
        sent = run(rate=1000, duration=None, count=1, burst=True)

    assert sent == 1
    track_batch_calls = [c for c in mock_post.call_args_list if "track_batch" in c.args[0]]
    assert len(track_batch_calls) == 1
    assert track_batch_calls[0].kwargs["headers"] == {"Authorization": "Bearer tok-123"}

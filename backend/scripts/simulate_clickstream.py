"""Generates realistic synthetic clickstream traffic and sends it through the
real POST /api/analytics/track_batch endpoint (exercises the actual
producer -> Kafka -> consumer -> Postgres path, not a shortcut). See
docs/superpowers/specs/2026-08-02-warehouse-dashboards-design.md for the full design.

Usage (from backend/, with the backend running):
    python scripts/simulate_clickstream.py --rate 5 --duration 60
    python scripts/simulate_clickstream.py --count 200 --burst
"""

import argparse
import os
import random
import sys
import time
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import text

from config import settings  # noqa: E402
from db import engine  # noqa: E402

EVENT_WEIGHTS = {
    "page_view": 50,
    "plan_viewed": 15,
    "workout_viewed": 15,
    "feature_used": 10,
    "plan_generated": 5,
    "workout_completed": 4,
    "gear_recommendation_viewed": 1,
}
URLS = ["/dashboard", "/plan", "/workouts", "/gear", "/nutrition", "/knowledge"]
ANONYMOUS_SESSION_RATIO = 0.3


def _load_user_pool(limit: int = 50) -> list[tuple[int, str]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, email FROM users ORDER BY random() LIMIT :limit"), {"limit": limit}
        ).fetchall()
    return [(row[0], row[1]) for row in rows]


def _mock_login_token(email: str) -> str | None:
    resp = httpx.post(f"{settings.API_BASE_URL}/api/auth/mock-login", json={"email": email})
    if resp.status_code != 200:
        print(f"  WARN: mock-login failed for {email} ({resp.status_code}): {resp.text[:200]}")
        return None
    return resp.json()["session_token"]


def _generate_event(
    user_pool: list[tuple[int, str]], session_ids: dict[int, str]
) -> tuple[dict, str, int | None, str | None]:
    is_anonymous = random.random() < ANONYMOUS_SESSION_RATIO or not user_pool
    event_name = random.choices(list(EVENT_WEIGHTS.keys()), weights=list(EVENT_WEIGHTS.values()), k=1)[0]
    event = {
        "event_name": event_name,
        "properties": {"simulated": True},
        "url": random.choice(URLS),
    }

    if is_anonymous:
        session_id = f"anon-{uuid.uuid4()}"
        return event, session_id, None, None

    user_id, email = random.choice(user_pool)
    session_id = session_ids.setdefault(user_id, f"user-{user_id}-{uuid.uuid4()}")
    return event, session_id, user_id, email


def run(rate: float, duration: float | None, count: int | None, burst: bool) -> int:
    user_pool = _load_user_pool()
    session_ids: dict[int, str] = {}
    tokens: dict[int, str] = {}
    sent = 0
    failed = 0
    start = time.time()

    while True:
        if count is not None and (sent + failed) >= count:
            break
        if duration is not None and (time.time() - start) >= duration:
            break

        event, session_id, user_id, email = _generate_event(user_pool, session_ids)

        headers = None
        if user_id is not None:
            if user_id not in tokens:
                token = _mock_login_token(email)
                if token is not None:
                    tokens[user_id] = token
            if user_id in tokens:
                headers = {"Authorization": f"Bearer {tokens[user_id]}"}

        resp = httpx.post(
            f"{settings.API_BASE_URL}/api/analytics/track_batch",
            json={"events": [event], "session_id": session_id},
            headers=headers,
        )
        if resp.status_code == 200:
            sent += 1
        else:
            failed += 1
            print(f"  WARN: event failed ({resp.status_code}): {resp.text[:200]}")

        if sent % 10 == 0 or (count is not None and sent == count):
            print(f"  sent={sent} failed={failed}")

        if not burst:
            time.sleep(1.0 / rate)

    print(f"Done: sent={sent} failed={failed}")
    return sent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=5.0, help="events/sec when not --burst")
    parser.add_argument("--duration", type=float, default=None, help="seconds to run")
    parser.add_argument("--count", type=int, default=None, help="total events to send")
    parser.add_argument("--burst", action="store_true", help="send as fast as possible instead of paced")
    args = parser.parse_args()

    if args.duration is None and args.count is None:
        parser.error("must specify --duration or --count")

    run(rate=args.rate, duration=args.duration, count=args.count, burst=args.burst)


if __name__ == "__main__":
    main()

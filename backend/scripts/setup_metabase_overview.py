"""Consolidates the most important cards from the 5 per-topic dashboards
(setup_metabase_dashboards.py) into a single "Overview" dashboard -- reuses
the existing cards by id (no query duplication), just places them together
in a compact 2-column grid. "Pipeline Health" is deliberately left as its
own separate dashboard: it's an ops/debugging view (is the DW pipeline
healthy), a different audience from the product-metrics overview here.

Requires setup_metabase_dashboards.py to have already run at least once
(the cards this script places must already exist).

Usage (from backend/):  python scripts/setup_metabase_overview.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402

from config import settings  # noqa: E402
from scripts.setup_metabase_dashboards import (  # noqa: E402
    _dashboard_card_ids,
    _ensure_dashboard,
    _existing_cards_by_name,
    _headers,
    _session_token,
)

httpx = httpx.Client(timeout=60.0)

OVERVIEW_NAME = "Overview"

# One card per topic area, picked for signal density -- not every card from
# the source dashboards. Coach-Assigned vs Self-Serve, Block Review RPE
# Distribution, and Top URLs stay drill-down-only in their original
# dashboards rather than crowding the top-level view.
OVERVIEW_CARDS = [
    "Daily Signups",
    "Activation Rate",
    "OAuth vs Email Signups",
    "Plans Created Per Day",
    "Generation Success Rate",
    "Median Days To First Plan",
    "Planned vs Completed Workouts Per Week",
    "Weekly Adherence Rate",
    "Events By Name",
    "Daily Active Sessions",
]


def _add_card_to_dashboard_at(token: str, dashboard_id: int, card_id: int, row: int, col: int, size_x: int) -> None:
    resp = httpx.get(f"{settings.METABASE_URL}/api/dashboard/{dashboard_id}", headers=_headers(token))
    resp.raise_for_status()
    existing_dashcards = resp.json().get("dashcards", [])

    new_dashcard = {
        "id": -1,
        "card_id": card_id,
        "row": row,
        "col": col,
        "size_x": size_x,
        "size_y": 4,
        "series": [],
        "parameter_mappings": [],
        "visualization_settings": {},
    }

    put_resp = httpx.put(
        f"{settings.METABASE_URL}/api/dashboard/{dashboard_id}",
        headers=_headers(token),
        json={"dashcards": existing_dashcards + [new_dashcard]},
    )
    if put_resp.status_code >= 400:
        print(f"PUT /api/dashboard/{dashboard_id} failed: {put_resp.status_code} {put_resp.text}")
    put_resp.raise_for_status()


def main():
    token = _session_token()
    dashboard_id = _ensure_dashboard(token, OVERVIEW_NAME)
    print(f"Dashboard '{OVERVIEW_NAME}' -> id {dashboard_id}")

    existing_cards = _existing_cards_by_name(token)
    placed_card_ids = _dashboard_card_ids(token, dashboard_id)

    missing = [name for name in OVERVIEW_CARDS if name not in existing_cards]
    if missing:
        sys.exit(f"Missing card(s), run setup_metabase_dashboards.py first: {missing}")

    # 2-column grid, 12/24 width each -- 5 rows for 10 cards.
    row = 0
    col = 0
    for name in OVERVIEW_CARDS:
        card_id = existing_cards[name]
        if card_id not in placed_card_ids:
            _add_card_to_dashboard_at(token, dashboard_id, card_id, row=row, col=col, size_x=12)
            placed_card_ids.add(card_id)
            print(f"  placed '{name}' (card id {card_id}) at row={row} col={col}")
        else:
            print(f"  '{name}' (card id {card_id}) already on dashboard, skipping")
        if col == 0:
            col = 12
        else:
            col = 0
            row += 4

    print(f"{settings.METABASE_URL}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()

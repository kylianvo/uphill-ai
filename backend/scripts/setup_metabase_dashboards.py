"""Provisions Metabase dashboards on top of the DuckDB warehouse via Metabase's
REST API -- idempotent, re-runnable. Requires the metabase-driver-init +
metabase Docker Compose services to already be up (see docker-compose.yml) and
a built warehouse (warehouse/uphill_dw.duckdb). See
docs/superpowers/specs/2026-08-02-warehouse-dashboards-design.md for the full design.

Usage (from backend/):  python scripts/setup_metabase_dashboards.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from config import settings  # noqa: E402

DB_NAME = "Warehouse (DuckDB)"
DUCKDB_FILE_PATH_IN_METABASE = "/warehouse/uphill_dw.duckdb"


def _session_token() -> str:
    """Bootstrap Metabase's first admin account if it hasn't been set up yet,
    then return a session token."""
    if not settings.METABASE_ADMIN_PASSWORD:
        sys.exit("METABASE_ADMIN_PASSWORD is not set -- add it to backend/.env")

    props = httpx.get(f"{settings.METABASE_URL}/api/session/properties").json()
    # Deviation from the brief: `setup-token` is present in the properties
    # response REGARDLESS of whether an admin already exists (verified live,
    # Metabase "latest" image, 2026-08) -- it is not itself a reliable signal
    # that setup hasn't run. `has-user-setup` is the correct flag to check.
    if props.get("setup-token") and not props.get("has-user-setup"):
        # Metabase's /api/setup response shape (verified live): the setup
        # call itself does NOT return a session id -- it returns the created
        # user object. A separate POST /api/session call (username/password)
        # is required to get the session token, same as the "already set up"
        # branch below.
        resp = httpx.post(
            f"{settings.METABASE_URL}/api/setup",
            json={
                "token": props["setup-token"],
                "user": {
                    "first_name": "Uphill",
                    "last_name": "Admin",
                    "email": settings.METABASE_ADMIN_EMAIL,
                    "password": settings.METABASE_ADMIN_PASSWORD,
                    "site_name": "Uphill AI",
                },
                "prefs": {"site_name": "Uphill AI", "site_locale": "en", "allow_tracking": False},
            },
        )
        if resp.status_code >= 400:
            print(f"/api/setup failed: {resp.status_code} {resp.text}")
        resp.raise_for_status()
        body = resp.json()
        if "id" in body:
            return body["id"]
        # Fall through to /api/session using the credentials we just created.

    resp = httpx.post(
        f"{settings.METABASE_URL}/api/session",
        json={"username": settings.METABASE_ADMIN_EMAIL, "password": settings.METABASE_ADMIN_PASSWORD},
    )
    if resp.status_code >= 400:
        print(f"/api/session failed: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()["id"]


def _headers(token: str) -> dict[str, str]:
    return {"X-Metabase-Session": token, "Content-Type": "application/json"}


def _ensure_database(token: str) -> int:
    """Return the DuckDB warehouse database's id, creating the connection if it
    doesn't already exist (idempotent -- safe to re-run)."""
    resp = httpx.get(f"{settings.METABASE_URL}/api/database", headers=_headers(token))
    resp.raise_for_status()
    for db in resp.json().get("data", []):
        if db["name"] == DB_NAME:
            return db["id"]

    resp = httpx.post(
        f"{settings.METABASE_URL}/api/database",
        headers=_headers(token),
        json={
            "engine": "duckdb",
            "name": DB_NAME,
            "details": {"database_file": DUCKDB_FILE_PATH_IN_METABASE, "read_only": True},
        },
    )
    if resp.status_code >= 400:
        print(f"/api/database create failed: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()["id"]


def _existing_cards_by_name(token: str) -> dict[str, int]:
    resp = httpx.get(f"{settings.METABASE_URL}/api/card", headers=_headers(token))
    resp.raise_for_status()
    body = resp.json()
    cards = body["data"] if isinstance(body, dict) else body
    return {c["name"]: c["id"] for c in cards}


def _create_card(token: str, database_id: int, name: str, sql: str, display: str) -> int:
    resp = httpx.post(
        f"{settings.METABASE_URL}/api/card",
        headers=_headers(token),
        json={
            "name": name,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql},
                "database": database_id,
            },
            "display": display,
            "visualization_settings": {},
        },
    )
    if resp.status_code >= 400:
        print(f"/api/card create failed for '{name}': {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()["id"]


def _ensure_dashboard(token: str, name: str) -> int:
    resp = httpx.get(f"{settings.METABASE_URL}/api/dashboard", headers=_headers(token))
    resp.raise_for_status()
    for dash in resp.json():
        if dash["name"] == name:
            return dash["id"]

    resp = httpx.post(
        f"{settings.METABASE_URL}/api/dashboard",
        headers=_headers(token),
        json={"name": name},
    )
    if resp.status_code >= 400:
        print(f"/api/dashboard create failed for '{name}': {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()["id"]


def _dashboard_card_ids(token: str, dashboard_id: int) -> set:
    """Return the set of card ids already placed on this dashboard, keyed by
    card_id (used to make card *placement* idempotent -- re-running the
    script must not add a second dashcard for the same card)."""
    resp = httpx.get(f"{settings.METABASE_URL}/api/dashboard/{dashboard_id}", headers=_headers(token))
    resp.raise_for_status()
    body = resp.json()
    dashcards = body.get("dashcards", [])
    return {dc.get("card_id") for dc in dashcards if dc.get("card_id") is not None}


def _add_card_to_dashboard(token: str, dashboard_id: int, card_id: int, row: int, col: int) -> None:
    # Deviation from the brief's sample: modern Metabase (verified live,
    # 2026-08) does not expose POST /api/dashboard/{id}/cards +
    # PUT /api/dashboard/{id}/cards for placing cards. The working endpoint is
    # PUT /api/dashboard/{id} with a full `dashcards` array in the body (each
    # entry needs a client-side negative `id` for new cards, per Metabase's
    # "new dashcard" convention). GET /api/dashboard/{id} returns the current
    # `dashcards` list, which must be included verbatim (existing cards) plus
    # the new entry, or previously-placed cards get wiped from the dashboard.
    resp = httpx.get(f"{settings.METABASE_URL}/api/dashboard/{dashboard_id}", headers=_headers(token))
    resp.raise_for_status()
    body = resp.json()
    existing_dashcards = body.get("dashcards", [])

    new_dashcard = {
        "id": -1,
        "card_id": card_id,
        "row": row,
        "col": col,
        "size_x": 6,
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


DASHBOARDS: list[dict] = [
    {
        "name": "User Growth & Activation",
        "cards": [
            (
                "Daily Signups",
                "select cast(created_at as date) as signup_date, count(*) as signups "
                "from marts.dim_user where is_current group by 1 order by 1",
                "line",
            ),
            (
                "OAuth vs Email Signups",
                "select provider, count(*) as users from marts.dim_user where is_current group by 1",
                "pie",
            ),
            (
                "Activation Rate",
                "select "
                "round(100.0 * count(distinct p.user_id) / nullif(count(distinct u.user_id), 0), 1) as activation_rate_pct "
                "from marts.dim_user u left join marts.dim_plan p on p.user_id = u.user_id where u.is_current",
                "scalar",
            ),
        ],
    },
    {
        "name": "Plan Generation Funnel",
        "cards": [
            (
                "Plans Created Per Day",
                "select date_key, count(*) as plans from marts.fct_plan_generation group by 1 order by 1",
                "line",
            ),
            (
                "Generation Success Rate",
                "select round(100.0 * avg(case when is_generation_success then 1.0 else 0 end), 1) as success_rate_pct "
                "from marts.fct_plan_generation",
                "scalar",
            ),
            (
                "Median Days To First Plan",
                "select median(days_to_first_plan) as median_days from marts.fct_plan_generation "
                "where days_to_first_plan is not null",
                "scalar",
            ),
            (
                "Coach-Assigned vs Self-Serve",
                "select p.is_coach_assigned, count(*) as plans "
                "from marts.fct_plan_generation f join marts.dim_plan p on p.plan_id = f.plan_id group by 1",
                "pie",
            ),
        ],
    },
    {
        "name": "Training Engagement",
        "cards": [
            (
                "Planned vs Completed Workouts Per Week",
                "select date_trunc('week', date_key) as week, count(*) as planned, "
                "sum(case when is_completed then 1 else 0 end) as completed "
                "from marts.fct_workout group by 1 order by 1",
                "line",
            ),
            (
                "Weekly Adherence Rate",
                "select date_trunc('week', date_key) as week, "
                "round(100.0 * sum(case when is_completed then 1 else 0 end) / nullif(count(*), 0), 1) as adherence_pct "
                "from marts.fct_workout group by 1 order by 1",
                "line",
            ),
            (
                "Block Review RPE Distribution",
                "select overall_rpe, count(*) as reviews from marts.fct_block_review "
                "where overall_rpe is not null group by 1 order by 1",
                "bar",
            ),
        ],
    },
    {
        "name": "Feature Adoption",
        "cards": [
            (
                "Events By Name",
                "select event_name, count(*) as events from marts.fct_analytics_event group by 1 order by 2 desc",
                "bar",
            ),
            (
                "Daily Active Sessions",
                "select date_key, count(distinct session_id) as active_sessions "
                "from marts.fct_analytics_event group by 1 order by 1",
                "line",
            ),
            (
                "Top URLs",
                "select url, count(*) as events from marts.fct_analytics_event "
                "where url is not null group by 1 order by 2 desc limit 20",
                "bar",
            ),
        ],
    },
    {
        "name": "Pipeline Health",
        "cards": [
            (
                "Last Run Status",
                "select status from meta.pipeline_runs order by run_timestamp desc limit 1",
                "scalar",
            ),
            (
                "Hours Since Last Successful Run",
                "select round(date_diff('minute', max(run_timestamp), current_timestamp) / 60.0, 1) as hours_since "
                "from meta.pipeline_runs where status = 'success'",
                "scalar",
            ),
            (
                "dbt Test Pass/Fail History",
                "select run_timestamp, dbt_tests_passed, dbt_tests_failed, dbt_tests_errored "
                "from meta.pipeline_runs order by run_timestamp",
                "line",
            ),
            (
                "Row Counts Per Run",
                "select run_timestamp, raw_row_counts from meta.pipeline_runs order by run_timestamp",
                "table",
            ),
        ],
    },
]


def main():
    token = _session_token()
    database_id = _ensure_database(token)
    print(f"Warehouse database id: {database_id}")

    for dashboard_def in DASHBOARDS:
        dashboard_id = _ensure_dashboard(token, dashboard_def["name"])
        print(f"Dashboard '{dashboard_def['name']}' -> id {dashboard_id}")

        existing_cards = _existing_cards_by_name(token)
        placed_card_ids = _dashboard_card_ids(token, dashboard_id)

        row = 0
        for name, sql, display in dashboard_def["cards"]:
            # Idempotent card creation: reuse an existing card with the same
            # name instead of creating a duplicate on re-run (deviation from
            # the brief, which noted _create_card is not idempotent -- fixed
            # here mirroring _ensure_database/_ensure_dashboard's pattern).
            if name in existing_cards:
                card_id = existing_cards[name]
                print(f"  card '{name}' already exists -> id {card_id}")
            else:
                card_id = _create_card(token, database_id, name, sql, display)
                existing_cards[name] = card_id
                print(f"  card '{name}' -> id {card_id}")

            if card_id not in placed_card_ids:
                _add_card_to_dashboard(token, dashboard_id, card_id, row=row, col=0)
                placed_card_ids.add(card_id)
            row += 4
        print(f"  {settings.METABASE_URL}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()

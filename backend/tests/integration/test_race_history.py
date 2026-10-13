from services.race_history import build_summary, prompt_summary


def _manual(client, headers, name="Mountain 50k"):
    response = client.post(
        "/api/race-history/results",
        headers=headers,
        json={
            "discipline": "trail",
            "race_name": name,
            "race_date": "2025-09-20",
            "distance_km": 50,
            "elevation_gain_m": 1500,
            "finish_time_sec": 22000,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_manual_result_is_owner_scoped_and_hidden_only_from_prompt(client, auth_headers):
    headers, user_id = auth_headers["headers"], auth_headers["user_id"]
    result = _manual(client, headers)
    hidden = client.patch(f"/api/race-history/results/{result['id']}", headers=headers, json={"hidden": True})
    assert hidden.status_code == 200
    assert build_summary(user_id)["longest_finish"]["id"] == result["id"]
    assert prompt_summary(user_id) == ""
    estimate = client.post(
        "/api/coach/goal-estimate",
        headers=headers,
        json={
            "distance_km": 50,
            "elevation_gain_m": 1500,
            "reference_result_id": result["id"],
        },
    )
    assert estimate.status_code == 200, estimate.text

    other = client.post("/api/auth/mock-login", json={"email": "another-runner@uphill.ai"}).json()
    other_headers = {"Authorization": f"Bearer {other['session_token']}"}
    assert (
        client.patch(
            f"/api/race-history/results/{result['id']}", headers=other_headers, json={"hidden": False}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/coach/goal-estimate",
            headers=other_headers,
            json={
                "distance_km": 50,
                "reference_result_id": result["id"],
            },
        ).status_code
        == 404
    )


def test_dnf_cannot_be_reference(client, auth_headers):
    response = client.post(
        "/api/race-history/results",
        headers=auth_headers["headers"],
        json={
            "discipline": "trail",
            "race_name": "DNF Race",
            "race_date": "2025-09-20",
            "distance_km": 50,
            "is_dnf": True,
        },
    )
    assert response.status_code == 200
    assert (
        client.post(
            "/api/coach/goal-estimate",
            headers=auth_headers["headers"],
            json={
                "distance_km": 50,
                "reference_result_id": response.json()["id"],
            },
        ).status_code
        == 404
    )


def test_vbm_selection_and_bib_evidence_survive_refresh(client, auth_headers, monkeypatch):
    from services import race_history

    parent = {
        "event": "FMM",
        "vbm_id": "SHARED RUNNER",
        "full_name": "SHARED RUNNER",
        "race_full_name": "TEST MARATHON 03/12/2023",
        "race_day": "2023-12-03",
        "mark": "03:39:14",
        "bib": "47107",
        "other_results_full": [
            {"race": "TEST MARATHON 03/12/2023", "time": "03:39:14", "bib": "47107"},
            {"race": "OTHER MARATHON 04/12/2022", "time": "03:42:00", "bib": "99999"},
        ],
    }
    monkeypatch.setattr(race_history, "_fetch", lambda *args, **kwargs: {"data": [parent]})
    headers = auth_headers["headers"]
    claim = client.post(
        "/api/race-history/claims", headers=headers, json={"source": "vbm", "external_id": "SHARED RUNNER"}
    ).json()
    assert race_history.sync_claim(claim["id"]) == 2
    results = client.get("/api/race-history", headers=headers).json()["results"]
    assert len(results) == 2 and all(not row["selected"] for row in results)
    selected = next(row for row in results if row["bib"] == "47107")
    assert (
        client.patch(
            f"/api/race-history/results/{selected['id']}", headers=headers, json={"selected": True}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/race-history/claims/{claim['id']}/verify-bib", headers=headers, json={"bib": "47107"}
        ).status_code
        == 200
    )
    assert race_history.sync_claim(claim["id"]) == 2
    refreshed = client.get("/api/race-history", headers=headers).json()
    assert next(row for row in refreshed["results"] if row["id"] == selected["id"])["verified"]
    assert sum(row["selected"] for row in refreshed["results"]) == 1


def _fail_fetch(*args, **kwargs):
    raise AssertionError("search must use the local mirror")


def test_vbm_search_matches_partial_names_locally(monkeypatch):
    from sqlalchemy import text

    from db import engine
    from services import race_history

    with engine.begin() as conn:
        for vbm_id in ("HOAI TRAN", "HOA THI TRAN", "HOANG VAN MINH"):
            conn.execute(
                text("INSERT INTO vbm_athletes (vbm_id, full_name, name_norm) VALUES (:id, :id, :norm)"),
                {"id": vbm_id, "norm": race_history.normalize_name(vbm_id)},
            )
    monkeypatch.setattr(race_history, "_fetch", _fail_fetch)
    # whole-word "HOA" outranks the shorter prefix-only "HOAI TRAN"
    assert [r["external_id"] for r in race_history.search_vbm("Tran Hoa")] == ["HOA THI TRAN", "HOAI TRAN"]
    assert race_history.search_vbm("Nguyen") == []


def test_utmb_mirror_refresh_pages_and_search_stays_local(monkeypatch):
    from services import race_history

    pages = {
        0: [
            {"uri": "1.van.vietvo", "fullname": "Van Viet VO", "sex": "H", "ageGroup": "35-39", "ip": 0},
            {"uri": "2.toan.vovan", "fullname": "Toàn VO VAN", "sex": "H", "ageGroup": "40-44", "ip": 612},
        ],
        1000: [{"uri": "3.hau.hathi", "fullname": "HAU HA THI", "sex": "F", "ageGroup": "35-39", "ip": 796}],
    }
    calls = []

    def fake_fetch(url, params=None, utmb=False):
        calls.append(params["offset"])
        return {"nbHits": 1001, "runners": pages[params["offset"]]}

    monkeypatch.setattr(race_history, "_fetch", fake_fetch)
    monkeypatch.setattr(race_history.time, "sleep", lambda _: None)
    assert race_history.refresh_utmb_mirror() == 3
    assert calls == [0, 1000]

    monkeypatch.setattr(race_history, "_fetch", _fail_fetch)
    found = race_history.search_utmb("vo van")
    assert [r["external_id"] for r in found] == ["2.toan.vovan", "1.van.vietvo"]  # indexed runner breaks the tie
    assert race_history.search_utmb("hau ha")[0]["external_id"] == "3.hau.hathi"
    assert found[0]["index"] == 612 and found[1]["index"] is None


def test_mirror_refresh_records_errors_and_skips_when_locked(monkeypatch):
    from sqlalchemy import text

    from db import engine
    from services import race_history

    def boom():
        raise RuntimeError("source down")

    monkeypatch.setitem(race_history._MIRRORS, "utmb", ("utmb_runners", boom))
    job = race_history.run_mirror_refresh(["utmb"])
    assert job["state"] == "error" and "source down" in job["error"]

    with engine.connect() as holder:
        holder.execute(text("SELECT pg_advisory_lock(:k)"), {"k": race_history._MIRROR_LOCK_ID})
        try:
            assert race_history.run_mirror_refresh(["utmb"]) is None
        finally:
            holder.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": race_history._MIRROR_LOCK_ID})


def test_linking_a_profile_syncs_immediately(client, auth_headers, monkeypatch):
    from services import race_history

    synced = []
    monkeypatch.setattr(race_history, "sync_claim_now", synced.append)
    claim = client.post(
        "/api/race-history/claims",
        headers=auth_headers["headers"],
        json={"source": "utmb", "external_id": "4133959.hau.hathi"},
    )
    assert claim.status_code == 202, claim.text
    assert synced == [claim.json()["id"]]


def test_manual_link_metadata_and_rank_only_patch(client, auth_headers):
    h = auth_headers["headers"]
    response = client.post(
        "/api/race-history/results",
        headers=h,
        json={
            "discipline": "road",
            "race_name": "City Marathon",
            "race_date": "2023-12-03",
            "distance_km": 42.195,
            "finish_time_sec": 13154,
            "location": "Can Tho",
            "result_url": "https://example.org/results/42",
            "rank_overall": 30,
            "total_overall": 100,
            "rank_gender": 5,
            "total_gender": 20,
            "rank_age_group": 2,
            "total_age_group": 5,
            "bib": "42",
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["source"] == "manual" and result.get("location") == "Can Tho"
    endpoint = f"/api/race-history/results/{result['id']}"
    for changes in [
        {"rank_overall": 101},
        {"rank_gender": 21},
        {"rank_age_group": 6},
        {"elevation_gain_m": -1},
        {"selected": None},
        {"hidden": None},
        {"race_name": None},
        {"result_url": "javascript:alert(1)"},
        {"unknown": "value"},
    ]:
        invalid = client.patch(endpoint, headers=h, json=changes)
        assert invalid.status_code == 422, (changes, invalid.text)
    cleared = client.patch(endpoint, headers=h, json={"result_url": None, "location": None, "elevation_gain_m": None})
    assert cleared.status_code == 200
    assert cleared.json()["result_url"] is None and cleared.json()["location"] is None
    assert cleared.json()["elevation_gain_m"] is None
    dnf = client.patch(endpoint, headers=h, json={"is_dnf": True})
    assert dnf.status_code == 200 and dnf.json()["finish_time_sec"] is None
    other = client.post("/api/auth/mock-login", json={"email": "race-other@uphill.ai"}).json()
    other_headers = {"Authorization": f"Bearer {other['session_token']}"}
    assert client.patch(endpoint, headers=other_headers, json={"location": "Elsewhere"}).status_code == 404


def test_reported_vbm_prs_require_confirmation_and_rejection_survives_sync(client, auth_headers, monkeypatch):
    from services import race_history

    parents = [
        {
            "event": "FMM",
            "race_full_name": "PREVIEW MARATHON 03/12/2023",
            "mark": "03:39:14",
            "bib": "42",
            "other_results_full": [{"race": "PREVIEW MARATHON 03/12/2023", "time": "03:39:14", "bib": "42"}],
        },
        {
            "event": "HMM",
            "race_full_name": "PREVIEW HALF 19/11/2023",
            "mark": "01:44:04",
            "bib": "21",
            "other_results_full": [{"race": "PREVIEW HALF 19/11/2023", "time": "01:44:04", "bib": "21"}],
        },
    ]
    for parent in parents:
        parent["full_name"] = "PREVIEW RUNNER"
    monkeypatch.setattr(race_history, "_fetch", lambda *args, **kwargs: {"data": parents})
    h = auth_headers["headers"]
    claim = client.post(
        "/api/race-history/claims", headers=h, json={"source": "vbm", "external_id": "PREVIEW PBS"}
    ).json()
    initial = client.get("/api/race-history", headers=h).json()
    assert initial["summary"]["road_prs"]["hm"] is None and initial["summary"]["road_prs"]["fm"] is None
    assert len(initial["results"]) == 2
    for row in initial["results"]:
        assert (
            client.patch(f"/api/race-history/results/{row['id']}", headers=h, json={"selected": True}).status_code
            == 200
        )
        assert (
            client.patch(
                f"/api/race-history/results/{row['id']}", headers=h, json={"result_url": "https://example.org"}
            ).status_code
            == 422
        )
    summary = client.get("/api/race-history", headers=h).json()["summary"]
    assert summary["road_prs"]["fm"]["time_sec"] == 13154 and summary["road_prs"]["hm"]["time_sec"] == 6244
    assert summary["road_fm_pr"] == summary["road_prs"]["fm"] and summary["road_hm_pr"] == summary["road_prs"]["hm"]
    half = next(row for row in initial["results"] if row["distance_km"] < 30)
    assert (
        client.patch(f"/api/race-history/results/{half['id']}", headers=h, json={"selected": False}).status_code == 200
    )
    race_history.sync_claim(claim["id"])
    refreshed = client.get("/api/race-history", headers=h).json()
    assert refreshed["summary"]["road_prs"]["hm"] is None
    assert not next(row for row in refreshed["results"] if row["id"] == half["id"])["selected"]


def test_local_preview_race_seed_is_scoped_and_idempotent(client, auth_headers):
    import db
    from scripts import seed_ios_preview
    from services import race_history

    seed = getattr(seed_ios_preview, "_seed_race_history", None)
    assert seed is not None, "Preview seed does not include race-history fixtures"
    retained = _manual(client, auth_headers["headers"], name="Keep this race")
    seed(auth_headers["user_id"])
    seed(auth_headers["user_id"])
    results = race_history.list_results(auth_headers["user_id"])
    assert len(results) == 10
    assert len(db.get_kb_chunks("race_courses", kind="race_profile")) == 4
    assert any(row["id"] == retained["id"] for row in results)
    assert sum(row["source"] == "vbm" and not row["selected"] for row in results) == 2

"""Integration tests for Phase 4: coach-facing goal/gear/pacing/nutrition
tool wrappers and the AI co-pilot chat. See
docs/superpowers/specs/2026-07-20-coach-role-design.md and
docs/superpowers/plans/2026-07-20-coach-role-phase4-coach-tools.md."""

from unittest.mock import patch

_VMM_WITH_PERCENTILES_CHUNK = {
    "title": "Vietnam Mountain Marathon (VMM) — Sa Pa, Vietnam",
    "content": "The VMM runs through Sa Pa...",
    "payload": {
        "race_name": "Vietnam Mountain Marathon",
        "aliases": ["VMM"],
        "distances": [{"label": "70km", "distance_km": 69.5, "elevation_gain_m": 4000}],
        "matching_hints": {"name_keywords": ["vmm", "vietnam mountain marathon"]},
        "results": [
            {
                "year": 2025,
                "distance_label": "70km",
                "distance_km": 69.5,
                "winner_time": "9:10:58",
                "percentiles": {
                    "overall": {
                        "p5": "9:30:00",
                        "p10": "10:00:00",
                        "p25": "11:00:00",
                        "p50": "13:00:00",
                        "p75": "15:00:00",
                        "p90": "17:00:00",
                    }
                },
            }
        ],
    },
}

_UTMB_WITH_PERCENTILES_CHUNK = {
    "title": "UTMB — Chamonix, France",
    "content": "UTMB circles Mont Blanc...",
    "payload": {
        "race_name": "UTMB",
        "aliases": [],
        "distances": [{"label": "170km", "distance_km": 171.0, "elevation_gain_m": 10000}],
        "matching_hints": {"name_keywords": ["utmb"]},
        "results": [
            {
                "year": 2025,
                "distance_label": "170km",
                "distance_km": 171.0,
                "winner_time": "19:30:00",
                "percentiles": {
                    "overall": {
                        "p5": "21:00:00",
                        "p10": "22:00:00",
                        "p25": "24:00:00",
                        "p50": "28:00:00",
                        "p75": "32:00:00",
                        "p90": "38:00:00",
                    }
                },
            }
        ],
    },
}


_UTMB_NO_PERCENTILES_CHUNK = {
    "title": "UTMB — Chamonix, France",
    "content": "UTMB circles Mont Blanc...",
    "payload": {
        "race_name": "UTMB",
        "aliases": [],
        "distances": [{"label": "170km", "distance_km": 171.0, "elevation_gain_m": 10000}],
        "matching_hints": {"name_keywords": ["utmb"]},
        "results": [
            {
                "year": 2025,
                "distance_label": "170km",
                "distance_km": 171.0,
                "winner_time": "19:30:00",
                # no "percentiles" key -- reference race resolves but has no
                # percentile data curated yet
            }
        ],
    },
}

_MULTI_DISTANCE_CHUNK = {
    "title": "Tarawera Ultramarathon — Rotorua, New Zealand",
    "content": "Tarawera runs through the Redwoods...",
    "payload": {
        "race_name": "Tarawera Ultramarathon",
        "aliases": [],
        "distances": [
            {"label": "100km", "distance_km": 102.0, "elevation_gain_m": 2900},
            {"label": "50km", "distance_km": 50.0, "elevation_gain_m": 1500},
        ],
        "matching_hints": {"name_keywords": ["tarawera", "tarawera ultramarathon"]},
        "results": [
            {
                "year": 2025,
                "distance_label": "100km",
                "distance_km": 102.0,
                "winner_time": "8:30:00",
                "percentiles": {
                    "overall": {
                        "p5": "9:00:00",
                        "p10": "9:30:00",
                        "p25": "10:30:00",
                        "p50": "12:00:00",
                        "p75": "14:00:00",
                        "p90": "16:00:00",
                    }
                },
            },
            {
                "year": 2025,
                "distance_label": "50km",
                "distance_km": 50.0,
                "winner_time": "4:00:00",
                "percentiles": {
                    "overall": {
                        "p5": "4:30:00",
                        "p10": "4:45:00",
                        "p25": "5:15:00",
                        "p50": "6:00:00",
                        "p75": "7:00:00",
                        "p90": "8:00:00",
                    }
                },
            },
        ],
    },
}


def _admin_headers(client):
    resp = client.post("/api/auth/mock-login", json={"email": "admin@uphill.ai"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def _make_coach(client, email="make-coach@uphill.ai"):
    resp = client.post("/api/auth/mock-login", json={"email": email})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {data['session_token']}"}
    promote = client.post(
        f"/api/admin/users/{user_id}/coach-status", json={"is_coach": True}, headers=_admin_headers(client)
    )
    assert promote.status_code == 200, promote.text
    return headers, user_id


def _link_coach_and_athlete(client, coach_headers, athlete_email):
    athlete_resp = client.post("/api/auth/mock-login", json={"email": athlete_email})
    athlete_headers = {"Authorization": f"Bearer {athlete_resp.json()['session_token']}"}
    athlete_id = athlete_resp.json()["user"]["id"]
    invite = client.post("/api/coaching/invite", json={"athlete_email": athlete_email}, headers=coach_headers).json()
    client.post(f"/api/coaching/invites/{invite['id']}/accept", headers=athlete_headers)
    return athlete_headers, athlete_id


_GOAL_ESTIMATE_PAYLOAD = {"distance_km": 50, "elevation_gain_m": 2000, "flat_pace_min_km": 5.5}


class TestCoachGoalEstimateEndpoint:
    def test_self_serve_goal_estimate_is_unaffected(self, client):
        """Regression guard for the _goal_estimate_core extraction."""
        resp = client.post("/api/coach/goal-estimate", json=_GOAL_ESTIMATE_PAYLOAD)
        assert resp.status_code == 200, resp.text
        assert "distance_km" in resp.json()

    def test_coach_can_get_a_goal_estimate_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "goalest-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "goalest-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/goal-estimate", json=_GOAL_ESTIMATE_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["distance_km"] == 50

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "goalest-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/goal-estimate",
            json=_GOAL_ESTIMATE_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403

    def test_athlete_can_use_it_on_themself(self, client, auth_headers):
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/goal-estimate",
            json=_GOAL_ESTIMATE_PAYLOAD,
            headers=auth_headers["headers"],
        )
        assert resp.status_code == 200


class TestGoalEstimateRaceDate:
    def test_race_date_derives_weeks_to_race(self, client):
        from datetime import date, timedelta

        far_future = (date.today() + timedelta(weeks=24)).isoformat()
        soon = (date.today() + timedelta(weeks=1)).isoformat()
        far_resp = client.post("/api/coach/goal-estimate", json={**_GOAL_ESTIMATE_PAYLOAD, "race_date": far_future})
        soon_resp = client.post("/api/coach/goal-estimate", json={**_GOAL_ESTIMATE_PAYLOAD, "race_date": soon})
        assert far_resp.status_code == 200, far_resp.text
        assert soon_resp.status_code == 200, soon_resp.text
        # 0.25%/week caps at 5% by week 20; 24 weeks out hits the cap, 1 week out doesn't
        assert far_resp.json()["improvement_pct"] == 5.0
        assert 0 < soon_resp.json()["improvement_pct"] < 5.0

    def test_explicit_weeks_to_race_takes_precedence_over_race_date(self, client):
        from datetime import date, timedelta

        far_future = (date.today() + timedelta(weeks=52)).isoformat()
        resp = client.post(
            "/api/coach/goal-estimate",
            json={**_GOAL_ESTIMATE_PAYLOAD, "race_date": far_future, "weeks_to_race": 0},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["improvement_pct"] == 0.0

    def test_malformed_race_date_is_ignored(self, client):
        resp = client.post("/api/coach/goal-estimate", json={**_GOAL_ESTIMATE_PAYLOAD, "race_date": "not-a-date"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["improvement_pct"] == 0.0


_PACING_PAYLOAD = {
    "checkpoints": [
        {"name": "Start", "distance_meters": 0, "elevation_m": 100},
        {"name": "Finish", "distance_meters": 10000, "elevation_m": 100},
    ],
    "target_flat_pace_min_km": 6.0,
}


class TestCoachCalculatePacingEndpoint:
    def test_self_serve_calculate_pacing_is_unaffected(self, client):
        resp = client.post("/api/coach/calculate-pacing", json=_PACING_PAYLOAD)
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    def test_coach_can_calculate_pacing_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "pacing-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "pacing-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/calculate-pacing", json=_PACING_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "pacing-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/calculate-pacing",
            json=_PACING_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403


_FUELING_PAYLOAD = {"distance_km": 50, "target_time_hours": 8}


class TestCoachCalculateFuelingEndpoint:
    def test_self_serve_calculate_fueling_is_unaffected(self, client):
        resp = client.post("/api/coach/calculate-fueling", json=_FUELING_PAYLOAD)
        assert resp.status_code == 200, resp.text

    def test_coach_can_calculate_fueling_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "fueling-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "fueling-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/calculate-fueling", json=_FUELING_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "fueling-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/calculate-fueling",
            json=_FUELING_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403


_GEAR_PAYLOAD = {"surface": "trail", "use_case": "training"}


class TestCoachRecommendShoesEndpoint:
    def test_self_serve_recommend_shoes_is_unaffected(self, client):
        resp = client.post("/api/coach/recommend-shoes", json=_GEAR_PAYLOAD)
        assert resp.status_code == 200, resp.text

    def test_coach_can_recommend_shoes_for_an_athlete(self, client):
        coach_headers, _ = _make_coach(client, "shoes-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "shoes-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/recommend-shoes", json=_GEAR_PAYLOAD, headers=coach_headers
        )
        assert resp.status_code == 200, resp.text

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "shoes-coach2@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/recommend-shoes",
            json=_GEAR_PAYLOAD,
            headers=coach_headers,
        )
        assert resp.status_code == 403


class TestCoachChatEndpoint:
    def test_coach_can_chat_about_an_athlete_with_no_active_plan(self, client):
        coach_headers, _ = _make_coach(client, "chat-coach1@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "chat-athlete1@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/chat",
            json={"messages": [{"role": "user", "content": "How is this athlete doing?"}]},
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["role"] == "assistant"
        assert isinstance(resp.json()["content"], str)
        assert len(resp.json()["content"]) > 0

    def test_coach_can_chat_about_an_athlete_with_an_active_plan(self, client, mock_plan_generation):
        coach_headers, _ = _make_coach(client, "chat-coach2@uphill.ai")
        athlete_headers, athlete_id = _link_coach_and_athlete(client, coach_headers, "chat-athlete2@uphill.ai")
        client.post(
            "/api/coach/generate-plan",
            json={
                "goal_type": "finish",
                "race_name": "Chat Context 50K",
                "race_date": "2027-05-01",
                "plan_start_date": "2027-03-15",
                "days_per_week": 4,
            },
            headers=athlete_headers,
        )
        resp = client.post(
            f"/api/coaching/athletes/{athlete_id}/chat",
            json={"messages": [{"role": "user", "content": "What's their current training block?"}]},
            headers=coach_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["role"] == "assistant"

    def test_empty_messages_is_rejected(self, client):
        coach_headers, _ = _make_coach(client, "chat-coach3@uphill.ai")
        _, athlete_id = _link_coach_and_athlete(client, coach_headers, "chat-athlete3@uphill.ai")
        resp = client.post(f"/api/coaching/athletes/{athlete_id}/chat", json={"messages": []}, headers=coach_headers)
        assert resp.status_code == 400

    def test_coach_without_a_link_is_forbidden(self, client, auth_headers):
        coach_headers, _ = _make_coach(client, "chat-coach4@uphill.ai")
        resp = client.post(
            f"/api/coaching/athletes/{auth_headers['user_id']}/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
            headers=coach_headers,
        )
        assert resp.status_code == 403


class TestGoalEstimatePercentileBlend:
    def test_blends_adjusted_time_when_both_races_have_curated_percentiles(self, client):
        payload = {
            "race_name": "UTMB",
            "reference_race_name": "VMM",
            "reference_distance_km": 69.5,
            "reference_time": "13:00:00",  # exactly the VMM p50
        }
        with patch("db.get_kb_chunks", return_value=[_VMM_WITH_PERCENTILES_CHUNK, _UTMB_WITH_PERCENTILES_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["percentile_transfer_mins"] is not None
        # runner at VMM's p50 should transfer to roughly UTMB's p50 (28:00:00 = 1680 mins)
        assert abs(body["percentile_transfer_mins"] - 1680.0) < 5.0
        assert body["percentile_years_used"] == {"target": 1, "reference": 1}
        # adjusted_time_mins must be the 50/50 blend, not the raw physics prediction
        assert body["adjusted_time_mins"] != body["predicted_time_mins"]
        expected_blend = (body["predicted_time_mins"] + body["percentile_transfer_mins"]) / 2.0
        assert abs(body["adjusted_time_mins"] - round(expected_blend, 1)) < 0.15
        assert body["goals"]["realistic"] == body["adjusted_time_mins"]

    def test_no_blend_when_reference_race_lacks_percentiles(self, client):
        payload = {
            "race_name": "UTMB",
            "distance_km": 171.0,
            "flat_pace_min_km": 6.0,
        }
        with patch("db.get_kb_chunks", return_value=[_UTMB_WITH_PERCENTILES_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("percentile_transfer_mins") is None
        assert body["adjusted_time_mins"] == body["predicted_time_mins"]

    def test_implausible_transfer_faster_than_target_winner_does_not_move_blend(self, client):
        # An unusually fast VMM reference time extrapolates, via the
        # percentile transfer, to a UTMB time faster than UTMB's own
        # curated winner (19:30:00 = 1170 mins) -- physically impossible.
        # The blend must not move adjusted_time_mins/goals in that case,
        # while percentile_transfer_mins is still reported for transparency.
        payload = {
            "race_name": "UTMB",
            "reference_race_name": "VMM",
            "reference_distance_km": 69.5,
            "reference_time": "8:00:00",
        }
        with patch("db.get_kb_chunks", return_value=[_VMM_WITH_PERCENTILES_CHUNK, _UTMB_WITH_PERCENTILES_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["percentile_transfer_mins"] is not None
        assert body["percentile_transfer_mins"] < 1170.0  # faster than UTMB's curated winner time
        assert body["adjusted_time_mins"] == body["predicted_time_mins"]
        assert body["goals"]["realistic"] == body["predicted_time_mins"]

    def test_no_blend_when_reference_distance_cannot_be_resolved(self, client):
        # reference_race_name matches a multi-distance KB entry but no
        # reference_distance_km is given, so match_race can't resolve a
        # single distance. The percentile-blend gate must not fall back to
        # an unfiltered (distance-mixed) percentile curve.
        payload = {
            "race_name": "UTMB",
            "reference_race_name": "Tarawera Ultramarathon",
            "reference_time": "10:00:00",
            "flat_pace_min_km": 6.0,
        }
        with patch("db.get_kb_chunks", return_value=[_UTMB_WITH_PERCENTILES_CHUNK, _MULTI_DISTANCE_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("percentile_transfer_mins") is None
        assert body["adjusted_time_mins"] == body["predicted_time_mins"]

    def test_rank_transfer_present_through_endpoint(self, client):
        # Minor #5: regression guard for rank_transfer_mins reaching the
        # endpoint response when both races have curated winner_time.
        payload = {
            "race_name": "UTMB",
            "reference_race_name": "VMM",
            "reference_distance_km": 69.5,
            "reference_time": "13:00:00",
        }
        with patch("db.get_kb_chunks", return_value=[_VMM_WITH_PERCENTILES_CHUNK, _UTMB_WITH_PERCENTILES_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # rank = 550.9667(VMM winner) / 780(reference time) ; target = 1170 / rank
        ref_winner = 9 * 60 + 10 + 58 / 60
        target_winner = 19 * 60 + 30
        rank = ref_winner / 780.0
        expected = round(target_winner / rank, 1)
        assert body["rank_transfer_mins"] == expected

    def test_no_blend_when_reference_race_resolves_but_lacks_percentiles(self, client):
        # Minor #6: target has percentiles, reference race resolves in the
        # KB (has a results entry) but that entry has no "percentiles" key.
        # The blend must not activate, but rank_transfer_mins (which only
        # needs winner_time) should still be computed.
        payload = {
            "race_name": "VMM",
            "reference_race_name": "UTMB",
            "reference_distance_km": 171.0,
            "reference_time": "20:00:00",
        }
        with patch("db.get_kb_chunks", return_value=[_VMM_WITH_PERCENTILES_CHUNK, _UTMB_NO_PERCENTILES_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("percentile_transfer_mins") is None
        assert body["adjusted_time_mins"] == body["predicted_time_mins"]
        assert body.get("rank_transfer_mins") is not None


_TECHNICAL_RACE_CHUNK = {
    "title": "Sapa Jungle Ultra — Sa Pa, Vietnam",
    "content": "A brutal jungle course...",
    "payload": {
        "race_name": "Sapa Jungle Ultra",
        "aliases": [],
        "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2000}],
        "matching_hints": {"name_keywords": ["sapa jungle ultra"]},
        "terrain": ["technical hand-and-knees scrambles on final climbs", "muddy rainy-season terrain"],
    },
}

_FLAT_RACE_CHUNK = {
    "title": "Coastal City Marathon — Da Nang, Vietnam",
    "content": "A flat coastal course...",
    "payload": {
        "race_name": "Coastal City Marathon",
        "aliases": [],
        "distances": [{"label": "50km", "distance_km": 50.0, "elevation_gain_m": 2000}],
        "matching_hints": {"name_keywords": ["coastal city marathon"]},
        "terrain": ["flat urban coastal road", "dragon bridge"],
    },
}


class TestGoalEstimateTerrainDifficulty:
    def test_technical_course_terrain_multiplier_reported_and_slower(self, client):
        payload = {"race_name": "Sapa Jungle Ultra", "flat_pace_min_km": 6.0}
        with patch("db.get_kb_chunks", return_value=[_TECHNICAL_RACE_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["terrain_multiplier_target"] > 1.0

    def test_flat_course_terrain_multiplier_is_one(self, client):
        payload = {"race_name": "Coastal City Marathon", "flat_pace_min_km": 6.0}
        with patch("db.get_kb_chunks", return_value=[_FLAT_RACE_CHUNK]):
            resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["terrain_multiplier_target"] == 1.0

    def test_technical_course_predicts_slower_than_flat_course_same_distance_elevation(self, client):
        with patch("db.get_kb_chunks", return_value=[_TECHNICAL_RACE_CHUNK]):
            technical_resp = client.post(
                "/api/coach/goal-estimate", json={"race_name": "Sapa Jungle Ultra", "flat_pace_min_km": 6.0}
            )
        with patch("db.get_kb_chunks", return_value=[_FLAT_RACE_CHUNK]):
            flat_resp = client.post(
                "/api/coach/goal-estimate", json={"race_name": "Coastal City Marathon", "flat_pace_min_km": 6.0}
            )
        assert technical_resp.json()["predicted_time_mins"] > flat_resp.json()["predicted_time_mins"]

    def test_no_race_name_gives_unchanged_terrain_multiplier(self, client):
        payload = {"distance_km": 50, "elevation_gain_m": 2000, "flat_pace_min_km": 6.0}
        resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["terrain_multiplier_target"] == 1.0


_GPX_PROFILE_CHECKPOINTS = [
    {
        "name": "Start",
        "distance_meters": 0,
        "elevation_meters": 1500.0,
        "segment_gain_meters": 0.0,
        "segment_loss_meters": 0.0,
    },
    {
        "name": "KM 10",
        "distance_meters": 10000.0,
        "elevation_meters": 3000.0,
        "segment_gain_meters": 1500.0,
        "segment_loss_meters": 0.0,
    },
    {
        "name": "KM 20",
        "distance_meters": 20000.0,
        "elevation_meters": 3000.0,
        "segment_gain_meters": 0.0,
        "segment_loss_meters": 0.0,
    },
]

_GPX_RACE_CHUNK = {
    "title": "High Altitude Ultra",
    "content": "A high mountain race...",
    "payload": {
        "race_name": "High Altitude Ultra",
        "aliases": [],
        "distances": [{"label": "20km", "distance_km": 20.0, "elevation_gain_m": 1500}],
        "matching_hints": {"name_keywords": ["high altitude ultra"]},
        "course_profiles": {
            "20km": {"checkpoints": _GPX_PROFILE_CHECKPOINTS, "source": "gpx_upload", "curated_at": "2026-08-22"}
        },
    },
}

_NO_PROFILE_RACE_CHUNK = {
    "title": "High Altitude Ultra No Profile",
    "content": "A high mountain race with no curated GPX yet...",
    "payload": {
        "race_name": "High Altitude Ultra No Profile",
        "aliases": [],
        "distances": [{"label": "20km", "distance_km": 20.0, "elevation_gain_m": 1500}],
        "matching_hints": {"name_keywords": ["high altitude ultra no profile"]},
    },
}


class TestGoalEstimateGpxProfile:
    def test_curated_profile_reported_and_slower_than_synthetic(self, client):
        with patch("db.get_kb_chunks", return_value=[_GPX_RACE_CHUNK]):
            gpx_resp = client.post(
                "/api/coach/goal-estimate", json={"race_name": "High Altitude Ultra", "flat_pace_min_km": 6.0}
            )
        with patch("db.get_kb_chunks", return_value=[_NO_PROFILE_RACE_CHUNK]):
            synthetic_resp = client.post(
                "/api/coach/goal-estimate",
                json={"race_name": "High Altitude Ultra No Profile", "flat_pace_min_km": 6.0},
            )
        assert gpx_resp.status_code == 200, gpx_resp.text
        assert synthetic_resp.status_code == 200, synthetic_resp.text
        assert gpx_resp.json()["target_profile_source"] == "gpx"
        assert synthetic_resp.json()["target_profile_source"] == "synthetic"
        assert gpx_resp.json()["predicted_time_mins"] > synthetic_resp.json()["predicted_time_mins"]

    def test_no_race_name_gives_synthetic_profile_source(self, client):
        payload = {"distance_km": 50, "elevation_gain_m": 2000, "flat_pace_min_km": 6.0}
        resp = client.post("/api/coach/goal-estimate", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["target_profile_source"] == "synthetic"

    def test_reference_curated_profile_reported_through_endpoint(self, client):
        with patch("db.get_kb_chunks", return_value=[_GPX_RACE_CHUNK]):
            resp = client.post(
                "/api/coach/goal-estimate",
                json={
                    "race_name": "High Altitude Ultra",
                    "reference_race_name": "High Altitude Ultra",
                    "reference_distance_km": 20.0,
                    "reference_time": "3:00:00",
                },
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["reference_profile_source"] == "gpx"

    def test_all_three_signals_compose_without_interference(self, client):
        # target+reference are DIFFERENT curated races so their percentile
        # curves diverge (a same-race target/reference pair makes the percentile
        # transfer trivially reproduce the raw physics prediction, which would
        # hide a real blending bug). Both races carry: a curated GPX profile,
        # terrain tags with a difficulty keyword, and curated percentile
        # results -- confirms none of the three sub-projects silently
        # overrides or double-counts another.
        target_chunk = {
            "title": "Triple Signal Target Ultra",
            "content": "A race with everything curated...",
            "payload": {
                "race_name": "Triple Signal Target Ultra",
                "aliases": [],
                "distances": [{"label": "20km", "distance_km": 20.0, "elevation_gain_m": 1500}],
                "matching_hints": {"name_keywords": ["triple signal target ultra"]},
                "terrain": ["technical hand-and-knees scrambles"],
                "course_profiles": {
                    "20km": {
                        "checkpoints": _GPX_PROFILE_CHECKPOINTS,
                        "source": "gpx_upload",
                        "curated_at": "2026-08-22",
                    }
                },
                "results": [
                    {
                        "year": 2025,
                        "distance_label": "20km",
                        "distance_km": 20.0,
                        "winner_time": "2:30:00",
                        "percentiles": {
                            "overall": {
                                "p5": "2:45:00",
                                "p10": "3:00:00",
                                "p25": "3:30:00",
                                "p50": "4:00:00",
                                "p75": "4:45:00",
                                "p90": "5:30:00",
                            }
                        },
                    }
                ],
            },
        }
        reference_chunk = {
            "title": "Triple Signal Reference Ultra",
            "content": "A different race with everything curated...",
            "payload": {
                "race_name": "Triple Signal Reference Ultra",
                "aliases": [],
                "distances": [{"label": "20km", "distance_km": 20.0, "elevation_gain_m": 1500}],
                "matching_hints": {"name_keywords": ["triple signal reference ultra"]},
                "terrain": ["technical hand-and-knees scrambles"],
                "course_profiles": {
                    "20km": {
                        "checkpoints": _GPX_PROFILE_CHECKPOINTS,
                        "source": "gpx_upload",
                        "curated_at": "2026-08-22",
                    }
                },
                # a noticeably faster field than the target race's, so the
                # percentile-rank transfer pulls the prediction away from the
                # raw physics number instead of trivially reproducing it
                "results": [
                    {
                        "year": 2025,
                        "distance_label": "20km",
                        "distance_km": 20.0,
                        "winner_time": "1:30:00",
                        "percentiles": {
                            "overall": {
                                "p5": "1:40:00",
                                "p10": "1:50:00",
                                "p25": "2:05:00",
                                "p50": "2:20:00",
                                "p75": "2:40:00",
                                "p90": "3:00:00",
                            }
                        },
                    }
                ],
            },
        }
        with patch("db.get_kb_chunks", return_value=[target_chunk, reference_chunk]):
            resp = client.post(
                "/api/coach/goal-estimate",
                json={
                    "race_name": "Triple Signal Target Ultra",
                    "reference_race_name": "Triple Signal Reference Ultra",
                    "reference_distance_km": 20.0,
                    "reference_time": "2:20:00",
                },
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["target_profile_source"] == "gpx"
        assert body["reference_profile_source"] == "gpx"
        assert body["terrain_multiplier_target"] > 1.0
        assert body["terrain_multiplier_reference"] > 1.0
        assert body["percentile_transfer_mins"] is not None
        # adjusted_time_mins must be the blend, not the raw physics number,
        # confirming percentile calibration still ran on top of the GPX+terrain result
        assert body["adjusted_time_mins"] != body["predicted_time_mins"]

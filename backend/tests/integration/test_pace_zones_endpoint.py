"""Integration tests for GET /api/auth/pace-zones."""

from services.plan_generator import PlanGenerator
from services.training_rules import TrainingRules


class TestPaceZonesEndpoint:
    def test_returns_zones_matching_estimate_pace_zones_for_the_current_user(self, client, auth_headers):
        profile_payload = {
            "age": 30,
            "current_weekly_km": 40.0,
            "max_hr": 190,
            "resting_hr": 50,
            "aet_hr": 140,
            "ant_hr": 165,
            "use_treadmill": False,
            "zone2_pace_min": "6:20",
            "zone2_pace_max": "5:30",
        }
        update_resp = client.post("/api/auth/update-profile", headers=auth_headers["headers"], json=profile_payload)
        assert update_resp.status_code == 200, update_resp.text

        resp = client.get("/api/auth/pace-zones", headers=auth_headers["headers"])
        assert resp.status_code == 200, resp.text
        body = resp.json()

        expected_pace = PlanGenerator.estimate_pace_zones("6:20", "5:30", 140, 165)
        expected_hr = TrainingRules.calculate_heart_rate_zones(190, 50)
        assert body == {
            "zone1_pace": expected_pace["zone1_pace"],
            "zone2_pace": expected_pace["zone2_pace"],
            "zone3_pace": expected_pace["zone3_pace"],
            "zone4_pace": expected_pace["zone4_pace"],
            "zone5_pace": expected_pace["zone5_pace"],
            "zone1_hr": f"{expected_hr['Zone 1']['min']}-{expected_hr['Zone 1']['max']} bpm",
            "zone2_hr": f"{expected_hr['Zone 2']['min']}-{expected_hr['Zone 2']['max']} bpm",
            "zone3_hr": f"{expected_hr['Zone 3']['min']}-{expected_hr['Zone 3']['max']} bpm",
            "zone4_hr": f"{expected_hr['Zone 4']['min']}-{expected_hr['Zone 4']['max']} bpm",
            "zone5_hr": f"{expected_hr['Zone 5']['min']}-{expected_hr['Zone 5']['max']} bpm",
        }

    def test_requires_authentication(self, client):
        resp = client.get("/api/auth/pace-zones")
        assert resp.status_code == 401

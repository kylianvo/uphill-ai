"""Unit tests for CorosAdapter -- the MCP client is stubbed, no network."""

from datetime import date

import pytest

from services.providers.coros import COROS_RUN_SPORT_TYPES, CorosAdapter

SPORT_RECORDS = """Sport Records — 2026-08-29 to 2026-09-02 (1 records)
========================

1. Trail Run — 2026-08-29
   Location: Sydney Trail Run
   Time Window: startTimestamp=1787982317 | endTimestamp=1787988291
   Duration: 1:30:34 | Distance: 15.03 km
   Average Pace: 6:02 /km | Avg HR: 148 bpm | Calories: 1040 kcal
   LabelId: 479959465976692837 | SportType: 102"""

ACTIVITY_DETAIL = """🏃 Trail Run Activity Details
========================================

Workout Time: 1:30:34
Distance: 15.03 km
Adjusted Pace: 5:55 /km
Average Heart Rate: 148 bpm
Elevation Gain / Loss: 98 m / 117 m
Training Load: 161
Aerobic TE: 3.4
Anaerobic TE: 0.4"""

DEVICES = """Bound Devices (1)
========================

1. COROS APEX PRO
   Bluetooth ID: 8772CC
   Model Name: COROS B17
   Serial Number: B17AJ13343"""


class StubMcp:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        return self.responses.get(name, "")


@pytest.mark.asyncio
async def test_fetch_activities_returns_canonical_activities():
    adapter = CorosAdapter(
        StubMcp(
            {
                "querySportRecords": SPORT_RECORDS,
                "getActivityDetail": ACTIVITY_DETAIL,
                "queryDevices": DEVICES,
            }
        )
    )
    activities = await adapter.fetch_activities(date(2026, 8, 29), date(2026, 9, 2))
    assert len(activities) == 1
    assert activities[0].external_id == "479959465976692837"
    assert activities[0].distance_km == 15.03


@pytest.mark.asyncio
async def test_activity_type_is_mapped_from_the_numeric_sport_type():
    adapter = CorosAdapter(
        StubMcp(
            {
                "querySportRecords": SPORT_RECORDS,
                "getActivityDetail": ACTIVITY_DETAIL,
                "queryDevices": DEVICES,
            }
        )
    )
    assert (await adapter.fetch_activities(date(2026, 8, 29), date(2026, 9, 2)))[0].activity_type == "trail_run"


@pytest.mark.asyncio
async def test_activity_carries_device_model_for_attribution():
    # COROS Agreement 14.5: displaying their data without naming the device
    # model is a material breach, so the adapter must populate it.
    adapter = CorosAdapter(
        StubMcp(
            {
                "querySportRecords": SPORT_RECORDS,
                "getActivityDetail": ACTIVITY_DETAIL,
                "queryDevices": DEVICES,
            }
        )
    )
    assert (await adapter.fetch_activities(date(2026, 8, 29), date(2026, 9, 2)))[0].device_model == "COROS APEX PRO"


@pytest.mark.asyncio
async def test_detail_fields_are_merged_onto_the_summary():
    adapter = CorosAdapter(
        StubMcp(
            {
                "querySportRecords": SPORT_RECORDS,
                "getActivityDetail": ACTIVITY_DETAIL,
                "queryDevices": DEVICES,
            }
        )
    )
    activity = (await adapter.fetch_activities(date(2026, 8, 29), date(2026, 9, 2)))[0]
    assert activity.elevation_gain_m == 98.0
    assert activity.training_load == 161.0
    assert activity.adjusted_pace_sec_per_km == 355.0


@pytest.mark.asyncio
async def test_requests_only_running_sport_types():
    stub = StubMcp({"querySportRecords": SPORT_RECORDS, "getActivityDetail": ACTIVITY_DETAIL, "queryDevices": DEVICES})
    await CorosAdapter(stub).fetch_activities(date(2026, 8, 29), date(2026, 9, 2))
    args = next(a for n, a in stub.calls if n == "querySportRecords")
    assert args["sportTypeCodes"] == COROS_RUN_SPORT_TYPES


@pytest.mark.asyncio
async def test_fetch_daily_metrics_merges_resting_hr_hrv_and_load_by_date():
    stub = StubMcp(
        {
            "queryRestingHeartRate": "Resting Heart Rate — Last 1 days\n========================\n\n2026-09-04: 57 bpm",
            "querySleepHrv": (
                "Sleep HRV — 2026-09-04 to 2026-09-04\n========================\n\n"
                "HRV Assessment — Last 7 days\n========================\n\n"
                "2026-09-04:\n  HRV Avg: 60 ms — Normal\n  Normal Range: 52 - 72 ms\n  Baseline: 62 ms"
            ),
            "queryTrainingLoadAssessment": (
                "Training Load Assessment\n========================\n\n"
                "2026-09-04\nComment: Optimized\nShort-Term Load: 77\n"
                "Long-Term Load: 71\nLoad Ratio: 1.08"
            ),
        }
    )
    metrics = await CorosAdapter(stub).fetch_daily_metrics(days=1)
    assert len(metrics) == 1
    assert metrics[0].metric_date == date(2026, 9, 4)
    assert metrics[0].resting_hr == 57
    assert metrics[0].hrv_ms == 60.0
    assert metrics[0].load_ratio == 1.08

"""Unit tests for CorosAdapter -- the MCP client is stubbed, no network."""

from datetime import date

import pytest

from services.mcp_client import McpError
from services.providers.coros import COROS_RUN_SPORT_TYPES, CorosAdapter, CorosDailyMetricsUnavailableError

SPORT_RECORDS = """Sport Records — 2026-08-29 to 2026-09-02 (1 records)
========================

1. Trail Run — 2026-08-29
   Location: Sydney Trail Run
   Time Window: startTimestamp=1787982317 | endTimestamp=1787988291
   Duration: 1:30:34 | Distance: 15.03 km
   Average Pace: 6:02 /km | Avg HR: 148 bpm | Calories: 1040 kcal
   LabelId: 479959465976692837 | SportType: 102"""

SPORT_RECORDS_TWO = """Sport Records — 2026-08-29 to 2026-09-02 (2 records)
========================

1. Trail Run — 2026-08-29
   Location: Sydney Trail Run
   Time Window: startTimestamp=1787982317 | endTimestamp=1787988291
   Duration: 1:30:34 | Distance: 15.03 km
   Average Pace: 6:02 /km | Avg HR: 148 bpm | Calories: 1040 kcal
   LabelId: 479959465976692837 | SportType: 102

2. Trail Run — 2026-08-30
   Location: Blue Mountains Trail Run
   Time Window: startTimestamp=1788068717 | endTimestamp=1788074691
   Duration: 1:15:00 | Distance: 12.50 km
   Average Pace: 6:00 /km | Avg HR: 145 bpm | Calories: 900 kcal
   LabelId: 479959465976692838 | SportType: 102"""

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

RESTING_HR_TEXT = "Resting Heart Rate — Last 1 days\n========================\n\n2026-09-04: 57 bpm"
SLEEP_HRV_TEXT = (
    "Sleep HRV — 2026-09-04 to 2026-09-04\n========================\n\n"
    "HRV Assessment — Last 7 days\n========================\n\n"
    "2026-09-04:\n  HRV Avg: 60 ms — Normal\n  Normal Range: 52 - 72 ms\n  Baseline: 62 ms"
)
TRAINING_LOAD_TEXT = (
    "Training Load Assessment\n========================\n\n"
    "2026-09-04\nComment: Optimized\nShort-Term Load: 77\n"
    "Long-Term Load: 71\nLoad Ratio: 1.08"
)


class StubMcp:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        return self.responses.get(name, "")


class FlakyDetailMcp:
    """Returns configured text for every tool, except getActivityDetail raises
    McpError for one specific labelId -- simulates a transient rate-limit or
    timeout hitting a single detail call mid-loop over several activities."""

    def __init__(self, responses: dict[str, str], failing_label_id: str):
        self.responses = responses
        self.failing_label_id = failing_label_id
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        if name == "getActivityDetail" and arguments.get("labelId") == self.failing_label_id:
            raise McpError("transient timeout")
        return self.responses.get(name, "")


class RaisingMcp:
    """Returns configured text for every tool, except tool names listed in
    `raising` raise the given exception instead."""

    def __init__(self, responses: dict[str, str], raising: dict[str, Exception]):
        self.responses = responses
        self.raising = raising
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        if name in self.raising:
            raise self.raising[name]
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
async def test_a_failed_detail_call_does_not_drop_other_activities():
    # Under rate limiting, getActivityDetail can raise McpError (timeout,
    # transport failure, isError result) rather than returning malformed
    # text. That must not abort fetch_activities and discard every activity
    # already collected -- the summary alone is enough to match an activity
    # against a planned session.
    stub = FlakyDetailMcp(
        {
            "querySportRecords": SPORT_RECORDS_TWO,
            "getActivityDetail": ACTIVITY_DETAIL,
            "queryDevices": DEVICES,
        },
        failing_label_id="479959465976692837",
    )
    activities = await CorosAdapter(stub).fetch_activities(date(2026, 8, 29), date(2026, 9, 2))
    assert len(activities) == 2
    by_id = {activity.external_id: activity for activity in activities}

    failed = by_id["479959465976692837"]
    assert failed.elevation_gain_m is None
    assert failed.training_load is None
    assert failed.distance_km == 15.03  # summary fields still present

    succeeded = by_id["479959465976692838"]
    assert succeeded.elevation_gain_m == 98.0
    assert succeeded.training_load == 161.0


@pytest.mark.asyncio
async def test_unrecognised_device_list_shape_degrades_to_none_with_a_warning(caplog):
    # COROS Agreement 14.5 requires naming the specific device model wherever
    # their data is shown and treats a failure to do so as a material breach.
    # A NULL device_model must never happen silently -- this must at least
    # log a clearly-named warning so the gap can be noticed.
    stub = StubMcp(
        {
            "querySportRecords": SPORT_RECORDS,
            "getActivityDetail": ACTIVITY_DETAIL,
            "queryDevices": "Bound Devices (0)\n========================\n\nNo devices bound.",
        }
    )
    with caplog.at_level("WARNING", logger="services.providers.coros"):
        activities = await CorosAdapter(stub).fetch_activities(date(2026, 8, 29), date(2026, 9, 2))

    assert activities[0].device_model is None
    events = [r.fields["event"] for r in caplog.records if hasattr(r, "fields")]
    assert "device_model_missing" in events


@pytest.mark.asyncio
async def test_queryDevices_failure_degrades_to_none_instead_of_aborting_the_batch(caplog):
    # A rate-limited or timed-out queryDevices call must not discard the whole
    # activity batch just to attribute a device model to it.
    stub = RaisingMcp(
        {
            "querySportRecords": SPORT_RECORDS,
            "getActivityDetail": ACTIVITY_DETAIL,
        },
        raising={"queryDevices": McpError("rate limited")},
    )
    with caplog.at_level("WARNING", logger="services.providers.coros"):
        activities = await CorosAdapter(stub).fetch_activities(date(2026, 8, 29), date(2026, 9, 2))

    assert len(activities) == 1
    assert activities[0].device_model is None
    events = [r.fields["event"] for r in caplog.records if hasattr(r, "fields")]
    assert "device_model_missing" in events


@pytest.mark.asyncio
async def test_fetch_daily_metrics_merges_resting_hr_hrv_and_load_by_date():
    stub = StubMcp(
        {
            "queryRestingHeartRate": RESTING_HR_TEXT,
            "querySleepHrv": SLEEP_HRV_TEXT,
            "queryTrainingLoadAssessment": TRAINING_LOAD_TEXT,
        }
    )
    metrics = await CorosAdapter(stub).fetch_daily_metrics(days=1)
    assert len(metrics) == 1
    assert metrics[0].metric_date == date(2026, 9, 4)
    assert metrics[0].resting_hr == 57
    assert metrics[0].hrv_ms == 60.0
    assert metrics[0].load_ratio == 1.08


@pytest.mark.asyncio
async def test_one_failed_daily_metric_source_still_merges_the_others():
    # queryRestingHeartRate, querySleepHrv and queryTrainingLoadAssessment are
    # independent sources -- one failing must not discard data successfully
    # parsed from the other two.
    stub = RaisingMcp(
        {
            "queryRestingHeartRate": RESTING_HR_TEXT,
            "querySleepHrv": SLEEP_HRV_TEXT,
        },
        raising={"queryTrainingLoadAssessment": McpError("rate limited")},
    )
    metrics = await CorosAdapter(stub).fetch_daily_metrics(days=1)
    assert len(metrics) == 1
    assert metrics[0].resting_hr == 57
    assert metrics[0].hrv_ms == 60.0
    assert metrics[0].load_ratio is None
    assert metrics[0].training_load_short is None


@pytest.mark.asyncio
async def test_all_daily_metric_sources_failing_raises_rather_than_returning_empty():
    # An empty list here would read downstream as "this athlete has no health
    # data today" -- the same silent-failure class the parsers were hardened
    # against in Task 5. A total outage across all three sources must raise.
    stub = RaisingMcp(
        {},
        raising={
            "queryRestingHeartRate": McpError("rate limited"),
            "querySleepHrv": McpError("rate limited"),
            "queryTrainingLoadAssessment": McpError("rate limited"),
        },
    )
    with pytest.raises(CorosDailyMetricsUnavailableError):
        await CorosAdapter(stub).fetch_daily_metrics(days=1)

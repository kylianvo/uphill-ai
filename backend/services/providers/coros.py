"""COROS adapter: MCP tool calls in, canonical dataclasses out.

Only running sport types are requested. COROS's numeric codes are documented in
the querySportRecords tool description; 100/101/102/103 are outdoor, indoor,
trail and track running respectively.

Note the device model comes from the account-level queryDevices tool, because no
MCP tool ties an activity to the device that recorded it. Where an athlete has
more than one watch bound this is a best guess -- the exact per-activity model is
only available inside the FIT file.
"""

from datetime import date
from typing import Any, Protocol

from log_utils import get_logger
from services.mcp_client import McpError
from services.providers import coros_parsers as parsers
from services.providers.base import CanonicalActivity, CanonicalDailyMetric

logger = get_logger(__name__)

PROVIDER = "coros"
COROS_RUN_SPORT_TYPES = [100, 101, 102, 103]

SPORT_TYPE_NAMES = {
    100: "outdoor_run",
    101: "indoor_run",
    102: "trail_run",
    103: "track_run",
}


class CorosDailyMetricsUnavailableError(RuntimeError):
    """Raised when every independent COROS daily-metric source failed.

    Returning an empty list in that situation would read downstream as "this
    athlete has no health data today", which is the same silent-failure class
    the COROS parsers were hardened against in Task 5 -- so a total outage
    across resting HR, sleep HRV and training load must raise, not silently
    produce zero rows. A partial outage (one or two sources failing) is not
    this error -- those cases return a merged result built from whatever
    succeeded.
    """


class SupportsCallTool(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str: ...


class CorosAdapter:
    def __init__(self, mcp: SupportsCallTool) -> None:
        self._mcp = mcp

    async def _primary_device_model(self) -> str | None:
        """Best-guess device attribution for COROS Agreement 14.5.

        No MCP tool ties an activity to the device that recorded it, so this
        reads the account's bound devices and returns the first one listed.
        Where more than one device is bound (e.g. a watch plus a separate HR
        strap), this is a guess, not a verified match -- the exact per-activity
        model is only available inside the FIT file.
        """
        text = await self._mcp.call_tool("queryDevices", {})
        for line in text.splitlines():
            stripped = line.strip()
            if stripped[:2].rstrip(".").isdigit() and "." in stripped[:3]:
                return stripped.split(".", 1)[1].strip()
        return None

    async def fetch_activities(self, since: date, until: date) -> list[CanonicalActivity]:
        text = await self._mcp.call_tool(
            "querySportRecords",
            {
                "startDate": since.strftime("%Y%m%d"),
                "endDate": until.strftime("%Y%m%d"),
                "sportTypeCodes": COROS_RUN_SPORT_TYPES,
                "minDistanceKm": None,
                "maxDistanceKm": None,
                "minDurationMinutes": None,
                "maxDurationMinutes": None,
                "maxAveragePace": None,
                "locationKeyword": None,
                "limit": 100,
            },
        )
        summaries = parsers.parse_sport_records(text)
        device_model = await self._primary_device_model()

        activities: list[CanonicalActivity] = []
        for summary in summaries:
            detail: dict[str, Any] = {}
            try:
                detail = parsers.parse_activity_detail(
                    await self._mcp.call_tool(
                        "getActivityDetail",
                        {
                            "labelId": summary["label_id"],
                            "sportType": summary["sport_type"],
                        },
                    )
                )
            except (parsers.CorosParseError, McpError) as exc:
                # A missing detail must not drop the activity -- the summary
                # alone is enough to match it against a planned session. This
                # also covers transient MCP failures (timeout, rate limit,
                # isError result) hitting a single detail call mid-loop --
                # those must not abort the whole batch and discard every
                # activity already collected.
                logger.warning(
                    "coros activity detail unavailable",
                    extra={
                        "fields": {
                            "service": "coros_adapter",
                            "event": "detail_missing",
                            "label_id": summary["label_id"],
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    },
                )

            activities.append(
                CanonicalActivity(
                    external_id=summary["label_id"],
                    provider=PROVIDER,
                    activity_type=SPORT_TYPE_NAMES.get(summary["sport_type"], "run"),
                    start_time=parsers.to_utc(summary["start_timestamp"]),
                    end_time=parsers.to_utc(summary["end_timestamp"]) if summary["end_timestamp"] else None,
                    duration_seconds=summary["duration_seconds"] or 0.0,
                    distance_km=summary["distance_km"],
                    elevation_gain_m=detail.get("elevation_gain_m"),
                    elevation_loss_m=detail.get("elevation_loss_m"),
                    avg_hr=summary["avg_hr"],
                    avg_pace_sec_per_km=summary["avg_pace_sec_per_km"],
                    adjusted_pace_sec_per_km=detail.get("adjusted_pace_sec_per_km"),
                    calories=summary["calories"],
                    training_load=detail.get("training_load"),
                    aerobic_te=detail.get("aerobic_te"),
                    anaerobic_te=detail.get("anaerobic_te"),
                    device_model=device_model,
                )
            )
        return activities

    async def fetch_daily_metrics(self, days: int = 7) -> list[CanonicalDailyMetric]:
        """Merge three independent COROS daily-metric sources by date.

        Each source (resting HR, sleep HRV, training load) is fetched and
        parsed independently. One source failing (a parse error or an MCP
        transport failure) must not discard data already obtained from the
        other two -- so each is guarded separately and contributes an empty
        result on failure. Only when all three fail does this raise, rather
        than silently returning `[]`, which downstream would otherwise read
        as "this athlete has no health data" instead of "COROS was
        unavailable".
        """
        resting: dict[date, int] = {}
        hrv: dict[date, dict[str, Any]] = {}
        load: dict[date, dict[str, Any]] = {}
        failures: list[tuple[str, Exception]] = []

        try:
            resting = parsers.parse_resting_hr(await self._mcp.call_tool("queryRestingHeartRate", {"days": days}))
        except (parsers.CorosParseError, McpError) as exc:
            failures.append(("queryRestingHeartRate", exc))
            logger.warning(
                "coros daily metric source unavailable",
                extra={
                    "fields": {
                        "service": "coros_adapter",
                        "event": "daily_metric_source_failed",
                        "source": "queryRestingHeartRate",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                },
            )

        try:
            hrv = parsers.parse_sleep_hrv(
                await self._mcp.call_tool("querySleepHrv", {"startDate": None, "endDate": None, "days": min(days, 7)})
            )
        except (parsers.CorosParseError, McpError) as exc:
            failures.append(("querySleepHrv", exc))
            logger.warning(
                "coros daily metric source unavailable",
                extra={
                    "fields": {
                        "service": "coros_adapter",
                        "event": "daily_metric_source_failed",
                        "source": "querySleepHrv",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                },
            )

        try:
            load = parsers.parse_training_load(await self._mcp.call_tool("queryTrainingLoadAssessment", {"days": days}))
        except (parsers.CorosParseError, McpError) as exc:
            failures.append(("queryTrainingLoadAssessment", exc))
            logger.warning(
                "coros daily metric source unavailable",
                extra={
                    "fields": {
                        "service": "coros_adapter",
                        "event": "daily_metric_source_failed",
                        "source": "queryTrainingLoadAssessment",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                },
            )

        if len(failures) == 3:
            names = ", ".join(name for name, _ in failures)
            last_exc = failures[-1][1]
            raise CorosDailyMetricsUnavailableError(f"all COROS daily-metric sources failed: {names}") from last_exc

        metrics: list[CanonicalDailyMetric] = []
        for day in sorted(set(resting) | set(hrv) | set(load)):
            hrv_row = hrv.get(day, {})
            load_row = load.get(day, {})
            metrics.append(
                CanonicalDailyMetric(
                    metric_date=day,
                    provider=PROVIDER,
                    resting_hr=resting.get(day),
                    hrv_ms=hrv_row.get("hrv_ms"),
                    hrv_baseline_ms=hrv_row.get("hrv_baseline_ms"),
                    hrv_status=hrv_row.get("hrv_status"),
                    training_load_short=load_row.get("training_load_short"),
                    training_load_long=load_row.get("training_load_long"),
                    load_ratio=load_row.get("load_ratio"),
                )
            )
        return metrics

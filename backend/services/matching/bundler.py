"""Groups fragmented activities into the sessions an athlete actually ran.

Athletes routinely stop and restart their watch mid-session: a short jog to the
gym, the treadmill session, sometimes a jog home. Matching a 0.57 km fragment
against a prescribed 10 km run is meaningless, and worse, the fragment can
occupy the day's only match slot.

Both parameters below are measured, not assumed. In three months of one real
COROS history there were seven fragmented days; five crossed sport types
(outdoor -> indoor), so grouping by exact type would miss the majority. The
largest real gap was 19m21s.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Activity types treated as one family for bundling. Crossing outdoor/indoor is
# the common real case, not an edge case.
RUN_TYPES = frozenset({"outdoor_run", "indoor_run", "trail_run", "track_run"})

BUNDLE_GAP_SECONDS = 30 * 60
NOISE_FLOOR_KM = 1.5
NOISE_FLOOR_SECONDS = 10 * 60


@dataclass
class SessionBundle:
    start_time: datetime
    duration_seconds: float
    distance_km: float
    elevation_gain_m: float
    avg_hr: int | None
    activity_ids: list[int] = field(default_factory=list)
    activity_types: set[str] = field(default_factory=set)

    @property
    def fragment_count(self) -> int:
        return len(self.activity_ids)


def _end_time(activity: dict) -> datetime:
    return activity["start_time"] + timedelta(seconds=float(activity["duration_seconds"] or 0.0))


def _weighted_hr(members: list[dict]) -> int | None:
    weighted = [(a["avg_hr"], float(a["duration_seconds"] or 0.0)) for a in members if a.get("avg_hr")]
    total = sum(d for _, d in weighted)
    if not weighted or total <= 0:
        return None
    return round(sum(hr * d for hr, d in weighted) / total)


def _to_bundle(members: list[dict]) -> SessionBundle:
    return SessionBundle(
        start_time=min(a["start_time"] for a in members),
        duration_seconds=sum(float(a["duration_seconds"] or 0.0) for a in members),
        distance_km=round(sum(float(a["distance_km"] or 0.0) for a in members), 4),
        elevation_gain_m=sum(float(a["elevation_gain_m"] or 0.0) for a in members),
        avg_hr=_weighted_hr(members),
        activity_ids=[a["id"] for a in members],
        activity_types={a["activity_type"] for a in members},
    )


def bundle_activities(activities: list[dict]) -> list[SessionBundle]:
    """Groups activities into session bundles. Input order is irrelevant.

    Only members of RUN_TYPES are bundled with each other; anything else is
    returned as its own single-member bundle so nothing is silently dropped.
    """
    if not activities:
        return []

    ordered = sorted(activities, key=lambda a: a["start_time"])
    bundles: list[SessionBundle] = []
    current: list[dict] = []

    for activity in ordered:
        if not current:
            current = [activity]
            session_end = _end_time(activity)
            continue

        # The session ends when its LAST-FINISHING member ends, which is not
        # necessarily its last-starting one: a short activity logged inside a
        # longer one would otherwise drag the session end backwards and split
        # a session that overlaps itself.
        previous = current[-1]
        both_runs = activity["activity_type"] in RUN_TYPES and previous["activity_type"] in RUN_TYPES
        gap = (activity["start_time"] - session_end).total_seconds()

        if both_runs and gap <= BUNDLE_GAP_SECONDS:
            current.append(activity)
            session_end = max(session_end, _end_time(activity))
        else:
            bundles.append(_to_bundle(current))
            current = [activity]
            session_end = _end_time(activity)

    bundles.append(_to_bundle(current))
    return bundles

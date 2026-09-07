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

BUNDLE_GAP_SECONDS = 60 * 60
WARMUP_GAP_SECONDS = 60 * 60
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
    primary_activity_id: int | None = None
    warmup_distance_km: float = 0.0
    warmup_duration_seconds: float = 0.0

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


def _is_warmup(a: dict) -> bool:
    dist = a.get("distance_km")
    dur = float(a.get("duration_seconds") or 0.0)
    if dist is not None and float(dist) > 0:
        return float(dist) <= NOISE_FLOOR_KM
    return dur <= NOISE_FLOOR_SECONDS


def _to_bundle(members: list[dict]) -> SessionBundle:
    if len(members) == 1:
        m = members[0]
        return SessionBundle(
            start_time=m["start_time"],
            duration_seconds=float(m["duration_seconds"] or 0.0),
            distance_km=round(float(m["distance_km"] or 0.0), 4),
            elevation_gain_m=float(m["elevation_gain_m"] or 0.0),
            avg_hr=m.get("avg_hr"),
            activity_ids=[m["id"]],
            activity_types={m["activity_type"]},
            primary_activity_id=m["id"],
            warmup_distance_km=0.0,
            warmup_duration_seconds=0.0,
        )

    primary = max(
        members,
        key=lambda a: (float(a.get("distance_km") or 0.0), float(a.get("duration_seconds") or 0.0)),
    )
    warmups = [a for a in members if a["id"] != primary["id"] and _is_warmup(a)]
    warmup_dist = round(sum(float(a.get("distance_km") or 0.0) for a in warmups), 4)
    warmup_dur = sum(float(a.get("duration_seconds") or 0.0) for a in warmups)

    return SessionBundle(
        start_time=min(a["start_time"] for a in members),
        duration_seconds=sum(float(a["duration_seconds"] or 0.0) for a in members),
        distance_km=round(sum(float(a["distance_km"] or 0.0) for a in members), 4),
        elevation_gain_m=sum(float(a["elevation_gain_m"] or 0.0) for a in members),
        avg_hr=_weighted_hr(members),
        activity_ids=[a["id"] for a in members],
        activity_types={a["activity_type"] for a in members},
        primary_activity_id=primary["id"],
        warmup_distance_km=warmup_dist,
        warmup_duration_seconds=warmup_dur,
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

        previous = current[-1]
        both_runs = activity["activity_type"] in RUN_TYPES and previous["activity_type"] in RUN_TYPES
        gap = (activity["start_time"] - session_end).total_seconds()

        is_warmup_candidate = _is_warmup(activity) or _is_warmup(previous)
        allowed_gap = WARMUP_GAP_SECONDS if is_warmup_candidate else BUNDLE_GAP_SECONDS

        if both_runs and gap <= allowed_gap:
            current.append(activity)
            session_end = max(session_end, _end_time(activity))
        else:
            bundles.append(_to_bundle(current))
            current = [activity]
            session_end = _end_time(activity)

    bundles.append(_to_bundle(current))
    return bundles

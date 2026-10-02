"""What we know about an athlete's current fitness, and where each number came from.

Plan generation used to read the km/week typed into a form and the stored AeT/AnT pair,
and nothing the watch measured. A 130 km/week athlete with default-looking thresholds was
demoted to `recreational` and handed 40-60 km weeks. This module assembles the measured
signals first and falls back to typed values, recording the source of each so a plan's
tier can be audited from plans.fitness_snapshot. Spec:
docs/superpowers/specs/2026-10-02-fitness-snapshot-design.md
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

import db
from services.athlete_tier import resolve_tier_explained

PROVIDER = "coros"
VOLUME_WEEKS = 4
MIN_COUNTED_WEEKS = 3
ASSESSMENT_MAX_AGE = timedelta(days=60)
READINESS_DAYS = 14


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def measured_weekly_volume(
    weeks: list[dict[str, Any]],
    first_activity_at: datetime | None,
    last_sync_at: datetime | None,
    today: date,
) -> tuple[float, float, date] | None:
    """Mean km and vert over the last complete weeks a sync actually covered.

    A week counts when it starts on or after the first synced activity (before that we
    simply have no data) and ends before the last sync (after that the week is partial).
    A counted week with no activity is a real zero. None when fewer than
    MIN_COUNTED_WEEKS weeks qualify."""
    if not last_sync_at or not first_activity_at:
        return None
    first_day = _aware(first_activity_at).date()
    sync = _aware(last_sync_at)
    by_start = {w["week_start"]: w for w in weeks}
    counted = []
    for i in range(1, VOLUME_WEEKS + 1):
        start = _monday(today) - timedelta(weeks=i)
        end = datetime.combine(start + timedelta(days=7), datetime.min.time(), tzinfo=UTC)
        if start >= first_day and end <= sync:
            counted.append((start, by_start.get(start, {"km": 0.0, "vert_m": 0.0})))
    if len(counted) < MIN_COUNTED_WEEKS:
        return None
    km = sum(w["km"] for _, w in counted) / len(counted)
    vert = sum(w["vert_m"] for _, w in counted) / len(counted)
    last_end = max(s for s, _ in counted) + timedelta(days=6)
    return round(km, 1), round(vert), last_end


def _hms(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


@dataclass
class FitnessSnapshot:
    weekly_km: float
    weekly_km_source: str
    weekly_vert_m: float | None
    volume_as_of: str | None
    threshold_pace: str | None
    threshold_pace_source: str | None
    assessment: dict[str, Any] | None
    utmb_index: int | None
    threshold_source: str
    gender: str | None
    readiness: dict[str, Any] | None
    notes: list[str] = field(default_factory=list)
    tier: str | None = None
    tier_reasons: list[str] = field(default_factory=list)

    def resolve_tier(
        self,
        explicit_tier: str | None,
        goal_type: str | None,
        max_continuous_jog_min: int | None,
        historical_max_distance_km: float | None,
        aet_hr: float | None,
        ant_hr: float | None,
    ) -> str:
        decision = resolve_tier_explained(
            explicit_tier=explicit_tier,
            goal_type=goal_type,
            current_weekly_km=self.weekly_km,
            max_continuous_jog_min=max_continuous_jog_min,
            historical_max_distance_km=historical_max_distance_km,
            aet_hr=aet_hr,
            ant_hr=ant_hr,
            threshold_source=self.threshold_source,
            marathon_prediction_sec=(self.assessment or {}).get("pred_marathon_sec"),
            gender=self.gender,
            utmb_index=self.utmb_index,
        )
        self.tier, self.tier_reasons = decision.tier, decision.reasons
        return self.tier

    def prompt_block(self, lang: str = "en") -> str:
        # English like the rest of the scheduler prompt; `lang` steers the output elsewhere.
        src = {"coros": "COROS", "self_reported": "self-reported"}
        lines = ["ATHLETE FITNESS SNAPSHOT"]
        vol = f"- Volume: {self.weekly_km:.0f} km/week"
        if self.weekly_vert_m:
            vol += f", {self.weekly_vert_m:,.0f} m vert"
        vol += f" ({src[self.weekly_km_source]}"
        vol += f", 4-week avg to {self.volume_as_of})" if self.volume_as_of else ")"
        lines.append(vol)
        a = self.assessment
        if a:
            day = _aware(a["measured_at"]).date().isoformat()
            preds = []
            if a.get("pred_marathon_sec"):
                preds.append(f"Marathon prediction {_hms(a['pred_marathon_sec'])}")
            if a.get("pred_hm_sec"):
                preds.append(f"half {_hms(a['pred_hm_sec'])}")
            if preds:
                lines.append(f"- {', '.join(preds)} (COROS, {day})")
            if a.get("vo2max"):
                lines.append(f"- VO2max {a['vo2max']:.0f} (COROS, {day})")
        if self.threshold_pace:
            lines.append(f"- Threshold pace {self.threshold_pace}/km ({src[self.threshold_pace_source or 'self_reported']})")
        if self.utmb_index:
            lines.append(f"- UTMB index {self.utmb_index}")
        r = self.readiness or {}
        if r.get("days_recorded"):
            bits = []
            if r.get("latest_load_ratio") is not None:
                bits.append(f"load ratio {r['latest_load_ratio']:.2f}")
            if r.get("latest_hrv_status"):
                bits.append(f"HRV {r['latest_hrv_status']}")
            if bits:
                lines.append(f"- {', '.join(bits)} (COROS, last {READINESS_DAYS} days)")
        if self.tier:
            lines.append(f"- Level: {self.tier} ({'; '.join(self.tier_reasons)})")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build(
    user_id: int,
    typed_weekly_km: float | None = None,
    typed_is_override: bool = False,
    today: date | None = None,
) -> FitnessSnapshot:
    today = today or date.today()
    user = db.get_user_by_id(user_id) or {}
    connection = db.get_connection(user_id, PROVIDER)
    connected = bool(connection and connection.get("status") == "active")
    notes: list[str] = []

    measured = None
    if connected:
        weeks = db.get_weekly_run_volumes(user_id, since=_monday(today) - timedelta(weeks=VOLUME_WEEKS))
        measured = measured_weekly_volume(
            weeks, db.get_first_activity_at(user_id, PROVIDER), connection.get("last_sync_at"), today
        )
        if measured is None:
            notes.append("COROS volume unused: fewer than 3 complete synced weeks")

    fallback_km = typed_weekly_km if typed_weekly_km is not None else user.get("current_weekly_km") or 30.0
    if typed_is_override and typed_weekly_km is not None:
        km, vert, as_of, km_src = float(typed_weekly_km), None, None, "self_reported"
        if measured:
            notes.append(f"athlete override of measured {measured[0]:.0f} km/week")
    elif measured:
        km, vert, as_of, km_src = measured[0], measured[1], measured[2].isoformat(), "coros"
    else:
        km, vert, as_of, km_src = float(fallback_km), None, None, "self_reported"

    assessment = db.get_latest_fitness_assessment(user_id)
    if assessment and today - _aware(assessment["measured_at"]).date() > ASSESSMENT_MAX_AGE:
        notes.append("COROS assessment older than 60 days, unused")
        assessment = None

    if assessment and assessment.get("threshold_pace"):
        tp, tp_src = assessment["threshold_pace"], "coros"
    elif user.get("threshold_pace"):
        tp, tp_src = user["threshold_pace"], "self_reported"
    else:
        tp, tp_src = None, None

    return FitnessSnapshot(
        weekly_km=km,
        weekly_km_source=km_src,
        weekly_vert_m=vert,
        volume_as_of=as_of,
        threshold_pace=tp,
        threshold_pace_source=tp_src,
        assessment=assessment,
        utmb_index=db.get_utmb_index(user_id),
        threshold_source=user.get("threshold_source") or "unknown",
        gender=user.get("gender"),
        readiness=db.get_recent_readiness_summary(user_id, days=READINESS_DAYS) if connected else None,
        notes=notes,
    )

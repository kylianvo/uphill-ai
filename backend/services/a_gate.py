"""When may the plan chase the A goal? B is the contract; A add-ons are earned.

The plan always carries the B goal. Extra race-specific work for A (more climbing at the course's required
rate, a goal-pace block) is added only while the evidence says the athlete can absorb it: aerobic speed is on
or ahead of the A line, recovery signals are fine, recent adherence is high and the plan itself backs the
goals. Any single failure puts the add-ons on hold, and the reasons are shown to the athlete.
"""

from dataclasses import dataclass, field
from typing import Any

from services.aerobic_speed import PathStatus

MIN_ADHERENCE = 0.8
ADHERENCE_WEEKS = 4
_FATIGUE = {"fatigued", "overreaching"}


@dataclass(frozen=True)
class Gate:
    open: bool
    reasons: list[str] = field(default_factory=list)


def adherence(workouts: list[dict[str, Any]], before_week: int, weeks: int = ADHERENCE_WEEKS) -> float | None:
    ws = [
        w
        for w in workouts
        if before_week - weeks <= (w.get("week_number") or 0) < before_week and w.get("type") != "Rest"
    ]
    return sum(1 for w in ws if w.get("is_completed") == 1) / len(ws) if ws else None


def evaluate(
    path: PathStatus | None,
    *,
    readiness_flag: str | None,
    workouts: list[dict[str, Any]],
    before_week: int,
    plan_supported: bool,
) -> Gate:
    reasons: list[str] = []
    if path is None:
        reasons.append("no aerobic-speed history yet")
    elif path.confidence == "low":
        reasons.append("too few weeks of aerobic-speed data")
    elif path.a == "behind":
        reasons.append("aerobic speed is behind the A line")
    if readiness_flag in _FATIGUE:
        reasons.append(f"recovery signals are {readiness_flag}")
    done = adherence(workouts, before_week)
    if done is None:
        reasons.append("no recent sessions to judge adherence")
    elif done < MIN_ADHERENCE:
        reasons.append(f"recent adherence is {round(done * 100)}%")
    if not plan_supported:
        reasons.append("the plan does not yet back the goal times")
    return Gate(not reasons, reasons)


def prompt_line(g: Gate) -> str:
    if g.open:
        return (
            "A-GOAL ADD-ONS: allowed. Add at most one extra race-specific session this block (climbing at the "
            "course's required rate, or a goal-pace block) if the athlete's days allow, inside every cap above."
        )
    return f"A-GOAL ADD-ONS: not yet ({'; '.join(g.reasons)}). Plan to the B goal only."


def log_line(g: Gate) -> str:
    if g.open:
        return "A-goal extras are allowed this block: aerobic speed, recovery and adherence all support them."
    return f"A-goal extras are on hold: {'; '.join(g.reasons)}. The plan stays on the B goal."

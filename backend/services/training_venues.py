"""Where an athlete can actually do each kind of session.

The doctrine assumes steep terrain on the doorstep: hill sprints on a 20%+ hill, ME
carries on a 30%+ slope, uphill intervals on real climbs. Most of our runners live in a
flat city, reach the mountains only at weekends or on a training camp, and own a
treadmill that tops out at 15%. Left to the model, those substitutions were made
differently on every run, from free-text notes.

This module turns the plan's Schedule Preferences into one deterministic venue ladder
per session type (first available option wins). The plan prompt states it as a hard
constraint, and post-processing uses the same answers to move sessions that landed on
a day with no venue for them.

Inputs, all on the `plans` row:
  training_environment -- home terrain: 'flat' | 'hilly' | 'mixed' (hills nearby)
  mountain_days        -- weekdays the athlete can reach hills/trails (e.g. weekend trips)
  stair_access         -- fire stairs in a tall building, a stadium, or a Stairmaster
  use_treadmill        -- has a treadmill
  treadmill_max_incline -- its top incline in % (15 standard, 25+ incline trainer)
  has_gym_access       -- has a gym
"""

import json
from dataclasses import dataclass
from typing import Any

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
STANDARD_TREADMILL_MAX = 15
INCLINE_TRAINER_MIN = 25


def parse_days(value: Any) -> tuple[str, ...]:
    """A day list as stored on `plans` (JSON text) or sent by the client (list)."""
    if not value:
        return ()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return ()
    if not isinstance(value, list | tuple):
        return ()
    return tuple(d for d in WEEKDAYS if d in value)


def _clamp_incline(value: Any) -> int:
    try:
        incline = int(value)
    except (TypeError, ValueError):
        return STANDARD_TREADMILL_MAX
    return max(STANDARD_TREADMILL_MAX, min(40, incline))


@dataclass(frozen=True)
class Venues:
    environment: str = "flat"
    mountain_days: tuple[str, ...] = ()
    stair_access: bool = False
    use_treadmill: bool = False
    treadmill_max_incline: int = STANDARD_TREADMILL_MAX
    has_gym_access: bool = False

    @classmethod
    def from_race_info(cls, race_info: dict[str, Any]) -> "Venues":
        return cls(
            environment=(race_info.get("training_environment") or "flat").lower(),
            mountain_days=parse_days(race_info.get("mountain_days")),
            stair_access=bool(race_info.get("stair_access")),
            use_treadmill=bool(race_info.get("use_treadmill")),
            treadmill_max_incline=_clamp_incline(race_info.get("treadmill_max_incline")),
            has_gym_access=bool(race_info.get("has_gym_access")),
        )

    @property
    def local_hills(self) -> bool:
        """Hills close enough to use on any day."""
        return self.environment in ("hilly", "mixed")

    def hills_on(self, day: str) -> bool:
        return self.local_hills or day in self.mountain_days

    @property
    def any_hills(self) -> bool:
        return self.local_hills or bool(self.mountain_days)

    @property
    def hills_only_some_days(self) -> bool:
        return not self.local_hills and bool(self.mountain_days)

    @property
    def incline_trainer(self) -> bool:
        return self.use_treadmill and self.treadmill_max_incline >= INCLINE_TRAINER_MIN

    def hill_sprint_venue(self, day: str) -> str | None:
        """'hill' | 'stairs' | 'treadmill', or None when the day has no venue."""
        if self.hills_on(day):
            return "hill"
        if self.stair_access:
            return "stairs"
        if self.use_treadmill:
            return "treadmill"
        return None

    @property
    def hill_sprints_possible(self) -> bool:
        return self.any_hills or self.stair_access or self.use_treadmill

    @property
    def treadmill_incline_cap(self) -> float:
        """Highest incline any treadmill session may use."""
        return float(self.treadmill_max_incline) if self.use_treadmill else float(STANDARD_TREADMILL_MAX)

    def _days(self, days: tuple[str, ...]) -> str:
        return ", ".join(days)

    def prompt_block(self, *, allows_intensity: bool, allows_me: bool) -> str:
        """The TRAINING VENUES section of the plan prompt (rule 5)."""
        if self.local_hills:
            hills = f"every day ({self.environment} home terrain)"
        elif self.mountain_days:
            hills = f"ONLY on {self._days(self.mountain_days)} (flat home terrain the rest of the week)"
        else:
            hills = "none — flat home terrain and no hill days"
        treadmill = (
            f"yes, max incline {self.treadmill_max_incline}%" + (" (incline trainer)" if self.incline_trainer else "")
            if self.use_treadmill
            else "no"
        )
        lines = [
            "\n5. TRAINING VENUES — hard constraints built from the athlete's Schedule Preferences. Use ONLY these:",
            f"   - Hills/trails: {hills}.",
            f"   - Stairs (fire stairs in a tall building, stadium, or Stairmaster): {'yes' if self.stair_access else 'no'}."
            f" Treadmill: {treadmill}. Gym: {'yes' if self.has_gym_access else 'no'}.",
        ]
        if not self.has_gym_access:
            lines.append(
                "   - No gym: NEVER prescribe weighted or machine-based Strength or ME — bodyweight only (step-ups, "
                "lunges, squats), plus a backpack for loaded step-ups."
            )
        if self.use_treadmill:
            lines.append(
                f"   - NEVER set `treadmill_incline` above {self.treadmill_max_incline}%, this athlete's treadmill maximum."
            )

        lines.append("   Venue for each session type (first available option wins):")
        if not allows_intensity:
            lines.append("   - NEVER prescribe a Hill Sprint, Hill Repeat, or Hill Bound session for this athlete.")
        if allows_intensity:
            if self.hill_sprints_possible:
                ladder = []
                if self.local_hills:
                    ladder.append("a 20%+ hill")
                elif self.mountain_days:
                    ladder.append(f"a 20%+ hill on {self._days(self.mountain_days)}")
                if self.stair_access:
                    ladder.append("steep stairs taken two at a time (any day)")
                if self.use_treadmill:
                    ladder.append(
                        f"treadmill at {min(self.treadmill_max_incline, INCLINE_TRAINER_MIN)}% with ~30 s reps "
                        "(bring the belt up to speed, sprint the final 10-15 s, step onto the side rails)"
                    )
                ladder.append("flat strides and bounding")
                lines.append("   - Hill Sprints: " + " → ".join(ladder) + ".")
                if self.hills_only_some_days and not (self.stair_access or self.use_treadmill):
                    lines.append(
                        f"     Schedule Hill Sprints ONLY on {self._days(self.mountain_days)}; other days get strides."
                    )
            else:
                lines.append(
                    "   - Hill Sprint/Hill Repeat/Hill Bound: NOT available (no hills, stairs or treadmill). NEVER "
                    "prescribe a Hill Sprint, Hill Repeat, or Hill Bound session — substitute flat strides and "
                    "bounding (or Fartlek/Surges) covering the same training purpose."
                )
        if allows_me:
            carry = []
            if self.any_hills:
                carry.append(
                    "weighted carries on a 30%+ slope"
                    + (f" on {self._days(self.mountain_days)}" if self.hills_only_some_days else "")
                )
            if self.stair_access:
                carry.append("stairs/Stairmaster with a 5-15% BW pack, laps of at least 5 min")
            if self.use_treadmill:
                carry.append(
                    "treadmill at 25% (incline trainer)"
                    if self.incline_trainer
                    else f"treadmill at {self.treadmill_max_incline}% with a 5-15% BW vest or pack"
                )
            carry.append("loaded box step-ups at home or in the gym")
            lines.append(
                "   - Muscular Endurance: the Gym ME progression works on ANY weekday in any city"
                + ("" if self.has_gym_access else " (bodyweight version)")
                + ". Outdoor-style ME: "
                + " → ".join(carry)
                + "."
            )
        if allows_intensity:
            uphill = []
            if self.any_hills:
                uphill.append(
                    "real climbs" + (f" on {self._days(self.mountain_days)}" if self.hills_only_some_days else "")
                )
            if self.use_treadmill:
                uphill.append(
                    f"treadmill at a steady incline up to {self.treadmill_max_incline}% "
                    "(effort is set by heart-rate zone, so grade matters less)"
                )
            if self.stair_access:
                uphill.append("stairs or Stairmaster")
            uphill.append("flat or rolling Zone 3")
            lines.append("   - Uphill/rolling intervals: " + " → ".join(uphill) + ".")
        city_vert = " or ".join(
            v
            for v, have in (("treadmill incline blocks", self.use_treadmill), ("stair laps", self.stair_access))
            if have
        )
        if self.hills_only_some_days:
            lines.append(
                f"   - Long run with vertical and any back-to-back overreach go on {self._days(self.mountain_days)}. "
                + (
                    f"In a week without a hill day, build the long run's vertical from {city_vert}."
                    if city_vert
                    else "Other days' runs are flat: do not invent climbing on them."
                )
            )
        elif not self.any_hills:
            lines.append(
                f"   - Long run vertical: no hills, so build it from {city_vert}."
                if city_vert
                else "   - No hills, stairs or treadmill: runs are flat"
                + ("; build climbing strength through ME instead." if allows_me else ".")
            )
        descents = (
            f"real descents on {self._days(self.mountain_days)}; otherwise "
            if self.hills_only_some_days
            else ("real descents, plus " if self.any_hills else "")
        )
        eccentric = "gym ME jumps and eccentric box step-downs" if allows_me else "eccentric box step-downs"
        lines.append(f"   - Downhill/eccentric preparation: {descents}{eccentric} (treadmills cannot descend).")
        return "\n".join(lines) + "\n"

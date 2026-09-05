"""Assigns session bundles to planned workouts, one to one.

A day can carry two planned sessions and two real bundles, so a bundle must not
claim two workouts and a workout must not be claimed twice. With a handful of
candidates per day a greedy pass over score-sorted pairs is sufficient and far
easier to reason about than an optimal assignment algorithm.

Ties are broken deterministically on (workout id, first activity id) so that
re-running the matcher over unchanged data always produces the same answer --
important, because the shadow-mode calibration compares runs against each
other. Both tie-break fields are stable, total orderings over the candidate
set: workout ids and activity ids are database primary keys, never repeated
within a single call, so the compound sort key never falls back to Python's
sort stability (and therefore never depends on input list order or dict/object
iteration order).

Thresholds are provisional. They are meant to be tuned against real shadow-mode
data before the matcher is allowed to write workouts.is_completed.
"""

from dataclasses import dataclass

from services.matching.bundler import SessionBundle
from services.matching.scorer import MatchScore, score_bundle

AUTO_ACCEPT_THRESHOLD = 0.80
SUGGEST_THRESHOLD = 0.55


@dataclass
class Assignment:
    bundle: SessionBundle
    workout_id: int | None
    score: MatchScore
    confidence_band: str  # "auto" | "suggest" | "unmatched"


def _band(total: float) -> str:
    if total >= AUTO_ACCEPT_THRESHOLD:
        return "auto"
    if total >= SUGGEST_THRESHOLD:
        return "suggest"
    return "unmatched"


def assign(bundles: list[SessionBundle], workouts: list[dict]) -> list[Assignment]:
    """Returns exactly one Assignment per bundle, in the order given.

    A bundle with no acceptable workout is returned with workout_id=None rather
    than dropped -- an unmatched activity is a real outcome the athlete should
    still see.
    """
    scored: list[tuple[float, int, int, SessionBundle, MatchScore]] = []
    for bundle in bundles:
        for workout in workouts:
            result = score_bundle(bundle, workout)
            if result.total >= SUGGEST_THRESHOLD:
                first_activity = bundle.activity_ids[0] if bundle.activity_ids else 0
                scored.append((result.total, int(workout["id"]), first_activity, bundle, result))

    # Highest score first; deterministic tie-break so repeated runs agree.
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))

    taken_bundles: set[int] = set()
    taken_workouts: set[int] = set()
    chosen: dict[int, tuple[int, MatchScore]] = {}

    for _total, workout_id, _first_activity, bundle, result in scored:
        bundle_key = id(bundle)
        if bundle_key in taken_bundles or workout_id in taken_workouts:
            continue
        taken_bundles.add(bundle_key)
        taken_workouts.add(workout_id)
        chosen[bundle_key] = (workout_id, result)

    assignments: list[Assignment] = []
    for bundle in bundles:
        picked = chosen.get(id(bundle))
        if picked is None:
            empty = MatchScore(total=0.0, components={}, reasons=["no workout scored high enough"])
            assignments.append(Assignment(bundle, None, empty, "unmatched"))
        else:
            workout_id, result = picked
            assignments.append(Assignment(bundle, workout_id, result, _band(result.total)))
    return assignments

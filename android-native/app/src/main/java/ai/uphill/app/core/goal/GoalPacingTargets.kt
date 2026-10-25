package ai.uphill.app.core.goal

import java.time.LocalDate
import java.time.temporal.ChronoUnit

/** Matches GoalEstimate's terrain targets after the assessment response is mapped on iOS. */
data class GoalPacingTargets(
    val climbing: Double,
    val flat: Double,
    val descent: Double,
    val average: Double,
)

fun GoalAssessmentResponse.pacingTargets(): GoalPacingTargets {
    val flat = context?.athlete?.easyPaceMinKm ?: 5.5
    val climbPenalty =
        ((elevationGainM ?: 0.0) / distanceKm.coerceAtLeast(1.0) * 0.08).coerceIn(2.5, 6.0)
    return GoalPacingTargets(
        flat + climbPenalty,
        flat,
        (flat * 0.88).coerceAtLeast(3.5),
        (goals?.b ?: 330.0) / distanceKm.coerceAtLeast(1.0),
    )
}

fun goalWeeksToRace(raceDate: LocalDate, today: LocalDate = LocalDate.now()): Int =
    (ChronoUnit.DAYS.between(today, raceDate).coerceAtLeast(0) / 7).toInt()

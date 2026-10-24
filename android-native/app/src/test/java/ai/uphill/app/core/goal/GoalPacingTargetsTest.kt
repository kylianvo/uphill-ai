package ai.uphill.app.core.goal

import java.time.LocalDate
import org.junit.Assert.*
import org.junit.Test

class GoalPacingTargetsTest {
    @Test
    fun targetsUseAssessmentEasyPaceGainAndRealisticGoal() {
        val response =
            GoalAssessmentResponse(
                distanceKm = 50.0,
                elevationGainM = 2200.0,
                goals = GoalTiers(300.0, 360.0, 420.0),
                context = GoalContext(athlete = GoalAthleteContext(6.0)),
            )
        val target = response.pacingTargets()
        assertEquals(9.52, target.climbing, 0.0001)
        assertEquals(6.0, target.flat, 0.0001)
        assertEquals(5.28, target.descent, 0.0001)
        assertEquals(7.2, target.average, 0.0001)
    }

    @Test
    fun absentContextUsesSourceDefaultsAndTerrainBounds() {
        val flatCourse = GoalAssessmentResponse(distanceKm = 50.0).pacingTargets()
        assertEquals(5.5, flatCourse.flat, 0.0001)
        assertEquals(8.0, flatCourse.climbing, 0.0001)
        assertEquals(6.6, flatCourse.average, 0.0001)
        val steepCourse =
            GoalAssessmentResponse(
                    distanceKm = 0.0,
                    elevationGainM = 1000.0,
                    context = GoalContext(athlete = GoalAthleteContext(3.0)),
                )
                .pacingTargets()
        assertEquals(9.0, steepCourse.climbing, 0.0001)
        assertEquals(3.5, steepCourse.descent, 0.0001)
        assertEquals(330.0, steepCourse.average, 0.0001)
    }

    @Test
    fun weeksUseWholeLocalDaysAndClampPastRaces() {
        val today = LocalDate.of(2026, 10, 14)
        assertEquals(0, goalWeeksToRace(today.minusDays(1), today))
        assertEquals(0, goalWeeksToRace(today.plusDays(6), today))
        assertEquals(1, goalWeeksToRace(today.plusDays(13), today))
        assertEquals(2, goalWeeksToRace(today.plusDays(14), today))
    }
}

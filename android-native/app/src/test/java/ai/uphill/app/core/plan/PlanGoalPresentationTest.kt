package ai.uphill.app.core.plan

import ai.uphill.app.core.models.Plan
import org.junit.Assert.*
import org.junit.Test

class PlanGoalPresentationTest {
    private val plan = Plan(id = 1, courseDistanceKm = 50.0)

    @Test
    fun pillWaitsForAssessmentAndRaceDistance() {
        assertNull(planGoalPill(plan, null))
        assertNull(planGoalPill(plan.copy(courseDistanceKm = null), PlanGoal()))
    }

    @Test
    fun noTargetFormatsOnlyStatusSuggestionWithIosRounding() {
        assertEquals(
            PlanGoalPresentation("Suggested %@", 61),
            planGoalPill(plan, PlanGoal(status = GoalStatus("no_target", 60.5))),
        )
        assertEquals("1:01", minutesText(60.5))
        assertEquals(
            "Not assessed yet",
            planGoalPill(plan, PlanGoal(status = GoalStatus("no_target")))?.key,
        )
        assertEquals(
            "On track",
            planGoalPill(plan, PlanGoal(status = GoalStatus("on_track", 61.0)))?.key,
        )
        assertEquals(
            "Ahead of target",
            planGoalPill(plan, PlanGoal(status = GoalStatus("ahead")))?.key,
        )
        assertEquals(
            "Behind target",
            planGoalPill(plan, PlanGoal(status = GoalStatus("behind")))?.key,
        )
    }

    @Test
    fun raceCardFallbackUsesPlanGoalType() {
        assertEquals(
            PlanGoalPresentation("Goal %lldh %@m", 91),
            planGoalText(plan.copy(goalType = "time", targetTimeHours = 90.5 / 60)),
        )
        assertNull(planGoalText(plan.copy(goalType = "time")))
        assertEquals("Goal: finish strong", planGoalText(plan)?.key)
        assertEquals("Goal: best possible time", planGoalText(plan.copy(goalType = "optimal"))?.key)
        assertNull(planGoalText(plan.copy(goalType = "start_running")))
    }
}

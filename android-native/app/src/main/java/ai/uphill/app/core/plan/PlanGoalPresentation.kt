package ai.uphill.app.core.plan

import ai.uphill.app.core.models.Plan
import kotlin.math.roundToInt

/** The source string key and time arguments used by the iOS plan header and race card. */
data class PlanGoalPresentation(val key: String, val minutes: Int? = null)

fun planGoalPill(plan: Plan, goal: PlanGoal?): PlanGoalPresentation? {
    if (goal == null || plan.courseDistanceKm == null) return null
    return when (goal.status.state) {
        "on_track" -> PlanGoalPresentation("On track")
        "ahead" -> PlanGoalPresentation("Ahead of target")
        "behind" -> PlanGoalPresentation("Behind target")
        "no_target" ->
            goal.status.suggestedMins?.let { PlanGoalPresentation("Suggested %@", it.roundToInt()) }
                ?: PlanGoalPresentation("Not assessed yet")
        else -> PlanGoalPresentation("Not assessed yet")
    }
}

fun planGoalText(plan: Plan): PlanGoalPresentation? =
    when (plan.goalType) {
        "time" ->
            plan.targetTimeHours?.let {
                PlanGoalPresentation("Goal %lldh %@m", (it * 60).roundToInt())
            }
        "finish" -> PlanGoalPresentation("Goal: finish strong")
        "optimal" -> PlanGoalPresentation("Goal: best possible time")
        else -> null
    }

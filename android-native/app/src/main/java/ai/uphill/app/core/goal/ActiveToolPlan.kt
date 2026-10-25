package ai.uphill.app.core.goal

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class ActiveToolPlanResponse(val active: Boolean = false, val plan: ActiveToolPlan? = null)

@Serializable
data class ActiveToolPlan(
    val id: Int,
    val raceName: String = "",
    val raceDate: String = "",
    val goalType: String = "",
    val courseDistanceKm: Double? = null,
    val courseElevationGainM: Double? = null,
    val targetTimeHours: Double? = null,
) {
    val targetMinutes
        get() = targetTimeHours?.takeIf { it > 0 }?.times(60)

    fun gearContext() =
        "$raceName on $raceDate, Goal: $goalType, Distance: ${courseDistanceKm?:"N/A"}km, Elevation: ${courseElevationGainM?:"N/A"}m" +
            (targetTimeHours?.takeIf { it > 0 }?.let { ", Target Time: ${it}h" } ?: "")
}

class ToolPlanService(private val api: APIClient) {
    suspend fun active(): ActiveToolPlan? =
        try {
            api.send<ActiveToolPlanResponse>(Endpoint("GET", "/api/coach/active-plan")).let {
                if (it.active) it.plan else null
            }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            null
        }

    suspend fun applyGoal(planId: Int, targetMinutes: Double) {
        api.element(
            Endpoint(
                "POST",
                "/api/plans/$planId/goal/apply",
                buildJsonObject { put("target_mins", targetMinutes) },
            )
        )
    }
}

/** Carries explicit tool actions across the standalone routes in the shell. */
object ToolHandoff {
    var pacingTargetMinutes: Double? = null
    var fuelingHours: Double? = null
}

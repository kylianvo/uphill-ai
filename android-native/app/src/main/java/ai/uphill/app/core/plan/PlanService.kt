package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.*
import java.time.ZonedDateTime
import kotlin.math.roundToInt
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable private data class WorkoutsResponse(val workouts: List<Workout>)

@Serializable private data class PlansResponse(val plans: List<Plan>)

@Serializable private data class MatchesResponse(val activities: List<WatchActivity> = emptyList())

class PlanService(val api: APIClient, val athleteId: Int? = null) {
    private val coachPrefix
        get() = athleteId?.let { "/api/coaching/athletes/$it" }

    private val prefix
        get() = coachPrefix ?: "/api/coach"

    private fun goalPath(id: Int) = "${coachPrefix ?: "/api"}/plans/$id/goal"

    suspend fun activePlan(): PlanSnapshot? {
        val snapshot =
            api.send<ActivePlanResponse>(Endpoint("GET", "$prefix/active-plan")).snapshot
                ?: return null
        if (athleteId != null) return snapshot
        val matches =
            runCatching { watchActivities(snapshot.plan.id) }
                .getOrDefault(emptyList())
                .filter { it.workoutId != null }
                .groupBy { it.workoutId }
        return snapshot.copy(
            workouts =
                snapshot.workouts.map { workout ->
                    matches[workout.id]?.firstOrNull()?.let { a ->
                        workout.copy(
                            matchedActivityId = a.activityId,
                            matchedDeviceModel = a.deviceModel,
                            matchedDistanceKm = a.distanceKm,
                            matchedDurationSeconds = a.durationSeconds,
                            matchedAvgHr = a.avgHr?.roundToInt(),
                        )
                    } ?: workout
                }
        )
    }

    suspend fun log(
        id: Int,
        completed: Int? = null,
        missed: Int? = null,
        rpe: Int? = null,
        notes: String? = null,
    ): List<Workout> =
        api.send<WorkoutsResponse>(
                Endpoint(
                    "PATCH",
                    "/api/coach/workouts/log",
                    buildJsonObject {
                        put("workout_id", id)
                        completed?.let { put("is_completed", it) }
                        missed?.let { put("is_missed", it) }
                        rpe?.let { put("rpe", it) }
                        notes?.let { put("notes", it) }
                    },
                )
            )
            .workouts

    suspend fun move(
        planId: Int,
        workoutId: Int,
        week: Int,
        day: Weekday,
        today: String,
    ): CalendarMoveResult =
        api.send(
            Endpoint(
                "POST",
                "/api/coach/calendar/move",
                buildJsonObject {
                    put("plan_id", planId)
                    put("client_today", today)
                    putJsonArray("operations") {
                        add(
                            buildJsonObject {
                                put("workout_id", workoutId)
                                put("target_week", week)
                                put("target_day", day.name)
                            }
                        )
                    }
                },
            )
        )

    suspend fun swap(
        planId: Int,
        week: Int,
        day1: Weekday,
        day2: Weekday,
        today: String,
    ): CalendarMoveResult =
        api.send(
            Endpoint(
                "POST",
                "/api/coach/modify-calendar",
                buildJsonObject {
                    put("plan_id", planId)
                    put("week_number", week)
                    put("day_1", day1.name)
                    put("day_2", day2.name)
                    put("client_today", today)
                },
            )
        )

    suspend fun deletePlan(id: Int) {
        check(athleteId == null)
        api.element(Endpoint("DELETE", "/api/coach/plans/$id"))
    }

    suspend fun recentPlans(): List<Plan> =
        api.send<PlansResponse>(Endpoint("GET", "$prefix/recent-plans")).plans

    suspend fun selectPlan(id: Int): PlanSnapshot? {
        check(athleteId == null)
        return api.send<ActivePlanResponse>(
                Endpoint("POST", "/api/coach/select-plan", buildJsonObject { put("plan_id", id) })
            )
            .snapshot
    }

    suspend fun blockCompletion(id: Int): BlockCompletionResponse =
        api.send(Endpoint("GET", "$prefix/block-completion/$id"))

    suspend fun weekReview(id: Int, week: Int): WeekReview =
        api.send(Endpoint("GET", "$prefix/week-review/$id/$week"))

    suspend fun blockEvaluation(id: Int, block: Int): BlockEvaluation =
        api.send(Endpoint("GET", "$prefix/block-evaluation/$id/$block"))

    suspend fun goal(id: Int, lang: String): PlanGoal =
        api.send(Endpoint("GET", goalPath(id), query = mapOf("lang" to lang)))

    suspend fun reassessGoal(id: Int, lang: String): PlanGoal =
        api.send(
            Endpoint(
                "POST",
                "${goalPath(id)}/reassess",
                buildJsonObject {
                    put("lang", lang)
                    put("exclude", JsonArray(emptyList()))
                },
            )
        )

    suspend fun applyGoal(id: Int, minutes: Double): PlanGoal =
        api.send(
            Endpoint(
                "POST",
                "${goalPath(id)}/apply",
                buildJsonObject { put("target_mins", minutes) },
            )
        )

    suspend fun watchActivities(id: Int): List<WatchActivity> =
        api.send<MatchesResponse>(
                Endpoint("GET", "/api/integrations/matching", query = mapOf("plan_id" to "$id"))
            )
            .activities

    suspend fun setMatch(activityId: Int, workoutId: Int?) {
        api.element(
            Endpoint(
                "PATCH",
                "/api/integrations/matching/$activityId",
                query = workoutId?.let { mapOf("workout_id" to "$it") } ?: emptyMap(),
            )
        )
    }

    suspend fun syncWatch(id: Int): Int {
        val result =
            api.element(
                    Endpoint(
                        "POST",
                        "/api/integrations/coros/sync",
                        query = mapOf("plan_id" to "$id"),
                    )
                )
                .jsonObject
        api.element(
            Endpoint(
                "POST",
                "/api/integrations/matching/run",
                query =
                    mapOf(
                        "plan_id" to "$id",
                        "tz_offset_minutes" to "${ZonedDateTime.now().offset.totalSeconds/60}",
                    ),
            )
        )
        return result["activities"]?.jsonPrimitive?.intOrNull ?: 0
    }

    suspend fun knowledge(topic: String, lang: String): JsonObject? =
        runCatching {
                api.element(
                        Endpoint(
                            "GET",
                            "/api/knowledge/cards",
                            query = mapOf("topic" to topic, "lang" to lang),
                        )
                    )
                    .jsonObject["cards"]
                    ?.jsonArray
                    ?.firstOrNull()
                    ?.jsonObject
            }
            .getOrNull()

    suspend fun ics(id: Int, raceDate: String, timePref: String): String =
        api.text(
            Endpoint(
                "GET",
                "/api/coach/export-ics",
                query = mapOf("plan_id" to "$id", "race_date" to raceDate, "time_pref" to timePref),
            )
        )
}

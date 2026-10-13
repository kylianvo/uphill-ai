package ai.uphill.app.core.coaching

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.networking.*
import kotlin.math.roundToInt
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class CoachedAthleteRow(
    val id: Int,
    val athleteId: Int,
    val athleteEmail: String,
    val athleteName: String? = null,
    val status: String = "active",
    val invitedAt: String? = null,
    val respondedAt: String? = null,
) {
    val displayName
        get() = athleteName?.takeIf { it.isNotBlank() } ?: athleteEmail
}

@Serializable
data class CoachingInvite(
    val id: Int,
    val coachId: Int,
    val coachEmail: String,
    val coachName: String? = null,
    val status: String = "invited",
    val invitedAt: String? = null,
) {
    val displayName
        get() = coachName?.takeIf { it.isNotBlank() } ?: coachEmail
}

@Serializable
data class CoachNote(
    val id: Int,
    val coachId: Int,
    val athleteId: Int,
    val targetType: String,
    val note: String,
    val targetId: Int? = null,
    val createdAt: String? = null,
)

@Serializable data class CoachNotesResponse(val notes: List<CoachNote> = emptyList())

@Serializable
data class CoachNoteCreatePayload(
    val targetType: String,
    val note: String,
    val targetId: Int? = null,
)

@Serializable
data class CoachAthleteActivePlan(
    val planId: Int,
    val raceName: String,
    val raceDate: String,
    val currentWeek: Int,
    val totalWeeks: Int,
)

@Serializable
data class CoachOverviewAthlete(
    val athleteId: Int,
    val name: String,
    val runnerLevel: String = "intermediate",
    val needsAttention: Boolean = false,
    val activePlan: CoachAthleteActivePlan? = null,
    val adherencePct: Double? = null,
    val missedStreak: Int = 0,
)

@Serializable
data class CoachDraftPlanItem(
    val planId: Int,
    val athleteId: Int,
    val athleteName: String,
    val raceName: String,
)

@Serializable
data class CoachPendingApprovalItem(
    val workoutId: Int,
    val planId: Int,
    val athleteId: Int,
    val athleteName: String,
    val title: String,
)

@Serializable
data class CoachActionItems(
    val draftPlans: List<CoachDraftPlanItem> = emptyList(),
    val pendingWorkoutApprovals: List<CoachPendingApprovalItem> = emptyList(),
)

@Serializable
data class CoachPhaseAlert(
    val athleteId: Int,
    val athleteName: String,
    val phase: String,
    val starts: String,
)

@Serializable data class WorkoutTypeMixEntry(val type: String, val count: Int, val pct: Double)

@Serializable data class AdherenceTrendEntry(val weekNumber: Int, val adherencePct: Double)

@Serializable data class MissedByDayEntry(val dayOfWeek: String, val count: Int)

@Serializable data class RaceBreakdownAthlete(val athleteId: Int, val name: String)

@Serializable
data class RaceBreakdownEntry(
    val raceName: String,
    val raceDate: String? = null,
    val count: Int,
    val athletes: List<RaceBreakdownAthlete> = emptyList(),
)

@Serializable
data class CoachRosterTotals(
    val distanceKm: Double? = null,
    val durationHours: Double? = null,
    val elevationGainM: Double? = null,
    val workoutCount: Int? = null,
)

@Serializable
data class CoachOverview(
    val athletes: List<CoachOverviewAthlete> = emptyList(),
    val actionItems: CoachActionItems = CoachActionItems(),
    val phaseAlerts: List<CoachPhaseAlert> = emptyList(),
    val workoutTypeMix: List<WorkoutTypeMixEntry> = emptyList(),
    val adherenceTrend: List<AdherenceTrendEntry> = emptyList(),
    val missedByDay: List<MissedByDayEntry> = emptyList(),
    val races: List<RaceBreakdownEntry> = emptyList(),
    val rosterTotals: CoachRosterTotals? = null,
    val athletesWithoutRace: Int? = 0,
)

fun coachPercent(fraction: Double) = "${(fraction*100).roundToInt()}%"

@Serializable
data class CoachPlan(
    val id: Int,
    val raceName: String,
    val raceDate: String,
    val totalWeeks: Int,
    val currentWeek: Int? = null,
    val planStatus: String? = null,
)

@Serializable
data class CoachWorkout(
    val id: Int,
    val planId: Int,
    val weekNumber: Int,
    val dayOfWeek: String,
    val title: String,
    val type: String,
    val durationMinutes: Double,
    val phase: String = "Base",
    val distanceKm: Double? = null,
    val targetZone: String = "Z2",
    val description: String? = null,
    val fuelingTip: String? = null,
    val approvedAt: String? = null,
    val isCompleted: Int? = null,
    val isMissed: Int? = null,
    val targetPace: String? = null,
    val targetHrRange: String? = null,
)

@Serializable data class CoachPlanSnapshot(val plan: CoachPlan, val workouts: List<CoachWorkout>)

@Serializable
data class CoachPlanResponse(
    val active: Boolean = false,
    val draft: Boolean = false,
    val plan: CoachPlan? = null,
    val workouts: List<CoachWorkout> = emptyList(),
) {
    val snapshot
        get() = plan?.takeIf { active || draft }?.let { CoachPlanSnapshot(it, workouts) }
}

@Serializable
data class CoachProfileUpdatePayload(
    val restingHr: Int? = null,
    val maxHr: Int? = null,
    val aetHr: Int? = null,
    val antHr: Int? = null,
    val zone2PaceMin: String? = null,
    val zone2PaceMax: String? = null,
    val thresholdPace: String? = null,
)

@Serializable
data class CoachWorkoutUpdatePayload(
    val title: String? = null,
    val type: String? = null,
    val durationMinutes: Double? = null,
    val distanceKm: Double? = null,
    val targetZone: String? = null,
    val description: String? = null,
    val fuelingTip: String? = null,
    val dayOfWeek: String? = null,
)

@Serializable
data class CoachWorkoutCreatePayload(
    val weekNumber: Int,
    val dayOfWeek: String,
    val phase: String,
    val title: String,
    val type: String,
    val durationMinutes: Double,
    val targetZone: String,
    val distanceKm: Double? = null,
    val description: String? = null,
    val fuelingTip: String? = null,
)

@Serializable
data class CoachWorkoutAiCreatePayload(
    val weekNumber: Int,
    val dayOfWeek: String,
    val workoutType: String,
    val durationMinutes: Double,
)

/** Editing sends only changed nonblank fields, matching iOS and the PATCH contract. */
data class PhysiologyDraft(
    val restingHr: String = "",
    val aetHr: String = "",
    val antHr: String = "",
    val maxHr: String = "",
    val zone2PaceMin: String = "",
    val zone2PaceMax: String = "",
    val thresholdPace: String = "",
) {
    private fun fields() =
        mapOf(
            "resting_hr" to restingHr,
            "aet_hr" to aetHr,
            "ant_hr" to antHr,
            "max_hr" to maxHr,
            "zone2_pace_min" to zone2PaceMin,
            "zone2_pace_max" to zone2PaceMax,
            "threshold_pace" to thresholdPace,
        )

    fun validate() {
        val hrs =
            listOf(restingHr, aetHr, antHr, maxHr)
                .filter { it.isNotBlank() }
                .map { it.trim().toIntOrNull() ?: error("Heart rate must be a whole number.") }
        val bounds =
            listOf(restingHr to 30..120, aetHr to 80..220, antHr to 90..225, maxHr to 120..230)
        require(
            bounds.all { (text, range) ->
                text.isBlank() || text.trim().toIntOrNull()?.let { it in range } == true
            }
        ) {
            "Heart rate is outside the supported range."
        }
        require(hrs.zipWithNext().all { it.first < it.second }) {
            "Resting HR, AeT, AnT and Max HR must increase in that order."
        }
        fun pace(s: String): Int? {
            if (s.isBlank()) return null
            require(Regex("\\d{1,2}:[0-5]\\d").matches(s.trim())) { "Enter pace as 5:30." }
            return s.trim()
                .split(':')
                .let { it[0].toInt() * 60 + it[1].toInt() }
                .also { require(it > 0) }
        }
        val slow = pace(zone2PaceMin)
        val fast = pace(zone2PaceMax)
        val threshold = pace(thresholdPace)
        require(slow == null || fast == null || slow >= fast) {
            "Zone 2 slow end must be slower than the fast end."
        }
        require(fast == null || threshold == null || threshold < fast) {
            "Threshold pace must be faster than Zone 2."
        }
    }

    fun patch(original: PhysiologyDraft): JsonObject {
        validate()
        return buildJsonObject {
            fields().forEach { (key, value) ->
                val v = value.trim()
                if (v.isNotEmpty() && v != original.fields()[key]?.trim()) {
                    if (key.endsWith("_hr")) put(key, v.toInt()) else put(key, v)
                }
            }
        }
    }

    companion object {
        fun from(u: User) =
            PhysiologyDraft(
                u.restingHr?.toString().orEmpty(),
                u.aetHr?.toString().orEmpty(),
                u.antHr?.toString().orEmpty(),
                u.maxHr?.toString().orEmpty(),
                u.zone2PaceMin.orEmpty(),
                u.zone2PaceMax.orEmpty(),
                u.thresholdPace.orEmpty(),
            )
    }
}

class CoachingService(private val api: APIClient) {
    suspend fun overview(
        days: Int = 14,
        level: String = "all",
        athleteId: Int? = null,
    ): CoachOverview =
        api.send(
            Endpoint(
                "GET",
                "/api/coaching/overview",
                query =
                    buildMap {
                        put("days", "$days")
                        if (level != "all") put("level", level)
                        athleteId?.let { put("athlete_id", "$it") }
                    },
            )
        )

    suspend fun roster(): List<CoachedAthleteRow> =
        api.send(Endpoint("GET", "/api/coaching/roster"))

    suspend fun invites(): List<CoachingInvite> =
        api.send(Endpoint("GET", "/api/coaching/my-invites"))

    suspend fun invite(email: String): CoachedAthleteRow {
        require(email.trim().contains('@')) { "Enter an email address." }
        return api.send(
            Endpoint(
                "POST",
                "/api/coaching/invite",
                buildJsonObject { put("athlete_email", email.trim()) },
            )
        )
    }

    suspend fun accept(id: Int) {
        api.text(Endpoint("POST", "/api/coaching/invites/$id/accept"))
    }

    suspend fun decline(id: Int) {
        api.text(Endpoint("POST", "/api/coaching/invites/$id/decline"))
    }

    suspend fun removeAthlete(id: Int) {
        api.text(Endpoint("DELETE", "/api/coaching/roster/$id"))
    }

    suspend fun profile(id: Int): User =
        api.send(Endpoint("GET", "/api/coaching/athletes/$id/profile"))

    suspend fun updateProfile(id: Int, patch: JsonObject): User =
        api.send(Endpoint("PATCH", "/api/coaching/athletes/$id/profile", patch))

    suspend fun activePlan(id: Int): CoachPlanSnapshot? =
        api.send<CoachPlanResponse>(Endpoint("GET", "/api/coaching/athletes/$id/active-plan"))
            .snapshot

    suspend fun draftPlan(id: Int): CoachPlanSnapshot? =
        api.send<CoachPlanResponse>(Endpoint("GET", "/api/coaching/athletes/$id/plans/draft"))
            .snapshot

    private fun workoutPath(athlete: Int, plan: Int, id: Int? = null) =
        "/api/coaching/athletes/$athlete/plans/$plan/workouts" + (id?.let { "/$it" } ?: "")

    suspend fun approve(athlete: Int, plan: Int, id: Int): CoachWorkout =
        api.send(Endpoint("POST", workoutPath(athlete, plan, id) + "/approve"))

    suspend fun removeWorkout(athlete: Int, plan: Int, id: Int): CoachWorkout =
        api.send(Endpoint("POST", workoutPath(athlete, plan, id) + "/remove"))

    suspend fun editWorkout(
        athlete: Int,
        plan: Int,
        id: Int,
        p: CoachWorkoutUpdatePayload,
    ): CoachWorkout =
        api.send(
            Endpoint("PUT", workoutPath(athlete, plan, id), JSONCoding.json.encodeToJsonElement(p))
        )

    suspend fun addWorkout(athlete: Int, plan: Int, p: CoachWorkoutCreatePayload): CoachWorkout =
        api.send(
            Endpoint("POST", workoutPath(athlete, plan), JSONCoding.json.encodeToJsonElement(p))
        )

    suspend fun aiCreateWorkout(
        athlete: Int,
        plan: Int,
        p: CoachWorkoutAiCreatePayload,
    ): CoachWorkout =
        api.send(
            Endpoint(
                "POST",
                workoutPath(athlete, plan) + "/ai-create",
                JSONCoding.json.encodeToJsonElement(p),
            )
        )

    suspend fun notes(id: Int, targetType: String? = null, targetId: Int? = null): List<CoachNote> =
        api.send<CoachNotesResponse>(
                Endpoint(
                    "GET",
                    "/api/coaching/athletes/$id/notes",
                    query =
                        buildMap {
                            targetType?.let { put("target_type", it) }
                            targetId?.let { put("target_id", "$it") }
                        },
                )
            )
            .notes

    suspend fun addNote(id: Int, p: CoachNoteCreatePayload): CoachNote {
        require(p.note.isNotBlank())
        return api.send(
            Endpoint(
                "POST",
                "/api/coaching/athletes/$id/notes",
                JSONCoding.json.encodeToJsonElement(p),
            )
        )
    }
}

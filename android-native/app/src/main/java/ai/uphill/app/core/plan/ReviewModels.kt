package ai.uphill.app.core.plan

import ai.uphill.app.core.models.Workout
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class BlockCompletion(
    val blockNumber: Int,
    val weekStart: Int,
    val weekEnd: Int,
    val completionPct: Double,
    val unlocked: Boolean,
    val aiLastWeekReview: String? = null,
    val aiThisWeekDescription: String? = null,
)

@Serializable
data class BlockCompletionResponse(
    val blocks: List<BlockCompletion> = emptyList(),
    val maxGeneratedWeek: Int = 0,
)

@Serializable
data class WeekPlannedVolume(
    val durationMinutes: Double? = null,
    val distanceKm: Double? = null,
    val elevationGainM: Double? = null,
    val workoutCount: Int? = null,
)

@Serializable
data class WeekActualVolume(
    val totalActualKm: Double? = null,
    val totalActualMinutes: Double? = null,
    val totalActualVertM: Double? = null,
    val matchedKm: Double? = null,
    val matchedCount: Int? = null,
    val unplannedKm: Double? = null,
    val unplannedHours: Double? = null,
    val unplannedCount: Int? = null,
)

@Serializable
data class WeekNarrative(
    val summary: String? = null,
    val highlights: List<String> = emptyList(),
    val watch: List<String> = emptyList(),
)

@Serializable
data class WeekReviewActual(
    val state: String,
    val distanceKm: Double? = null,
    val durationMinutes: Double? = null,
)

@Serializable
data class WeekReviewEntry(
    val workoutId: Int,
    val actual: WeekReviewActual,
    val dayOfWeek: String? = null,
    val title: String? = null,
    val type: String? = null,
)

@Serializable
data class WeekReview(
    val weekNumber: Int,
    val completionPct: Double,
    val checkboxCompletionPct: Double? = null,
    val perWorkout: List<WeekReviewEntry> = emptyList(),
    val narrative: WeekNarrative? = null,
    val planned: WeekPlannedVolume? = null,
    val actual: WeekActualVolume? = null,
)

@Serializable data class GoalTiers(val a: Double, val b: Double, val c: Double)

@Serializable data class GoalAnchor(val id: String, val method: String, val minutes: Double)

@Serializable
data class GoalAssessment(
    val id: Int = 0,
    val goals: GoalTiers? = null,
    val confidence: String? = null,
    val reasoning: List<JsonElement> = emptyList(),
    val missing: List<JsonElement> = emptyList(),
    val engine: String? = null,
    val createdAt: String? = null,
    val context: JsonObject? = null,
    val anchors: List<GoalAnchor> = emptyList(),
) {
    val reasoningText
        get() = reasoning.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }

    val missingText
        get() = missing.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }
}

@Serializable
data class GoalStatus(val state: String = "not_assessed", val suggestedMins: Double? = null)

@Serializable
data class PlanGoal(
    val assessment: GoalAssessment? = null,
    val status: GoalStatus = GoalStatus(),
    val targetTimeHours: Double? = null,
) {
    val suggestedMinutes
        get() =
            (status.suggestedMins ?: assessment?.goals?.b)?.takeIf {
                targetTimeHours == null ||
                    kotlin.math.round(targetTimeHours * 60) != kotlin.math.round(it)
            }
}

@Serializable
data class BlockEvaluation(
    val blockNumber: Int,
    val sessionsTotal: Int,
    val sessionsCompleted: Int,
    val sessionsMissed: Int,
    val completionPct: Double,
    val plannedKm: Double,
    val actualKm: Double,
    val avgQualityScore: Double? = null,
    val qualityGrade: String? = null,
    val coachingTakeaways: List<String> = emptyList(),
    val coachSummary: String? = null,
    val coachNotes: List<String> = emptyList(),
)

@Serializable
data class WatchActivity(
    val activityId: Int,
    val workoutId: Int? = null,
    val workoutTitle: String? = null,
    val distanceKm: Double? = null,
    val durationSeconds: Double? = null,
    val avgHr: Double? = null,
    val startTime: String? = null,
    val deviceModel: String? = null,
    val matchMethod: String? = null,
    val sourceProvider: String? = null,
) {
    val settled
        get() = workoutId != null && matchMethod in listOf("auto", "manual")
}

@Serializable
data class ScheduleWarning(val code: String, val params: Map<String, JsonElement> = emptyMap()) {
    val values
        get() = params.mapValues { (_, v) -> (v as? JsonPrimitive)?.contentOrNull.orEmpty() }
}

@Serializable
data class CalendarMoveResult(
    val workouts: List<Workout>,
    val warnings: List<ScheduleWarning> = emptyList(),
)

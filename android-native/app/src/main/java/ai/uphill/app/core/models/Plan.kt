package ai.uphill.app.core.models

import kotlinx.serialization.Serializable

@Serializable
enum class Weekday {
    Monday,
    Tuesday,
    Wednesday,
    Thursday,
    Friday,
    Saturday,
    Sunday;

    val offset
        get() = ordinal

    val short
        get() = name.take(3)

    companion object {
        fun parse(value: String?) = entries.firstOrNull { it.name == value } ?: Monday
    }
}

@Serializable
data class Plan(
    val id: Int,
    val raceName: String = "",
    val raceDate: String = "",
    val goalType: String = "finish",
    val targetTimeHours: Double? = null,
    val totalWeeks: Int = 1,
    val currentWeek: Int? = null,
    val courseDistanceKm: Double? = null,
    val courseElevationGainM: Double? = null,
    val startDate: String? = null,
    val planStatus: String? = null,
    val createdAt: String? = null,
    val longRunDay: String? = null,
    val daysPerWeek: Int? = null,
    val preferredRunDays: String? = null,
    val doubleSessionDays: String? = null,
    val hasGymAccess: Boolean? = null,
    val useTreadmill: Boolean? = null,
    val trainingEnvironment: String? = null,
    val mountainDays: String? = null,
    val stairAccess: Boolean? = null,
    val treadmillMaxIncline: Int? = null,
    val maxContinuousJogMin: Int? = null,
)

@Serializable
data class Workout(
    val id: Int,
    val planId: Int,
    val weekNumber: Int,
    val dayOfWeek: String = "Monday",
    val phase: String = "",
    val title: String = "",
    val type: String = "",
    val durationMinutes: Double = 0.0,
    val distanceKm: Double? = null,
    val targetZone: String = "",
    val targetHrRange: String? = null,
    val targetPace: String? = null,
    val treadmillIncline: String? = null,
    val treadmillSpeed: String? = null,
    val elevationGainM: Double? = null,
    val gradePercent: Double? = null,
    val intervalReps: Int? = null,
    val intervalRepValue: Double? = null,
    val intervalRepUnit: String? = null,
    val walkIntervalValue: Double? = null,
    val description: String? = null,
    val fuelingTip: String? = null,
    val source: String? = null,
    val isCompleted: Int? = null,
    val isMissed: Int? = null,
    val approvedAt: String? = null,
    val rpe: Int? = null,
    val notes: String? = null,
    val sessionSlot: String? = null,
    val isPriority: Boolean = false,
    val matchedActivityId: Int? = null,
    val matchedDeviceModel: String? = null,
    val matchedDistanceKm: Double? = null,
    val matchedDurationSeconds: Double? = null,
    val matchedAvgHr: Int? = null,
    val matchedSourceProvider: String? = null,
) {
    val weekday
        get() = Weekday.parse(dayOfWeek)

    val isRest
        get() = type == "Rest" || durationMinutes == 0.0

    val matchedFromAppleHealth
        get() = matchedSourceProvider == "apple_health"

    val matchedSourceName
        get() = if (matchedFromAppleHealth) "Apple Health" else "COROS"

    val isMatched
        get() = matchedActivityId != null || (matchedDistanceKm ?: 0.0) > 0

    val isDone
        get() = isCompleted == 1 || (isCompleted != 0 && isMatched)

    val isMissedFlag
        get() = isMissed == 1

    val isStrengthOrME
        get() =
            listOf(type, title).any {
                val value = it.lowercase()
                value.contains("strength") || value.contains("muscular endurance") || value == "me"
            }
}

@Serializable data class PlanSnapshot(val plan: Plan, val workouts: List<Workout> = emptyList())

@Serializable
data class ActivePlanResponse(
    val active: Boolean,
    val plan: Plan? = null,
    val workouts: List<Workout>? = null,
) {
    val snapshot
        get() = if (active && plan != null) PlanSnapshot(plan, workouts.orEmpty()) else null
}

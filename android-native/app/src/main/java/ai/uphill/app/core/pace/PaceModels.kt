package ai.uphill.app.core.pace

import kotlinx.serialization.Serializable

@Serializable
data class CourseCheckpoint(
    val name: String,
    val distanceMeters: Double,
    val elevationMeters: Double,
    val segmentGainMeters: Double,
    val segmentLossMeters: Double,
)

@Serializable
data class PacedCheckpoint(
    val name: String,
    val distanceKm: Double,
    val elevationM: Double,
    val targetPace: String,
    val splitTime: String,
    val cumulativeTimeMins: Double,
    val flatEquivalentKm: Double,
    val gradePct: Double,
    val effort: String,
    val tempC: Double? = null,
    val rainMm: Double? = null,
    val afterSunset: Boolean? = null,
    val energyKcal: Int? = null,
)

@Serializable
data class PacingRequest(
    val checkpoints: List<CourseCheckpoint>,
    val targetTimeMins: Double? = null,
    val targetFlatPaceMinKm: Double? = null,
    val splitBias: Double? = null,
    val runnerWeightKg: Double? = null,
    val raceStartIso: String? = null,
)

data class GpxCourseResult(
    val fileName: String,
    val totalDistanceKm: Double,
    val totalElevationGainM: Double,
    val totalElevationLossM: Double,
    val minElevationM: Double,
    val maxElevationM: Double,
    val checkpoints: List<CourseCheckpoint>,
    val trackpointCount: Int,
    val waypointNames: List<String>,
)

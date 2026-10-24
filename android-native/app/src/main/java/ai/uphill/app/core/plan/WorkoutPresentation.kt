package ai.uphill.app.core.plan

/** Mirror iOS: the tile label already supplies /km; normalize range separators. */
fun paceTileValue(pace: String?): String =
    pace
        ?.trim()
        ?.replace(Regex("\\s*/\\s*km\\s*$", RegexOption.IGNORE_CASE), "")
        ?.replace(Regex("\\s*[-–—]\\s*"), "–")
        ?.takeIf { it.isNotEmpty() } ?: "—"

fun workoutChipLabel(workout: ai.uphill.app.core.models.Workout): String {
    val type = workout.type.lowercase()
    return when {
        type.contains("interval") || type.contains("hill") -> "Intervals"
        type.contains("long") -> "Long"
        type.contains("recovery") -> "Recovery"
        type.contains("easy") || type.contains("aerobic") -> "Easy"
        type.contains("tempo") -> "Tempo"
        type.contains("threshold") -> "Threshold"
        type.contains("me") || type.contains("muscular") -> "ME"
        type.contains("strength") -> "Strength"
        type.contains("cross") -> "Cross"
        type == "rest" -> "Rest"
        else -> workout.type
    }
}

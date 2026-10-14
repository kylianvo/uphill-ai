package ai.uphill.app.designsystem

import ai.uphill.app.core.models.Workout
import androidx.compose.ui.graphics.Color

/** Shared light-mode effort palette from current iOS WorkoutTypePresentation. */
fun workoutEffortColor(workout: Workout): Color {
    val type = workout.type.lowercase()
    val zone = workout.targetZone.lowercase()
    return when {
        type.contains("strength") || type.contains("me") || type.contains("muscular") ->
            Color(0xFF7C3AED)
        type.contains("interval") ||
            type.contains("hill") ||
            zone.contains('4') ||
            zone.contains('5') -> Color(0xFFDC2626)
        type.contains("tempo") || type.contains("threshold") || zone.contains('3') ->
            Color(0xFFB45309)
        type.contains("long") -> Color(0xFF047857)
        type.contains("recovery") || zone.contains('1') -> Color(0xFF0E7490)
        type.contains("easy") || zone.contains('2') -> Color(0xFF2563EB)
        type.contains("cross") -> Color(0xFF0F766E)
        else -> Color(0xFF6B7280)
    }
}

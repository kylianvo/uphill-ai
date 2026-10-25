package ai.uphill.app.designsystem

import ai.uphill.app.core.models.Workout
import androidx.compose.ui.graphics.toArgb
import org.junit.Assert.assertEquals
import org.junit.Test

class WorkoutColorsTest {
    @Test
    fun effortColorsFollowCurrentIOSPriorityAndRecoveryDiffersFromEasy() {
        fun color(type: String, zone: String = "Z2") =
            workoutEffortColor(Workout(1, 1, 1, title = type, type = type, targetZone = zone))
                .toArgb()
        assertEquals(0xFFDC2626.toInt(), color("Hill Repeats"))
        assertEquals(0xFF7C3AED.toInt(), color("Strength", "Z4"))
        assertEquals(0xFF047857.toInt(), color("Long Run"))
        assertEquals(0xFF0E7490.toInt(), color("Recovery Run"))
        assertEquals(0xFF2563EB.toInt(), color("Easy Run"))
        assertEquals(0xFFB45309.toInt(), color("Threshold"))
    }
}

package ai.uphill.app.core.plan

import ai.uphill.app.core.models.Workout
import org.junit.Assert.*
import org.junit.Test

class WorkoutDetailContentTest {
    private val workout =
        Workout(
            1,
            93,
            2,
            title = "Aerobic Run",
            type = "Easy",
            durationMinutes = 60.0,
            targetPace = "6:10-6:50",
        )

    @Test
    fun labelledNotesStayOutOfExecutionAndExplicitMainDurationWins() {
        val content =
            WorkoutDetailContent.make(
                workout.copy(
                    description =
                        "Overall: Build the base. / Process: Warm-up: 10 min jog → Main Set: 25 min steady → Cool-down: 5 min walk / Benefit: Aerobic capacity / Warning: Avoid heavy breathing / Coach note: Keep it conversational"
                )
            )
        assertEquals("Build the base.", content.intent)
        assertEquals("Aerobic capacity", content.benefit)
        assertEquals("Avoid heavy breathing", content.warning)
        assertEquals("Keep it conversational", content.coachNotes)
        assertEquals(listOf("Warm-up", "Main Set", "Cool-down"), content.steps.map { it.phase })
        assertEquals("25 min", content.steps[1].duration)
        assertEquals(listOf("25 min steady"), content.steps[1].steps)
        assertFalse(content.steps.any { it.steps.any { step -> step.contains("heavy breathing") } })
    }

    @Test
    fun intervalAndTreadmillTargetsKeepBackendRangeStrings() {
        val intervals =
            workout.copy(
                type = "Interval",
                intervalReps = 5,
                intervalRepValue = 3.0,
                intervalRepUnit = "min",
                walkIntervalValue = 2.0,
                treadmillSpeed = "8.1-9.2",
                treadmillIncline = "2-4",
            )
        val ordinary = WorkoutDetailContent.make(intervals).steps[1]
        assertEquals("5 × 3 min @ 6:10-6:50", ordinary.target)
        assertEquals("Recovery: 2 min jog / walk", ordinary.recovery)
        val treadmill = WorkoutDetailContent.make(intervals, true).steps[1]
        assertEquals("8.1-9.2 km/h · 2-4% grade", treadmill.target)
        assertEquals("Maintain stable uphill cadence", treadmill.recovery)
    }

    @Test
    fun misplacedStrengthPrescriptionsAreRecoveredIntoMainSet() {
        val content =
            WorkoutDetailContent.make(
                workout.copy(
                    type = "Strength",
                    description =
                        "Overall: Build strength. Squats 3 sets of 8 reps. Process: 5 min warm-up → General strength → 5 min cool-down Benefit: Support running economy.",
                )
            )
        assertEquals("Build strength.", content.intent)
        assertTrue(content.steps[1].steps.any { it.contains("Squats 3 sets of 8 reps") })
        assertFalse(content.intent!!.contains("Squats"))
    }

    @Test
    fun plainDescriptionIsPreservedAndRestHasOnlyMainStep() {
        val description = "Khởi động 10 phút → 30 phút chạy nhẹ → Thả lỏng 5 phút"
        val content = WorkoutDetailContent.make(workout.copy(description = description))
        assertEquals(description, content.overview)
        assertEquals("30 phút", content.steps[1].duration)
        assertEquals(
            1,
            WorkoutDetailContent.make(workout.copy(type = "Rest", durationMinutes = 0.0)).steps.size,
        )
    }
}

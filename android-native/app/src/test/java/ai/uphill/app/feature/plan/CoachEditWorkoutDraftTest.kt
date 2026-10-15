package ai.uphill.app.feature.plan

import ai.uphill.app.core.models.Workout
import org.junit.Assert.*
import org.junit.Test

class CoachEditWorkoutDraftTest {
    private val workout =
        Workout(
            18,
            93,
            2,
            title = "Easy",
            type = "Easy",
            durationMinutes = 45.0,
            distanceKm = 8.5,
            targetZone = "Zone 2",
        )

    @Test
    fun editPreservesWorkoutFieldsAndParsesDecimalComma() {
        val draft =
            CoachEditWorkoutDraft.from(workout)
                .copy(title = "  Aerobic Run  ", distance = "9,5", description = "Steady effort")
        val payload = draft.payload()
        assertEquals("Aerobic Run", payload.title)
        assertEquals("Easy", payload.type)
        assertEquals(45.0, payload.durationMinutes!!, 0.0)
        assertEquals(9.5, payload.distanceKm!!, 0.0)
        assertEquals("Zone 2", payload.targetZone)
        assertEquals("Steady effort", payload.description)
        assertNull(payload.dayOfWeek)
    }

    @Test
    fun invalidEditsCannotProduceWritePayload() {
        val draft = CoachEditWorkoutDraft.from(workout)
        listOf(
                draft.copy(title = " "),
                draft.copy(duration = "NaN"),
                draft.copy(duration = "1441"),
                draft.copy(distance = "-1"),
                draft.copy(distance = "nonsense"),
            )
            .forEach { assertTrue(runCatching { it.payload() }.isFailure) }
        assertNull(draft.copy(distance = "", description = "").payload().distanceKm)
    }
}

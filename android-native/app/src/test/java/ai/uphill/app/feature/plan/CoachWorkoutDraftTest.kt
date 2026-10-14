package ai.uphill.app.feature.plan

import org.junit.Assert.*
import org.junit.Test

class CoachWorkoutDraftTest {
    @Test
    fun manualPayloadKeepsSourceDefaultsAndParsesCommaDistance() {
        val payload =
            CoachWorkoutDraft(3, title = "  Aerobic Run  ", distance = "8,5").manualPayload()
        assertEquals(3, payload.weekNumber)
        assertEquals("Wednesday", payload.dayOfWeek)
        assertEquals("Specific", payload.phase)
        assertEquals("Aerobic Run", payload.title)
        assertEquals("Easy", payload.type)
        assertEquals("Zone 2", payload.targetZone)
        assertEquals(8.5, payload.distanceKm!!, 0.0)
        assertEquals(50.0, payload.durationMinutes, 0.0)
        assertNull(payload.description)
    }

    @Test
    fun aiPayloadUsesTypeDurationAndSelectedDayWithoutManualTitle() {
        val payload =
            CoachWorkoutDraft(4, day = "Friday", type = "Threshold", duration = "40")
                .aiPayload("  Hill intervals, steady cadence  ")
        assertEquals(4, payload.weekNumber)
        assertEquals("Friday", payload.dayOfWeek)
        assertEquals("Threshold", payload.workoutType)
        assertEquals(40.0, payload.durationMinutes, 0.0)
        assertEquals("Hill intervals, steady cadence", payload.intent)
    }

    @Test
    fun invalidFieldsNeverProduceWritePayloads() {
        val valid = CoachWorkoutDraft(1, title = "Easy Run")
        listOf(
                valid.copy(title = " "),
                valid.copy(duration = "NaN"),
                valid.copy(duration = "1441"),
                valid.copy(distance = "-2"),
                valid.copy(distance = "nope"),
                valid.copy(week = 0),
                valid.copy(day = "Funday"),
            )
            .forEach { assertTrue(runCatching { it.manualPayload() }.isFailure) }
        assertTrue(runCatching { valid.copy(duration = "0").aiPayload() }.isFailure)
        assertNull(valid.copy(distance = "").manualPayload().distanceKm)
    }
}

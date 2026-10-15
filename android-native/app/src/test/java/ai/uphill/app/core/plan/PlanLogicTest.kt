package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.JSONCoding
import java.time.LocalDate
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class PlanLogicTest {
    private val plan =
        Plan(
            id = 1,
            raceName = "VMM",
            raceDate = "2026-12-19",
            goalType = "finish",
            totalWeeks = 12,
            startDate = "2026-09-30",
        )

    @Test
    fun datesUseMondayAndLocalCalendarDays() {
        assertEquals(LocalDate.parse("2026-09-28"), PlanCalendar.weekOneMonday(plan, emptyList()))
        assertEquals(
            LocalDate.parse("2026-10-10"),
            PlanCalendar.date(2, Weekday.Saturday, plan, emptyList()),
        )
        assertEquals(2, PlanCalendar.currentWeek(plan, emptyList(), LocalDate.parse("2026-10-05")))
        assertNull(PlanCalendar.day("2026-9-3"))
    }

    @Test
    fun legacyPlanRaceWorkoutDeterminesFirstWeek() {
        val race =
            Workout(id = 1, planId = 1, weekNumber = 10, title = "TARGET EVENT", type = "Race")
        assertEquals(
            LocalDate.parse("2026-10-12"),
            PlanCalendar.weekOneMonday(plan.copy(startDate = null), listOf(race)),
        )
    }

    @Test
    fun backendRangesStayStringsAndMissingPriorityIsFalse() {
        val workout =
            JSONCoding.json.decodeFromString<Workout>(
                """{"id":1,"plan_id":1,"week_number":1,"day_of_week":"Monday","phase":"Base","title":"Easy","type":"Run","duration_minutes":45,"target_zone":"Zone 2","treadmill_speed":"8.1-9.2","treadmill_incline":"2-4"}"""
            )
        assertEquals("8.1-9.2", workout.treadmillSpeed)
        assertEquals("2-4", workout.treadmillIncline)
        assertFalse(workout.isPriority)
        assertFalse(workout.copy(isCompleted = 0, matchedActivityId = 9).isDone)
    }

    @Test
    fun draftDoesNotSendRaceFieldsForStartRunning() {
        val draft =
            PlanSetupDraft(goal = SetupGoal.StartRunning, raceName = "Old race", distanceKm = 50.0)
        val body = draft.body("vi", onboarding = false)
        assertFalse(body.containsKey("race_name"))
        assertFalse(body.containsKey("course_distance_km"))
        assertEquals("start_running", body["goal_type"]?.jsonPrimitive?.content)
    }

    @Test
    fun scheduleChangesAreOnlyChangedFieldsAndResetDayDoubleSessions() {
        val initial =
            plan.copy(
                daysPerWeek = 4,
                preferredRunDays = "[\"Tuesday\",\"Thursday\",\"Saturday\",\"Sunday\"]",
                longRunDay = "Saturday",
                doubleSessionDays = "[\"Sunday\"]",
            )
        val draft = ScheduleDraft(initial)
        assertTrue(draft.changes().isEmpty())
        draft.changeDaysPerWeek(3)
        assertEquals(emptySet<Weekday>(), draft.doubleSessionDays)
        assertEquals(JsonArray(emptyList()), draft.changes()["double_session_days"])
        assertFalse(draft.changes().containsKey("has_gym_access"))
    }

    @Test
    fun calendarGridAlwaysUsesSixMondayBasedRows() {
        val cells =
            PlanCalendar.monthGrid(
                java.time.YearMonth.of(2026, 10),
                PlanSnapshot(plan, emptyList()),
                LocalDate.parse("2026-10-14"),
            )
        assertEquals(42, cells.size)
        assertEquals(LocalDate.parse("2026-09-28"), cells.first().date)
        assertEquals(1, cells.count { it.isToday })
    }

    @Test
    fun zoneValidationRejectsDescendingHeartRatesAndInvalidPaces() {
        assertNotNull(PlanSetupDraft(restingHr = 60, aetHr = 150, antHr = 140).zonesError())
        assertNotNull(PlanSetupDraft(zone2PaceMin = "5:60").zonesError())
        assertNull(
            PlanSetupDraft(
                    restingHr = 60,
                    aetHr = 140,
                    antHr = 160,
                    maxHr = 190,
                    zone2PaceMin = "7:00",
                    zone2PaceMax = "6:00",
                    thresholdPace = "5:00",
                )
                .zonesError()
        )
    }
}

package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import java.time.LocalDate
import java.time.YearMonth
import org.junit.Assert.*
import org.junit.Test

class CalendarMonthTest {
    private val plan = Plan(1, "VMM", "2026-12-19", "finish", totalWeeks = 12, startDate = "2026-09-30")
    private val workouts =
        listOf(
            Workout(
                1,
                1,
                1,
                dayOfWeek = "Monday",
                title = "Neighbor",
                type = "Easy",
                durationMinutes = 100.0,
                distanceKm = 20.0,
            ),
            Workout(
                2,
                1,
                1,
                dayOfWeek = "Thursday",
                title = "Run",
                type = "Easy",
                durationMinutes = 60.0,
                distanceKm = 10.0,
                isCompleted = 1,
            ),
            Workout(
                3,
                1,
                1,
                dayOfWeek = "Friday",
                title = "Rest",
                type = "Rest",
                durationMinutes = 90.0,
                distanceKm = 30.0,
            ),
            Workout(
                4,
                1,
                2,
                dayOfWeek = "Monday",
                title = "Strength",
                type = "Strength",
                durationMinutes = 50.0,
            ),
            Workout(
                5,
                1,
                12,
                dayOfWeek = "Saturday",
                title = "TARGET EVENT",
                type = "Race",
                durationMinutes = 1200.0,
                distanceKm = 200.0,
            ),
        )
    private val snapshot = PlanSnapshot(plan, workouts)

    @Test
    fun totalsExcludeRestAndNeighboringMonthsButWeekRowIncludesSpillover() {
        val month =
            CalendarMonth.make(YearMonth.of(2026, 10), snapshot, LocalDate.parse("2026-10-15"))
        assertEquals(5, month.weeks.size)
        assertEquals(10.0, month.km, 0.001)
        assertEquals(110.0 / 60, month.hours, 0.001)
        assertEquals(2, month.sessionsTotal)
        assertEquals(1, month.sessionsDone)
        assertEquals(30.0, month.weeks.first().km, 0.001)
        assertEquals(LocalDate.parse("2026-09-28"), month.weeks.first().cells.first().date)
        assertTrue(month.isCurrentMonth)
    }

    @Test
    fun raceDoesNotFlattenTrainingBarsAndScaleIsStableAcrossMonths() {
        val october = CalendarMonth.make(YearMonth.of(2026, 10), snapshot)
        val december = CalendarMonth.make(YearMonth.of(2026, 12), snapshot)
        assertEquals(20.0, october.maxSessionLoad, 0.001)
        assertEquals(october.maxSessionLoad, december.maxSessionLoad, 0.001)
        assertEquals(200.0, october.maxWeekKm, 0.001)
        assertEquals(5.0, workouts[3].calendarLoad, 0.001)
    }

    @Test
    fun gridRetainsGeneratedWeeksBeyondNominalPlanLength() {
        val month =
            CalendarMonth.make(
                YearMonth.of(2026, 10),
                snapshot.copy(plan = plan.copy(totalWeeks = 1)),
            )
        assertEquals(2, month.weeks[1].weekNumber)
    }

    @Test
    fun focusUsesTodayInsideSelectedWeekOtherwiseItsThursday() {
        assertEquals(
            LocalDate.parse("2026-10-08"),
            PlanCalendar.focusDate(2, snapshot, LocalDate.parse("2026-10-15")),
        )
        assertEquals(
            LocalDate.parse("2026-10-06"),
            PlanCalendar.focusDate(2, snapshot, LocalDate.parse("2026-10-06")),
        )
    }
}

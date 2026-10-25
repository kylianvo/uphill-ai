package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import java.time.LocalDate
import java.time.YearMonth
import java.time.temporal.ChronoUnit

val CalendarDayCell.sessions: List<Workout>
    get() = workouts.filter { !it.isRest }
val CalendarDayCell.km: Double
    get() = sessions.sumOf { it.distanceKm ?: 0.0 }
val Workout.calendarLoad: Double
    get() = distanceKm?.takeIf { it > 0 } ?: durationMinutes / 10

data class CalendarWeekRow(val cells: List<CalendarDayCell>) {
    val weekNumber: Int?
        get() = cells.first().weekNumber

    val km: Double
        get() = cells.sumOf { it.km }

    val containsToday: Boolean
        get() = cells.any { it.isToday }
}

data class CalendarMonth(
    val weeks: List<CalendarWeekRow>,
    val isCurrentMonth: Boolean,
    val km: Double,
    val hours: Double,
    val sessionsDone: Int,
    val sessionsTotal: Int,
    val maxSessionLoad: Double,
    val maxWeekKm: Double,
) {
    companion object {
        fun make(
            month: YearMonth,
            snapshot: PlanSnapshot,
            today: LocalDate = LocalDate.now(),
        ): CalendarMonth {
            val lastWeek =
                maxOf(
                    snapshot.plan.totalWeeks,
                    snapshot.workouts.maxOfOrNull { it.weekNumber } ?: 0,
                )
            val extended =
                snapshot.copy(plan = snapshot.plan.copy(totalWeeks = lastWeek.coerceAtLeast(1)))
            val start = PlanCalendar.monday(month.atDay(1))
            val end = PlanCalendar.monday(month.atEndOfMonth()).plusDays(6)
            val cells =
                PlanCalendar.monthGrid(month, extended, today)
                    .take(ChronoUnit.DAYS.between(start, end).toInt() + 1)
            val sessions = cells.filter { it.isCurrentMonth }.flatMap { it.sessions }
            val raceDay = PlanCalendar.day(snapshot.plan.raceDate)
            val training =
                snapshot.workouts.filter {
                    !it.isRest &&
                        PlanCalendar.date(
                            it.weekNumber,
                            it.weekday,
                            snapshot.plan,
                            snapshot.workouts,
                        ) != raceDay
                }
            val weekKm =
                snapshot.workouts
                    .filter { !it.isRest }
                    .groupBy { it.weekNumber }
                    .values
                    .map { week -> week.sumOf { it.distanceKm ?: 0.0 } }
            return CalendarMonth(
                cells.chunked(7).map(::CalendarWeekRow),
                month == YearMonth.from(today),
                sessions.sumOf { it.distanceKm ?: 0.0 },
                sessions.sumOf { it.durationMinutes } / 60,
                sessions.count { it.isDone },
                sessions.size,
                training.maxOfOrNull { it.calendarLoad } ?: 0.0,
                weekKm.maxOrNull() ?: 0.0,
            )
        }
    }
}

fun PlanCalendar.focusDate(
    week: Int,
    snapshot: PlanSnapshot,
    today: LocalDate = LocalDate.now(),
): LocalDate {
    val monday = date(week, Weekday.Monday, snapshot.plan, snapshot.workouts) ?: return today
    return if (ChronoUnit.DAYS.between(monday, today) in 0..6) today else monday.plusDays(3)
}

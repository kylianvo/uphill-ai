package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import java.time.*
import java.time.temporal.ChronoUnit

data class CalendarDayCell(
    val date: LocalDate,
    val isCurrentMonth: Boolean,
    val isToday: Boolean,
    val isRaceDay: Boolean,
    val weekNumber: Int?,
    val workouts: List<Workout>,
)

object PlanCalendar {
    fun day(raw: String?): LocalDate? =
        raw?.take(10)
            ?.takeIf { it.matches(Regex("\\d{4}-\\d{2}-\\d{2}")) }
            ?.let { runCatching { LocalDate.parse(it) }.getOrNull() }

    fun monday(date: LocalDate): LocalDate = date.minusDays((date.dayOfWeek.value - 1).toLong())

    fun weekOneMonday(plan: Plan, workouts: List<Workout>): LocalDate? =
        day(plan.startDate)?.let(::monday)
            ?: day(plan.raceDate)?.let { race ->
                monday(race)
                    .minusWeeks(
                        ((workouts
                                .firstOrNull {
                                    it.title.uppercase().contains("TARGET EVENT") ||
                                        it.type.uppercase() == "RACE"
                                }
                                ?.weekNumber ?: plan.totalWeeks) - 1)
                            .toLong()
                    )
            }

    fun date(week: Int, weekday: Weekday, plan: Plan, workouts: List<Workout>): LocalDate? =
        weekOneMonday(plan, workouts)?.plusDays(((week - 1) * 7 + weekday.offset).toLong())

    fun currentWeek(plan: Plan, workouts: List<Workout>, now: LocalDate = LocalDate.now()): Int =
        weekOneMonday(plan, workouts)?.let {
            (Math.floorDiv(ChronoUnit.DAYS.between(it, now).toInt(), 7) + 1).coerceIn(
                1,
                plan.totalWeeks.coerceAtLeast(1),
            )
        } ?: 1

    fun resolveCurrentWeek(
        plan: Plan,
        workouts: List<Workout>,
        now: LocalDate = LocalDate.now(),
    ): Int =
        currentWeek(plan, workouts, now).let { week ->
            workouts.maxOfOrNull { it.weekNumber }?.let { week.coerceAtMost(it) } ?: week
        }

    fun daysToRace(raw: String?, now: LocalDate = LocalDate.now()): Int? =
        day(raw)?.let { ChronoUnit.DAYS.between(now, it).toInt().takeIf { n -> n >= 0 } }

    fun monthGrid(
        month: YearMonth,
        snapshot: PlanSnapshot,
        today: LocalDate = LocalDate.now(),
    ): List<CalendarDayCell> {
        val byDate =
            snapshot.workouts.groupBy {
                date(it.weekNumber, it.weekday, snapshot.plan, snapshot.workouts)
            }
        val start = monday(month.atDay(1))
        val weekOne = weekOneMonday(snapshot.plan, snapshot.workouts)
        return (0..41).map { offset ->
            val date = start.plusDays(offset.toLong())
            val week =
                weekOne
                    ?.let { Math.floorDiv(ChronoUnit.DAYS.between(it, date).toInt(), 7) + 1 }
                    ?.takeIf { it in 1..snapshot.plan.totalWeeks }
            CalendarDayCell(
                date,
                YearMonth.from(date) == month,
                date == today,
                date == day(snapshot.plan.raceDate),
                week,
                byDate[date].orEmpty(),
            )
        }
    }
}

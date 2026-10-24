package ai.uphill.app.core.plan

import ai.uphill.app.core.models.PlanSnapshot
import ai.uphill.app.core.models.Workout
import java.time.LocalDate

/** A suggestion is not confirmation; mirror iOS's date/rest guards before writing a log. */
internal fun pendingWatchCompletions(
    snapshot: PlanSnapshot,
    activities: List<WatchActivity>,
    today: LocalDate = LocalDate.now(),
): List<Workout> {
    val settled = activities.filter { it.settled }.mapNotNull { it.workoutId }.toSet()
    return snapshot.workouts.filter { workout ->
        val date =
            PlanCalendar.date(workout.weekNumber, workout.weekday, snapshot.plan, snapshot.workouts)
        workout.id in settled &&
            !workout.isDone &&
            !workout.isRest &&
            date != null &&
            !date.isAfter(today)
    }
}

package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import java.time.LocalDate
import org.junit.Assert.*
import org.junit.Test

class WatchReconciliationTest {
    @Test
    fun onlySettledPastNonRestUnfinishedWorkoutsCanBeCompleted() {
        val workouts =
            listOf(
                Workout(1, 93, 1, durationMinutes = 40.0, isCompleted = 0),
                Workout(2, 93, 3, durationMinutes = 40.0, isCompleted = 0),
                Workout(3, 93, 1, type = "Rest", isCompleted = 0),
                Workout(4, 93, 1, durationMinutes = 40.0, isCompleted = 1),
                Workout(5, 93, 1, durationMinutes = 40.0, isCompleted = 0),
            )
        val snapshot = PlanSnapshot(Plan(93, totalWeeks = 8, startDate = "2026-10-05"), workouts)
        val activities =
            workouts.map {
                WatchActivity(
                    it.id + 100,
                    it.id,
                    matchMethod = if (it.id == 5) "suggest" else "auto",
                )
            }
        assertEquals(
            listOf(1),
            pendingWatchCompletions(snapshot, activities, LocalDate.of(2026, 10, 13)).map { it.id },
        )
    }

    @Test
    fun unknownPlanDatesNeverProduceCompletionWrites() {
        val workout = Workout(1, 93, 1, durationMinutes = 40.0, isCompleted = 0)
        val snapshot = PlanSnapshot(Plan(93), listOf(workout))
        assertTrue(
            pendingWatchCompletions(snapshot, listOf(WatchActivity(100, 1, matchMethod = "manual")))
                .isEmpty()
        )
    }
}

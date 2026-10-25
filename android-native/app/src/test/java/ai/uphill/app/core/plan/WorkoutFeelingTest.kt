package ai.uphill.app.core.plan

import org.junit.Assert.*
import org.junit.Test

class WorkoutFeelingTest {
    @Test
    fun storedOddRpeValuesKeepTheIosFeelingBand() {
        assertNull(WorkoutFeeling.from(null))
        assertEquals(
            listOf(2, 2, 4, 4, 6, 6, 8, 8, 10, 10),
            (1..10).map { WorkoutFeeling.from(it)!!.rpe },
        )
    }
}

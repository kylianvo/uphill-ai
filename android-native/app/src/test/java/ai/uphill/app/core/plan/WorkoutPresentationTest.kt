package ai.uphill.app.core.plan

import org.junit.Assert.assertEquals
import org.junit.Test

class WorkoutPresentationTest {
    @Test
    fun paceTileRemovesRepeatedUnitsAndNormalizesTheRangeLikeIOS() {
        assertEquals("6:10–6:50", paceTileValue(" 6:10 - 6:50 /KM "))
        assertEquals("6:10–6:50", paceTileValue("6:10 — 6:50"))
        assertEquals("6:10", paceTileValue("6:10 / km"))
        assertEquals("—", paceTileValue(null))
        assertEquals("—", paceTileValue(" /km "))
    }
}

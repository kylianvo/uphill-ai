package ai.uphill.app.core.goal

import ai.uphill.app.core.networking.JSONCoding
import org.junit.Assert.*
import org.junit.Test

class ActiveToolPlanTest {
    @Test
    fun activePlanFixtureSuppliesToolContextAndTarget() {
        val res =
            JSONCoding.json.decodeFromString<ActiveToolPlanResponse>(
                javaClass.getResource("/active_plan.json")!!.readText()
            )
        assertEquals(42.0, res.plan!!.courseDistanceKm!!, 0.0)
        assertTrue(res.plan!!.gearContext().contains("Vietnam Mountain Marathon"))
        assertEquals(390.0, res.plan!!.targetMinutes!!, 0.0)
    }
}

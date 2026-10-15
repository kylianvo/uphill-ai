package ai.uphill.app.core.pace

import ai.uphill.app.core.gear.*
import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.JSONCoding
import ai.uphill.app.core.nutrition.*
import org.junit.Assert.*
import org.junit.Test

class ToolsLogicTest {
    @Test
    fun syntheticCourseAndLocalPacingMatchIos() {
        val course = PacingCalculator.synthesizeCourse(50.0, 2000.0, intervalKm = 5.0)
        assertEquals(11, course.size)
        assertEquals(50000.0, course.last().distanceMeters, 0.01)
        assertEquals(1.0, PacingCalculator.gradePaceMultiplier(0.0), 0.01)
        assertTrue(PacingCalculator.gradePaceMultiplier(0.1) > 1)
        val paced = PacingCalculator.calculate(course, targetTimeMins = 330.0)
        assertEquals(course.size, paced.size)
        assertTrue(paced.last().energyKcal!! > 500)
        assertEquals("06:00", PacingCalculator.clockEtas(paced, mapOf(1 to 10), "06:00").first())
    }

    @Test
    fun gpxParsesTrackAndRoutePointsAndRejectsEmpty() {
        val xml =
            "<gpx><wpt lat=\"22.33\" lon=\"103.85\"><name>CP1</name></wpt><trk><trkseg>" +
                (0..8).joinToString("") {
                    "<trkpt lat=\"${22.30+it*.01}\" lon=\"${103.82+it*.01}\"><ele>${1500+it*50}</ele></trkpt>"
                } +
                "</trkseg></trk></gpx>"
        val result = GpxCourseParser.parse(xml.toByteArray(), "sapa.gpx", 3.0)
        assertEquals(9, result.trackpointCount)
        assertTrue(result.totalDistanceKm > 5)
        assertEquals("Start", result.checkpoints.first().name)
        assertEquals("Finish", result.checkpoints.last().name)
        assertEquals(listOf("CP1"), result.waypointNames)
        try {
            GpxCourseParser.parse(byteArrayOf(), "empty")
            fail("Empty GPX accepted")
        } catch (_: IllegalArgumentException) {}
    }

    @Test
    fun malformedXmlRecoversCompleteTrackpoints() {
        val xml =
            "<gpx><trk><trkseg><trkpt lat=\"22.3\" lon=\"103.82\"><ele>1500</ele></trkpt><trkpt lat=\"22.31\" lon=\"103.83\"><ele>1550</ele></trkpt>"
        val route = GpxCourseParser.parse(xml.toByteArray(), "broken.gpx")
        assertEquals(2, route.trackpointCount)
        assertTrue(route.totalDistanceKm > 1)
    }

    @Test
    fun shoeRotationReplacesSlotAndClampsWear() {
        val shoe = ShoeItem("daily", "Nike", "Pegasus", 900.0, 700.0)
        assertEquals(1.0, shoe.wearRatio, 0.0)
        assertEquals(0.0, shoe.remainingKm, 0.0)
        val rotation = ShoeRotation(listOf(shoe)).setShoe(shoe.copy(model = "Vomero"))
        assertEquals(1, rotation.shoes.size)
        assertEquals("Vomero", rotation.shoe("daily")?.model)
    }

    @Test
    fun nutritionTotalsAndClassification() {
        val plan =
            NutritionPlan(
                hourlyPlan =
                    listOf(HourlyEntry(1, "Gel", 60.0, 500.0), HourlyEntry(2, "Drink", 80.0, 700.0))
            )
        assertEquals(140.0, plan.totalCarbs, 0.0)
        assertEquals(70.0, plan.avgCarbsPerHour, 0.0)
        assertEquals("solid", NutritionProduct("Maurten", "Solid 160").format)
        assertEquals("drink_mix", NutritionProduct("Tailwind", "Endurance mix").format)
    }

    @Test
    fun assessmentMapsAbcAndFieldRejectsNonmonotonicAnchors() {
        val response =
            JSONCoding.json.decodeFromString<GoalAssessmentResponse>(
                """{"distance_km":50,"goals":{"a":300,"b":330,"c":360},"context":{"athlete":{"easy_pace_min_km":6}}}"""
            )
        assertEquals(330.0, response.goals!!.b, 0.0)
        assertEquals(390.5, GoalTime.parseTime("6:30:30")!!, 0.0)
        val bench =
            RaceBenchmark(
                2025,
                finishers = 100,
                winnerTime = "3:00",
                percentiles =
                    mapOf("overall" to PercentileSet(p10 = "4:00", p25 = "3:30", p50 = "6:00")),
            )
        val curve = FieldCurve.anchors(bench, "overall")
        assertEquals(listOf(1.0, 10.0, 50.0), curve.map { it.percentile })
        assertEquals(30.0, FieldCurve.percentile(300.0, curve), 0.001)
    }
}

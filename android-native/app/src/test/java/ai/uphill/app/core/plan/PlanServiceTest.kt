package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

class PlanServiceTest {
    @Test
    fun swapUsesBackendDayUnderscoreKeysAndClientDate() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("{\"workouts\":[]}"))
            PlanService(APIClient({ server.url("/").toString() }, MemoryTokenStore("token")))
                .swap(3, 2, Weekday.Monday, Weekday.Saturday, "2026-10-14")
            val request = server.takeRequest()
            assertEquals("/api/coach/modify-calendar", request.path)
            val body = JSONCoding.json.parseToJsonElement(request.body.readUtf8()).jsonObject
            assertEquals("Monday", body["day_1"]?.jsonPrimitive?.content)
            assertEquals("Saturday", body["day_2"]?.jsonPrimitive?.content)
            assertEquals("2026-10-14", body["client_today"]?.jsonPrimitive?.content)
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun coachReadUsesAthleteScopeAndDoesNotFetchOwnWatchMatches() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("{\"active\":false}"))
            assertNull(
                PlanService(
                        APIClient({ server.url("/").toString() }, MemoryTokenStore()),
                        athleteId = 7,
                    )
                    .activePlan()
            )
            assertEquals("/api/coaching/athletes/7/active-plan", server.takeRequest().path)
            assertEquals(1, server.requestCount)
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun fixturePlanAndReviewsDecode() {
        fun fixture(name: String) =
            requireNotNull(javaClass.classLoader?.getResource(name)) { name }.readText()
        assertNotNull(
            JSONCoding.json
                .decodeFromString<ActivePlanResponse>(fixture("active_plan.json"))
                .snapshot
        )
        assertNull(
            JSONCoding.json
                .decodeFromString<ActivePlanResponse>(fixture("active_plan_none.json"))
                .snapshot
        )
        assertTrue(
            JSONCoding.json
                .decodeFromString<BlockCompletionResponse>(fixture("block_completion.json"))
                .blocks
                .isNotEmpty()
        )
        assertTrue(
            JSONCoding.json.decodeFromString<WeekReview>(fixture("week_review.json")).weekNumber > 0
        )
        assertNotNull(JSONCoding.json.decodeFromString<PlanGoal>(fixture("plan_goal.json")))
    }
}

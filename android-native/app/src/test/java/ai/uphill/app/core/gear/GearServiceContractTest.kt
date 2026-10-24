package ai.uphill.app.core.gear

import ai.uphill.app.core.goal.*
import ai.uphill.app.core.knowledge.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.nutrition.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.*
import org.junit.Assert.*
import org.junit.Test

class GearServiceContractTest {
    @Test
    fun rotationUsesAuthenticatedPutAndSnakeCase() = runBlocking {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("{\"shoes\":[]}"))
            val api = APIClient({ server.url("/").toString() }, MemoryTokenStore("session"))
            GearService(api)
                .save(ShoeRotation(listOf(ShoeItem("trail", "Hoka", "Speedgoat", 42.0))))
            val req = server.takeRequest()
            assertEquals("PUT", req.method)
            assertEquals("/api/shoe-rotation", req.path)
            assertEquals("Bearer session", req.getHeader("Authorization"))
            val body = JSONCoding.json.parseToJsonElement(req.body.readUtf8()).jsonObject
            assertEquals(
                42.0,
                body["shoes"]!!.jsonArray[0].jsonObject["distance_km"]!!.jsonPrimitive.double,
                0.0,
            )
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun recommendationAndFeedbackArePublic() = runBlocking {
        val server = MockWebServer()
        server.start()
        try {
            val api = APIClient({ server.url("/").toString() }, MemoryTokenStore("session"))
            server.enqueue(MockResponse().setBody("{\"recommendations\":[],\"tips\":[]}"))
            GearService(api).recommend(GearParams())
            assertNull(server.takeRequest().getHeader("Authorization"))
            server.enqueue(MockResponse().setBody("{}"))
            GearService(api).feedback("opaque", -1)
            val request = server.takeRequest()
            assertEquals("/api/feedback/result", request.path)
            assertNull(request.getHeader("Authorization"))
            assertEquals(
                -1,
                JSONCoding.json
                    .parseToJsonElement(request.body.readUtf8())
                    .jsonObject["value"]!!
                    .jsonPrimitive
                    .int,
            )
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun knowledgeFallbackFiltersTopicAndPreservesVietnamese() = runBlocking {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setResponseCode(404))
            val service =
                KnowledgeService(APIClient({ server.url("/").toString() }, MemoryTokenStore()))
            val cards = service.cards("Nutrition", "vi")
            assertEquals(2, cards.size)
            assertTrue(cards.all { it.topic == "Nutrition" })
            assertTrue(cards.any { it.summary.contains("đường ruột") })
            assertEquals("/api/knowledge/cards?lang=vi&topic=Nutrition", server.takeRequest().path)
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun nutritionRequestPreservesSelectedFormats() = runBlocking {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(
                MockResponse().setBody("{\"products\":[],\"hourly_plan\":[],\"tips\":[]}")
            )
            NutritionService(APIClient({ server.url("/").toString() }, MemoryTokenStore("session")))
                .calculate(
                    NutritionParams(
                        targetTimeHours = 4.0,
                        targetCarbH = 60.0,
                        preferredFormat = listOf("gel", "drink_mix"),
                    )
                )
            val req = server.takeRequest()
            assertNull(req.getHeader("Authorization"))
            val body = JSONCoding.json.parseToJsonElement(req.body.readUtf8()).jsonObject
            assertEquals(60.0, body["target_carb_h"]!!.jsonPrimitive.double, 0.0)
            assertEquals(2, body["preferred_format"]!!.jsonArray.size)
        } finally {
            server.shutdown()
        }
    }
}

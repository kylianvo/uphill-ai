package ai.uphill.app.core.integrations

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.*
import org.junit.Assert.*
import org.junit.Test

class CorosTest {
    @Test
    fun fitnessUsesBackendVo2maxKeyAndPushRefusalIsReadable() = runTest {
        val fitness =
            JSONCoding.json.decodeFromString<FitnessSyncResult>(
                "{\"status\":\"synced\",\"coros_vo2max\":59.2}"
            )
        assertEquals(59.2, fitness.corosVo2Max!!, 0.001)
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(
                MockResponse()
                    .setResponseCode(429)
                    .setBody("{\"detail\":{\"code\":\"PUSH_limit\"}}")
            )
            val service =
                DeviceConnectionService(
                    APIClient({ server.url("/").toString() }, MemoryTokenStore())
                )
            val result = service.pushToCoros("vi", "2026-10-14")
            assertFalse(result.isSuccess)
            assertEquals("PUSH_limit", result.errorCode)
            val body =
                JSONCoding.json.parseToJsonElement(server.takeRequest().body.readUtf8()).jsonObject
            assertEquals("2026-10-14", body["client_today"]!!.jsonPrimitive.content)
            assertEquals("vi", body["lang"]!!.jsonPrimitive.content)
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun callbackRequiresExactRouteNonEmptyStateAndToken() {
        assertNotNull(CorosCallback.parse("uphillai://coros/callback?state=a&token=b"))
        listOf(
                "https://coros/callback?state=a&token=b",
                "uphillai://evil/coros/callback?state=a&token=b",
                "uphillai://coros/else?state=a&token=b",
                "uphillai://coros/callback?state=&token=b",
                "uphillai://coros/callback?state=a&state=c&token=b",
            )
            .forEach { assertNull(CorosCallback.parse(it)) }
    }

    @Test
    fun stateMismatchExpiredAndReplayAreRejected() {
        val store = MemoryCorosFlowStore()
        val validator = CorosFlowValidator(store) { 1000L }
        validator.begin("a")
        assertFalse(validator.consume("b"))
        assertTrue(validator.consume("a"))
        assertFalse(validator.consume("a"))
        validator.begin("x")
        assertFalse(
            CorosFlowValidator(store) { 1000L + CorosFlowValidator.MAX_AGE_MS + 1 }.consume("x")
        )
    }

    @Test
    fun completionPostsOneTimeStateAndToken() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("{\"connected\":true}"))
            val service =
                DeviceConnectionService(
                    APIClient({ server.url("/").toString() }, MemoryTokenStore("session"))
                )
            assertTrue(service.completeCoros("expected", "one-time-token"))
            val req = server.takeRequest()
            assertEquals("POST", req.method)
            assertEquals("/api/integrations/coros/complete", req.path)
            val body = JSONCoding.json.parseToJsonElement(req.body.readUtf8()).jsonObject
            assertEquals("expected", body["state"]!!.jsonPrimitive.content)
            assertEquals("one-time-token", body["token"]!!.jsonPrimitive.content)
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun syncMatchesWorkoutsAfterImport() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("{\"activities\":3,\"daily_metrics\":5}"))
            server.enqueue(MockResponse().setBody("{}"))
            val s =
                DeviceConnectionService(
                    APIClient({ server.url("/").toString() }, MemoryTokenStore())
                )
            assertEquals(3, s.syncNow(30).activities)
            assertTrue(server.takeRequest().path!!.startsWith("/api/integrations/coros/sync?"))
            assertTrue(server.takeRequest().path!!.startsWith("/api/integrations/matching/run?"))
        } finally {
            server.shutdown()
        }
    }
}

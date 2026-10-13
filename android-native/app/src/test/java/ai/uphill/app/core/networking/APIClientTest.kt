package ai.uphill.app.core.networking

import kotlinx.coroutines.test.runTest
import kotlinx.serialization.Serializable
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test

class APIClientTest {
    @Serializable data class Wire(val weeklyKm: Double)

    @Test
    fun `snake case JSON decodes and unknown fields are ignored`() {
        assertEquals(
            25.5,
            JSONCoding.json.decodeFromString<Wire>("""{"weekly_km":25.5,"future":true}""").weeklyKm,
            0.0,
        )
    }

    @Test
    fun `authenticated requests carry token and query values are escaped`() = runTest {
        MockWebServer().use { server ->
            server.enqueue(MockResponse().setBody("""{"weekly_km":25.5}"""))
            val api = APIClient({ server.url("/").toString() }, MemoryTokenStore("token"))
            val result = api.send<Wire>(Endpoint("GET", "/api/test", query = mapOf("q" to "a&b")))
            assertEquals(25.5, result.weeklyKm, 0.0)
            val request = server.takeRequest()
            assertEquals("Bearer token", request.getHeader("Authorization"))
            assertEquals("a&b", request.requestUrl!!.queryParameter("q"))
        }
    }

    @Test
    fun `login unauthorized preserves server error and does not expire session`() = runTest {
        MockWebServer().use { server ->
            server.enqueue(
                MockResponse().setResponseCode(401).setBody("""{"detail":"Invalid password"}""")
            )
            var expired = false
            val api =
                APIClient(
                    { server.url("/").toString() },
                    MemoryTokenStore("token"),
                    onUnauthorized = { expired = true },
                )
            val error =
                runCatching {
                        api.send<Wire>(Endpoint("POST", "/api/auth/login", requiresAuth = false))
                    }
                    .exceptionOrNull()
            assertTrue(error is APIError.Http)
            assertEquals("Invalid password", error!!.message)
            assertFalse(expired)
            assertNull(server.takeRequest().getHeader("Authorization"))
        }
    }

    @Test
    fun `authenticated unauthorized expires session`() = runTest {
        MockWebServer().use { server ->
            server.enqueue(MockResponse().setResponseCode(401))
            var expired = false
            val api =
                APIClient(
                    { server.url("/").toString() },
                    MemoryTokenStore("token"),
                    onUnauthorized = { expired = true },
                )
            assertTrue(
                runCatching { api.send<Wire>(Endpoint("GET", "/api/auth/me")) }.exceptionOrNull()
                    is APIError.Unauthorized
            )
            assertTrue(expired)
        }
    }

    @Test
    fun `422 schedule guard preserves scalar parameters`() {
        val error =
            APIError.from(
                422,
                """{"detail":{"code":"G4_window","params":{"week":3,"blocked":true,"empty":null}}}""",
            ) as APIError.ScheduleGuard
        assertEquals("G4_window", error.code)
        assertEquals(mapOf("week" to "3", "blocked" to "true", "empty" to ""), error.params)
    }

    @Test
    fun `malformed error body is still an HTTP error`() {
        assertEquals(503, (APIError.from(503, "<html>Unavailable</html>") as APIError.Http).status)
    }
}

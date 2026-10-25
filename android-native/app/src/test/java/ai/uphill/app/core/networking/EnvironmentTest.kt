package ai.uphill.app.core.networking

import ai.uphill.app.BuildConfig
import org.junit.Assert.*
import org.junit.Test

class EnvironmentTest {
    @Test
    fun `release ignores debug environment override`() {
        assertEquals(
            "https://api.uphill-ai.io.vn",
            AppEnvironment.baseURL(false, "http://localhost:8000"),
        )
        if (!BuildConfig.DEBUG)
            assertEquals("https://api.uphill-ai.io.vn", BuildConfig.API_BASE_URL)
    }
}

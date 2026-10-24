package ai.uphill.app.core.auth

import ai.uphill.app.core.networking.*
import kotlinx.serialization.json.*

class AuthService(private val api: APIClient) {
    suspend fun login(email: String, password: String): AuthResponse =
        api.send(
            Endpoint(
                "POST",
                "/api/auth/login",
                buildJsonObject {
                    put("email", email)
                    put("password", password)
                },
                requiresAuth = false,
            )
        )

    suspend fun register(name: String, email: String, password: String): AuthResponse =
        api.send(
            Endpoint(
                "POST",
                "/api/auth/register",
                buildJsonObject {
                    put("name", name)
                    put("email", email)
                    put("password", password)
                },
                requiresAuth = false,
            )
        )

    suspend fun google(idToken: String): AuthResponse =
        api.send(
            Endpoint(
                "POST",
                "/api/auth/google",
                buildJsonObject { put("credential", idToken) },
                requiresAuth = false,
            )
        )

    suspend fun me(): User = api.send(Endpoint("GET", "/api/auth/me"))

    suspend fun logout() {
        try {
            api.text(Endpoint("POST", "/api/auth/logout"))
        } catch (_: APIError) {}
    }
}

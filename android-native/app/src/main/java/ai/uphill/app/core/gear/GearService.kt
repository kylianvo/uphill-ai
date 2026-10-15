package ai.uphill.app.core.gear

import ai.uphill.app.core.networking.*
import kotlinx.serialization.json.*

class GearService(private val api: APIClient) {
    suspend fun recommend(params: GearParams): GearPlan =
        api.send(
            Endpoint(
                "POST",
                "/api/coach/recommend-shoes",
                JSONCoding.json.encodeToJsonElement(params),
                requiresAuth = false,
            )
        )

    suspend fun rotation(): ShoeRotation = api.send(Endpoint("GET", "/api/shoe-rotation"))

    suspend fun save(rotation: ShoeRotation): ShoeRotation =
        api.send(
            Endpoint("PUT", "/api/shoe-rotation", JSONCoding.json.encodeToJsonElement(rotation))
        )

    suspend fun feedback(token: String, value: Int) {
        api.element(
            Endpoint(
                "POST",
                "/api/feedback/result",
                buildJsonObject {
                    put("token", token)
                    put("value", value)
                },
                requiresAuth = false,
            )
        )
    }
}

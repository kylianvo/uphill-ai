package ai.uphill.app.core.nutrition

import ai.uphill.app.core.networking.*
import kotlinx.serialization.json.*

class NutritionService(private val api: APIClient) {
    suspend fun calculate(params: NutritionParams): NutritionPlan =
        api.send(
            Endpoint(
                "POST",
                "/api/coach/calculate-fueling",
                JSONCoding.json.encodeToJsonElement(params),
                requiresAuth = false,
            )
        )

    suspend fun catalog(): List<CatalogProduct> =
        api.send(Endpoint("GET", "/api/coach/nutrition-catalog", requiresAuth = false))

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

package ai.uphill.app.core.goal

import ai.uphill.app.core.networking.*
import kotlinx.serialization.json.encodeToJsonElement

class GoalService(private val api: APIClient) {
    suspend fun assess(request: GoalRequest): GoalAssessmentResponse =
        api.send(Endpoint("POST", "/api/goal/assess", JSONCoding.json.encodeToJsonElement(request)))

    suspend fun match(name: String): RaceMatchResponse =
        api.send(
            Endpoint(
                "GET",
                "/api/kb/match-race",
                query = mapOf("name" to name),
                requiresAuth = false,
            )
        )
}

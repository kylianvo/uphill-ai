package ai.uphill.app.core.profile

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.networking.*
import kotlinx.serialization.json.*

class ProfileService(private val api: APIClient) {
    suspend fun update(user: User, fields: Map<String, String>): User {
        val original =
            buildJsonObject {
                    put("age", user.age ?: 30)
                    put("max_hr", user.maxHr ?: 185)
                    put("resting_hr", user.restingHr ?: 60)
                    put("aet_hr", user.aetHr ?: 135)
                    put("ant_hr", user.antHr ?: 165)
                    put("gender", user.gender?.let(::JsonPrimitive) ?: JsonNull)
                    put("height_cm", user.heightCm?.let(::JsonPrimitive) ?: JsonNull)
                    put("weight_kg", user.weightKg?.let(::JsonPrimitive) ?: JsonNull)
                    put("zone2_pace_min", user.zone2PaceMin?.let(::JsonPrimitive) ?: JsonNull)
                    put("zone2_pace_max", user.zone2PaceMax?.let(::JsonPrimitive) ?: JsonNull)
                    put("threshold_pace", user.thresholdPace?.let(::JsonPrimitive) ?: JsonNull)
                    put("pace_zone_model", user.paceZoneModel ?: "5_zone")
                    put("athlete_notes", user.athleteNotes?.let(::JsonPrimitive) ?: JsonNull)
                }
                .toMutableMap()
        for ((key, value) in fields) original[key] =
            when {
                value.isBlank() -> JsonNull
                key in setOf("age", "max_hr", "resting_hr", "aet_hr", "ant_hr") ->
                    JsonPrimitive(value.toInt())
                key in setOf("height_cm", "weight_kg") -> JsonPrimitive(value.toDouble())
                else -> JsonPrimitive(value)
            }
        return api.send(Endpoint("POST", "/api/auth/update-profile", JsonObject(original)))
    }

    suspend fun password(value: String) {
        api.text(
            Endpoint("POST", "/api/auth/set-password", buildJsonObject { put("password", value) })
        )
    }

    suspend fun acknowledge(): User =
        api.send(Endpoint("POST", "/api/auth/coach-profile-changes/ack"))

    suspend fun zones(model: String): JsonObject =
        api.element(Endpoint("GET", "/api/auth/pace-zones", query = mapOf("model" to model)))
            .jsonObject
}

package ai.uphill.app.core.networking

import kotlinx.serialization.json.JsonElement

data class Endpoint(
    val method: String,
    val path: String,
    val body: JsonElement? = null,
    val query: Map<String, String> = emptyMap(),
    val requiresAuth: Boolean = true,
)

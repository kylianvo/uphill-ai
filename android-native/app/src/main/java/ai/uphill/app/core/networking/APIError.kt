package ai.uphill.app.core.networking

import kotlinx.serialization.json.*

sealed class APIError(message: String) : Exception(message) {
    class Unauthorized : APIError("Your session has expired. Please sign in again.")

    class Http(val status: Int, message: String? = null, val code: String? = null) :
        APIError(message ?: "Something went wrong ($status). Please try again.")

    class ScheduleGuard(val status: Int, val code: String, val params: Map<String, String>) :
        APIError(code)

    class Decoding(cause: Throwable) : APIError("Unexpected response from the server.") {
        init {
            initCause(cause)
        }
    }

    class Transport(cause: Throwable) :
        APIError("Can't reach Uphill. Check your connection and try again.") {
        init {
            initCause(cause)
        }
    }

    companion object {
        fun from(status: Int, body: String, requiresAuth: Boolean = true): APIError {
            if (status == 401 && requiresAuth) return Unauthorized()
            val detail =
                runCatching { JSONCoding.json.parseToJsonElement(body).jsonObject["detail"] }
                    .getOrNull()
            if (detail is JsonPrimitive && detail.isString) return Http(status, detail.content)
            if (detail is JsonObject) {
                val code = (detail["code"] as? JsonPrimitive)?.contentOrNull
                if (status == 422 && code != null) {
                    val params =
                        (detail["params"] as? JsonObject).orEmpty().mapValues { (_, value) ->
                            when (value) {
                                JsonNull -> ""
                                is JsonPrimitive -> value.content
                                else -> value.toString()
                            }
                        }
                    return ScheduleGuard(status, code, params)
                }
                return Http(status, (detail["message"] as? JsonPrimitive)?.contentOrNull, code)
            }
            return Http(status)
        }
    }
}

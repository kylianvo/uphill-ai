package ai.uphill.app.core.chat

import ai.uphill.app.core.networking.JSONCoding
import java.util.UUID
import kotlinx.serialization.json.*

data class ChatTool(
    val id: String,
    val name: String,
    val cardType: String?,
    val data: JsonObject?,
) {
    companion object {
        fun decode(o: JsonObject) =
            ChatTool(
                o.s("tool_call_id"),
                o.s("name"),
                o.s("card_type").ifBlank { null },
                o["card_data"] as? JsonObject,
            )
    }
}

data class ChatMessage(
    val id: String,
    val numericId: Int?,
    val role: String,
    val content: String,
    val requestId: String? = null,
    val citations: List<JsonObject> = emptyList(),
    val tools: List<ChatTool> = emptyList(),
    val interrupted: Boolean = false,
    val feedback: Int? = null,
) {
    fun encode(): JsonObject = buildJsonObject {
        put("id", id)
        numericId?.let { put("message_id", it) }
        put("role", role)
        put("content", content)
        requestId?.let { put("request_id", it) }
        put("interrupted", interrupted)
        feedback?.let { put("feedback", it) }
        put("citations", JsonArray(citations))
        put(
            "tool_calls",
            JsonArray(
                tools.map { tool ->
                    buildJsonObject {
                        put("tool_call_id", tool.id)
                        put("name", tool.name)
                        tool.cardType?.let { put("card_type", it) }
                        tool.data?.let { put("card_data", it) }
                    }
                }
            ),
        )
    }

    companion object {
        fun decode(o: JsonObject): ChatMessage {
            val id = o.s("id").ifBlank { UUID.randomUUID().toString() }
            val rawTools = o["tool_calls"] ?: o["tool_calls_json"]
            val tools =
                when (rawTools) {
                    is JsonArray -> rawTools
                    is JsonPrimitive ->
                        runCatching {
                                JSONCoding.json.parseToJsonElement(rawTools.content).jsonArray
                            }
                            .getOrNull()
                    else -> null
                }
            return ChatMessage(
                id,
                (o["id"] as? JsonPrimitive)?.intOrNull
                    ?: (o["message_id"] as? JsonPrimitive)?.intOrNull,
                o.s("role"),
                o.s("content"),
                o.s("request_id").ifBlank { null },
                (o["citations"] as? JsonArray).orEmpty().mapNotNull { it as? JsonObject },
                tools.orEmpty().mapNotNull { (it as? JsonObject)?.let(ChatTool::decode) },
                (o["interrupted"] as? JsonPrimitive)?.booleanOrNull ?: false,
                (o["feedback"] as? JsonPrimitive)?.intOrNull,
            )
        }
    }
}

data class ChatThread(
    val messages: List<ChatMessage>,
    val hasMore: Boolean = false,
    val proposals: Map<Int, JsonObject> = emptyMap(),
) {
    companion object {
        fun decode(raw: String): ChatThread {
            val o = JSONCoding.json.parseToJsonElement(raw).jsonObject
            return ChatThread(
                (o["messages"] as? JsonArray).orEmpty().map { ChatMessage.decode(it.jsonObject) },
                (o["has_more"] as? JsonPrimitive)?.booleanOrNull ?: false,
                (o["proposals"] as? JsonObject)
                    .orEmpty()
                    .mapNotNull { (key, value) ->
                        val id = key.toIntOrNull() ?: return@mapNotNull null
                        val detail =
                            when (value) {
                                is JsonObject -> value
                                is JsonPrimitive -> buildJsonObject { put("status", value) }
                                else -> return@mapNotNull null
                            }
                        id to detail
                    }
                    .toMap(),
            )
        }
    }
}

internal fun JsonObject.s(key: String): String =
    (this[key] as? JsonPrimitive)?.contentOrNull.orEmpty()

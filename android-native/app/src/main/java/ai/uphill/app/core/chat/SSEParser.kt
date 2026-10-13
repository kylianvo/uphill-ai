package ai.uphill.app.core.chat

import ai.uphill.app.core.networking.JSONCoding
import java.io.ByteArrayOutputStream
import kotlinx.serialization.json.*

class PrematureClose : Exception("The response was interrupted.")

data class ChatEvent(val type: String, val data: JsonObject)

class SSEParser {
    private val buffer = ByteArrayOutputStream()
    private var terminated = false

    fun feed(bytes: ByteArray): List<ChatEvent> {
        buffer.write(bytes)
        val events = mutableListOf<ChatEvent>()
        while (true) {
            val pending = buffer.toByteArray()
            var end = -1
            var delimiter = 0
            for (i in 0 until pending.size - 1) {
                if (pending[i] == 10.toByte() && pending[i + 1] == 10.toByte()) {
                    end = i
                    delimiter = 2
                    break
                }
                if (
                    i + 3 < pending.size &&
                        pending[i] == 13.toByte() &&
                        pending[i + 1] == 10.toByte() &&
                        pending[i + 2] == 13.toByte() &&
                        pending[i + 3] == 10.toByte()
                ) {
                    end = i
                    delimiter = 4
                    break
                }
            }
            if (end < 0) break
            val frame = pending.copyOfRange(0, end).toString(Charsets.UTF_8)
            buffer.reset()
            buffer.write(pending.copyOfRange(end + delimiter, pending.size))
            decode(frame)?.let { event ->
                events += event
                if (event.type in setOf("done", "error")) terminated = true
            }
        }
        return events
    }

    fun finish() {
        if (!terminated) throw PrematureClose()
    }

    private fun decode(frame: String): ChatEvent? {
        var type: String? = null
        val lines = mutableListOf<String>()
        for (line in frame.lineSequence()) when {
            line.startsWith("event:") -> type = line.substring(6).trim()
            line.startsWith("data:") -> lines += line.substring(5).trim()
        }
        if (lines.isEmpty()) return null
        val data =
            runCatching { JSONCoding.json.parseToJsonElement(lines.joinToString("\n")).jsonObject }
                .getOrNull() ?: return null
        val eventType = type ?: data["type"]?.jsonPrimitive?.contentOrNull ?: return null
        if (
            eventType !in
                setOf(
                    "status",
                    "token",
                    "citations",
                    "tool_call",
                    "tool_result",
                    "clarify",
                    "done",
                    "error",
                )
        )
            return null
        return ChatEvent(eventType, data)
    }
}

package ai.uphill.app.core.chat

import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class SSEParserTest {
    @Test
    fun `split UTF8 and CRLF boundaries preserve tokens`() {
        val bytes =
            "event: token\r\ndata: {\"text\":\"Chào bạn\"}\r\n\r\nevent: done\r\ndata: {\"request_id\":\"r1\"}\r\n\r\n"
                .toByteArray()
        val parser = SSEParser()
        val events = bytes.flatMap { parser.feed(byteArrayOf(it)) }
        assertEquals(2, events.size)
        assertEquals("Chào bạn", events[0].data["text"]!!.jsonPrimitive.content)
        parser.finish()
    }

    @Test
    fun `comment heartbeat and invalid frames are skipped`() {
        val parser = SSEParser()
        val events =
            parser.feed(
                ": heartbeat\n\nevent: unknown\ndata: {}\n\nevent: token\ndata: broken\n\nevent: error\ndata: {\"code\":\"busy\"}\n\n"
                    .toByteArray()
            )
        assertEquals(listOf("error"), events.map { it.type })
        parser.finish()
    }

    @Test
    fun `premature close reports interrupted stream`() {
        val parser = SSEParser()
        parser.feed("event: token\ndata: {\"text\":\"hello\"}\n\n".toByteArray())
        assertTrue(runCatching { parser.finish() }.exceptionOrNull() is PrematureClose)
    }

    @Test
    fun `multiline data joins and type field can identify event`() {
        val parser = SSEParser()
        val result =
            parser.feed("data: {\"type\":\"done\",\ndata: \"message_id\":8}\n\n".toByteArray())
        assertEquals("done", result.single().type)
        assertEquals(8, result.single().data["message_id"]!!.jsonPrimitive.int)
    }

    @Test
    fun `thread fixture preserves numeric ids proposals and cards`() {
        val body = javaClass.classLoader!!.getResource("chat_thread.json")!!.readText()
        val thread = ChatThread.decode(body)
        assertEquals(101, thread.messages.first().numericId)
        assertEquals("schedule_proposal", thread.messages[1].tools.first().cardType)
        assertEquals("proposed", thread.proposals[7]?.get("status")?.jsonPrimitive?.content)
    }

    @Test
    fun `thread accepts live proposal status objects`() {
        val thread =
            ChatThread.decode(
                """{"messages":[],"proposals":{"7":{"status":"proposed","kind":"rebuild","stale_reason":null,"result":null}}}"""
            )
        assertEquals("proposed", thread.proposals[7]?.get("status")?.jsonPrimitive?.content)
    }
}

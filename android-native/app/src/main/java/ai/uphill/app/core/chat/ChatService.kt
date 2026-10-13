package ai.uphill.app.core.chat

import ai.uphill.app.core.networking.*
import java.io.IOException
import java.time.LocalDate
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.*
import okhttp3.*

class ChatService(private val api: APIClient) {
    suspend fun thread(before: Int? = null): ChatThread =
        ChatThread.decode(
            api.text(
                Endpoint(
                    "GET",
                    "/api/coach/chat/thread",
                    query =
                        buildMap {
                            put("limit", "50")
                            if (before != null) put("before_id", before.toString())
                        },
                )
            )
        )

    fun stream(
        requestId: String,
        message: String?,
        retryOf: String?,
        lang: String,
    ): Flow<ChatEvent> = callbackFlow {
        val endpoint =
            Endpoint(
                "POST",
                "/api/coach/chat/stream",
                buildJsonObject {
                    put("request_id", requestId)
                    if (message != null) put("message", message)
                    if (retryOf != null) put("retry_of", retryOf)
                    put("lang", lang)
                    put("client_today", LocalDate.now().toString())
                },
            )
        val client =
            api.http
                .newBuilder()
                .callTimeout(0, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .build()
        val call =
            client.newCall(
                api.request(endpoint).newBuilder().header("Accept", "text/event-stream").build()
            )
        val reader =
            launch(Dispatchers.IO) {
                try {
                    val response =
                        suspendCancellableCoroutine<Response> { continuation ->
                            continuation.invokeOnCancellation { call.cancel() }
                            call.enqueue(
                                object : Callback {
                                    override fun onFailure(call: Call, e: IOException) {
                                        if (continuation.isActive)
                                            continuation.resumeWith(
                                                Result.failure(APIError.Transport(e))
                                            )
                                    }

                                    override fun onResponse(call: Call, response: Response) {
                                        continuation.resume(response) { _, value, _ ->
                                            value.close()
                                        }
                                    }
                                }
                            )
                        }
                    response.use {
                        if (!it.isSuccessful) {
                            val error = APIError.from(it.code, it.body?.string().orEmpty())
                            if (error is APIError.Unauthorized) api.onUnauthorized()
                            throw error
                        }
                        val parser = SSEParser()
                        val source = it.body?.source() ?: throw PrematureClose()
                        while (isActive && !source.exhausted()) {
                            val chunk =
                                source.readByteArray(
                                    minOf(
                                        4096L,
                                        source.buffer.size.takeIf { size -> size > 0 } ?: 1L,
                                    )
                                )
                            val events = parser.feed(chunk)
                            events.forEach { event -> send(event) }
                            if (events.any { event -> event.type in setOf("done", "error") }) break
                        }
                        parser.finish()
                    }
                    close()
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    close(e)
                }
            }
        awaitClose {
            call.cancel()
            reader.cancel()
        }
    }

    suspend fun clear() {
        api.text(Endpoint("DELETE", "/api/coach/chat/thread"))
    }

    suspend fun feedback(messageId: Int, value: Int) {
        api.text(
            Endpoint(
                "POST",
                "/api/coach/chat/messages/$messageId/feedback",
                buildJsonObject { put("value", value) },
            )
        )
    }

    suspend fun sources(messageId: Int): JsonObject =
        api.element(Endpoint("GET", "/api/coach/chat/messages/$messageId/sources")).jsonObject

    suspend fun proposal(id: Int): JsonObject =
        api.element(Endpoint("GET", "/api/coach/chat/proposals/$id")).jsonObject

    suspend fun apply(id: Int) {
        api.text(
            Endpoint(
                "POST",
                "/api/coach/chat/proposals/$id/apply",
                buildJsonObject { put("client_today", LocalDate.now().toString()) },
            )
        )
    }

    suspend fun discard(id: Int) {
        api.text(Endpoint("POST", "/api/coach/chat/proposals/$id/discard"))
    }

    suspend fun refreshTurn(id: String): JsonObject =
        api.element(Endpoint("GET", "/api/coach/chat/turns/$id")).jsonObject
}

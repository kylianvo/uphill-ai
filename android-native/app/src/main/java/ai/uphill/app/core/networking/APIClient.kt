package ai.uphill.app.core.networking

import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.JsonElement
import okhttp3.*
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody

class APIClient(
    val baseURL: () -> String,
    val tokenStore: TokenStore,
    val http: OkHttpClient =
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .callTimeout(30, TimeUnit.SECONDS)
            .build(),
    val onUnauthorized: suspend () -> Unit = {},
) {
    fun request(endpoint: Endpoint): Request {
        val url = (baseURL().trimEnd('/') + endpoint.path).toHttpUrl().newBuilder()
        endpoint.query.forEach { (key, value) -> url.addQueryParameter(key, value) }
        val builder = Request.Builder().url(url.build()).header("Accept", "application/json")
        if (endpoint.requiresAuth)
            tokenStore.read()?.let { builder.header("Authorization", "Bearer $it") }
        val body = endpoint.body?.toString()?.toRequestBody("application/json".toMediaType())
        return builder
            .method(
                endpoint.method,
                if (endpoint.method in setOf("POST", "PUT", "PATCH"))
                    body ?: "{}".toRequestBody("application/json".toMediaType())
                else body,
            )
            .build()
    }

    suspend fun execute(endpoint: Endpoint): Response {
        val call = http.newCall(request(endpoint))
        val response = suspendCancellableCoroutine { continuation ->
            continuation.invokeOnCancellation { call.cancel() }
            call.enqueue(
                object : Callback {
                    override fun onFailure(call: Call, e: IOException) {
                        if (continuation.isActive)
                            continuation.resumeWithException(APIError.Transport(e))
                    }

                    override fun onResponse(call: Call, response: Response) {
                        continuation.resume(response) { _, value, _ -> value.close() }
                    }
                }
            )
        }
        if (!response.isSuccessful) {
            val error =
                response.use {
                    APIError.from(it.code, it.body?.string().orEmpty(), endpoint.requiresAuth)
                }
            if (error is APIError.Unauthorized) handleUnauthorized(response.request)
            throw error
        }
        return response
    }

    suspend fun handleUnauthorized(request: Request) {
        val authorization = request.header("Authorization") ?: return
        if (authorization == tokenStore.read()?.let { "Bearer $it" }) onUnauthorized()
    }

    suspend fun text(endpoint: Endpoint): String =
        withContext(Dispatchers.IO) { execute(endpoint).use { it.body?.string().orEmpty() } }

    suspend fun element(endpoint: Endpoint): JsonElement =
        try {
            JSONCoding.json.parseToJsonElement(text(endpoint).ifBlank { "{}" })
        } catch (e: kotlinx.serialization.SerializationException) {
            throw APIError.Decoding(e)
        }

    suspend inline fun <reified T> send(endpoint: Endpoint): T {
        val raw = text(endpoint)
        return try {
            JSONCoding.json.decodeFromString<T>(raw.ifBlank { "{}" })
        } catch (e: kotlinx.serialization.SerializationException) {
            throw APIError.Decoding(e)
        }
    }
}

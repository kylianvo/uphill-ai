package ai.uphill.app.feature.gear

import ai.uphill.app.core.gear.ShoeItem
import ai.uphill.app.core.gear.ShoeRotation
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.networking.JSONCoding
import ai.uphill.app.core.networking.MemoryTokenStore
import androidx.lifecycle.ViewModelStore
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.serialization.encodeToString
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody.Companion.toResponseBody
import okio.Buffer
import org.junit.Assert.*
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class GearViewModelTest {
    @Test
    fun editsWhileRotationIsLoadingDoNotSaveAnEmptyReplacement() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val releaseGet = CountDownLatch(1)
        val puts = AtomicInteger()
        val store = ViewModelStore()
        val api = client { chain ->
            val request = chain.request()
            if (request.method == "PUT") puts.incrementAndGet()
            if (request.url.encodedPath == "/api/shoe-rotation") {
                assertTrue(releaseGet.await(5, TimeUnit.SECONDS))
                response(request, "{\"shoes\":[]}")
            } else response(request, "{\"active\":false}")
        }
        try {
            val vm = GearViewModel(api)
            store.put("gear", vm)
            assertTrue(vm.state.value.loading)
            vm.rotation(ShoeRotation(listOf(ShoeItem("daily", "Nike", "Pegasus"))))
            assertTrue(vm.state.value.rotation.shoes.isEmpty())
            assertFalse(vm.state.value.saving)
            advanceTimeBy(601)
            runCurrent()
            assertEquals(0, puts.get())
            releaseGet.countDown()
            awaitState(vm) { it.loaded }
            assertEquals(0, puts.get())
        } finally {
            releaseGet.countDown()
            store.clear()
            Dispatchers.resetMain()
        }
    }

    @Test
    fun failedLoadBlocksWritesAndRetryPreservesOtherSlotsWhenSaving() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val gets = AtomicInteger()
        val puts = AtomicInteger()
        val saved = AtomicReference<ShoeRotation>()
        val existing =
            ShoeRotation(
                listOf(ShoeItem("race", "Nike", "Alphafly"), ShoeItem("trail", "Hoka", "Speedgoat"))
            )
        val store = ViewModelStore()
        val api = client { chain ->
            val request = chain.request()
            when {
                request.url.encodedPath != "/api/shoe-rotation" ->
                    response(request, "{\"active\":false}")
                request.method == "PUT" -> {
                    puts.incrementAndGet()
                    val body = Buffer().also { request.body!!.writeTo(it) }.readUtf8()
                    saved.set(JSONCoding.json.decodeFromString<ShoeRotation>(body))
                    response(request, body)
                }
                gets.incrementAndGet() == 1 ->
                    response(request, "{\"detail\":\"Rotation unavailable\"}", 503)
                else -> response(request, JSONCoding.json.encodeToString(existing))
            }
        }
        try {
            val vm = GearViewModel(api)
            store.put("gear", vm)
            awaitState(vm) { !it.loading && it.error != null }
            assertFalse(vm.state.value.loaded)
            vm.rotation(ShoeRotation(listOf(ShoeItem("daily", "Nike", "Pegasus"))))
            assertFalse(vm.state.value.saving)
            assertTrue(vm.state.value.rotation.shoes.isEmpty())
            advanceTimeBy(601)
            runCurrent()
            assertEquals(0, puts.get())
            vm.loadRotation()
            awaitState(vm) { it.loaded }
            vm.rotation(vm.state.value.rotation.setShoe(ShoeItem("daily", "Asics", "Novablast")))
            advanceTimeBy(601)
            runCurrent()
            awaitState(vm) { !it.saving }
            assertEquals(1, puts.get())
            assertEquals(existing.shoe("race"), saved.get().shoe("race"))
            assertEquals(existing.shoe("trail"), saved.get().shoe("trail"))
            assertEquals("Novablast", saved.get().shoe("daily")?.model)
        } finally {
            store.clear()
            Dispatchers.resetMain()
        }
    }

    private suspend fun awaitState(vm: GearViewModel, predicate: (GearState) -> Boolean) =
        withContext(Dispatchers.Default) { withTimeout(5000) { vm.state.first(predicate) } }

    private fun client(interceptor: Interceptor) =
        APIClient(
            { "https://uphill.test" },
            MemoryTokenStore("token"),
            OkHttpClient.Builder().addInterceptor(interceptor).build(),
        )

    private fun response(request: Request, body: String, code: Int = 200) =
        Response.Builder()
            .request(request)
            .protocol(Protocol.HTTP_1_1)
            .code(code)
            .message("test")
            .body(body.toResponseBody("application/json".toMediaType()))
            .build()
}

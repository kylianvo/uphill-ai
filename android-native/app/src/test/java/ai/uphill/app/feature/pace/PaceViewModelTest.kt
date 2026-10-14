package ai.uphill.app.feature.pace

import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.networking.JSONCoding
import ai.uphill.app.core.networking.MemoryTokenStore
import ai.uphill.app.core.pace.PacedCheckpoint
import ai.uphill.app.core.pace.PacingRequest
import androidx.lifecycle.ViewModelStore
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
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
class PaceViewModelTest {
    @Test
    fun rapidChangesDebounceToTheLatestTarget() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val requests = ConcurrentLinkedQueue<Double>()
        val store = ViewModelStore()
        val api = client { target -> requests.add(target) }
        try {
            val vm = PaceViewModel(api)
            store.put("pace", vm)
            vm.calculate(PacingRequest(emptyList(), 300.0), "Race", 10.0, debounce = true)
            advanceTimeBy(100)
            vm.calculate(PacingRequest(emptyList(), 360.0), "Race", 10.0, debounce = true)
            advanceTimeBy(349)
            runCurrent()
            assertTrue(requests.isEmpty())
            advanceTimeBy(2)
            runCurrent()
            awaitTarget(vm, 360.0)
            assertEquals(listOf(360.0), requests.toList())
        } finally {
            store.clear()
            Dispatchers.resetMain()
        }
    }

    @Test
    fun anOlderResponseCannotReplaceTheNewerCalculation() = runTest {
        Dispatchers.setMain(UnconfinedTestDispatcher(testScheduler))
        val firstStarted = CountDownLatch(1)
        val releaseFirst = CountDownLatch(1)
        val firstFinished = CountDownLatch(1)
        val store = ViewModelStore()
        val api = client { target ->
            if (target == 300.0) {
                firstStarted.countDown()
                try {
                    assertTrue(releaseFirst.await(5, TimeUnit.SECONDS))
                } finally {
                    firstFinished.countDown()
                }
            }
        }
        try {
            val vm = PaceViewModel(api)
            store.put("pace", vm)
            vm.calculate(PacingRequest(emptyList(), 300.0), "Race", 10.0)
            withContext(Dispatchers.Default) { assertTrue(firstStarted.await(5, TimeUnit.SECONDS)) }
            vm.calculate(PacingRequest(emptyList(), 360.0), "Race", 10.0)
            awaitTarget(vm, 360.0)
            releaseFirst.countDown()
            withContext(Dispatchers.Default) {
                assertTrue(firstFinished.await(5, TimeUnit.SECONDS))
            }
            runCurrent()
            assertEquals(360.0, vm.state.value.paced.last().cumulativeTimeMins, 0.0)
            assertFalse(vm.state.value.busy)
        } finally {
            releaseFirst.countDown()
            store.clear()
            Dispatchers.resetMain()
        }
    }

    private suspend fun awaitTarget(vm: PaceViewModel, target: Double) =
        withContext(Dispatchers.Default) {
            withTimeout(5000) {
                vm.state.first { !it.busy && it.paced.lastOrNull()?.cumulativeTimeMins == target }
            }
        }

    private fun client(onCalculate: (Double) -> Unit): APIClient {
        val http =
            OkHttpClient.Builder()
                .addInterceptor { chain ->
                    val request = chain.request()
                    val body =
                        when (request.url.encodedPath) {
                            "/api/coach/calculate-pacing" -> {
                                val raw = Buffer().also { request.body!!.writeTo(it) }.readUtf8()
                                val target =
                                    JSONCoding.json
                                        .decodeFromString<PacingRequest>(raw)
                                        .targetTimeMins!!
                                onCalculate(target)
                                JSONCoding.json.encodeToString(
                                    listOf(
                                        PacedCheckpoint(
                                            "Finish",
                                            10.0,
                                            0.0,
                                            "6:00",
                                            "1:00:00",
                                            target,
                                            10.0,
                                            0.0,
                                            "run",
                                        )
                                    )
                                )
                            }
                            "/api/coach/pace-strategy/benchmarks" -> "{\"matched\":false}"
                            else -> "{\"active\":false}"
                        }
                    response(request, body)
                }
                .build()
        return APIClient({ "https://uphill.test" }, MemoryTokenStore("token"), http)
    }

    private fun response(request: Request, body: String) =
        Response.Builder()
            .request(request)
            .protocol(Protocol.HTTP_1_1)
            .code(200)
            .message("test")
            .body(body.toResponseBody("application/json".toMediaType()))
            .build()
}

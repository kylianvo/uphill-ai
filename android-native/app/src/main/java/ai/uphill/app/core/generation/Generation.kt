package ai.uphill.app.core.generation

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.*
import android.content.Context
import java.io.File
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable data class JobStart(val jobId: String)

@Serializable data class OnboardingResult(val jobId: String? = null, val user: User? = null)

@Serializable
data class JobStatus(
    val status: String,
    val planId: Int? = null,
    val plan: Plan? = null,
    val workouts: List<Workout>? = null,
    val error: String? = null,
) {
    val snapshot
        get() = plan?.let { PlanSnapshot(it, workouts.orEmpty()) }
}

sealed interface JobOutcome {
    data class Done(val snapshot: PlanSnapshot?) : JobOutcome

    data class Failed(val message: String) : JobOutcome

    data object Lost : JobOutcome

    data object Cancelled : JobOutcome
}

class JobPoller(
    private val status: suspend (String) -> JobStatus,
    private val intervalMs: Long = 2000,
    private val timeoutMs: Long = 240000,
    private val sleep: suspend (Long) -> Unit = { delay(it) },
) {
    suspend fun wait(jobId: String): JobOutcome {
        var failures = 0
        repeat((timeoutMs / intervalMs.coerceAtLeast(1)).toInt().coerceAtLeast(1)) { attempt ->
            try {
                currentCoroutineContext().ensureActive()
                val result = status(jobId)
                failures = 0
                when (result.status) {
                    "done" -> return JobOutcome.Done(result.snapshot)
                    "error" ->
                        return JobOutcome.Failed(
                            result.error ?: "We couldn't build this plan. Please try again."
                        )
                }
            } catch (_: CancellationException) {
                return JobOutcome.Cancelled
            } catch (e: APIError.Http) {
                return if (e.status == 404) JobOutcome.Lost
                else JobOutcome.Failed(e.message.orEmpty())
            } catch (_: APIError.Transport) {
                failures++
                if (failures >= 5) return JobOutcome.Failed(offlineMessage)
            } catch (e: Exception) {
                return JobOutcome.Failed(e.message.orEmpty())
            }
            if (attempt < (timeoutMs / intervalMs.coerceAtLeast(1)).toInt() - 1)
                try {
                    sleep(intervalMs)
                } catch (_: CancellationException) {
                    return JobOutcome.Cancelled
                }
        }
        return JobOutcome.Failed(slowMessage)
    }

    companion object {
        const val slowMessage =
            "This is taking longer than usual. Your plan may still appear: pull down on the Plan tab in a minute to check."
        const val offlineMessage =
            "Lost connection while building your plan. It may still finish: pull down on the Plan tab to check."
    }
}

class GenerationService(private val api: APIClient, val athleteId: Int? = null) {
    private val prefix
        get() = athleteId?.let { "/api/coaching/athletes/$it" } ?: "/api/coach"

    suspend fun onboarding(body: JsonObject): OnboardingResult =
        api.send(Endpoint("POST", "/api/auth/onboarding", body))

    suspend fun generate(body: JsonObject): JobStart =
        api.send(Endpoint("POST", "/api/coach/generate-plan", body))

    suspend fun nextBlock(body: JsonObject): JobStart =
        api.send(Endpoint("POST", "$prefix/generate-next-block", body))

    suspend fun adapt(body: JsonObject): JobStart =
        api.send(Endpoint("POST", "$prefix/adapt-week", body))

    suspend fun status(id: String): JobStatus =
        api.send(Endpoint("GET", "/api/coach/plan-status/$id"))
}

@Serializable
data class RunningJob(
    val kind: String,
    val jobId: String,
    val startedAt: Long,
    val summary: List<String> = emptyList(),
    val userId: Int,
    val athleteId: Int? = null,
)

data class GenerationState(val running: RunningJob? = null, val outcome: JobOutcome? = null)

/**
 * Shared process-level job center. Disk state survives process death; account keys prevent crossing
 * sessions.
 */
class GenerationCenter
private constructor(private val file: File, private val api: APIClient, private val userId: Int) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var task: Job? = null
    private val mutable = MutableStateFlow(GenerationState())
    val state: StateFlow<GenerationState> = mutable.asStateFlow()

    fun track(
        kind: String,
        id: String,
        summary: List<String> = emptyList(),
        athleteId: Int? = null,
    ) = start(RunningJob(kind, id, System.currentTimeMillis(), summary, userId, athleteId))

    fun resume() {
        if (mutable.value.running != null) return
        val saved =
            runCatching { JSONCoding.json.decodeFromString<RunningJob>(file.readText()) }
                .getOrNull() ?: return
        if (saved.userId != userId) {
            file.delete()
            return
        }
        start(saved)
    }

    fun clearOutcome() {
        mutable.value = mutable.value.copy(outcome = null)
    }

    fun reset() {
        task?.cancel()
        task = null
        mutable.value = GenerationState()
        file.delete()
    }

    private fun start(running: RunningJob) {
        task?.cancel()
        mutable.value = GenerationState(running)
        file.parentFile?.mkdirs()
        file.writeText(JSONCoding.json.encodeToString(RunningJob.serializer(), running))
        task =
            scope.launch {
                val result =
                    JobPoller(GenerationService(api, running.athleteId)::status).wait(running.jobId)
                if (
                    !isActive ||
                        result == JobOutcome.Cancelled ||
                        mutable.value.running?.jobId != running.jobId
                )
                    return@launch
                // Do not revive data after a sign-out, even when the request completed
                // concurrently.
                if (api.tokenStore.read() == null) {
                    reset()
                    return@launch
                }
                file.delete()
                mutable.value = GenerationState(outcome = result)
            }
    }

    companion object {
        private val instances = mutableMapOf<String, GenerationCenter>()

        @Synchronized
        fun get(context: Context, api: APIClient, userId: Int): GenerationCenter {
            val key = "${api.baseURL()}:$userId"
            return instances
                .getOrPut(key) {
                    GenerationCenter(
                        File(context.filesDir, "generation/job-$userId.json"),
                        api,
                        userId,
                    )
                }
                .also { it.resume() }
        }

        @Synchronized
        fun resetAll() {
            instances.values.forEach { it.reset() }
            instances.clear()
        }
    }
}

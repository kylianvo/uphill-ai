package ai.uphill.app.core.integrations

import ai.uphill.app.core.networking.*
import android.content.Context
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import java.net.URI
import java.net.URLDecoder
import java.time.LocalDate
import java.time.ZonedDateTime
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class CorosConnectionStatus(
    val connected: Boolean,
    val lastSyncAt: String? = null,
    val deviceModel: String? = null,
)

@Serializable
data class DeviceConnectionStatus(val coros: CorosConnectionStatus? = null) {
    val isCorosConnected
        get() = coros?.connected == true
}

@Serializable data class DeviceSyncResult(val activities: Int, val dailyMetrics: Int)

@Serializable
data class FitnessSyncResult(
    val status: String,
    val thresholdPace: String? = null,
    @SerialName("coros_vo2max") val corosVo2Max: Double? = null,
    val corosRunningLevel: Double? = null,
)

@Serializable
data class CorosPushSummary(
    val mode: String? = null,
    val daysSent: Int = 0,
    val workoutsSent: Int = 0,
    val leftInUphill: Int = 0,
    val lockedDays: Int = 0,
    val invalid: Int = 0,
    val stale: Int? = null,
    val windowEnd: String = "",
    val planStart: String? = null,
)

@Serializable
data class CorosPushStatus(
    val connected: Boolean,
    val lastPushedAt: String? = null,
    val outOfDate: Boolean? = null,
    val partial: Boolean? = null,
    val lastSummary: CorosPushSummary? = null,
)

@Serializable
data class CorosPushOutcome(
    val status: String,
    val summary: CorosPushSummary? = null,
    val lastPushedAt: String? = null,
    val errorCode: String? = null,
) {
    val isSuccess
        get() = status in listOf("sent", "partial")
}

@Serializable private data class ConnectResponse(val authorizeUrl: String)

@Serializable private data class CompleteResponse(val connected: Boolean)

class DeviceConnectionService(private val api: APIClient) {
    suspend fun fetchStatus(): DeviceConnectionStatus =
        api.send(Endpoint("GET", "/api/integrations/status"))

    suspend fun connectCorosURL(): String =
        api.send<ConnectResponse>(
                Endpoint(
                    "GET",
                    "/api/integrations/coros/connect",
                    query = mapOf("platform" to "native"),
                )
            )
            .authorizeUrl

    suspend fun completeCoros(state: String, token: String): Boolean =
        api.send<CompleteResponse>(
                Endpoint(
                    "POST",
                    "/api/integrations/coros/complete",
                    buildJsonObject {
                        put("state", state)
                        put("token", token)
                    },
                )
            )
            .connected

    suspend fun syncNow(days: Int = 30): DeviceSyncResult {
        val res: DeviceSyncResult =
            api.send(
                Endpoint("POST", "/api/integrations/coros/sync", query = mapOf("days" to "$days"))
            )
        api.text(
            Endpoint(
                "POST",
                "/api/integrations/matching/run",
                query =
                    mapOf(
                        "days" to "$days",
                        "tz_offset_minutes" to "${ZonedDateTime.now().offset.totalSeconds/60}",
                    ),
            )
        )
        return res
    }

    suspend fun syncFitness(): FitnessSyncResult =
        api.send(Endpoint("POST", "/api/integrations/coros/sync-fitness"))

    suspend fun disconnectCoros() {
        api.text(Endpoint("DELETE", "/api/integrations/coros"))
    }

    suspend fun fetchPushStatus(today: String = LocalDate.now().toString()): CorosPushStatus =
        api.send(
            Endpoint(
                "GET",
                "/api/integrations/coros/push-status",
                query = mapOf("client_today" to today),
            )
        )

    suspend fun pushToCoros(
        lang: String,
        today: String = LocalDate.now().toString(),
    ): CorosPushOutcome {
        try {
            return api.send(
                Endpoint(
                    "POST",
                    "/api/integrations/coros/push",
                    buildJsonObject {
                        put("client_today", today)
                        put("lang", lang)
                    },
                )
            )
        } catch (error: APIError.Http) {
            val code = error.code ?: throw error
            return CorosPushOutcome("error", errorCode = code)
        } catch (error: APIError.ScheduleGuard) {
            return CorosPushOutcome("error", errorCode = error.code)
        }
    }
}

// The expected state survives activity and process recreation; a callback consumes it once.
interface CorosFlowStore {
    fun read(): Pair<String, Long>?

    fun write(value: Pair<String, Long>?)
}

class MemoryCorosFlowStore : CorosFlowStore {
    private var flow: Pair<String, Long>? = null

    override fun read() = flow

    override fun write(value: Pair<String, Long>?) {
        flow = value
    }
}

class PersistedCorosFlowStore(context: Context) : CorosFlowStore {
    private val prefs =
        context.applicationContext.getSharedPreferences("coros_oauth", Context.MODE_PRIVATE)

    override fun read(): Pair<String, Long>? =
        prefs.getString("state", null)?.let { it to prefs.getLong("created", 0) }

    override fun write(value: Pair<String, Long>?) {
        prefs
            .edit()
            .apply {
                if (value == null) clear()
                else {
                    putString("state", value.first)
                    putLong("created", value.second)
                }
            }
            .commit()
    }
}

class CorosFlowValidator(
    private val store: CorosFlowStore,
    private val clock: () -> Long = { System.currentTimeMillis() },
) {
    @Synchronized
    fun begin(state: String) {
        require(state.isNotBlank())
        store.write(state to clock())
    }

    @Synchronized
    fun consume(state: String): Boolean {
        val expected = store.read() ?: return false
        val age = clock() - expected.second
        if (age !in 0..MAX_AGE_MS) {
            store.write(null)
            return false
        }
        if (state != expected.first) return false
        store.write(null)
        return true
    }

    companion object {
        const val MAX_AGE_MS = 15 * 60 * 1000L
    }
}

data class CorosCallback(val state: String, val token: String) {
    companion object {
        fun query(uri: URI): Map<String, List<String>> =
            uri.rawQuery
                .orEmpty()
                .split('&')
                .filter { it.isNotBlank() }
                .map { it.split('=', limit = 2) }
                .groupBy(
                    { URLDecoder.decode(it[0], "UTF-8") },
                    { URLDecoder.decode(it.getOrElse(1) { "" }, "UTF-8") },
                )

        fun parse(url: String): CorosCallback? =
            runCatching {
                    val u = URI(url)
                    if (
                        u.scheme != "uphillai" ||
                            u.host != "coros" ||
                            u.path != "/callback" ||
                            u.userInfo != null ||
                            u.port != -1
                    )
                        return null
                    val q = query(u)
                    if (q["result"]?.singleOrNull() == "error") return null
                    val state =
                        q["state"]?.singleOrNull()?.takeIf { it.isNotBlank() } ?: return null
                    val token =
                        q["token"]?.singleOrNull()?.takeIf { it.isNotBlank() } ?: return null
                    CorosCallback(state, token)
                }
                .getOrNull()
    }
}

class CorosOAuthCoordinator(
    private val context: Context,
    private val service: DeviceConnectionService,
) {
    private val validator = CorosFlowValidator(PersistedCorosFlowStore(context))
    private val completionMutex = Mutex()

    suspend fun begin() {
        val url = service.connectCorosURL()
        val parsed = URI(url)
        require(
            parsed.scheme == "https" && !parsed.host.isNullOrBlank() && parsed.userInfo == null
        ) {
            "Invalid COROS authorization URL."
        }
        val state =
            CorosCallback.query(parsed)["state"]?.singleOrNull()?.takeIf { it.isNotBlank() }
                ?: error("Missing COROS authorization state.")
        validator.begin(state)
        CustomTabsIntent.Builder()
            .build()
            .apply { intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK) }
            .launchUrl(context, Uri.parse(url))
    }

    suspend fun handleCallback(url: String): Boolean =
        completionMutex.withLock {
            val callback =
                CorosCallback.parse(url) ?: error("Invalid callback response from COROS.")
            require(validator.consume(callback.state)) {
                "Authorization security check failed or the connection expired."
            }
            service.completeCoros(callback.state, callback.token)
        }
}

/** Call on app foreground and every fifteen minutes while RESUMED. */
class CorosForegroundSync(
    private val service: DeviceConnectionService,
    private val clock: () -> Long = { System.currentTimeMillis() },
) {
    private var lastSynced: Long? = null
    private val mutex = Mutex()

    suspend fun syncIfDue(): Boolean =
        mutex.withLock {
            val now = clock()
            if (lastSynced?.let { now - it < 15 * 60 * 1000L } == true) return false
            if (!service.fetchStatus().isCorosConnected) return false
            service.syncNow(7)
            lastSynced = now
            true
        }
}

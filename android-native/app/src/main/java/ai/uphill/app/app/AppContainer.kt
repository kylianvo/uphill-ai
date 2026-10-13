package ai.uphill.app.app

import ai.uphill.app.BuildConfig
import ai.uphill.app.core.auth.*
import ai.uphill.app.core.chat.ChatHistory
import ai.uphill.app.core.generation.GenerationCenter
import ai.uphill.app.core.goal.ToolHandoff
import ai.uphill.app.core.integrations.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.persistence.*
import ai.uphill.app.core.plan.TrainingNavigation
import android.app.Application
import java.io.File
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

class AppContainer(context: Application) {
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    val settings = SettingsStore(context)
    val language = settings.language.stateIn(scope, SharingStarted.Eagerly, "en")
    private var environment: String? = null
    val tokens = KeystoreTokenStore(context.filesDir)
    val cache = OfflineCache(File(context.filesDir, "offline"))
    val chatHistory = ChatHistory(context)
    val session =
        SessionStore(
            tokens,
            { cache.load<User>("user") },
            { cache.save("user", it) },
            {
                cache.clear()
                GenerationCenter.resetAll()
                TrainingNavigation.clear()
                ToolHandoff.pacingTargetMinutes = null
                ToolHandoff.fuelingHours = null
                scope.launch { chatHistory.clear() }
                context.getSharedPreferences("coros_oauth", 0).edit().clear().apply()
            },
        )
    val api =
        APIClient(
            { AppEnvironment.baseURL(BuildConfig.DEBUG, environment) },
            tokens,
            onUnauthorized = { session.signOut() },
        )
    val auth = AuthService(api)
    val coros = DeviceConnectionService(api)
    val corosOAuth = CorosOAuthCoordinator(context, coros)
    val corosSync = CorosForegroundSync(coros)

    init {
        scope.launch { settings.environment.collect { environment = it } }
        scope.launch {
            environment = settings.environment.first()
            session.restore { auth.me() }
        }
    }
}

class UphillApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}

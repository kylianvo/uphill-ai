package ai.uphill.app

import ai.uphill.app.app.RootNav
import ai.uphill.app.app.UphillApplication
import ai.uphill.app.core.auth.AuthResponse
import ai.uphill.app.core.auth.User
import ai.uphill.app.core.localization.localizedText
import ai.uphill.app.core.networking.JSONCoding
import ai.uphill.app.designsystem.UphillTheme
import android.content.res.Configuration
import androidx.activity.compose.LocalActivityResultRegistryOwner
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry
import androidx.test.runner.lifecycle.Stage
import java.util.Locale
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.*
import org.junit.*

/** Opt-in real emulator screenshots, using recorded responses in the production app shell. */
class VisualEvidenceTest {
    @get:Rule val ui = createComposeRule()

    @Test
    fun captureMajorScreensInBothLanguages() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        Assume.assumeTrue(
            InstrumentationRegistry.getArguments().getString("captureEvidence") == "true"
        )
        val variant = InstrumentationRegistry.getArguments().getString("captureVariant") ?: "normal"
        val context = instrumentation.targetContext
        val container = (context.applicationContext as UphillApplication).container
        fun fixture(name: String) =
            instrumentation.context.assets.open(name).bufferedReader().use { it.readText() }
        val server = MockWebServer()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val body =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/auth/me" -> fixture("auth_me.json")
                            "/api/coach/active-plan" -> fixture("active_plan.json")
                            "/api/coach/block-completion/93" -> fixture("block_completion.json")
                            "/api/coach/week-review/93/2" -> fixture("week_review.json")
                            "/api/plans/93/goal" -> fixture("plan_goal.json")
                            "/api/coach/recent-plans" -> fixture("recent_plans.json")
                            "/api/coach/chat/thread" -> fixture("chat_thread.json")
                            "/api/auth/pace-zones" -> fixture("pace_zones.json")
                            "/api/auth/fitness-snapshot" -> "{}"
                            "/api/race-history" -> """{"results":[],"claims":[],"road_pbs":{}}"""
                            "/api/shoe-rotation" -> """{"shoes":[]}"""
                            "/api/integrations/matching" -> """{"activities":[]}"""
                            "/api/integrations/status" -> """{"coros":{"connected":false}}"""
                            "/api/knowledge/cards" -> """{"cards":[]}"""
                            "/api/knowledge/topics" -> "[]"
                            "/api/coach/nutrition-catalog" -> "[]"
                            "/api/coach/pace-strategy/benchmarks" -> """{"matched":false}"""
                            "/api/coaching/my-invites" -> """{"invites":[]}"""
                            else -> "{}"
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(body)
                }
            }
        server.start()
        val previousEnvironment = container.api.baseURL()
        val previousLanguage = container.language.value
        val activityConfigurations = mutableMapOf<android.app.Activity, Configuration>()
        // Dialogs use the host activity's resources rather than the configured LocalContext.
        @Suppress("DEPRECATION")
        fun configureActivityLanguage(lang: String) {
            ui.runOnIdle {
                ActivityLifecycleMonitorRegistry.getInstance()
                    .getActivitiesInStage(Stage.RESUMED)
                    .forEach { activity ->
                        activityConfigurations.putIfAbsent(
                            activity,
                            Configuration(activity.resources.configuration),
                        )
                        val configuration =
                            Configuration(activity.resources.configuration).apply {
                                setLocale(Locale.forLanguageTag(lang))
                            }
                        activity.resources.updateConfiguration(
                            configuration,
                            activity.resources.displayMetrics,
                        )
                    }
            }
        }
        fun localized(key: String, lang: String): String {
            val configuration =
                Configuration(context.resources.configuration).apply {
                    setLocale(Locale.forLanguageTag(lang))
                }
            return localizedText(context.createConfigurationContext(configuration), key)
        }
        fun waitText(text: String) {
            ui.waitUntil(15000) {
                ui.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty()
            }
        }
        fun tab(key: String, lang: String) {
            ui.onNode(hasText(localized(key, lang)) and hasClickAction()).performClick()
        }
        fun capture(name: String, lang: String) {
            ui.waitForIdle()
            ui.mainClock.advanceTimeBy(500)
            ui.waitForIdle()
            val path = "/sdcard/Download/uphill-evidence/$variant/$name-$lang.png"
            instrumentation.uiAutomation
                .executeShellCommand("mkdir -p /sdcard/Download/uphill-evidence/$variant")
                .use { java.io.FileInputStream(it.fileDescriptor).readBytes() }
            instrumentation.uiAutomation.executeShellCommand("screencap -p $path").use {
                java.io.FileInputStream(it.fileDescriptor).readBytes()
            }
        }
        try {
            runBlocking {
                container.settings.environment(server.url("/").toString())
                container.settings.language("en")
            }
            ui.waitUntil(10000) { container.api.baseURL() == server.url("/").toString() }
            container.session.signOut()
            ui.setContent {
                val lang by container.language.collectAsState()
                val registryOwner = LocalActivityResultRegistryOwner.current
                val configuration =
                    Configuration(context.resources.configuration).apply {
                        setLocale(Locale.forLanguageTag(lang))
                    }
                CompositionLocalProvider(
                    LocalActivityResultRegistryOwner provides requireNotNull(registryOwner),
                    LocalContext provides context.createConfigurationContext(configuration),
                    LocalConfiguration provides configuration,
                ) {
                    UphillTheme { RootNav(container) }
                }
            }
            capture("sign-in", "en")
            val user =
                JSONCoding.json
                    .decodeFromString<User>(fixture("auth_me.json"))
                    .copy(onboardingComplete = true)
            ui.runOnIdle { container.session.signIn(AuthResponse("fixture-evidence-only", user)) }
            for (lang in listOf("en", "vi")) {
                runBlocking { container.settings.language(lang) }
                ui.waitUntil(10000) { container.language.value == lang }
                configureActivityLanguage(lang)
                tab("Plan", lang)
                ui.waitUntil(15000) {
                    ui.onAllNodesWithTag("plan.list").fetchSemanticsNodes().isNotEmpty()
                }
                ui.onNodeWithTag("plan.list").performScrollToIndex(0)
                waitText("Vietnam Mountain Marathon 42K")
                capture("plan", lang)
                ui.onNodeWithTag("plan.list").performScrollToNode(hasText("Hill Repeats"))
                ui.onNodeWithText("Hill Repeats").performClick()
                waitText(localized("Done", lang))
                capture("workout", lang)
                instrumentation.uiAutomation.executeShellCommand("input keyevent 4").use {
                    java.io.FileInputStream(it.fileDescriptor).readBytes()
                }
                tab("Coach", lang)
                waitText("Can we move tomorrow's tempo run")
                capture("chat", lang)
                tab("Me", lang)
                waitText(user.name)
                ui.onNode(hasText(localized("Me", lang)) and !hasClickAction()).performScrollTo()
                capture("me", lang)
                if (variant == "normal") {
                    for ((name, label) in
                        listOf(
                            "pace" to "Pace Strategy",
                            "goal" to "Goal Determiner",
                            "nutrition" to "Nutrition Lab",
                            "gear" to "Gear Vault",
                            "knowledge" to "Knowledge Hub",
                            "race-history" to "Race history",
                        )) {
                        tab("Me", lang)
                        waitText(localized(label, lang))
                        ui.onNodeWithText(localized(label, lang)).performScrollTo().performClick()
                        val configuration =
                            Configuration(context.resources.configuration).apply {
                                setLocale(Locale.forLanguageTag(lang))
                            }
                        val resources = context.createConfigurationContext(configuration).resources
                        val resourceName =
                            if (name == "race-history") "p6_race_history"
                            else
                                "tools_" +
                                    label.lowercase().replace(Regex("[^a-z0-9]+"), "_").trim('_')
                        val headingId =
                            resources.getIdentifier(resourceName, "string", context.packageName)
                        waitText(
                            if (headingId != 0) resources.getString(headingId)
                            else localized(label, lang)
                        )
                        capture(name, lang)
                        val backId =
                            resources.getIdentifier("tools_back", "string", context.packageName)
                        val backLabel =
                            if (name != "race-history" && backId != 0) resources.getString(backId)
                            else localized("Back", lang)
                        ui.onNodeWithText(backLabel).performClick()
                        waitText(localized("Tools & Labs", lang))
                    }
                }
            }
        } finally {
            container.session.signOut()
            runBlocking {
                container.settings.environment(previousEnvironment)
                container.settings.language(previousLanguage)
            }
            @Suppress("DEPRECATION")
            ui.runOnIdle {
                activityConfigurations.forEach { (activity, configuration) ->
                    activity.resources.updateConfiguration(
                        configuration,
                        activity.resources.displayMetrics,
                    )
                }
            }
            server.shutdown()
        }
    }
}

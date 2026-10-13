package ai.uphill.app

import ai.uphill.app.core.auth.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.persistence.*
import ai.uphill.app.designsystem.UphillTheme
import ai.uphill.app.feature.auth.*
import ai.uphill.app.feature.chat.ChatScreen
import ai.uphill.app.feature.gear.GearScreen
import ai.uphill.app.feature.onboarding.OnboardingScreen
import ai.uphill.app.feature.plan.PlanScreen
import ai.uphill.app.feature.racehistory.RaceHistoryScreen
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import okhttp3.mockwebserver.*
import org.junit.*
import org.junit.Assert.*

/** Runs native UI through real HTTP requests against recorded backend responses. */
class NativeFlowTest {
    @get:Rule val ui = createComposeRule()
    private lateinit var server: MockWebServer
    private lateinit var api: APIClient
    private val user = User(7, "ios-fixtures@uphill.ai", "Athlete", onboardingComplete = true)

    private fun fixture(name: String) =
        InstrumentationRegistry.getInstrumentation()
            .context
            .assets
            .open(name)
            .bufferedReader()
            .use { it.readText() }

    @Before
    fun start() {
        server = MockWebServer()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val path = request.requestUrl!!.encodedPath
                    val body =
                        when (path) {
                            "/api/coach/active-plan" -> fixture("active_plan.json")
                            "/api/coach/block-completion/93" -> fixture("block_completion.json")
                            "/api/coach/week-review/93/2" -> fixture("week_review.json")
                            "/api/plans/93/goal" -> fixture("plan_goal.json")
                            "/api/coach/recent-plans" -> fixture("recent_plans.json")
                            "/api/integrations/matching" -> "{\"activities\":[]}"
                            "/api/knowledge/cards" -> "{\"cards\":[]}"
                            "/api/shoe-rotation" -> "{\"shoes\":[]}"
                            "/api/race-history" -> "{\"results\":[],\"claims\":[],\"road_pbs\":{}}"
                            "/api/auth/fitness-snapshot" -> "{}"
                            "/api/coach/chat/thread" -> fixture("chat_thread.json")
                            "/api/auth/login" ->
                                return MockResponse()
                                    .setResponseCode(401)
                                    .setBody("{\"detail\":\"Invalid password\"}")
                            "/api/coach/chat/stream" ->
                                return MockResponse()
                                    .setHeader("Content-Type", "text/event-stream")
                                    .setBody(
                                        "event: token\ndata: {\"text\":\"Keep this run easy.\"}\n\nevent: done\ndata: {\"message_id\":120}\n\n"
                                    )
                            else -> "{}"
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(body)
                }
            }
        server.start()
        val baseURL = server.url("/").toString()
        api = APIClient({ baseURL }, MemoryTokenStore("fixture-session-token"))
    }

    @After
    fun stop() {
        server.shutdown()
    }

    private fun waitText(text: String) {
        ui.waitUntil(15000) {
            ui.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun signInShowsCredentialFailureWithoutSessionExpiry() {
        val session = SessionStore(MemoryTokenStore(), { null }, {}, {})
        val model = SignInViewModel(AuthService(api), session)
        ui.setContent { UphillTheme { SignInScreen(model) } }
        ui.onNodeWithTag("signin.email").performTextInput("runner@example.com")
        ui.onNodeWithTag("signin.password").performTextInput("incorrect-password")
        ui.onNodeWithTag("signin.submit").performClick()
        waitText("Invalid password")
        assertEquals(SessionState.SignedOut, session.state.value)
    }

    @Test
    fun onboardingSelectsGoalAndReachesTrainingSchedule() {
        ui.setContent {
            UphillTheme { OnboardingScreen(api, user.copy(onboardingComplete = false), "en", {}) }
        }
        ui.onNodeWithText("Start running").performClick()
        waitText("Connect your watch")
        ui.onNodeWithText("Next").performClick()
        waitText("Your training week")
    }

    @Test
    fun planOpensWorkoutDetailFromRecordedSchedule() {
        ui.setContent { UphillTheme { PlanScreen(api, user, "en", {}) } }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithText("Hill Repeats").performScrollTo().performClick()
        waitText("Mark missed")
    }

    @Test
    fun scheduleChangeEnablesRebuildAndAsksForConfirmation() {
        ui.setContent { UphillTheme { PlanScreen(api, user, "en", {}) } }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithText("Manage").performClick()
        waitText("Edit schedule and training venues")
        ui.onNodeWithText("Edit schedule and training venues").performScrollTo().performClick()
        waitText("Weekly Schedule")
        ui.onNodeWithText("Rebuild week").assertIsNotEnabled()
        ui.onNodeWithText("Hilly").performScrollTo().performClick()
        ui.onNodeWithText("Rebuild week").performScrollTo().assertIsEnabled().performClick()
        waitText("Rebuild this week around your new schedule?")
    }

    @Test
    fun chatStreamsReplyAfterSendingTurn() {
        ui.setContent { UphillTheme { ChatScreen(api, user, "en", {}) } }
        waitText("Can we move tomorrow's tempo run")
        ui.onNodeWithTag("chat.input").performTextInput("How easy should this run be?")
        ui.onNodeWithTag("chat.send").performClick()
        waitText("Keep this run easy.")
    }

    @Test
    fun rebuildProposalShowsDraftAndCanBeApplied() {
        var applied = false
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val path = request.requestUrl!!.encodedPath
                    val body =
                        when (path) {
                            "/api/coach/active-plan" -> fixture("active_plan.json")
                            "/api/coach/chat/thread" ->
                                """{"messages":[{"id":501,"role":"assistant","content":"A revised week","tool_calls":[{"tool_call_id":"rebuild","card_type":"schedule_rebuild","card_data":{"proposal_id":8,"week":2}}]}],"proposals":{"8":{"status":"proposed","kind":"rebuild"}}}"""
                            "/api/coach/chat/proposals/8/apply" -> {
                                applied = true
                                "{}"
                            }
                            "/api/coach/chat/proposals/8" ->
                                if (applied) """{"id":8,"status":"applied"}"""
                                else
                                    """{"id":8,"status":"proposed","diff":{"days":[{"day":"Tuesday","kept":[],"before":[{"title":"Tempo","duration_minutes":45}],"after":[{"title":"Easy recovery","duration_minutes":30}]}],"totals":{"before":{"min":45,"km":8,"vert":0},"after":{"min":30,"km":5,"vert":0}}},"warnings":[]}"""
                            else -> "{}"
                        }
                    return MockResponse()
                        .setBody(body)
                        .setHeader("Content-Type", "application/json")
                }
            }
        ui.setContent { UphillTheme { ChatScreen(api, user, "en", {}) } }
        waitText("Easy recovery")
        ui.onNodeWithText("Apply").performScrollTo().performClick()
        waitText("applied")
        assertTrue(applied)
    }

    @Test
    fun raceHistoryOpensManualResultForm() {
        ui.setContent { UphillTheme { RaceHistoryScreen(api, user, "en", {}) } }
        waitText("Race history")
        ui.onNodeWithText("Add race").performClick()
        waitText("Race name")
    }

    @Test
    fun shoeRotationOpensSlotEditor() {
        ui.setContent { UphillTheme { GearScreen(api, user, "en", {}) } }
        waitText("Gear Vault")
        ui.onNodeWithText("Shoe rotation").performClick()
        waitText("daily")
    }
}

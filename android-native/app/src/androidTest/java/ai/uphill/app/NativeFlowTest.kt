package ai.uphill.app

import ai.uphill.app.core.auth.*
import ai.uphill.app.core.goal.ToolHandoff
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.persistence.*
import ai.uphill.app.designsystem.UphillTheme
import ai.uphill.app.feature.auth.*
import ai.uphill.app.feature.chat.ChatScreen
import ai.uphill.app.feature.gear.GearScreen
import ai.uphill.app.feature.nutrition.NutritionScreen
import ai.uphill.app.feature.onboarding.OnboardingScreen
import ai.uphill.app.feature.pace.PaceScreen
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
        ToolHandoff.pacingTargetMinutes = null
        ToolHandoff.fuelingHours = null
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
        ui.onNodeWithTag("plan.list").performScrollToNode(hasText("Hill Repeats"))
        ui.onNodeWithText("Hill Repeats").performClick()
        waitText("Mark missed")
    }

    @Test
    fun coachCanApproveEditDiscussAndRemoveAScopedWorkout() {
        val originalDispatcher = server.dispatcher
        val plan = org.json.JSONObject(fixture("active_plan.json"))
        plan
            .getJSONObject("plan")
            .put("start_date", java.time.LocalDate.now().minusWeeks(1).toString())
        val workouts = plan.getJSONArray("workouts")
        val workout =
            (0 until workouts.length())
                .map { workouts.getJSONObject(it) }
                .first { it.getString("title") == "Hill Repeats" && it.getInt("week_number") == 2 }
        val workoutId = workout.getInt("id")
        workout.put("approved_at", org.json.JSONObject.NULL)
        val prefix = "/api/coaching/athletes/7"
        val workoutPath = "$prefix/plans/93/workouts/$workoutId"
        var edited = false
        var removed = false
        var posted = false
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val path = request.requestUrl!!.encodedPath
                    val body =
                        when (path) {
                            "$prefix/active-plan" -> plan.toString()
                            "$workoutPath/approve" -> {
                                workout.put("approved_at", "2026-10-14T09:00:00Z")
                                workout.toString()
                            }
                            workoutPath -> {
                                val payload = org.json.JSONObject(request.body.readUtf8())
                                assertEquals("PUT", request.method)
                                assertEquals("Updated hill session", payload.getString("title"))
                                assertTrue(payload.isNull("day_of_week"))
                                workout.put("title", payload.getString("title"))
                                workout.put("approved_at", org.json.JSONObject.NULL)
                                edited = true
                                workout.toString()
                            }
                            "$workoutPath/remove" -> {
                                removed = true
                                workout.toString()
                            }
                            "$prefix/notes" ->
                                if (request.method == "POST") {
                                    val payload = org.json.JSONObject(request.body.readUtf8())
                                    assertEquals("workout", payload.getString("target_type"))
                                    assertEquals(workoutId, payload.getInt("target_id"))
                                    posted = true
                                    """{"id":10,"coach_id":19,"athlete_id":7,"target_type":"workout","target_id":$workoutId,"note":"Keep the climb controlled."}"""
                                } else """{"notes":[]}"""
                            else -> return originalDispatcher.dispatch(request)
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(body)
                }
            }
        ui.setContent {
            UphillTheme { PlanScreen(api, user.copy(role = "coach"), "en", {}, athleteId = 7) }
        }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithTag("plan.list").performScrollToNode(hasText("Hill Repeats"))
        ui.onNodeWithText("Hill Repeats").performClick()
        ui.waitUntil(15000) {
            ui.onAllNodesWithTag("detail.coach.approveWorkout").fetchSemanticsNodes().isNotEmpty()
        }
        ui.onNodeWithTag("detail.coach.approveWorkout").performScrollTo().performClick()
        ui.waitUntil(15000) {
            ui.onAllNodesWithTag("detail.coach.approveWorkout").fetchSemanticsNodes().isEmpty()
        }
        ui.waitUntil(15000) {
            ui.onAllNodes(hasTestTag("detail.coach.editWorkout") and isEnabled())
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        ui.onNodeWithTag("detail.coach.editWorkout").performScrollTo().performClick()
        ui.waitUntil(15000) {
            ui.onAllNodesWithTag("coach.edit.title").fetchSemanticsNodes().isNotEmpty()
        }
        ui.onNodeWithTag("coach.edit.title")
            .performScrollTo()
            .performTextReplacement("Updated hill session")
        ui.onNodeWithTag("coach.edit.save").performScrollTo().performClick()
        ui.waitUntil(15000) {
            ui.onAllNodesWithTag("detail.coach.editWorkout").fetchSemanticsNodes().isNotEmpty()
        }
        waitText("Updated hill session")
        ui.onNodeWithTag("coach.note.input")
            .performScrollTo()
            .performTextInput("Keep the climb controlled.")
        ui.onNodeWithTag("coach.note.post").performScrollTo().performClick()
        waitText("Keep the climb controlled.")
        ui.onNodeWithTag("detail.coach.removeWorkout").performScrollTo().performClick()
        waitText("This will permanently remove the workout")
        ui.onNodeWithTag("coach.remove.confirm").performClick()
        ui.waitUntil(15000) {
            ui.onAllNodesWithTag("coach.remove.confirm").fetchSemanticsNodes().isEmpty()
        }
        assertTrue(edited)
        assertTrue(posted)
        assertTrue(removed)
    }

    @Test
    fun savingWorkoutFeelingKeepsTheDetailOpenWithConfirmation() {
        val originalDispatcher = server.dispatcher
        val plan = org.json.JSONObject(fixture("active_plan.json"))
        val workouts = plan.getJSONArray("workouts")
        val workout =
            (0 until workouts.length())
                .map { workouts.getJSONObject(it) }
                .first { it.getString("title") == "Hill Repeats" }
        ai.uphill.app.core.plan.TrainingNavigation.workoutId.value = workout.getInt("id")
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val body =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coach/active-plan" -> plan.toString()
                            "/api/coach/workouts/log" -> {
                                val payload = org.json.JSONObject(request.body.readUtf8())
                                assertEquals(6, payload.getInt("rpe"))
                                workout.put("rpe", payload.getInt("rpe"))
                                """{"workouts":$workouts}"""
                            }
                            else -> return originalDispatcher.dispatch(request)
                        }
                    return MockResponse()
                        .setBody(body)
                        .setHeader("Content-Type", "application/json")
                }
            }
        ui.setContent { UphillTheme { PlanScreen(api, user, "en", {}) } }
        waitText("HOW DID IT FEEL?")
        ui.onNodeWithTag("detail.feeling.6").performScrollTo().performClick()
        ui.onNodeWithText("Save Log").performScrollTo().performClick()
        waitText("Saved")
        ui.onNodeWithTag("detail.feeling.6").assertExists()
    }

    @Test
    fun aToolKeepsItsOriginatingTabSelected() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val container =
            (context.applicationContext as ai.uphill.app.app.UphillApplication).container
        val previous = container.api.baseURL()
        val url = server.url("/").toString()
        try {
            kotlinx.coroutines.runBlocking { container.settings.environment(url) }
            ui.waitUntil(10000) { container.api.baseURL() == url }
            container.session.signOut()
            ui.setContent { UphillTheme { ai.uphill.app.app.RootNav(container) } }
            ui.runOnIdle { container.session.signIn(AuthResponse("fixture-session-only", user)) }
            waitText("Vietnam Mountain Marathon 42K")
            ui.onNode(hasText("Me") and hasClickAction()).performClick()
            waitText("Pace Strategy")
            ui.onNodeWithText("Pace Strategy").performScrollTo().performClick()
            waitText("Pace strategy")
            ui.onNode(hasText("Me") and hasClickAction()).assertIsSelected()
        } finally {
            container.session.signOut()
            kotlinx.coroutines.runBlocking { container.settings.environment(previous) }
        }
    }

    @Test
    fun syncingSuggestedWatchMatchDoesNotCompleteTheWorkout() {
        val originalDispatcher = server.dispatcher
        val plan = org.json.JSONObject(fixture("active_plan.json"))
        val workout = plan.getJSONArray("workouts").getJSONObject(0)
        workout.put("is_completed", 0)
        workout.put("is_missed", 1)
        val patches = java.util.concurrent.atomic.AtomicInteger()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val body =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coach/active-plan" -> plan.toString()
                            "/api/integrations/matching" ->
                                """{"activities":[{"activity_id":123,"workout_id":${workout.getInt("id")},"distance_km":5,"match_method":"suggest"}]}"""
                            "/api/integrations/coros/sync" -> """{"activities":1}"""
                            "/api/integrations/matching/run" -> "{}"
                            "/api/coach/workouts/log" -> {
                                patches.incrementAndGet()
                                """{"workouts":${plan.getJSONArray("workouts")}}"""
                            }
                            else -> return originalDispatcher.dispatch(request)
                        }
                    return MockResponse()
                        .setBody(body)
                        .setHeader("Content-Type", "application/json")
                }
            }
        ui.setContent { UphillTheme { PlanScreen(api, user, "en", {}) } }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithText("Manage").performClick()
        waitText("Sync watch")
        ui.onNodeWithText("Sync watch").performScrollTo().performClick()
        waitText("COROS · 1")
        assertEquals(0, patches.get())
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
    fun chatWeekReviewRendersLiveNestedNarrative() {
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val body =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coach/active-plan" -> fixture("active_plan.json")
                            "/api/coach/chat/thread" ->
                                """{"messages":[{"id":601,"role":"assistant","content":"Weekly reflection","tool_calls":[{"tool_call_id":"review","card_type":"week_review","card_data":{"week_number":2,"completion_pct":80,"planned":{"distance_km":42},"actual":{"total_actual_km":40},"narrative":{"summary":"Stable aerobic week.","highlights":["Completed the long run."],"watch":["Keep recovery easy."]}}}]}]}"""
                            else -> "{}"
                        }
                    return MockResponse().setBody(body)
                }
            }
        ui.setContent { UphillTheme { ChatScreen(api, user, "en", {}) } }
        waitText("Stable aerobic week.")
        ui.onNodeWithText("Completed the long run.").assertExists()
        ui.onNodeWithText("Keep recovery easy.").assertExists()
    }

    @Test
    fun raceHistoryOpensManualResultForm() {
        ui.setContent { UphillTheme { RaceHistoryScreen(api, user, "en", {}) } }
        waitText("Race history")
        ui.onNodeWithText("Add race").performClick()
        waitText("Race name")
    }

    @Test
    fun paceKeepsSelectedGoalWhenPlanLoads() {
        ToolHandoff.pacingTargetMinutes = 360.0
        ui.setContent { UphillTheme { PaceScreen(api, user, "en", {}) } }
        waitText("42.0")
        ui.onNodeWithTag("pace.target").assert(hasAnyDescendant(hasText("360.0")))
    }

    @Test
    fun nutritionKeepsPacingDurationWhenPlanLoads() {
        ToolHandoff.fuelingHours = 6.0
        ui.setContent { UphillTheme { NutritionScreen(api, user, "en", {}) } }
        waitText("42.0")
        ui.onNodeWithTag("nutrition.duration").assert(hasAnyDescendant(hasText("6.0")))
    }

    @Test
    fun shoeRotationOpensSlotEditor() {
        ui.setContent { UphillTheme { GearScreen(api, user, "en", {}) } }
        waitText("Gear Vault")
        ui.onNodeWithText("Shoe rotation").performClick()
        waitText("daily")
    }
}

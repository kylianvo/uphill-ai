package ai.uphill.app

import ai.uphill.app.core.auth.*
import ai.uphill.app.core.goal.ToolHandoff
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.persistence.*
import ai.uphill.app.feature.auth.*
import ai.uphill.app.feature.chat.ChatScreen
import ai.uphill.app.feature.gear.GearScreen
import ai.uphill.app.feature.nutrition.NutritionScreen
import ai.uphill.app.feature.onboarding.OnboardingScreen
import ai.uphill.app.feature.pace.PaceScreen
import ai.uphill.app.feature.plan.PlanScreen
import ai.uphill.app.feature.racehistory.RaceHistoryScreen
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.launch
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
        ui.setContent { AppFixture { SignInScreen(model) } }
        ui.onNodeWithTag("signin.email").performTextInput("runner@example.com")
        ui.onNodeWithTag("signin.password").performTextInput("incorrect-password")
        ui.onNodeWithTag("signin.submit").performClick()
        waitText("Invalid password")
        assertEquals(SessionState.SignedOut, session.state.value)
    }

    @Test
    fun onboardingSelectsGoalAndReachesTrainingSchedule() {
        ui.setContent {
            AppFixture { OnboardingScreen(api, user.copy(onboardingComplete = false), "en", {}) }
        }
        ui.onNodeWithText("Getting started").performClick()
        waitText("Connect your watch")
        ui.onNodeWithText("Next").performClick()
        waitText("Your training week")
    }

    @Test
    fun onboardingSeparatesTrailAndRoadGoalsAndCarriesTerrainIntoDetails() {
        ui.setContent {
            AppFixture { OnboardingScreen(api, user.copy(onboardingComplete = false), "en", {}) }
        }
        ui.onNodeWithText("This sets the shape of your whole plan.").assertExists()
        ui.onNodeWithText("A trail race").assertExists()
        ui.onNodeWithText("A road race").assertExists()
        ui.onNodeWithText("A distance").assertExists()
        ui.onNodeWithText("Getting started").assertExists()
        ui.onNodeWithText("A specific race").assertDoesNotExist()
        ui.onNodeWithText("Next").assertDoesNotExist()
        ui.onNodeWithContentDescription("Close").assertIsDisplayed()
        ui.onNodeWithText("A road race").performClick()
        waitText("Race name")
        ui.onNodeWithText("Road").assertIsSelected()
        ui.onNodeWithText("If I know the race, I know its distance and climbing.").assertExists()
    }

    @Test
    fun planOpensWorkoutDetailFromRecordedSchedule() {
        ui.setContent { AppFixture { PlanScreen(api, user, "en", {}) } }
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
            AppFixture {
                PlanScreen(api, user.copy(role = "coach", isCoach = true), "en", {}, athleteId = 7)
            }
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
    fun monthCalendarOpensADayBeforeItsWorkoutAndCanReturnToWeekList() {
        val haptics = java.util.concurrent.atomic.AtomicInteger()
        ui.setContent {
            androidx.compose.runtime.CompositionLocalProvider(
                androidx.compose.ui.platform.LocalHapticFeedback provides
                    object : androidx.compose.ui.hapticfeedback.HapticFeedback {
                        override fun performHapticFeedback(
                            hapticFeedbackType:
                                androidx.compose.ui.hapticfeedback.HapticFeedbackType
                        ) {
                            haptics.incrementAndGet()
                        }
                    }
            ) {
                AppFixture { PlanScreen(api, user, "en", {}) }
            }
        }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithTag("plan.list").performScrollToNode(hasContentDescription("Calendar"))
        ui.onNodeWithContentDescription("Calendar").performClick()
        ui.onNodeWithTag("calendar.next").performScrollTo().performClick()
        ui.onNodeWithTag("calendar.today").performScrollTo().performClick()
        ui.onNodeWithTag("calendar.grid").performScrollTo().performTouchInput { swipeLeft() }
        ui.onNodeWithTag("calendar.today").performScrollTo().performClick()
        ui.onAllNodesWithText("6", useUnmergedTree = false)
            .onFirst()
            .performScrollTo()
            .performClick()
        waitText("Open week 3 in list")
        ui.onNodeWithText("Hill Repeats").assertExists()
        ui.onNodeWithText("Open week 3 in list").performClick()
        ui.onNodeWithContentDescription("Calendar").assertExists()
        ui.onNodeWithTag("plan.list").performScrollToNode(hasText("Hill Repeats"))
        ui.onNodeWithText("Hill Repeats").assertIsDisplayed()
        assertEquals("One selection haptic for each month change", 4, haptics.get())
    }

    @Test
    fun coachCanChooseThirtyDaysEliteAndSearchTheRoster() {
        val original = server.dispatcher
        val queries = java.util.concurrent.CopyOnWriteArrayList<Pair<String?, String?>>()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val url = request.requestUrl!!
                    val name =
                        when (url.encodedPath) {
                            "/api/coaching/overview" -> {
                                queries.add(
                                    url.queryParameter("days") to url.queryParameter("level")
                                )
                                "coaching_overview.json"
                            }
                            "/api/coaching/roster" -> "coaching_roster.json"
                            "/api/coaching/my-invites" -> "coaching_my_invites.json"
                            else -> return original.dispatch(request)
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(fixture(name))
                }
            }
        ui.setContent {
            AppFixture {
                ai.uphill.app.feature.coaching.AthletesScreen(
                    api,
                    user.copy(isCoach = true),
                    "en",
                    {},
                )
            }
        }
        waitText("Target: 80%")
        ui.onNodeWithText("30d").performScrollTo().performClick()
        ui.waitUntil(15000) { queries.any { it.first == "30" } }
        ui.waitUntil(15000) {
            ui.onAllNodes(hasText("Elite") and isEnabled()).fetchSemanticsNodes().isNotEmpty()
        }
        ui.onNodeWithText("Elite").performScrollTo().performClick()
        ui.waitUntil(15000) { queries.any { it.first == "30" && it.second == "elite" } }
        ui.onNodeWithTag("coach.section.roster").performScrollTo().performClick()
        ui.onNodeWithTag("coach.roster.search").performScrollTo().performTextInput("Preview")
        ui.onNodeWithText("Preview Runner").assertExists()
        ui.onNodeWithText("Pending Invitee").assertDoesNotExist()
    }

    @Test
    fun coachRosterInvitesInlineAndRaceRowFiltersWithoutLeavingHub() {
        val original = server.dispatcher
        val invites = java.util.concurrent.CopyOnWriteArrayList<String>()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val name =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coaching/overview" -> "coaching_overview.json"
                            "/api/coaching/roster" -> "coaching_roster.json"
                            "/api/coaching/my-invites" -> "coaching_my_invites.json"
                            "/api/coaching/invite" -> {
                                invites.add(request.body.readUtf8())
                                return MockResponse()
                                    .setHeader("Content-Type", "application/json")
                                    .setBody("{}")
                            }
                            else -> return original.dispatch(request)
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(fixture(name))
                }
            }
        ui.setContent {
            AppFixture {
                ai.uphill.app.feature.coaching.AthletesScreen(
                    api,
                    user.copy(isCoach = true),
                    "en",
                    {},
                )
            }
        }
        waitText("Roster Progress")
        ui.onNodeWithText("Draft plans to finish").assertExists()
        ui.onNodeWithText("Workouts pending approval").assertExists()
        ui.onNodeWithTag("coach.race.0").performScrollTo().performClick()
        ui.onNodeWithTag("coach.roster.search").assertTextContains("Vietnam Mountain Marathon 42K")
        ui.onNodeWithText("Preview Runner").assertExists()
        ui.onNodeWithText("Pending Invitee").assertDoesNotExist()
        ui.onNodeWithContentDescription("Clear search").performScrollTo().performClick()
        ui.onNodeWithText("Pending Invitee").assertExists()
        ui.onNodeWithTag("coach.invite.email")
            .performScrollTo()
            .performTextInput("  new.runner@example.com  ")
        ui.onNodeWithTag("coach.invite.send").performClick()
        waitText("Invitation sent to new.runner@example.com!")
        assertEquals(
            "new.runner@example.com",
            org.json.JSONObject(invites.single()).getString("athlete_email"),
        )
    }

    @Test
    fun coachProfileReadsPreferencesEditsThresholdsAndPostsGeneralNotes() {
        val original = server.dispatcher
        val profile = org.json.JSONObject(fixture("coaching_athlete_profile.json"))
        val patches = java.util.concurrent.CopyOnWriteArrayList<String>()
        val noteRequests = java.util.concurrent.CopyOnWriteArrayList<String>()
        val noteQueries = java.util.concurrent.CopyOnWriteArrayList<String?>()
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val body =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coaching/overview" -> fixture("coaching_overview.json")
                            "/api/coaching/roster" -> fixture("coaching_roster.json")
                            "/api/coaching/my-invites" -> "[]"
                            "/api/coaching/athletes/7/profile" -> {
                                if (request.method == "PATCH") {
                                    val patch = request.body.readUtf8()
                                    patches.add(patch)
                                    profile.put(
                                        "resting_hr",
                                        org.json.JSONObject(patch).getInt("resting_hr"),
                                    )
                                }
                                profile.toString()
                            }
                            "/api/coaching/athletes/7/notes" -> {
                                if (request.method == "POST") {
                                    val note = request.body.readUtf8()
                                    noteRequests.add(note)
                                    org.json
                                        .JSONObject(note)
                                        .put("id", 99)
                                        .put("coach_id", 39)
                                        .put("athlete_id", 7)
                                        .toString()
                                } else {
                                    noteQueries.add(
                                        request.requestUrl!!.queryParameter("target_type")
                                    )
                                    "{\"notes\":[]}"
                                }
                            }
                            else -> return original.dispatch(request)
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(body)
                }
            }
        ui.setContent {
            AppFixture {
                ai.uphill.app.feature.coaching.AthletesScreen(
                    api,
                    user.copy(isCoach = true),
                    "en",
                    {},
                )
            }
        }
        waitText("Roster Progress")
        ui.onNodeWithTag("coach.section.roster").performScrollTo().performClick()
        ui.onNodeWithTag("coach.profile.7").performScrollTo().performClick()
        waitText("Physiology & Threshold Zones")
        ui.onNodeWithText("Training Preferences & Constraints").assertExists()
        ui.onNodeWithText("4 days/week").assertExists()
        ui.onNodeWithText("Saturday").assertExists()
        ui.onNodeWithTag("coach.profile.edit").performScrollTo().performClick()
        ui.onNode(hasText("Resting HR") and hasSetTextAction()).performTextReplacement("55")
        ui.onNodeWithText("Save", useUnmergedTree = true).performScrollTo().performClick()
        waitText("55 bpm")
        assertEquals(55, org.json.JSONObject(patches.single()).getInt("resting_hr"))
        assertEquals(1, org.json.JSONObject(patches.single()).length())
        ui.onNodeWithTag("coach.profile.note.input")
            .performScrollTo()
            .performTextInput("Keep the easy days easy.")
        ui.onNodeWithTag("coach.profile.note.post").performScrollTo()
        ui.onNodeWithText("Done").assertIsDisplayed()
        ui.onNodeWithTag("coach.profile.note.post").performClick()
        waitText("Keep the easy days easy.")
        val note = org.json.JSONObject(noteRequests.single())
        assertEquals("general", note.getString("target_type"))
        assertTrue(note.isNull("target_id"))
        assertEquals("Keep the easy days easy.", note.getString("note"))
        assertTrue(noteQueries.contains("general"))
    }

    @Test
    fun coachDashboardShowsChartsWithTargetAndAllWeekdays() {
        val original = server.dispatcher
        server.dispatcher =
            object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    val name =
                        when (request.requestUrl!!.encodedPath) {
                            "/api/coaching/overview" -> "coaching_overview.json"
                            "/api/coaching/roster" -> "coaching_roster.json"
                            "/api/coaching/my-invites" -> "coaching_my_invites.json"
                            else -> return original.dispatch(request)
                        }
                    return MockResponse()
                        .setHeader("Content-Type", "application/json")
                        .setBody(fixture(name))
                }
            }
        ui.setContent {
            AppFixture {
                ai.uphill.app.feature.coaching.AthletesScreen(
                    api,
                    user.copy(role = "coach", isCoach = true),
                    "en",
                    {},
                )
            }
        }
        waitText("Target: 80%")
        ui.onNodeWithTag("coach.adherence.chart").performScrollTo().assertExists()
        ui.onNodeWithTag("coach.missed.chart").performScrollTo().assertExists()
        ui.onNodeWithTag("coach.missed.chart")
            .assertContentDescriptionEquals(
                "Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 1, Sat: 0, Sun: 0"
            )
    }

    @Test
    fun setupCalendarEnforcesItsDateWindowAndPreservesTheSelectedDay() {
        var selected: java.time.LocalDate? = null
        ui.setContent {
            AppFixture {
                ai.uphill.app.feature.onboarding.SetupDatePicker(
                    java.time.LocalDate.of(2026, 10, 17),
                    java.time.LocalDate.of(2026, 10, 16),
                    java.time.LocalDate.of(2026, 10, 20),
                ) {
                    selected = it
                }
            }
        }
        fun day(number: Int) =
            ui.onNodeWithText(
                java.time.LocalDate.of(2026, 10, number)
                    .format(
                        java.time.format.DateTimeFormatter.ofPattern(
                            "EEEE, MMMM d, yyyy",
                            java.util.Locale.US,
                        )
                    ),
                substring = true,
            )
        day(15).assertIsNotEnabled()
        day(16).assertIsEnabled()
        day(20).assertIsEnabled()
        day(21).assertIsNotEnabled()
        day(19).performClick()
        ui.waitUntil { selected == java.time.LocalDate.of(2026, 10, 19) }
        assertEquals(java.time.LocalDate.of(2026, 10, 19), selected)
    }

    @Test
    fun profileShoeRotationUsesNeutralEmptySlotsAndKeepsSlotActions() {
        var selected: String? = null
        val rotation =
            ai.uphill.app.core.gear.ShoeRotation(
                listOf(
                    ai.uphill.app.core.gear.ShoeItem("daily", "Nike", "Pegasus 41", 630.0, 700.0)
                )
            )
        ui.setContent {
            AppFixture { ai.uphill.app.feature.me.ProfileShoeRotation(rotation) { selected = it } }
        }
        ui.onNodeWithTag("profile.rotation.daily.image", useUnmergedTree = true).assertExists()
        ui.onNodeWithTag("profile.rotation.tempo.empty", useUnmergedTree = true).assertExists()
        ui.onNodeWithTag("profile.rotation.tempo.image", useUnmergedTree = true)
            .assertDoesNotExist()
        ui.onNodeWithText("90%").assertExists()
        ui.onNodeWithTag("profile.rotation.tempo").performClick()
        assertEquals("tempo", selected)
    }

    @Test
    fun vietnameseCalendarWeeklyHeaderKeepsOneLineAtLargeText() {
        ui.setContent {
            val context = androidx.compose.ui.platform.LocalContext.current
            val configuration =
                android.content.res
                    .Configuration(androidx.compose.ui.platform.LocalConfiguration.current)
                    .apply { setLocale(java.util.Locale.forLanguageTag("vi")) }
            val density = androidx.compose.ui.platform.LocalDensity.current
            androidx.compose.runtime.CompositionLocalProvider(
                androidx.compose.ui.platform.LocalContext provides
                    context.createConfigurationContext(configuration),
                androidx.compose.ui.platform.LocalConfiguration provides configuration,
                androidx.compose.ui.platform.LocalDensity provides
                    androidx.compose.ui.unit.Density(density.density, 1.3f),
            ) {
                AppFixture { PlanScreen(api, user, "vi", {}) }
            }
        }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithTag("plan.list").performScrollToNode(hasContentDescription("Lịch"))
        ui.onNodeWithContentDescription("Lịch").performClick()
        ui.onNodeWithTag("plan.list").performScrollToNode(hasTestTag("calendar.weekHeader"))
        val results = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
        ui.onNodeWithTag("calendar.weekHeader").performSemanticsAction(
            androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult
        ) {
            it(results)
        }
        assertEquals(1, results.single().lineCount)
        assertFalse(results.single().hasVisualOverflow)
        ui.onNodeWithTag("calendar.weekHeader").assertTextEquals("km/tuần")
    }

    @Test
    fun largeTextWorkoutPaceKeepsEachTimeIntact() {
        ui.setContent {
            val density = androidx.compose.ui.platform.LocalDensity.current
            androidx.compose.runtime.CompositionLocalProvider(
                androidx.compose.ui.platform.LocalDensity provides
                    androidx.compose.ui.unit.Density(density.density, 1.3f)
            ) {
                AppFixture {
                    androidx.compose.foundation.layout.Column(
                        androidx.compose.ui.Modifier.width(371.dp)
                    ) {
                        ai.uphill.app.feature.plan.WorkoutDetailBody(
                            ai.uphill.app.core.models.Workout(
                                1,
                                93,
                                2,
                                title = "Hill Repeats",
                                type = "Interval",
                                durationMinutes = 60.0,
                                targetPace = "6:10-6:50 /km",
                            ),
                            null,
                            {},
                        )
                    }
                }
            }
        }
        val results = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
        ui.onAllNodesWithText("6:10", substring = true, useUnmergedTree = true)
            .onFirst()
            .performSemanticsAction(
                androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult
            ) {
                it(results)
            }
        val layout = results.single()
        val lines =
            (0 until layout.lineCount).map {
                layout.layoutInput.text.text.substring(
                    layout.getLineStart(it),
                    layout.getLineEnd(it),
                )
            }
        assertTrue(
            "Pace split across lines: $lines",
            lines.any { it.contains("6:10") } && lines.any { it.contains("6:50") },
        )
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
        ui.setContent { AppFixture { PlanScreen(api, user, "en", {}) } }
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
            ui.setContent { AppFixture { ai.uphill.app.app.RootNav(container) } }
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
        ui.setContent { AppFixture { PlanScreen(api, user, "en", {}) } }
        waitText("Vietnam Mountain Marathon 42K")
        ui.onNodeWithText("Manage").performClick()
        waitText("Sync watch")
        ui.onNodeWithText("Sync watch").performScrollTo().performClick()
        waitText("COROS · 1")
        assertEquals(0, patches.get())
    }

    @Test
    fun scheduleChangeEnablesRebuildAndAsksForConfirmation() {
        ui.setContent { AppFixture { PlanScreen(api, user, "en", {}) } }
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
        ui.setContent { AppFixture { ChatScreen(api, user, "en", {}) } }
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
        ui.setContent { AppFixture { ChatScreen(api, user, "en", {}) } }
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
        ui.setContent { AppFixture { ChatScreen(api, user, "en", {}) } }
        waitText("Stable aerobic week.")
        ui.onNodeWithText("Completed the long run.").assertExists()
        ui.onNodeWithText("Keep recovery easy.").assertExists()
    }

    @Test
    fun knowledgeSearchFindsKeyPointsAndWhitespaceKeepsTheLibrary() = verifyKnowledgeLibrary("en")

    @Test
    fun knowledgeLibraryWorksInVietnamese() = verifyKnowledgeLibrary("vi")

    private fun verifyKnowledgeLibrary(lang: String) {
        val original = server.dispatcher
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (request.requestUrl!!.encodedPath == "/api/knowledge/cards") {
                    return MockResponse().setHeader("Content-Type", "application/json").setBody(
                        """{"cards":[{"id":801,"chapter_title":"Fueling on long runs","summary":"Practise your race plan.","key_points":["Check your sodium budget."],"tags":["electrolytes","race-day-fueling"],"topic":"Nutrition"},{"id":802,"chapter_title":"Aerobic base","summary":"Keep easy work easy.","key_points":["Build consistency."],"topic":"Training"}]}"""
                    )
                }
                return original.dispatch(request)
            }
        }
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val configuration = android.content.res.Configuration(context.resources.configuration).apply {
            setLocale(java.util.Locale.forLanguageTag(lang))
        }
        val localizedContext = context.createConfigurationContext(configuration)
        ui.setContent {
            CompositionLocalProvider(LocalContext provides localizedContext, LocalConfiguration provides configuration) {
                AppFixture { ai.uphill.app.feature.knowledge.KnowledgeScreen(api, user, lang, {}) }
            }
        }
        waitText("Fueling on long runs")
        captureFixtureScreenshot("knowledge-library-$lang")
        val search = ui.onNodeWithTag("knowledge.search")
        search.performClick().performTextInput("SoDiUm")
        ui.onNodeWithText("Fueling on long runs").assertExists()
        ui.onNodeWithText("Aerobic base").assertDoesNotExist()
        ui.onNodeWithText("Check your sodium budget.").assertDoesNotExist()
        ui.onNodeWithText("Fueling on long runs").performClick()
        ui.onNodeWithText("Check your sodium budget.").assertExists()
        ui.onNodeWithText("#electrolytes", useUnmergedTree = true).performScrollTo().assertIsDisplayed()
        assertAboveKeyboard("#electrolytes")
        captureFixtureScreenshot("knowledge-expanded-$lang")
        ui.onNodeWithText("Fueling on long runs").performClick()
        ui.onNodeWithText("Check your sodium budget.").assertDoesNotExist()
        ui.onNodeWithText("#electrolytes").assertDoesNotExist()
        captureFixtureScreenshot("knowledge-keypoint-search-$lang")
        search.performTextReplacement("no-matches")
        waitText(ai.uphill.app.core.localization.localizedText(localizedContext, "No cards matching \"%@\"", "no-matches"))
        val emptyHint = ai.uphill.app.core.localization.localizedText(localizedContext,
            "Try searching for terms like aerobic, carbs, sodium, sleep, or poles.")
        ui.onNodeWithText(emptyHint, useUnmergedTree = true).performScrollTo()
        assertAboveKeyboard(emptyHint)
        captureFixtureScreenshot("knowledge-empty-$lang")
        search.performTextReplacement("   ")
        ui.onAllNodesWithText("Fueling on long runs").assertCountEquals(1)
        ui.onAllNodesWithText("Aerobic base").assertCountEquals(1)
        ui.onNodeWithTag("knowledge.topic.Nutrition").performScrollTo().performClick()
        ui.onNodeWithText("Fueling on long runs").assertExists()
        ui.onNodeWithText("Aerobic base").assertDoesNotExist()
    }

    @Test
    fun knowledgeSourceIngestionClearsTheSubmittedLinkAfterSuccess() = verifyKnowledgeSource("en")

    @Test
    fun knowledgeSourceErrorsKeepTheLinkAndRetryInVietnamese() = verifyKnowledgeSource("vi")

    private fun verifyKnowledgeSource(lang: String) {
        val original = server.dispatcher
        val submitted = java.util.concurrent.CopyOnWriteArrayList<String>()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                return when (request.requestUrl!!.encodedPath) {
                    "/api/rag/sources" -> MockResponse().setBody(
                        """[{"id":9,"title":"Training notes","type":"pdf","url":"https://example.com/notes.pdf"},{"id":10,"title":"Uphill practice podcast","type":"youtube","url":"https://example.com/podcast"}]"""
                    )
                    "/api/rag/link" -> {
                        submitted.add(org.json.JSONObject(request.body.readUtf8()).getString("url"))
                        if (submitted.size == 1) MockResponse().setResponseCode(503)
                        else MockResponse().setBody("{}")
                    }
                    else -> original.dispatch(request)
                }
            }
        }
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val configuration = android.content.res.Configuration(context.resources.configuration).apply {
            setLocale(java.util.Locale.forLanguageTag(lang))
        }
        val localizedContext = context.createConfigurationContext(configuration)
        ui.setContent {
            CompositionLocalProvider(LocalContext provides localizedContext, LocalConfiguration provides configuration) {
                AppFixture { ai.uphill.app.feature.knowledge.KnowledgeScreen(api, user.copy(role = "admin"), lang, {}) }
            }
        }
        ui.onNodeWithTag("knowledge.sources.toggle").performScrollTo().performClick()
        val input = ui.onNodeWithTag("knowledge.source.url")
        input.performScrollTo().performTextInput("not-a-link")
        ui.onNodeWithTag("knowledge.source.submit").assertIsNotEnabled()
        input.performTextReplacement("https://example.com/endurance")
        ui.onNodeWithTag("knowledge.source.submit").performScrollTo().performClick()
        val errorText = ai.uphill.app.core.localization.localizedText(localizedContext,
            "Something went wrong (%lld). Please try again.", 503L)
        waitText(errorText)
        assertEquals("https://example.com/endurance",
            input.fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text)
        ui.onNodeWithTag("knowledge.sources.panel").performScrollTo()
        ui.onNodeWithText(errorText).assertIsDisplayed()
        captureFixtureScreenshot("knowledge-source-error-$lang")
        ui.onNodeWithTag("knowledge.source.submit").performScrollTo().performClick()
        waitText(ai.uphill.app.core.localization.localizedText(localizedContext, "Source added to indexing queue"))
        assertEquals(listOf("https://example.com/endurance", "https://example.com/endurance"), submitted.toList())
        ui.waitUntil(5000) {
            input.fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text.isEmpty()
        }
        ui.onNodeWithTag("knowledge.sources.panel").performScrollTo()
        captureFixtureScreenshot("knowledge-source-success-$lang")
    }

    @Test
    fun knowledgeReadersCanBrowseSourcesWithoutAdminIngestionControls() {
        val original = server.dispatcher
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (request.requestUrl!!.encodedPath == "/api/rag/sources") return MockResponse().setBody(
                    """[{"id":9,"title":"Training notes","type":"pdf","url":"https://example.com/notes.pdf"}]"""
                )
                return original.dispatch(request)
            }
        }
        ui.setContent { AppFixture { ai.uphill.app.feature.knowledge.KnowledgeScreen(api, user, "en", {}) } }
        ui.onNodeWithTag("knowledge.sources.toggle").performScrollTo().performClick()
        waitText("Training notes")
        ui.onNodeWithTag("knowledge.source.url").assertDoesNotExist()
        ui.onNodeWithTag("knowledge.source.submit").assertDoesNotExist()
        ui.onNodeWithTag("knowledge.sources.panel").performScrollTo()
        captureFixtureScreenshot("knowledge-sources-reader-en")
    }

    @Test
    fun sessionRestoreShowsRetryWithoutClearingTheToken() = verifyRestoreRetry("en")

    @Test
    fun sessionRestoreShowsVietnameseRetry() = verifyRestoreRetry("vi")

    private fun verifyRestoreRetry(lang: String) {
        val original = server.dispatcher
        val attempts = java.util.concurrent.atomic.AtomicInteger()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (request.requestUrl!!.encodedPath == "/api/auth/me") {
                    assertEquals("Bearer fixture-session-only", request.getHeader("Authorization"))
                    return if (attempts.getAndIncrement() == 0) MockResponse().setResponseCode(503)
                    else MockResponse().setHeader("Content-Type", "application/json").setBody(fixture("auth_me.json"))
                }
                return original.dispatch(request)
            }
        }
        val tokens = MemoryTokenStore("fixture-session-only")
        var cleared = false
        val session = SessionStore(tokens, { null }, {}, { cleared = true })
        val auth = AuthService(APIClient({ server.url("/").toString() }, tokens))
        kotlinx.coroutines.runBlocking { session.restore { auth.me() } }
        assertEquals(SessionState.Restoring, session.state.value)
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val configuration = android.content.res.Configuration(context.resources.configuration).apply {
            setLocale(java.util.Locale.forLanguageTag(lang))
        }
        val localizedContext = context.createConfigurationContext(configuration)
        ui.setContent {
            CompositionLocalProvider(LocalContext provides localizedContext, LocalConfiguration provides configuration) {
                val state by session.state.collectAsState()
                val error by session.restoreError.collectAsState()
                val scope = rememberCoroutineScope()
                AppFixture {
                    if (state is SessionState.SignedIn) androidx.compose.material3.Text("Session restored")
                    else ai.uphill.app.feature.launch.LaunchScreen(
                        error = error?.let { ai.uphill.app.core.localization.localizedError(localizedContext, it) },
                        onRetry = { scope.launch { session.restore { auth.me() } } },
                    )
                }
            }
        }
        val retry = ai.uphill.app.core.localization.localizedText(localizedContext, "Try again")
        waitText(retry)
        captureFixtureScreenshot("session-restore-error-$lang")
        ui.onNodeWithText(retry).performClick()
        waitText("Session restored")
        assertEquals("fixture-session-only", tokens.read())
        assertFalse(cleared)
        assertNull(session.restoreError.value)
        assertEquals(2, attempts.get())
    }

    private fun assertAboveKeyboard(text: String) {
        val visible = android.graphics.Rect()
        ui.waitUntil(5000) {
            var keyboardVisible = false
            InstrumentationRegistry.getInstrumentation().runOnMainSync {
                val activity = androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry.getInstance()
                    .getActivitiesInStage(androidx.test.runner.lifecycle.Stage.RESUMED).first()
                val view = activity.window.decorView
                view.getWindowVisibleDisplayFrame(visible)
                keyboardVisible = androidx.core.view.ViewCompat.getRootWindowInsets(view)
                    ?.isVisible(androidx.core.view.WindowInsetsCompat.Type.ime()) == true
            }
            keyboardVisible
        }
        ui.waitForIdle()
        val bounds = ui.onNodeWithText(text, useUnmergedTree = true).fetchSemanticsNode().boundsInWindow
        assertTrue("Text bottom ${bounds.bottom} exceeds keyboard top ${visible.bottom}",
            bounds.bottom <= visible.bottom)
    }

    private fun captureFixtureScreenshot(name: String) {
        val args = InstrumentationRegistry.getArguments()
        if (args.getString("captureEvidence") != "true") return
        ui.waitForIdle()
        val variant = args.getString("captureVariant") ?: "normal"
        val automation = InstrumentationRegistry.getInstrumentation().uiAutomation
        val directory = "/sdcard/Download/uphill-evidence/$variant"
        automation.executeShellCommand("mkdir -p $directory").use {
            java.io.FileInputStream(it.fileDescriptor).readBytes()
        }
        automation.executeShellCommand("screencap -p $directory/$name.png").use {
            java.io.FileInputStream(it.fileDescriptor).readBytes()
        }
    }

    @Test
    fun raceHistoryOpensManualResultForm() {
        ui.setContent { AppFixture { RaceHistoryScreen(api, user, "en", {}) } }
        waitText("Race history")
        ui.onNodeWithText("Add race").performClick()
        waitText("Race name")
    }

    @Test
    fun paceKeepsSelectedGoalWhenPlanLoads() {
        ToolHandoff.pacingTargetMinutes = 360.0
        ui.setContent { AppFixture { PaceScreen(api, user, "en", {}) } }
        waitText("42")
        assertEquals(360f, ui.onNodeWithTag("pace.target").fetchSemanticsNode()
            .config[androidx.compose.ui.semantics.SemanticsProperties.ProgressBarRangeInfo].current, .01f)
        val strategy = ui.onNodeWithTag("pace.bias").performScrollTo()
        strategy.performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.SetProgress) { it(-.03f) }
        ui.onNodeWithText("Conservative Start (Negative Split)").assertExists()
        strategy.performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.SetProgress) { it(.03f) }
        ui.onNodeWithText("Aggressive Start (Positive Split)").assertExists()
        strategy.performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.SetProgress) { it(.01f) }
        ui.onNodeWithText("Even Effort (Optimal Economy)").assertExists()
    }

    @Test
    fun nutritionKeepsPacingDurationWhenPlanLoads() {
        ToolHandoff.fuelingHours = 6.0
        ui.setContent { AppFixture { NutritionScreen(api, user, "en", {}) } }
        waitText("42.0")
        ui.onNodeWithTag("nutrition.duration").assert(hasAnyDescendant(hasText("6.0")))
    }

    @Test
    fun shoeRotationOpensSlotEditor() {
        ui.setContent { AppFixture { GearScreen(api, user, "en", {}) } }
        waitText("Gear Vault")
        ui.onNodeWithText("Shoe rotation").performClick()
        waitText("daily")
    }
}

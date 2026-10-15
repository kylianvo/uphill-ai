package ai.uphill.app

import ai.uphill.app.core.auth.*
import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.gear.*
import ai.uphill.app.core.generation.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.plan.PlanService
import ai.uphill.app.core.profile.ProfileService
import ai.uphill.app.designsystem.UphillTheme
import ai.uphill.app.feature.plan.PlanScreen
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import java.util.UUID
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.Assert.*

/** Opt-in checks against an isolated local backend; never accepts a production URL. */
class LiveBackendFlowTest {
    @get:Rule val ui = createComposeRule()

    @Test
    fun localAuthGenerationRotationAndCoachingContracts(): Unit = runBlocking {
        val url = InstrumentationRegistry.getArguments().getString("liveBackendURL")
        Assume.assumeTrue(url?.startsWith("http://10.0.2.2:") == true)
        val suffix = UUID.randomUUID().toString().take(8)
        fun client() = APIClient({ requireNotNull(url) }, MemoryTokenStore())
        suspend fun register(api: APIClient, role: String): AuthResponse {
            val response =
                AuthService(api)
                    .register(
                        "Android $role evidence",
                        "android-$role-$suffix@example.test",
                        "LocalAndroidEvidence123",
                    )
            api.tokenStore.write(response.sessionToken)
            return response
        }
        val athleteApi = client()
        val athlete = register(athleteApi, "athlete")
        val generation = GenerationService(athleteApi)
        val started =
            generation.onboarding(
                buildJsonObject {
                    put("goal_type", "start_running")
                    put("lang", "en")
                    put("age", 30)
                    put("days_per_week", 3)
                    put("current_weekly_km", 12)
                    put("long_run_day", "Sunday")
                    put(
                        "preferred_run_days",
                        buildJsonArray {
                            add("Tuesday")
                            add("Thursday")
                            add("Sunday")
                        },
                    )
                }
            )
        assertNotNull(started.jobId)
        val outcome =
            JobPoller(generation::status, timeoutMs = 60000).wait(requireNotNull(started.jobId))
        assertTrue(
            "Local onboarding generation did not finish: $outcome",
            outcome is JobOutcome.Done,
        )
        val profile = AuthService(athleteApi).me()
        assertTrue(profile.onboardingComplete)
        ProfileService(athleteApi)
            .update(profile, mapOf("gemini_api_key" to "fake-local-key-to-preserve"))
        val updated =
            ProfileService(athleteApi)
                .update(profile, mapOf("athlete_notes" to "Android local integration evidence"))
        assertEquals("Android local integration evidence", updated.athleteNotes)
        assertEquals(
            "fake-local-key-to-preserve",
            athleteApi
                .element(Endpoint("GET", "/api/auth/me"))
                .jsonObject["gemini_api_key"]!!
                .jsonPrimitive
                .content,
        )
        ProfileService(athleteApi).update(updated, mapOf("gemini_api_key" to ""))
        val plans = PlanService(athleteApi)
        val snapshot = requireNotNull(plans.activePlan())
        assertTrue(snapshot.workouts.isNotEmpty())
        val workout = snapshot.workouts.first { !it.isRest }
        val logged = plans.log(workout.id, completed = 1, rpe = 3, notes = "Comfortable effort")
        assertEquals(1, logged.first { it.id == workout.id }.isCompleted)
        val gear = GearService(athleteApi)
        val rotation =
            ShoeRotation(listOf(ShoeItem("daily", "Nike", "Pegasus 41", distanceKm = 12.0)))
        gear.save(rotation)
        assertEquals(rotation, gear.rotation())

        val coachApi = client()
        val coach = register(coachApi, "coach")
        val adminApi = client()
        val admin =
            adminApi.send<AuthResponse>(
                Endpoint(
                    "POST",
                    "/api/auth/mock-login",
                    buildJsonObject { put("email", "admin@uphill.ai") },
                    requiresAuth = false,
                )
            )
        adminApi.tokenStore.write(admin.sessionToken)
        adminApi.text(
            Endpoint(
                "POST",
                "/api/admin/users/${coach.user.id}/coach-status",
                buildJsonObject { put("is_coach", true) },
            )
        )
        assertTrue(AuthService(coachApi).me().isCoach)
        val coaching = CoachingService(coachApi)
        coaching.invite(athlete.user.email)
        val athleteCoaching = CoachingService(athleteApi)
        val invite = athleteCoaching.invites().first { it.coachId == coach.user.id }
        athleteCoaching.accept(invite.id)
        assertTrue(coaching.roster().any { it.athleteId == athlete.user.id })
        assertEquals(snapshot.plan.id, coaching.activePlan(athlete.user.id)?.plan?.id)
        val added =
            coaching.addWorkout(
                athlete.user.id,
                snapshot.plan.id,
                CoachWorkoutCreatePayload(
                    1,
                    "Friday",
                    "Base",
                    "Coach local session",
                    "Easy",
                    30.0,
                    "Zone 2",
                    4.0,
                ),
            )
        val edited =
            coaching.editWorkout(
                athlete.user.id,
                snapshot.plan.id,
                added.id,
                CoachWorkoutUpdatePayload(title = "Reviewed local session", durationMinutes = 35.0),
            )
        assertEquals("Reviewed local session", edited.title)
        assertEquals("Friday", edited.dayOfWeek)
        assertNull(edited.approvedAt)
        assertNotNull(coaching.approve(athlete.user.id, snapshot.plan.id, added.id).approvedAt)
        val note =
            coaching.addNote(
                athlete.user.id,
                CoachNoteCreatePayload("workout", "Keep the climb controlled.", workout.id),
            )
        assertTrue(
            athleteCoaching.notes(athlete.user.id, "workout", workout.id).any { it.id == note.id }
        )
        coaching.removeWorkout(athlete.user.id, snapshot.plan.id, added.id)
        val removed = coaching.activePlan(athlete.user.id)!!.workouts.first { it.id == added.id }
        assertEquals("Rest", removed.type)
        assertEquals(0.0, removed.durationMinutes, 0.0)
        AuthService(coachApi).logout()
        AuthService(adminApi).logout()
        ai.uphill.app.core.plan.TrainingNavigation.workoutId.value = workout.id
        ui.setContent { UphillTheme { PlanScreen(athleteApi, updated, "en", {}) } }
        ui.waitUntil(15000) {
            ui.onAllNodesWithText(snapshot.plan.raceName).fetchSemanticsNodes().isNotEmpty()
        }
        ui.waitUntil(15000) {
            ui.onAllNodesWithText("Keep the climb controlled.").fetchSemanticsNodes().isNotEmpty()
        }
        ui.onNodeWithText("Notes from your coach").performScrollTo().assertExists()
    }
}

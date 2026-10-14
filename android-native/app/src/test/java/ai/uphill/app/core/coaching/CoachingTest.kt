package ai.uphill.app.core.coaching

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.*
import org.junit.Assert.*
import org.junit.Test

class CoachingTest {
    @Test
    fun fixturesDecodeRosterOverviewNotesAndPlans() {
        fun text(n: String) = javaClass.classLoader!!.getResource(n)!!.readText()
        assertTrue(
            JSONCoding.json
                .decodeFromString<List<CoachedAthleteRow>>(text("coaching_roster.json"))
                .isNotEmpty()
        )
        assertTrue(
            JSONCoding.json
                .decodeFromString<CoachOverview>(text("coaching_overview.json"))
                .athletes
                .isNotEmpty()
        )
        assertTrue(
            JSONCoding.json
                .decodeFromString<CoachNotesResponse>(text("coaching_notes.json"))
                .notes
                .isNotEmpty()
        )
        assertNotNull(
            JSONCoding.json
                .decodeFromString<CoachPlanResponse>(text("coaching_athlete_draft_plan.json"))
                .snapshot
        )
    }

    @Test
    fun aiCreateAndNotesUseAthleteScopedEndpoints() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            val fixture =
                javaClass.classLoader!!.getResource("coaching_athlete_draft_plan.json")!!.readText()
            val w =
                JSONCoding.json.parseToJsonElement(fixture).jsonObject["workouts"]!!.jsonArray[1]
            server.enqueue(MockResponse().setBody(w.toString()))
            server.enqueue(
                MockResponse()
                    .setBody(
                        javaClass.classLoader!!.getResource("coaching_notes.json")!!.readText()
                    )
            )
            val service =
                CoachingService(APIClient({ server.url("/").toString() }, MemoryTokenStore("t")))
            service.aiCreateWorkout(
                7,
                169,
                CoachWorkoutAiCreatePayload(
                    2,
                    "Tuesday",
                    "Threshold",
                    40.0,
                    "Control the downhill cadence.",
                ),
            )
            val req = server.takeRequest()
            assertEquals("/api/coaching/athletes/7/plans/169/workouts/ai-create", req.path)
            val body = JSONCoding.json.parseToJsonElement(req.body.readUtf8()).jsonObject
            assertEquals("Threshold", body["workout_type"]!!.jsonPrimitive.content)
            assertEquals(40.0, body["duration_minutes"]!!.jsonPrimitive.double, 0.001)
            assertEquals("Control the downhill cadence.", body["intent"]!!.jsonPrimitive.content)
            service.notes(7, "workout", 1806)
            val notesReq = server.takeRequest()
            assertEquals("workout", notesReq.requestUrl!!.queryParameter("target_type"))
            assertEquals("1806", notesReq.requestUrl!!.queryParameter("target_id"))
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun inviteAcceptsTheLinkResponseWithoutRosterEmailDecoration() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(
                MockResponse()
                    .setBody(
                        """{"id":10,"coach_id":5,"athlete_id":7,"status":"invited","invited_at":"2026-10-15T00:00:00Z","responded_at":null}"""
                    )
            )
            val service =
                CoachingService(
                    APIClient({ server.url("/").toString() }, MemoryTokenStore("token"))
                )
            service.invite("  runner@example.test  ")
            val request = server.takeRequest()
            assertEquals("POST", request.method)
            assertEquals("/api/coaching/invite", request.path)
            assertEquals(
                "runner@example.test",
                JSONCoding.json
                    .parseToJsonElement(request.body.readUtf8())
                    .jsonObject["athlete_email"]!!
                    .jsonPrimitive
                    .content,
            )
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun physiologyOnlyPatchesChangedFieldsAndValidatesOrder() {
        val d =
            PhysiologyDraft(
                restingHr = "50",
                aetHr = "140",
                antHr = "160",
                maxHr = "185",
                zone2PaceMin = "7:00",
                zone2PaceMax = "6:00",
                thresholdPace = "5:00",
            )
        d.validate()
        assertTrue(runCatching { d.copy(aetHr = "190").validate() }.isFailure)
        assertTrue(runCatching { d.copy(zone2PaceMin = "5:00").validate() }.isFailure)
        val patch = d.patch(d.copy(restingHr = "49"))
        assertEquals(setOf("resting_hr"), patch.keys)
    }
}

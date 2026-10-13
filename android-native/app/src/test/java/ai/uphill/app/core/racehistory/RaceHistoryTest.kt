package ai.uphill.app.core.racehistory

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.*
import okhttp3.mockwebserver.*
import org.junit.Assert.*
import org.junit.Test

class RaceHistoryTest {
    @Test
    fun draftRejectsInvalidDurationRankAndUnsafeLink() {
        val valid = ManualRaceDraft(raceName = "Race", distance = "50", duration = "5:30:00")
        assertEquals(19800, valid.payload().finishTimeSec)
        listOf(
                valid.copy(duration = "1:60:00"),
                valid.copy(rankOverall = "10", totalOverall = "3"),
                valid.copy(resultUrl = "https://user:password@example.com/results"),
                valid.copy(distance = "NaN"),
            )
            .forEach { assertTrue(runCatching { it.payload() }.isFailure) }
        assertNull(valid.copy(isDnf = true, duration = "bad").payload().finishTimeSec)
    }

    @Test
    fun badgesUseLatestSelectedFinishAndExcludeDnf() {
        val early =
            RaceResult(
                1,
                raceName = "R",
                raceDate = "2025-01-01",
                distanceKm = 50.0,
                finishTimeSec = 10000,
            )
        val latest = early.copy(id = 2, raceDate = "2026-01-01", finishTimeSec = 12000)
        val dnf = latest.copy(id = 3, raceDate = "2026-02-01", isDnf = true)
        assertEquals(
            2,
            DistanceBadge.derive(listOf(early, latest, dnf))
                .first { it.category == DistanceCategory.FIFTY_K }
                .result!!
                .id,
        )
        assertNull(DistanceCategory.match(80.0))
    }

    @Test
    fun patchClearsOptionalFields() {
        val p = ManualRaceDraft(raceName = "R", distance = "42.2", duration = "3:30:00").payload()
        assertEquals(JsonNull, p.patch()["bib"])
        assertEquals(JsonNull, p.patch()["user_note"])
    }

    @Test
    fun detailsDecodeSharedFixtures() {
        for (name in
            listOf("race_detail.json", "race_detail_missing.json", "race_detail_ambiguous.json")) {
            val text = javaClass.classLoader!!.getResource(name)!!.readText()
            val detail = JSONCoding.json.decodeFromString<RaceDetailResponse>(text)
            assertTrue(detail.result.id > 0)
        }
    }

    @Test
    fun searchUsesQueryAndBibUsesPost() = runTest {
        val server = MockWebServer()
        server.start()
        try {
            server.enqueue(MockResponse().setBody("[]"))
            server.enqueue(MockResponse().setBody("{}"))
            val s =
                RaceHistoryService(APIClient({ server.url("/").toString() }, MemoryTokenStore("t")))
            s.search("utmb", "Nguyen Van")
            assertEquals("Nguyen Van", server.takeRequest().requestUrl!!.queryParameter("q"))
            s.verifyBib(9, "321")
            val req = server.takeRequest()
            assertEquals("/api/race-history/claims/9/verify-bib", req.path)
            assertEquals(
                "321",
                JSONCoding.json
                    .parseToJsonElement(req.body.readUtf8())
                    .jsonObject["bib"]!!
                    .jsonPrimitive
                    .content,
            )
        } finally {
            server.shutdown()
        }
    }
}

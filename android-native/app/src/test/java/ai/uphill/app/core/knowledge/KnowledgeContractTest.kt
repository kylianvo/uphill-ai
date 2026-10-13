package ai.uphill.app.core.knowledge

import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.JSONCoding
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class KnowledgeContractTest {
    @Test
    fun sharedRaceMatchFixtureDecodes() {
        val raw = javaClass.getResource("/race_match.json")!!.readText()
        assertFalse(JSONCoding.json.decodeFromString<RaceMatchResponse>(raw).matched)
    }

    @Test
    fun sharedGoalFixtureAcceptsMissingOptionalFieldData() {
        val raw =
            JSONCoding.json
                .parseToJsonElement(javaClass.getResource("/plan_goal.json")!!.readText())
                .jsonObject["assessment"]!!
                .toString()
        val goal = JSONCoding.json.decodeFromString<GoalAssessmentResponse>(raw)
        assertEquals(42.0, goal.distanceKm, 0.0)
        assertNull(goal.goals)
        assertTrue(goal.missing!!.contains("watch"))
    }

    @Test
    fun cardDefaultsAllowMinimalBackendCard() {
        val card =
            JSONCoding.json
                .decodeFromString<KnowledgeCardsResponse>(
                    """{"cards":[{"id":1,"chapter_title":"Aerobic","summary":"Base"}]}"""
                )
                .cards
                .single()
        assertTrue(card.keyPoints.isEmpty())
        assertEquals("Training", card.topic)
    }
}

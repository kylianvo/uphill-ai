package ai.uphill.app.core.knowledge

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.*

class KnowledgeService(private val api: APIClient) {
    suspend fun cards(topic: String? = null, lang: String = "en"): List<KnowledgeCard> {
        val q = mutableMapOf("lang" to lang)
        if (topic != null && topic != "All") q["topic"] = topic
        return try {
            api.send<KnowledgeCardsResponse>(Endpoint("GET", "/api/knowledge/cards", query = q))
                .cards
                .ifEmpty { curatedCards(lang, topic) }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            curatedCards(lang, topic)
        }
    }

    suspend fun topics(): List<String> =
        try {
            api.send<List<String>>(Endpoint("GET", "/api/knowledge/topics")).let {
                if ("All" in it) it else listOf("All") + it
            }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            listOf("All", "Training", "Nutrition", "Recovery", "Pacing", "Mindset", "Gear")
        }

    suspend fun sources(): List<KnowledgeSource> = api.send(Endpoint("GET", "/api/rag/sources"))

    suspend fun addLink(url: String) {
        api.element(Endpoint("POST", "/api/rag/link", buildJsonObject { put("url", url) }))
    }

    companion object {
        fun curatedCards(lang: String, topic: String? = null): List<KnowledgeCard> =
            CuratedKnowledge.cards(lang).filter {
                topic == null || topic == "All" || it.topic.equals(topic, true)
            }
    }
}

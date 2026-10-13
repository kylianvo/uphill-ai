package ai.uphill.app.core.knowledge

import kotlinx.serialization.Serializable

@Serializable
data class KnowledgeCard(
    val id: Int,
    val chapterTitle: String,
    val summary: String,
    val keyPoints: List<String> = emptyList(),
    val tags: List<String> = emptyList(),
    val topic: String = "Training",
    val sourceLabel: String? = null,
)

@Serializable data class KnowledgeCardsResponse(val cards: List<KnowledgeCard> = emptyList())

@Serializable
data class KnowledgeSource(
    val id: Int,
    val title: String,
    val type: String,
    val url: String? = null,
)

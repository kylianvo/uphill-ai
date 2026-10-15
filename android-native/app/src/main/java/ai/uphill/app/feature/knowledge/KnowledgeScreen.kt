package ai.uphill.app.feature.knowledge

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.knowledge.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class KnowledgeState(
    val cards: List<KnowledgeCard> = emptyList(),
    val topics: List<String> = emptyList(),
    val sources: List<KnowledgeSource> = emptyList(),
    val busy: Boolean = false,
    val error: String? = null,
    val linkAdded: Boolean = false,
)

class KnowledgeViewModel(api: APIClient) : ViewModel() {
    private val service = KnowledgeService(api)
    private val mutable = MutableStateFlow(KnowledgeState())
    val state = mutable.asStateFlow()

    fun load(lang: String) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                coroutineScope {
                    val cards = async { service.cards(lang = lang) }
                    val topics = async { service.topics() }
                    val sources = async {
                        try {
                            service.sources()
                        } catch (e: CancellationException) {
                            throw e
                        } catch (_: Exception) {
                            emptyList()
                        }
                    }
                    mutable.value = KnowledgeState(cards.await(), topics.await(), sources.await())
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(busy = false, error = e.message) }
            }
        }
    }

    fun addLink(url: String) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null, linkAdded = false) }
            try {
                service.addLink(url)
                val sources = service.sources()
                mutable.update { it.copy(busy = false, linkAdded = true, sources = sources) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(busy = false, error = e.message) }
            }
        }
    }
}

@Composable
fun KnowledgeScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("knowledge-${user.id}") { KnowledgeViewModel(api) }
    val state by vm.state.collectAsState()
    val context = LocalContext.current
    var topic by rememberSaveable { mutableStateOf("All") }
    var search by rememberSaveable { mutableStateOf("") }
    var sources by rememberSaveable { mutableStateOf(false) }
    var dailyCardId by rememberSaveable { mutableStateOf<Int?>(null) }
    var link by rememberSaveable { mutableStateOf("") }
    LaunchedEffect(lang) { vm.load(lang) }
    LaunchedEffect(state.cards) {
        if (state.cards.none { it.id == dailyCardId }) dailyCardId = state.cards.randomOrNull()?.id
    }
    ToolPage("Knowledge Hub", onNavigate) {
        ToolField("Search knowledge", search, { search = it })
        ToolError(state.error)
        if (state.busy)
            LinearProgressIndicator(modifier = androidx.compose.ui.Modifier.fillMaxWidth())
        if (search.isEmpty() && topic == "All")
            state.cards
                .firstOrNull { it.id == dailyCardId }
                ?.let { featured ->
                    ToolPanel("Daily insight") {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                            TextButton(onClick = { dailyCardId = state.cards.randomOrNull()?.id }) {
                                Text(L("Shuffle"))
                            }
                        }
                        KnowledgeCardBody(featured)
                    }
                }
        ToolOptions("Topics", state.topics, setOf(topic)) { topic = it }
        val filtered =
            state.cards.filter {
                (topic == "All" || it.topic.equals(topic, true)) &&
                    (search.isBlank() ||
                        "${it.chapterTitle} ${it.summary} ${it.tags.joinToString()}"
                            .contains(search, true) ||
                        it.keyPoints.any { point -> point.contains(search, true) })
            }
        if (filtered.isEmpty() && !state.busy) Text(TT("No knowledge cards found."))
        filtered.forEach { card -> ToolPanel { KnowledgeCardBody(card) } }
        TextButton(onClick = { sources = !sources }) { Text(TT("Knowledge sources")) }
        if (sources) {
            ToolPanel("Knowledge sources") {
                state.sources.forEach { s ->
                    Column {
                        Text(s.title, style = MaterialTheme.typography.titleSmall)
                        Text(TT(s.type))
                        s.url?.let { url ->
                            TextButton(
                                onClick = {
                                    context.startActivity(
                                        Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                    )
                                }
                            ) {
                                Text(TT("Open source"))
                            }
                        }
                    }
                }
                ToolField("Source URL", link, { link = it })
                ToolSubmit(
                    "Add source",
                    state.busy,
                    runCatching {
                            Uri.parse(link).scheme in listOf("http", "https") &&
                                Uri.parse(link).host != null
                        }
                        .getOrDefault(false),
                ) {
                    vm.addLink(link.trim())
                }
                if (state.linkAdded) Text(TT("Source added"), color = UH.accentInk)
            }
        }
    }
}

@Composable
private fun KnowledgeCardBody(card: KnowledgeCard) {
    var expanded by rememberSaveable(card.id) { mutableStateOf(false) }
    Text(TT(card.topic), color = UH.accentInk, style = MaterialTheme.typography.labelLarge)
    Text(card.chapterTitle, style = MaterialTheme.typography.titleLarge)
    Text(card.summary)
    if (card.keyPoints.isNotEmpty()) {
        TextButton(onClick = { expanded = !expanded }) {
            Text(TT(if (expanded) "Show less" else "Key points"))
        }
        if (expanded) card.keyPoints.forEach { Text("• $it") }
    }
    if (card.tags.isNotEmpty())
        Text(
            card.tags.joinToString(" · "),
            color = UH.muted,
            style = MaterialTheme.typography.labelSmall,
        )
    card.sourceLabel?.let {
        Text(it, color = UH.secondary, style = MaterialTheme.typography.labelSmall)
    }
}

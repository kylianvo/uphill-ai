package ai.uphill.app.feature.knowledge

import ai.uphill.app.R
import androidx.compose.ui.res.stringResource
import ai.uphill.app.core.auth.User
import ai.uphill.app.core.knowledge.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.localization.localizedError
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import android.content.Intent
import android.net.Uri
import androidx.compose.animation.*
import androidx.compose.animation.core.spring
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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
    val error: Throwable? = null,
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
                mutable.update { it.copy(busy = false, error = e) }
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
                mutable.update { it.copy(busy = false, error = e) }
            }
        }
    }
}

@Composable
fun KnowledgeScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("knowledge-${user.id}") { KnowledgeViewModel(api) }
    val state by vm.state.collectAsState()
    val context = LocalContext.current
    val reduced = LocalReduceMotion.current
    var topic by rememberSaveable { mutableStateOf("All") }
    var search by rememberSaveable { mutableStateOf("") }
    var sources by rememberSaveable { mutableStateOf(false) }
    var dailyCardId by rememberSaveable { mutableStateOf<Int?>(null) }
    var link by rememberSaveable { mutableStateOf("") }
    LaunchedEffect(lang) { vm.load(lang) }
    LaunchedEffect(state.cards) {
        if (state.cards.none { it.id == dailyCardId }) dailyCardId = state.cards.randomOrNull()?.id
    }
    LaunchedEffect(state.linkAdded) { if (state.linkAdded) link = "" }
    val filtered = state.cards.filter {
        (topic == "All" || it.topic.equals(topic, true)) &&
            (search.isBlank() ||
                "${it.chapterTitle} ${it.summary} ${it.tags.joinToString()}".contains(search, true) ||
                it.keyPoints.any { point -> point.contains(search, true) })
    }
    ToolPage("Knowledge Hub", onNavigate) {
        Column(verticalArrangement = Arrangement.spacedBy(UH.Space.section)) {
            KnowledgeHeader(search, { search = it })
            if (!sources) ToolError(state.error?.let { localizedError(context, it) })
            if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (search.isEmpty() && topic == "All") {
                state.cards.firstOrNull { it.id == dailyCardId }?.let { featured ->
                    KnowledgeDaily(featured) { dailyCardId = state.cards.randomOrNull()?.id }
                }
            }
            KnowledgeTopics(state.topics, topic) { topic = it }
            Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp)) {
                Text(stringResource(R.string.knowledgeui_insights_count, filtered.size), fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp, fontWeight = FontWeight.Bold, color = UH.muted)
                Spacer(Modifier.weight(1f))
                if (topic != "All") Text(L(topic).uppercase(), fontFamily = FontFamily.Monospace,
                    fontSize = 10.sp, fontWeight = FontWeight.Bold, color = UH.accentInk)
            }
            if (filtered.isEmpty() && !state.busy) KnowledgeEmpty(search)
            if (filtered.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    filtered.forEach { card -> key(card.id) { KnowledgeCardView(card) } }
                }
            }
            ToolPanel(radius = UH.Radius.landing, modifier = Modifier.testTag("knowledge.sources.panel")) {
                Column {
                Row(
                    Modifier.fillMaxWidth().testTag("knowledge.sources.toggle")
                        .clickable { sources = !sources }.padding(vertical = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Default.FolderOpen, null, Modifier.size(18.dp), tint = UH.muted)
                    Text(L("Indexed Sources & Documentation"), Modifier.weight(1f),
                        style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold,
                        color = UH.secondary)
                    Icon(if (sources) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        null, Modifier.size(16.dp), tint = UH.muted)
                }
                AnimatedVisibility(
                    visible = sources,
                    enter = if (reduced) EnterTransition.None else expandVertically(spring(dampingRatio = 1f, stiffness = 320f)) + fadeIn(spring(dampingRatio = 1f, stiffness = 320f)),
                    exit = if (reduced) ExitTransition.None else shrinkVertically(spring(dampingRatio = 1f, stiffness = 320f)) + fadeOut(spring(dampingRatio = 1f, stiffness = 320f)),
                ) {
                    Column(Modifier.padding(top = 10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    HorizontalDivider(color = UH.line)
                    if (state.sources.isEmpty() && !state.busy) Text(L("No sources available."),
                        style = MaterialTheme.typography.bodySmall, color = UH.muted)
                    state.sources.forEach { source ->
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Icon(when (source.type) {
                                "pdf" -> Icons.Default.Description
                                "youtube" -> Icons.Default.SmartDisplay
                                else -> Icons.Default.Language
                            }, null, Modifier.size(16.dp),
                                tint = if (source.type == "youtube") Color.Red else UH.accentInk)
                            Text(source.title, Modifier.weight(1f), maxLines = 1,
                                overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.bodySmall)
                            Text(source.type.uppercase(), fontFamily = FontFamily.Monospace,
                                fontSize = 9.sp, fontWeight = FontWeight.Bold, color = UH.muted)
                            source.url?.let { url ->
                                IconButton(onClick = { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }) {
                                    Icon(Icons.Default.OpenInNew, TT("Open source"), Modifier.size(16.dp))
                                }
                            }
                        }
                    }
                    if (user.role == "admin") {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        OutlinedTextField(link, { link = it }, Modifier.weight(1f).testTag("knowledge.source.url"),
                            placeholder = { Text(L("Add link: https://uphillathlete.com/..."), maxLines = 1, overflow = TextOverflow.Ellipsis) },
                            singleLine = true, textStyle = MaterialTheme.typography.bodySmall,
                            shape = RoundedCornerShape(UH.Radius.control),
                            colors = OutlinedTextFieldDefaults.colors(unfocusedContainerColor = UH.surface))
                        val valid = runCatching { Uri.parse(link.trim()).let {
                            it.scheme in listOf("http", "https") && it.host != null
                        } }.getOrDefault(false)
                        Button(onClick = { vm.addLink(link.trim()) }, enabled = valid && !state.busy,
                            modifier = Modifier.testTag("knowledge.source.submit"),
                            shape = RoundedCornerShape(UH.Radius.control),
                            colors = ButtonDefaults.buttonColors(containerColor = UH.ink, contentColor = Color.White)) {
                            Text(if (state.busy) "..." else L("Ingest"), style = MaterialTheme.typography.bodySmall,
                                fontWeight = FontWeight.Bold)
                        }
                    }
                    ToolError(state.error?.let { localizedError(context, it) })
                    if (state.linkAdded) Text(L("Source added to indexing queue"),
                        style = MaterialTheme.typography.bodySmall, color = UH.accentInk)
                    }
                    }
                }
                }
            }
        }
    }
}

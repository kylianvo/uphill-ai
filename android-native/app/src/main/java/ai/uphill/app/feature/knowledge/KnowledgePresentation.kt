package ai.uphill.app.feature.knowledge

import ai.uphill.app.core.knowledge.KnowledgeCard
import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.*
import androidx.compose.animation.*
import androidx.compose.animation.core.spring
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.outlined.Book
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

@Composable
internal fun KnowledgeHeader(search: String, onSearch: (String) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(L("SCIENCE & PRACTICE"), fontFamily = FontFamily.Monospace, fontSize = 11.sp,
                fontWeight = FontWeight.Bold, letterSpacing = .8.sp, color = UH.accentInk)
            Text(L("Mountain Running Library"), style = MaterialTheme.typography.titleLarge)
            Text(L("Curated endurance physiology, gut training protocol, uphill biomechanics, and mental models from verified sport science."),
                style = MaterialTheme.typography.bodySmall, color = UH.secondary)
        }
        val hint = L("Search topics, keywords or #tags...")
        val clear = L("Clear search")
        val shape = RoundedCornerShape(UH.Radius.control)
        BasicTextField(search, onSearch,
            modifier = Modifier.fillMaxWidth().testTag("knowledge.search").heightIn(min = 48.dp)
                .border(1.dp, UH.line, shape).background(UH.surface, shape).padding(10.dp),
            singleLine = true, textStyle = MaterialTheme.typography.bodyLarge.copy(color = UH.ink),
            cursorBrush = SolidColor(UH.accentInk),
            decorationBox = { input ->
                Row(Modifier.heightIn(min = 28.dp), verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.Search, null, Modifier.size(18.dp), tint = UH.muted)
                    Box(Modifier.weight(1f)) {
                        if (search.isEmpty()) Text(hint, style = MaterialTheme.typography.bodyLarge, color = UH.muted,
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                        input()
                    }
                    if (search.isNotEmpty()) IconButton(onClick = { onSearch("") }, Modifier.size(28.dp)) {
                        Icon(Icons.Default.Cancel, clear, Modifier.size(18.dp), tint = UH.muted)
                    }
                }
            })
    }
}

@Composable
internal fun KnowledgeDaily(card: KnowledgeCard, shuffle: () -> Unit) {
    val haptic = LocalHapticFeedback.current
    Surface(shape = RoundedCornerShape(UH.Radius.panel), color = Color.Transparent,
        border = BorderStroke(1.dp, UH.accentInk.copy(alpha = .3f))) {
        Column(Modifier.background(Brush.linearGradient(listOf(UH.accentInk.copy(alpha = .08f), UH.surface)))
            .padding(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Icon(Icons.Default.Lightbulb, null, Modifier.size(18.dp), tint = UH.accentInk)
                Text(L("DAILY INSIGHT"), Modifier.weight(1f), fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp, fontWeight = FontWeight.Bold, color = UH.accentInk)
                Row(Modifier.border(1.dp, UH.line, RoundedCornerShape(50)).background(UH.surface, RoundedCornerShape(50)).clip(RoundedCornerShape(50))
                    .clickable(role = Role.Button) {
                        haptic.performHapticFeedback(HapticFeedbackType.SegmentTick)
                        shuffle()
                    }.padding(horizontal = 10.dp, vertical = 6.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Shuffle, null, Modifier.size(14.dp))
                    Text(L("Shuffle"), fontFamily = FontFamily.Monospace, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
            }
            KnowledgeCardView(card)
        }
    }
}

@Composable
internal fun KnowledgeTopics(topics: List<String>, selectedTopic: String, onTopic: (String) -> Unit) {
    val haptic = LocalHapticFeedback.current
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        topics.forEach { topic ->
            val active = topic.equals(selectedTopic, true)
            val shape = RoundedCornerShape(50)
            Row(Modifier.testTag("knowledge.topic.$topic").semantics { selected = active }
                .border(1.dp, if (active) UH.ink else UH.line, shape)
                .background(if (active) UH.ink else UH.surface, shape).clip(shape)
                .clickable(role = Role.Button) {
                    haptic.performHapticFeedback(HapticFeedbackType.SegmentTick)
                    onTopic(topic)
                }.padding(horizontal = 12.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(5.dp), verticalAlignment = Alignment.CenterVertically) {
                val color = if (active) Color.White else UH.ink
                if (topic != "All") Icon(knowledgeTopicIcon(topic), null, Modifier.size(14.dp), tint = color)
                Text(L(topic), style = MaterialTheme.typography.bodySmall,
                    fontWeight = if (active) FontWeight.Bold else FontWeight.Medium, color = color)
            }
        }
    }
}

@Composable
internal fun KnowledgeCardView(card: KnowledgeCard) {
    var expanded by rememberSaveable(card.id) { mutableStateOf(false) }
    val reduced = LocalReduceMotion.current
    val color = when (card.topic.lowercase(Locale.ROOT)) {
        "training" -> Color(.23f, .51f, .96f)
        "nutrition" -> Color(.06f, .72f, .51f)
        "recovery" -> Color(.55f, .36f, .96f)
        "pacing" -> Color(.96f, .62f, .04f)
        "mindset" -> Color(.93f, .28f, .60f)
        "gear" -> Color(.08f, .72f, .65f)
        else -> UH.accentInk
    }
    Surface(onClick = { expanded = !expanded }, Modifier.fillMaxWidth().testTag("knowledge.card.${card.id}"),
        shape = RoundedCornerShape(UH.Radius.landing), color = Color.White, border = BorderStroke(1.dp, UH.line)) {
        Column(Modifier.padding(16.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Row(Modifier.background(color.copy(alpha = .12f), RoundedCornerShape(50)).padding(horizontal = 8.dp, vertical = 3.dp),
                    horizontalArrangement = Arrangement.spacedBy(5.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(knowledgeTopicIcon(card.topic), null, Modifier.size(12.dp), tint = color)
                    Text(L(card.topic).uppercase(), fontFamily = FontFamily.Monospace, fontSize = 10.sp,
                        fontWeight = FontWeight.Bold, letterSpacing = .5.sp, color = color)
                }
                Spacer(Modifier.weight(1f))
                Icon(if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                    null, Modifier.size(16.dp), tint = UH.muted)
            }
            Text(card.chapterTitle, style = MaterialTheme.typography.titleLarge)
            Text(card.summary, style = MaterialTheme.typography.bodySmall, color = UH.secondary)
            }
            AnimatedVisibility(
                visible = expanded && (card.keyPoints.isNotEmpty() || card.tags.isNotEmpty()),
                enter = if (reduced) EnterTransition.None else expandVertically(spring(dampingRatio = .8f, stiffness = 440f)) + fadeIn(spring(dampingRatio = .8f, stiffness = 440f)),
                exit = if (reduced) ExitTransition.None else shrinkVertically(spring(dampingRatio = .8f, stiffness = 440f)) + fadeOut(spring(dampingRatio = .8f, stiffness = 440f)),
            ) {
                Column(Modifier.padding(top = 16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            if (card.keyPoints.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    card.keyPoints.forEach { point ->
                        Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                            Box(Modifier.padding(top = 6.dp).size(4.dp).background(color, RoundedCornerShape(50)))
                            Text(point, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
            if (card.tags.isNotEmpty()) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(5.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    card.tags.forEach { tag ->
                        Text("#$tag", Modifier.border(1.dp, UH.line, RoundedCornerShape(50))
                            .background(UH.surface, RoundedCornerShape(50)).padding(horizontal = 6.dp, vertical = 2.dp),
                            fontFamily = FontFamily.Monospace, fontSize = 10.sp, fontWeight = FontWeight.Medium, color = UH.muted)
                    }
                }
            }
                }
            }
        }
    }
}

@Composable
internal fun KnowledgeEmpty(query: String) {
    ToolPanel(radius = UH.Radius.landing, modifier = Modifier.testTag("knowledge.empty")) {
        Column(Modifier.fillMaxWidth().padding(vertical = 20.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Icon(Icons.Outlined.Book, null, Modifier.size(32.dp), tint = UH.muted)
            Text(L("No cards matching \"%@\"", query), style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium)
            Text(L("Try searching for terms like aerobic, carbs, sodium, sleep, or poles."),
                style = MaterialTheme.typography.bodySmall, color = UH.secondary,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        }
    }
}

private fun knowledgeTopicIcon(topic: String): ImageVector = when (topic.lowercase(Locale.ROOT)) {
    "training" -> Icons.Default.Landscape
    "nutrition" -> Icons.Default.Restaurant
    "recovery" -> Icons.Default.KingBed
    "pacing" -> Icons.Default.Timer
    "mindset" -> Icons.Default.Psychology
    "gear" -> Icons.Default.Backpack
    else -> Icons.Default.Book
}

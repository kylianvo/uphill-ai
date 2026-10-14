package ai.uphill.app.feature.plan

import ai.uphill.app.core.localization.L
import ai.uphill.app.core.models.*
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.DirectionsRun
import androidx.compose.material.icons.automirrored.filled.DirectionsWalk
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.time.format.DateTimeFormatter

@Composable
internal fun WorkoutDetailBody(workout: Workout, snapshot: PlanSnapshot?, onClose: () -> Unit) {
    var treadmill by remember(workout.id) { mutableStateOf(false) }
    val content = remember(workout, treadmill) { WorkoutDetailContent.make(workout, treadmill) }
    val zoneColor =
        when {
            workout.isStrengthOrME -> Color(0xFF8B5CF6)
            workout.targetZone.contains('5') -> Color(0xFFEF4444)
            workout.targetZone.contains('4') -> Color(0xFFF43F5E)
            workout.targetZone.contains('3') -> Color(0xFFF59E0B)
            else -> Color(0xFF3B82F6)
        }
    TextButton(onClick = onClose) { Text(L("Done")) }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Surface(
            color = zoneColor.copy(alpha = .12f),
            shape = RoundedCornerShape(20.dp),
            border = BorderStroke(1.dp, zoneColor.copy(alpha = .3f)),
        ) {
            Text(
                P(workout.type),
                Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                color = zoneColor,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
            )
        }
        if (workout.isPriority)
            Text(
                L("PRIORITY"),
                Modifier.background(UH.activeFill, RoundedCornerShape(12.dp))
                    .padding(horizontal = 8.dp, vertical = 3.dp),
                color = UH.accentInk,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
            )
    }
    Text(workout.title, fontSize = 24.sp, fontWeight = FontWeight.Bold, color = UH.ink)
    val locale = LocalConfiguration.current.locales[0]
    val date =
        snapshot?.let {
            PlanCalendar.date(workout.weekNumber, workout.weekday, it.plan, it.workouts)
        }
    val subtitle =
        date?.format(DateTimeFormatter.ofPattern("EEEE, d MMMM", locale)) ?: P(workout.dayOfWeek)
    Text(
        "$subtitle · ${L("%@ Phase", P(workout.phase))}",
        color = UH.secondary,
        style = MaterialTheme.typography.bodySmall,
    )
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        DetailMetric(L("DURATION"), "${workout.durationMinutes.toInt()} min", Modifier.weight(1f))
        DetailMetric(
            L("EST. DISTANCE"),
            if (workout.isStrengthOrME) "—"
            else
                workout.distanceKm?.takeIf { it > 0 }?.let { String.format(locale, "%.1f km", it) }
                    ?: "—",
            Modifier.weight(1f),
        )
        DetailMetric(
            L("PACE (/KM)"),
            if (workout.isStrengthOrME) "—"
            else workout.targetPace?.takeIf(String::isNotBlank) ?: "—",
            Modifier.weight(1f),
        )
    }
    val effort =
        listOfNotNull(
                workout.targetHrRange?.takeIf(String::isNotBlank)?.let { "HR $it" },
                workout.targetZone.takeIf(String::isNotBlank),
                workout.elevationGainM
                    ?.takeIf { it > 0 }
                    ?.let { "+${it.toInt()} m ${L("elevation gain")}" },
            )
            .joinToString(" · ")
    if (effort.isNotEmpty())
        Text(effort, color = UH.muted, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        DetailLabel(L("HOW TO EXECUTE"), Modifier.weight(1f))
        FilterChip(
            selected = treadmill,
            onClick = { treadmill = !treadmill },
            label = { Text(L("Treadmill"), fontSize = 11.sp) },
            leadingIcon = {
                Icon(Icons.AutoMirrored.Filled.DirectionsRun, null, Modifier.size(14.dp))
            },
            modifier = Modifier.testTag("detail.treadmill"),
        )
    }
    OutlinedCard(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, UH.line),
    ) {
        Column(Modifier.fillMaxWidth().padding(16.dp)) {
            content.steps.forEachIndexed { index, step ->
                val color = if (step.phase == "Main Set") zoneColor else UH.muted
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(
                            Modifier.size(24.dp).background(color.copy(alpha = .15f), CircleShape),
                            contentAlignment = Alignment.Center,
                        ) {
                            Icon(
                                when (step.phase) {
                                    "Warm-up" -> Icons.Default.ArrowUpward
                                    "Main Set" -> Icons.Default.PlayArrow
                                    else -> Icons.Default.Air
                                },
                                null,
                                Modifier.size(14.dp),
                                tint = color,
                            )
                        }
                        if (index != content.steps.lastIndex)
                            Box(
                                Modifier.padding(vertical = 2.dp)
                                    .width(2.dp)
                                    .height(52.dp)
                                    .background(UH.line)
                            )
                    }
                    Column(
                        Modifier.weight(1f)
                            .padding(
                                bottom = if (index == content.steps.lastIndex) 0.dp else 16.dp
                            ),
                        verticalArrangement = Arrangement.spacedBy(3.dp),
                    ) {
                        Text(
                            L(step.phase).uppercase(locale) +
                                (step.duration?.let { " · $it" } ?: ""),
                            color = color,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            stepText(step.target),
                            color = UH.ink,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        step.recovery?.let {
                            Text(stepText(it), color = UH.secondary, fontSize = 12.sp)
                        }
                        step.steps
                            .filter { it != step.target && it != step.recovery }
                            .forEach { Text(stepText(it), color = UH.secondary, fontSize = 12.sp) }
                    }
                }
            }
        }
    }
    workout.fuelingTip?.takeIf(String::isNotBlank)?.let { tip ->
        Surface(
            color = UH.accent.copy(alpha = .08f),
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, UH.accent.copy(alpha = .3f)),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                DetailLabel(L("NUTRITION & FUELING"), color = UH.accentInk)
                Text(tip, fontSize = 13.sp)
            }
        }
    }
    val overall = content.intent ?: content.overview
    if (overall != null || content.reason != null || content.benefit != null)
        OutlinedCard(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
            border = BorderStroke(1.dp, UH.line),
            modifier = Modifier.testTag("detail.aboutSession"),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                DetailLabel(L("ABOUT THIS SESSION"), color = UH.accentInk)
                overall?.let { Text(it, fontSize = 14.sp, fontWeight = FontWeight.Medium) }
                content.reason?.let {
                    Text("${L("Why:")} $it", color = UH.secondary, fontSize = 13.sp)
                }
                content.benefit?.let { Text("${L("Benefit:")} $it", fontSize = 13.sp) }
            }
        }
    content.warning?.let { warning ->
        Surface(
            color = UH.warningFill,
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, UH.warningInk.copy(alpha = .3f)),
        ) {
            Row(
                Modifier.fillMaxWidth().padding(12.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Icon(
                    Icons.Default.Warning,
                    null,
                    tint = UH.warningInk,
                    modifier = Modifier.size(18.dp),
                )
                Column {
                    DetailLabel(L("COMMON MISTAKE"), color = UH.warningInk)
                    Text(warning, fontSize = 13.sp)
                }
            }
        }
    }
    content.coachNotes?.let { quote ->
        OutlinedCard(
            shape = RoundedCornerShape(8.dp),
            colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
            border = BorderStroke(1.dp, UH.line),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text("“$quote”", fontSize = 14.sp)
                DetailLabel("– Coach Uphill", color = UH.accentInk)
            }
        }
    }
    if (workout.isMatched)
        OutlinedCard(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
            border = BorderStroke(1.dp, UH.line),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(
                        if (workout.matchedFromAppleHealth) Icons.Default.Favorite
                        else Icons.Default.Watch,
                        null,
                        tint = if (workout.matchedFromAppleHealth) UH.healthPink else UH.accentInk,
                    )
                    Text(workout.matchedSourceName, fontWeight = FontWeight.SemiBold)
                }
                Text(
                    "${workout.matchedDistanceKm ?: 0} km · ${((workout.matchedDurationSeconds ?: 0.0) / 60).toInt()} min · ${workout.matchedAvgHr ?: 0} bpm",
                    color = UH.secondary,
                )
            }
        }
}

@Composable
private fun RowScope.DetailMetric(label: String, value: String, modifier: Modifier) {
    Surface(
        modifier,
        color = Color.White,
        shape = RoundedCornerShape(8.dp),
        border = BorderStroke(1.dp, UH.line),
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            DetailLabel(label)
            Text(
                value,
                fontFamily = FontFamily.Monospace,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                color = UH.ink,
            )
        }
    }
}

@Composable
private fun DetailLabel(text: String, modifier: Modifier = Modifier, color: Color = UH.muted) {
    Text(
        text,
        modifier,
        fontFamily = FontFamily.Monospace,
        fontSize = 10.sp,
        fontWeight = FontWeight.Bold,
        color = color,
    )
}

@Composable
private fun stepText(text: String): String =
    when {
        text.startsWith("Target pace: ") ->
            L("Target pace:") + " " + text.removePrefix("Target pace: ")
        text.startsWith("Recovery: ") -> L("Recovery") + ": " + L(text.removePrefix("Recovery: "))
        else -> L(text)
    }

@Composable
internal fun WorkoutFeelingSelector(rpe: Int?, onChange: (Int?) -> Unit) {
    val active = WorkoutFeeling.from(rpe)
    DetailLabel(L("HOW DID IT FEEL?"))
    Row(
        Modifier.fillMaxWidth().height(IntrinsicSize.Min),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        WorkoutFeeling.entries.forEach { feeling ->
            val color =
                when (feeling) {
                    WorkoutFeeling.VeryLight -> Color(0xFF06B6D4)
                    WorkoutFeeling.Light -> Color(0xFF10B981)
                    WorkoutFeeling.Moderate -> Color(0xFF3B82F6)
                    WorkoutFeeling.Hard -> Color(0xFFF59E0B)
                    WorkoutFeeling.MaxEffort -> Color(0xFFEF4444)
                }
            Surface(
                onClick = { onChange(if (active == feeling) null else feeling.rpe) },
                modifier =
                    Modifier.weight(1f).fillMaxHeight().testTag("detail.feeling.${feeling.rpe}"),
                color = if (active == feeling) color.copy(alpha = .12f) else UH.surface,
                shape = RoundedCornerShape(8.dp),
                border = BorderStroke(1.dp, if (active == feeling) color else UH.line),
            ) {
                Column(
                    Modifier.padding(horizontal = 4.dp, vertical = 10.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Icon(
                        when (feeling) {
                            WorkoutFeeling.VeryLight -> Icons.Default.Eco
                            WorkoutFeeling.Light -> Icons.AutoMirrored.Filled.DirectionsWalk
                            WorkoutFeeling.Moderate -> Icons.AutoMirrored.Filled.DirectionsRun
                            WorkoutFeeling.Hard -> Icons.Default.Whatshot
                            WorkoutFeeling.MaxEffort -> Icons.Default.Bolt
                        },
                        null,
                        tint = color,
                        modifier = Modifier.size(20.dp),
                    )
                    Text(
                        L(feeling.label),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    )
                }
            }
        }
    }
    active?.let { feeling ->
        Surface(
            color = UH.surface,
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, UH.line),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text(L(feeling.label), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                Text(L(feeling.subtitle), color = UH.secondary, fontSize = 13.sp)
                Text(L(feeling.guidance), fontSize = 12.sp)
            }
        }
    }
}

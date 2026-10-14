package ai.uphill.app.feature.plan

import ai.uphill.app.core.coaching.CoachWorkoutAiCreatePayload
import ai.uphill.app.core.coaching.CoachWorkoutCreatePayload
import ai.uphill.app.core.coaching.CoachingService
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.models.Weekday
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.plan.P
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.SecondaryButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.UnfoldMore
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

internal data class CoachWorkoutDraft(
    val week: Int,
    val day: String = "Wednesday",
    val type: String = "Easy",
    val title: String = "",
    val zone: String = "Zone 2",
    val distance: String = "8.0",
    val duration: String = "50",
    val description: String = "",
) {
    private fun minutes(ai: Boolean): Double {
        require(week in 1..24 && Weekday.entries.any { it.name == day }) {
            "Choose a valid week and day."
        }
        val value = duration.replace(',', '.').toDoubleOrNull()
        require(value != null && value.isFinite() && value in 0.0..1440.0) {
            "Enter duration between 0 and 1,440 minutes."
        }
        require(!ai || value > 0) { "AI workout duration must be positive." }
        return value
    }

    fun manualPayload(): CoachWorkoutCreatePayload {
        val minutes = minutes(false)
        require(title.isNotBlank()) { "Enter a title." }
        val km = distance.takeIf { it.isNotBlank() }?.replace(',', '.')?.toDoubleOrNull()
        require(distance.isBlank() || (km != null && km.isFinite() && km > 0)) {
            "Enter a positive distance."
        }
        return CoachWorkoutCreatePayload(
            week,
            day,
            "Specific",
            title.trim(),
            type,
            minutes,
            zone,
            km,
            description.ifEmpty { null },
        )
    }

    fun aiPayload(intent: String? = null): CoachWorkoutAiCreatePayload =
        CoachWorkoutAiCreatePayload(
            week,
            day,
            type,
            minutes(true),
            intent?.trim()?.takeIf { it.isNotEmpty() },
        )
}

@Composable
internal fun CoachAddWorkoutSheet(
    api: APIClient,
    athleteId: Int,
    planId: Int,
    initialWeek: Int,
    onAdded: () -> Unit,
    onClose: () -> Unit,
) {
    val service = remember(api) { CoachingService(api) }
    val scope = rememberCoroutineScope()
    var draft by remember(athleteId, planId) { mutableStateOf(CoachWorkoutDraft(initialWeek)) }
    var aiPrompt by remember { mutableStateOf("") }
    var showAi by remember { mutableStateOf(false) }
    var submitting by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    fun submit(ai: Boolean) {
        if (submitting) return
        val manual =
            if (ai) null
            else
                runCatching { draft.manualPayload() }
                    .getOrElse {
                        error = it.message
                        return
                    }
        val generated =
            if (!ai) null
            else
                runCatching { draft.aiPayload(aiPrompt) }
                    .getOrElse {
                        error = it.message
                        return
                    }
        submitting = true
        error = null
        scope.launch {
            try {
                if (generated != null) service.aiCreateWorkout(athleteId, planId, generated)
                else service.addWorkout(athleteId, planId, requireNotNull(manual))
                onAdded()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                error = e.message
            } finally {
                submitting = false
            }
        }
    }
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(L("Add Workout"), Modifier.weight(1f), style = MaterialTheme.typography.titleMedium)
        TextButton(onClick = onClose, enabled = !submitting) { Text(P("Cancel")) }
        TextButton(onClick = { submit(false) }, enabled = draft.title.isNotBlank() && !submitting) {
            Text(L("Add"))
        }
    }
    Column(
        Modifier.fillMaxWidth().background(UH.surface, RoundedCornerShape(12.dp)).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                L("Coach AI Co-Creation"),
                Modifier.weight(1f),
                style = MaterialTheme.typography.titleMedium,
                color = UH.accentInk,
            )
            TextButton(onClick = { showAi = !showAi }, enabled = !submitting) {
                Text(L(if (showAi) "Manual form" else "Use AI generator"))
            }
        }
        if (showAi) {
            Text(
                L("Describe the intended session:"),
                style = MaterialTheme.typography.bodySmall,
                color = UH.secondary,
            )
            OutlinedTextField(
                aiPrompt,
                { aiPrompt = it },
                Modifier.fillMaxWidth(),
                enabled = !submitting,
                label = { Text(L("Session intent or prompt...")) },
                minLines = 3,
                maxLines = 5,
            )
            PrimaryButton(
                onClick = { submit(true) },
                modifier = Modifier.fillMaxWidth(),
                enabled = aiPrompt.isNotBlank() && !submitting,
            ) {
                Text(L("Generate & Insert Session"))
            }
        }
    }
    Text(L("Session Details"), style = MaterialTheme.typography.titleMedium)
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        CoachChoice(
            P("Week"),
            draft.week.toString(),
            (1..24).map { it.toString() },
            !submitting,
            Modifier.weight(1f),
        ) {
            draft = draft.copy(week = it.toInt())
        }
        CoachChoice(
            L("Day"),
            draft.day,
            Weekday.entries.map { it.name },
            !submitting,
            Modifier.weight(1f),
        ) {
            draft = draft.copy(day = it)
        }
    }
    CoachChoice(
        L("Workout Type"),
        draft.type,
        listOf(
            "Easy",
            "Recovery",
            "Long Run",
            "Aerobic Capacity",
            "Tempo",
            "Threshold",
            "Interval",
            "Muscular Endurance",
            "Strength",
            "Cross-Training",
        ),
        !submitting,
    ) {
        draft = draft.copy(type = it)
    }
    OutlinedTextField(
        draft.title,
        { draft = draft.copy(title = it) },
        Modifier.fillMaxWidth(),
        enabled = !submitting,
        label = { Text(L("Title")) },
        placeholder = { Text(L("e.g. Aerobic Base Run + Strides")) },
    )
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedTextField(
            draft.distance,
            { draft = draft.copy(distance = it) },
            Modifier.weight(1f),
            enabled = !submitting,
            label = { Text(L("Distance (km)")) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        )
        OutlinedTextField(
            draft.duration,
            { draft = draft.copy(duration = it) },
            Modifier.weight(1f),
            enabled = !submitting,
            label = { Text(L("Duration (min)")) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        )
    }
    CoachChoice(
        L("Target Intensity Zone"),
        draft.zone,
        listOf("Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Rest"),
        !submitting,
    ) {
        draft = draft.copy(zone = it)
    }
    OutlinedTextField(
        draft.description,
        { draft = draft.copy(description = it) },
        Modifier.fillMaxWidth(),
        enabled = !submitting,
        label = { Text(L("Instructions / Execution Description")) },
        placeholder = { Text(L("Warm up 10 min easy, then...")) },
        minLines = 3,
        maxLines = 6,
    )
    if (submitting) LinearProgressIndicator(Modifier.fillMaxWidth())
    error?.let { Text(P(it), color = UH.danger, style = MaterialTheme.typography.bodySmall) }
}

@Composable
internal fun CoachChoice(
    label: String,
    value: String,
    choices: List<String>,
    enabled: Boolean,
    modifier: Modifier = Modifier.fillMaxWidth(),
    onChange: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Column(modifier) {
        Text(label, style = MaterialTheme.typography.bodySmall, color = UH.secondary)
        Box {
            SecondaryButton(
                onClick = { expanded = true },
                enabled = enabled,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(P(value), Modifier.weight(1f))
                Icon(Icons.Default.UnfoldMore, null)
            }
            DropdownMenu(expanded, { expanded = false }) {
                choices.forEach { choice ->
                    DropdownMenuItem(
                        text = { Text(P(choice)) },
                        onClick = {
                            expanded = false
                            onChange(choice)
                        },
                    )
                }
            }
        }
    }
}

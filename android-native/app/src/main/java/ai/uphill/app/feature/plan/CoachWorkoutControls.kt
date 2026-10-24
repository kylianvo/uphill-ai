package ai.uphill.app.feature.plan

import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.models.Workout
import ai.uphill.app.core.plan.P
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.SecondaryButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

internal data class CoachEditWorkoutDraft(
    val title: String,
    val type: String,
    val zone: String,
    val distance: String,
    val duration: String,
    val description: String,
) {
    fun payload(): CoachWorkoutUpdatePayload {
        require(title.isNotBlank()) { "Enter a title." }
        val minutes = duration.replace(',', '.').toDoubleOrNull()
        require(minutes != null && minutes.isFinite() && minutes in 0.0..1440.0) {
            "Enter duration between 0 and 1,440 minutes."
        }
        val km = distance.takeIf { it.isNotBlank() }?.replace(',', '.')?.toDoubleOrNull()
        require(distance.isBlank() || (km != null && km.isFinite() && km > 0)) {
            "Enter a positive distance."
        }
        return CoachWorkoutUpdatePayload(
            title.trim(),
            type,
            minutes,
            km,
            zone,
            description.ifEmpty { null },
        )
    }

    companion object {
        fun from(workout: Workout) =
            CoachEditWorkoutDraft(
                workout.title,
                workout.type,
                workout.targetZone,
                workout.distanceKm?.toString().orEmpty(),
                workout.durationMinutes.toString(),
                workout.description.orEmpty(),
            )
    }
}

@Composable
internal fun CoachWorkoutControls(model: PlanViewModel, workout: Workout, onClose: () -> Unit) {
    val athlete = model.athleteId ?: return
    val service = remember(model.api) { CoachingService(model.api) }
    val scope = rememberCoroutineScope()
    var busy by remember(workout.id) { mutableStateOf(false) }
    var error by remember(workout.id) { mutableStateOf<String?>(null) }
    var editing by remember(workout.id) { mutableStateOf(false) }
    var removing by remember(workout.id) { mutableStateOf(false) }
    fun action(close: Boolean = false, block: suspend () -> Unit) {
        if (busy) return
        busy = true
        error = null
        scope.launch {
            try {
                block()
                model.refresh()
                if (close) onClose()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                error = e.message
            } finally {
                busy = false
            }
        }
    }
    if (editing) {
        var draft by remember(workout.id) { mutableStateOf(CoachEditWorkoutDraft.from(workout)) }
        Text(L("Edit Workout"), style = MaterialTheme.typography.titleLarge)
        CoachChoice(L("Workout Type"), draft.type, coachWorkoutTypes, !busy) {
            draft = draft.copy(type = it)
        }
        OutlinedTextField(
            draft.title,
            { draft = draft.copy(title = it) },
            Modifier.fillMaxWidth().testTag("coach.edit.title"),
            enabled = !busy,
            label = { Text(L("Title")) },
        )
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(
                draft.distance,
                { draft = draft.copy(distance = it) },
                Modifier.weight(1f),
                enabled = !busy,
                label = { Text(L("Distance (km)")) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            )
            OutlinedTextField(
                draft.duration,
                { draft = draft.copy(duration = it) },
                Modifier.weight(1f),
                enabled = !busy,
                label = { Text(L("Duration (min)")) },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            )
        }
        CoachChoice(
            L("Target Intensity Zone"),
            draft.zone,
            listOf("Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Rest"),
            !busy,
        ) {
            draft = draft.copy(zone = it)
        }
        OutlinedTextField(
            draft.description,
            { draft = draft.copy(description = it) },
            Modifier.fillMaxWidth(),
            enabled = !busy,
            label = { Text(L("Description & Execution Steps")) },
            minLines = 4,
            maxLines = 8,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            SecondaryButton(
                onClick = {
                    editing = false
                    error = null
                },
                enabled = !busy,
            ) {
                Text(P("Cancel"))
            }
            PrimaryButton(
                onClick = {
                    val payload =
                        runCatching { draft.payload() }
                            .getOrElse {
                                error = it.message
                                return@PrimaryButton
                            }
                    action {
                        service.editWorkout(athlete, workout.planId, workout.id, payload)
                        editing = false
                    }
                },
                enabled = !busy && draft.title.isNotBlank(),
                modifier = Modifier.testTag("coach.edit.save"),
            ) {
                Text(L("Save"))
            }
        }
    } else {
        if (workout.approvedAt == null) {
            PrimaryButton(
                onClick = { action { service.approve(athlete, workout.planId, workout.id) } },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth().testTag("detail.coach.approveWorkout"),
                colors =
                    ButtonDefaults.buttonColors(
                        containerColor = UH.accentInk,
                        contentColor = Color.White,
                    ),
            ) {
                Text(L("Approve Workout"))
            }
            Text(
                L("This session was created for the athlete and is awaiting your review."),
                style = MaterialTheme.typography.bodySmall,
                color = UH.secondary,
            )
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            SecondaryButton(
                onClick = { editing = true },
                enabled = !busy,
                modifier = Modifier.testTag("detail.coach.editWorkout"),
            ) {
                Text(L("Edit Workout"))
            }
            TextButton(
                onClick = { removing = true },
                enabled = !busy,
                modifier = Modifier.testTag("detail.coach.removeWorkout"),
            ) {
                Text(L("Remove Workout"), color = UH.danger)
            }
        }
    }
    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    error?.let { Text(P(it), color = UH.danger) }
    if (removing)
        AlertDialog(
            onDismissRequest = { if (!busy) removing = false },
            title = { Text(L("Remove Workout")) },
            text = {
                Text(
                    L(
                        "This will permanently remove the workout from the runner's training schedule."
                    )
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        action(close = true) {
                            service.removeWorkout(athlete, workout.planId, workout.id)
                        }
                    },
                    enabled = !busy,
                    modifier = Modifier.testTag("coach.remove.confirm"),
                ) {
                    Text(L("Remove"), color = UH.danger)
                }
            },
            dismissButton = {
                TextButton(onClick = { removing = false }, enabled = !busy) { Text(P("Cancel")) }
            },
        )
}

internal val coachWorkoutTypes =
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
    )

@Composable
internal fun WorkoutCoachNotes(
    service: CoachingService,
    athleteId: Int,
    workoutId: Int,
    coach: Boolean,
) {
    val scope = rememberCoroutineScope()
    val locale = LocalConfiguration.current.locales[0]
    var notes by remember(athleteId, workoutId) { mutableStateOf<List<CoachNote>>(emptyList()) }
    var loading by remember(athleteId, workoutId) { mutableStateOf(true) }
    var posting by remember(athleteId, workoutId) { mutableStateOf(false) }
    var error by remember(athleteId, workoutId) { mutableStateOf<String?>(null) }
    var draft by remember(athleteId, workoutId) { mutableStateOf("") }
    var expanded by remember(athleteId, workoutId) { mutableStateOf(true) }
    suspend fun load() {
        loading = true
        error = null
        try {
            notes = service.notes(athleteId, "workout", workoutId)
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            error = e.message
        } finally {
            loading = false
        }
    }
    LaunchedEffect(service, athleteId, workoutId) { load() }
    if (!coach && notes.none { it.coachId != athleteId }) return
    Column(
        Modifier.fillMaxWidth()
            .background(UH.surface, RoundedCornerShape(12.dp))
            .padding(16.dp)
            .testTag("detail.coachNotesThread"),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        TextButton(onClick = { expanded = !expanded }, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Default.Forum, null, Modifier.size(16.dp), tint = UH.accent)
            Spacer(Modifier.width(8.dp))
            Text(
                if (coach) L("Coach Notes (%lld)", notes.size) else L("Notes from your coach"),
                Modifier.weight(1f),
                color = UH.ink,
            )
            Icon(
                if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                null,
                Modifier.size(16.dp),
                tint = UH.secondary,
            )
        }
        if (expanded) {
            if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
            else if (notes.isEmpty())
                Text(
                    L("No coach notes yet. Leave training feedback or execution advice here."),
                    color = UH.muted,
                    style = MaterialTheme.typography.bodySmall,
                )
            notes.forEach { note ->
                Column(
                    Modifier.fillMaxWidth()
                        .background(UH.hover, RoundedCornerShape(8.dp))
                        .padding(10.dp),
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    if (!coach)
                        Text(
                            if (note.coachId == athleteId) L("You") else "Coach",
                            color = UH.muted,
                            style = MaterialTheme.typography.labelSmall,
                        )
                    Text(note.note)
                    note.createdAt?.let { raw ->
                        runCatching {
                                OffsetDateTime.parse(raw)
                                    .atZoneSameInstant(ZoneId.systemDefault())
                                    .format(
                                        DateTimeFormatter.ofLocalizedDateTime(FormatStyle.SHORT)
                                            .withLocale(locale)
                                    )
                            }
                            .getOrNull()
                            ?.let {
                                Text(
                                    it,
                                    color = UH.muted,
                                    style = MaterialTheme.typography.labelSmall,
                                )
                            }
                    }
                }
            }
            error?.let {
                Text(P(it), color = UH.danger)
                TextButton(onClick = { scope.launch { load() } }, enabled = !loading && !posting) {
                    Text(P("Retry"))
                }
            }
            OutlinedTextField(
                draft,
                { draft = it },
                Modifier.fillMaxWidth().testTag("coach.note.input"),
                enabled = !posting,
                label = {
                    Text(
                        if (coach) L("Add a note for this %@...", L("workout"))
                        else L("Reply to your coach…")
                    )
                },
                maxLines = 4,
            )
            PrimaryButton(
                onClick = {
                    if (posting || draft.isBlank()) return@PrimaryButton
                    posting = true
                    error = null
                    val text = draft.trim()
                    scope.launch {
                        try {
                            val created =
                                service.addNote(
                                    athleteId,
                                    CoachNoteCreatePayload("workout", text, workoutId),
                                )
                            notes = listOf(created) + notes
                            draft = ""
                        } catch (e: CancellationException) {
                            throw e
                        } catch (e: Exception) {
                            error = e.message
                        } finally {
                            posting = false
                        }
                    }
                },
                enabled = !posting && draft.isNotBlank(),
                modifier = Modifier.testTag("coach.note.post"),
            ) {
                Text(L(if (coach) "Post" else "Reply"))
            }
        }
    }
}

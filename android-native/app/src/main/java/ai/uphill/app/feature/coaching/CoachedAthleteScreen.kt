package ai.uphill.app.feature.coaching

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.racehistory.*
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.*

private val weekdays =
    listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
private val workoutTypes =
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
fun CoachedAthleteScreen(
    api: APIClient,
    user: User,
    lang: String,
    onNavigate: (String) -> Unit,
    athleteId: Int,
) {
    val service = remember(api) { CoachingService(api) }
    val races = remember(api) { RaceHistoryService(api) }
    val vm: CoachedAthleteViewModel =
        viewModel(key = "athlete-$athleteId") { CoachedAthleteViewModel(service, athleteId) }
    val state by vm.state.collectAsState()
    var editPhysiology by remember { mutableStateOf(false) }
    var useDraft by remember { mutableStateOf(false) }
    var week by remember { mutableIntStateOf(1) }
    var editWorkout by remember { mutableStateOf<CoachWorkout?>(null) }
    var addWorkout by remember { mutableStateOf(false) }
    var removing by remember { mutableStateOf<CoachWorkout?>(null) }
    var noteTarget by remember { mutableStateOf<Pair<String, Int?>?>(null) }
    var raceHistory by remember { mutableStateOf<RaceHistoryResponse?>(null) }
    var raceError by remember { mutableStateOf<String?>(null) }
    var raceDetail by remember { mutableStateOf<Int?>(null) }
    LaunchedEffect(vm) {
        vm.load()
        try {
            raceHistory = races.athleteHistory(athleteId)
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            raceError = e.message
        }
    }
    val snapshot = if (useDraft) state.draft else state.active
    LaunchedEffect(snapshot?.plan?.id) { week = snapshot?.plan?.currentWeek ?: 1 }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(state.profile?.name ?: P6("athlete"), style = MaterialTheme.typography.headlineMedium)
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.error?.let {
            Text(P6Error(it), color = UH.danger)
            TextButton(onClick = vm::load) { Text(P6("retry")) }
        }
        state.profile?.let { profile ->
            P6Card {
                Text(profile.email, color = UH.secondary)
                Text(
                    listOfNotNull(
                            profile.gender,
                            profile.age?.let { "$it" },
                            profile.currentWeeklyKm?.let { "$it km/week" },
                        )
                        .joinToString(" · ")
                )
                Row {
                    Text(
                        P6("physiology"),
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.weight(1f),
                    )
                    TextButton(
                        onClick = { editPhysiology = true },
                        enabled = !state.busy && user.isCoach,
                    ) {
                        Text(P6("edit"))
                    }
                }
                val fields =
                    listOf(
                        "resting_hr" to profile.restingHr?.toString(),
                        "aet_hr" to profile.aetHr?.toString(),
                        "ant_hr" to profile.antHr?.toString(),
                        "max_hr" to profile.maxHr?.toString(),
                        "zone2_pace_min" to profile.zone2PaceMin,
                        "zone2_pace_max" to profile.zone2PaceMax,
                        "threshold_pace" to profile.thresholdPace,
                    )
                fields.forEach { (key, value) ->
                    Text(
                        P6(key) +
                            " · " +
                            (value ?: "—") +
                            (if (key.endsWith("_hr")) " bpm" else " /km")
                    )
                    val source = profile.fieldSources?.get(key) as? JsonObject
                    source?.let {
                        val who = (it["by_name"] as? JsonPrimitive)?.contentOrNull
                        val origin = (it["source"] as? JsonPrimitive)?.contentOrNull
                        Text(
                            if (who != null) P6("set_by", who)
                            else if (origin == "athlete") P6("entered_by_athlete")
                            else P6("app_default"),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.muted,
                        )
                    }
                }
                profile.injuryHistory
                    ?.takeIf { it.isNotBlank() }
                    ?.let {
                        Text(P6("injury_history"), style = MaterialTheme.typography.titleSmall)
                        Text(it)
                    }
                profile.athleteNotes
                    ?.takeIf { it.isNotBlank() }
                    ?.let {
                        Text(P6("athlete_notes"), style = MaterialTheme.typography.titleSmall)
                        Text(it)
                    }
            }
        }
        P6Card {
            Text(P6("training_plan"), style = MaterialTheme.typography.titleLarge)
            Row {
                FilterChip(
                    selected = !useDraft,
                    onClick = { useDraft = false },
                    label = { Text(P6("active_plan")) },
                )
                Spacer(Modifier.width(8.dp))
                FilterChip(
                    selected = useDraft,
                    onClick = { useDraft = true },
                    label = { Text(P6("draft")) },
                )
            }
            if (snapshot == null) Text(P6("no_plan"))
            else {
                Text(snapshot.plan.raceName, style = MaterialTheme.typography.titleMedium)
                Text(snapshot.plan.raceDate)
                if (!useDraft)
                    TextButton(onClick = { onNavigate("athlete-plan/$athleteId") }) {
                        Text(P6("training_plan"))
                    }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    P6Choice(
                        "week",
                        week.toString(),
                        (1..snapshot.plan.totalWeeks).map { it.toString() },
                    ) {
                        week = it.toInt()
                    }
                    if (user.isCoach)
                        Button(onClick = { addWorkout = true }, enabled = !state.busy) {
                            Text(P6("add_workout"))
                        }
                }
                TextButton(onClick = { noteTarget = "plan" to snapshot.plan.id }) {
                    Text(P6("plan_notes"))
                }
            }
        }
        snapshot
            ?.workouts
            ?.filter { it.weekNumber == week }
            ?.sortedWith(
                compareBy<CoachWorkout> { weekdays.indexOf(it.dayOfWeek) }.thenBy { it.id }
            )
            ?.forEach { w ->
                P6Card {
                    Text(P6Option(w.dayOfWeek), color = UH.secondary)
                    Text(w.title, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "${w.type} · ${w.durationMinutes.toInt()} min · ${w.distanceKm ?: "—"} km · ${w.targetZone}"
                    )
                    w.targetPace?.let { Text("Pace $it") }
                    w.targetHrRange?.let { Text("HR $it") }
                    w.description?.let { Text(it) }
                    w.fuelingTip?.let { Text(it, color = UH.secondary) }
                    Text(
                        P6(if (w.approvedAt != null) "approved" else "awaiting_approval"),
                        color = UH.accentInk,
                    )
                    if (user.isCoach)
                        Row {
                            TextButton(onClick = { editWorkout = w }, enabled = !state.busy) {
                                Text(P6("edit"))
                            }
                            TextButton(
                                onClick = {
                                    vm.action { service.approve(athleteId, w.planId, w.id) }
                                },
                                enabled = !state.busy && w.approvedAt == null,
                            ) {
                                Text(P6("approve"))
                            }
                            TextButton(onClick = { removing = w }, enabled = !state.busy) {
                                Text(P6("remove"), color = UH.danger)
                            }
                        }
                    TextButton(onClick = { noteTarget = "workout" to w.id }) {
                        Text(P6("workout_notes"))
                    }
                }
            }
        if (raceHistory != null)
            P6Card {
                Text(P6("race_history"), style = MaterialTheme.typography.titleMedium)
                raceHistory!!
                    .results
                    .filter { it.selected && !it.hidden }
                    .forEach { r ->
                        TextButton(onClick = { raceDetail = r.id }) {
                            Text("${r.raceName} · ${r.duration}")
                        }
                    }
            }
        raceError?.let { Text(P6Error(it), color = UH.danger) }
        P6Card {
            Text(P6("coach_notes"), style = MaterialTheme.typography.titleMedium)
            state.notes.forEach { n ->
                Text(n.note)
                Text(
                    listOfNotNull(n.targetType, n.createdAt).joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = UH.secondary,
                )
                HorizontalDivider()
            }
            if (user.isCoach)
                OutlinedButton(
                    onClick = { noteTarget = "general" to null },
                    enabled = !state.busy,
                ) {
                    Text(P6("add_note"))
                }
        }
    }
    state.profile?.let { p ->
        if (editPhysiology)
            PhysiologyDialog(p, state.busy, state.error, { editPhysiology = false }) { patch ->
                vm.action({ editPhysiology = false }) { service.updateProfile(athleteId, patch) }
            }
    }
    if (addWorkout || editWorkout != null)
        snapshot?.let { s ->
            WorkoutDialog(
                editWorkout,
                s.plan,
                week,
                state.busy,
                state.error,
                {
                    addWorkout = false
                    editWorkout = null
                },
                onSave = { create, update, ai ->
                    val existing = editWorkout
                    vm.action({
                        addWorkout = false
                        editWorkout = null
                    }) {
                        when {
                            ai != null -> service.aiCreateWorkout(athleteId, s.plan.id, ai)
                            existing != null && update != null ->
                                service.editWorkout(athleteId, s.plan.id, existing.id, update)
                            create != null -> service.addWorkout(athleteId, s.plan.id, create)
                        }
                    }
                },
            )
        }
    removing?.let { w ->
        AlertDialog(
            onDismissRequest = { removing = null },
            title = { Text(P6("remove_workout")) },
            text = { Text(w.title) },
            confirmButton = {
                TextButton(
                    onClick = {
                        vm.action({ removing = null }) {
                            service.removeWorkout(athleteId, w.planId, w.id)
                        }
                    },
                    enabled = !state.busy,
                ) {
                    Text(P6("remove"))
                }
            },
            dismissButton = { TextButton(onClick = { removing = null }) { Text(P6("cancel")) } },
        )
    }
    noteTarget?.let { target ->
        NoteDialog(
            target,
            state.notes,
            state.busy,
            state.error,
            user.isCoach,
            { noteTarget = null },
        ) { note ->
            vm.action({ noteTarget = null }) {
                service.addNote(
                    athleteId,
                    CoachNoteCreatePayload(target.first, note, target.second),
                )
            }
        }
    }
    raceDetail?.let { RaceDetailDialog(races, it, { raceDetail = null }, athleteId) }
}

@Composable
private fun PhysiologyDialog(
    profile: User,
    busy: Boolean,
    serverError: String?,
    onDismiss: () -> Unit,
    onSave: (JsonObject) -> Unit,
) {
    val original = remember(profile) { PhysiologyDraft.from(profile) }
    var d by remember(profile) { mutableStateOf(original) }
    var error by remember { mutableStateOf<String?>(null) }
    P6Dialog("edit_zones", onDismiss) {
        (error ?: serverError)?.let { Text(P6Error(it), color = UH.danger) }
        P6Field("resting_hr", d.restingHr) { d = d.copy(restingHr = it) }
        P6Field("aet_hr", d.aetHr) { d = d.copy(aetHr = it) }
        P6Field("ant_hr", d.antHr) { d = d.copy(antHr = it) }
        P6Field("max_hr", d.maxHr) { d = d.copy(maxHr = it) }
        P6Field("zone2_pace_min", d.zone2PaceMin) { d = d.copy(zone2PaceMin = it) }
        P6Field("zone2_pace_max", d.zone2PaceMax) { d = d.copy(zone2PaceMax = it) }
        P6Field("threshold_pace", d.thresholdPace) { d = d.copy(thresholdPace = it) }
        Text(P6("zone_edit_help", profile.name), style = MaterialTheme.typography.bodySmall)
        Button(
            onClick = {
                runCatching { d.patch(original) }
                    .onSuccess { if (it.isNotEmpty()) onSave(it) }
                    .onFailure { error = it.message }
            },
            enabled = !busy && d != original,
        ) {
            Text(P6("save"))
        }
        TextButton(onClick = onDismiss, enabled = !busy) { Text(P6("cancel")) }
    }
}

@Composable
private fun WorkoutDialog(
    workout: CoachWorkout?,
    plan: CoachPlan,
    initialWeek: Int,
    busy: Boolean,
    serverError: String?,
    onDismiss: () -> Unit,
    onSave:
        (
            CoachWorkoutCreatePayload?, CoachWorkoutUpdatePayload?, CoachWorkoutAiCreatePayload?,
        ) -> Unit,
) {
    var week by remember(workout?.id) { mutableIntStateOf(workout?.weekNumber ?: initialWeek) }
    var day by remember(workout?.id) { mutableStateOf(workout?.dayOfWeek ?: "Monday") }
    var type by remember(workout?.id) { mutableStateOf(workout?.type ?: "Easy") }
    var title by remember(workout?.id) { mutableStateOf(workout?.title.orEmpty()) }
    var duration by
        remember(workout?.id) { mutableStateOf(workout?.durationMinutes?.toString() ?: "50") }
    var distance by
        remember(workout?.id) { mutableStateOf(workout?.distanceKm?.toString().orEmpty()) }
    var zone by remember(workout?.id) { mutableStateOf(workout?.targetZone ?: "Zone 2") }
    var description by remember(workout?.id) { mutableStateOf(workout?.description.orEmpty()) }
    var fueling by remember(workout?.id) { mutableStateOf(workout?.fuelingTip.orEmpty()) }
    var error by remember { mutableStateOf<String?>(null) }
    fun submit(ai: Boolean) {
        runCatching {
                val minutes = duration.toDoubleOrNull()
                require(minutes != null && minutes.isFinite() && minutes >= 0 && minutes <= 1440) {
                    "Enter duration between 0 and 1,440 minutes."
                }
                val km = distance.takeIf { it.isNotBlank() }?.replace(',', '.')?.toDoubleOrNull()
                require(ai || distance.isBlank() || (km != null && km.isFinite() && km > 0)) {
                    "Enter a positive distance."
                }
                if (ai) {
                    require(minutes!! > 0) { "AI workout duration must be positive." }
                    onSave(null, null, CoachWorkoutAiCreatePayload(week, day, type, minutes))
                } else {
                    require(title.isNotBlank()) { "Enter a title." }
                    if (workout != null)
                        onSave(
                            null,
                            CoachWorkoutUpdatePayload(
                                title.trim(),
                                type,
                                minutes,
                                km,
                                zone,
                                description,
                                fueling,
                                day,
                            ),
                            null,
                        )
                    else
                        onSave(
                            CoachWorkoutCreatePayload(
                                week,
                                day,
                                "Specific",
                                title.trim(),
                                type,
                                minutes!!,
                                zone,
                                km,
                                description.ifBlank { null },
                                fueling.ifBlank { null },
                            ),
                            null,
                            null,
                        )
                }
            }
            .onFailure { error = it.message }
    }
    P6Dialog(if (workout == null) "add_workout" else "edit_workout", onDismiss) {
        (error ?: serverError)?.let { Text(P6Error(it), color = UH.danger) }
        if (workout == null)
            P6Choice("week", week.toString(), (1..plan.totalWeeks).map { it.toString() }) {
                week = it.toInt()
            }
        P6Choice("day", day, weekdays) { day = it }
        P6Choice("workout_type", type, workoutTypes) { type = it }
        P6Field("duration", duration) { duration = it }
        if (workout == null) {
            Text(P6("ai_duration_help"), style = MaterialTheme.typography.bodySmall)
            OutlinedButton(onClick = { submit(true) }, enabled = !busy) { Text(P6("ai_create")) }
        }
        P6Field("title", title) { title = it }
        P6Field("distance", distance) { distance = it }
        P6Choice(
            "target_zone",
            zone,
            listOf("Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Rest"),
        ) {
            zone = it
        }
        P6Field("description", description) { description = it }
        P6Field("fueling", fueling) { fueling = it }
        Button(onClick = { submit(false) }, enabled = !busy && title.isNotBlank()) {
            Text(P6("save"))
        }
        TextButton(onClick = onDismiss, enabled = !busy) { Text(P6("cancel")) }
    }
}

@Composable
private fun NoteDialog(
    target: Pair<String, Int?>,
    notes: List<CoachNote>,
    busy: Boolean,
    error: String?,
    canWrite: Boolean,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
) {
    var note by remember(target) { mutableStateOf("") }
    P6Dialog("coach_notes", onDismiss) {
        notes
            .filter { it.targetType == target.first && it.targetId == target.second }
            .forEach {
                Text(it.note)
                it.createdAt?.let { Text(it, color = UH.secondary) }
                HorizontalDivider()
            }
        error?.let { Text(P6Error(it), color = UH.danger) }
        if (canWrite) {
            P6Field("note", note) { note = it }
            Button(onClick = { onSave(note.trim()) }, enabled = !busy && note.isNotBlank()) {
                Text(P6("save"))
            }
        }
        TextButton(onClick = onDismiss) { Text(P6("close")) }
    }
}

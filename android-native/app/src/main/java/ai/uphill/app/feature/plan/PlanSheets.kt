package ai.uphill.app.feature.plan

import ai.uphill.app.core.models.*
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import java.io.File
import java.time.*
import kotlinx.coroutines.launch
import kotlinx.serialization.json.*

@Composable
internal fun WorkoutDetail(
    model: PlanViewModel,
    workout: Workout,
    state: PlanState,
    onMove: () -> Unit,
    onMatch: () -> Unit,
    onClose: () -> Unit,
    currentUserId: Int,
) {
    val current = state.snapshot?.workouts?.firstOrNull { it.id == workout.id } ?: workout
    var rpe by remember(current.id) { mutableStateOf(current.rpe) }
    var notes by remember(current.id) { mutableStateOf(current.notes.orEmpty()) }
    var saved by remember(current.id) { mutableStateOf(false) }
    LaunchedEffect(rpe, notes) { saved = false }
    WorkoutDetailBody(current, state.snapshot, onClose)
    if (model.athleteId != null) {
        CoachWorkoutControls(model, current, onClose)
    } else if (current.approvedAt == null) {
        Text(
            ai.uphill.app.core.localization.L("Waiting for your coach's approval"),
            color = UH.secondary,
        )
    } else {
        WorkoutFeelingSelector(rpe) { rpe = it }
        OutlinedTextField(
            value = notes,
            onValueChange = { notes = it },
            label = {
                Text(
                    ai.uphill.app.core.localization.L("Add session notes (legs, terrain, weather)…")
                )
            },
            modifier = Modifier.fillMaxWidth(),
        )
        val enabled = state.cachedAt == null && !state.busy
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = { model.log(current, if (current.isDone) 0 else 1, 0, rpe, notes) },
                enabled = enabled,
            ) {
                Text(P(if (current.isDone) "Undo done" else "Mark done"))
            }
            OutlinedButton(
                onClick = { model.log(current, 0, if (current.isMissedFlag) 0 else 1, rpe, notes) },
                enabled = enabled,
            ) {
                Text(P(if (current.isMissedFlag) "Undo missed" else "Mark missed"))
            }
            OutlinedButton(
                onClick = { model.log(current, null, null, rpe, notes) { saved = true } },
                enabled = enabled && (rpe != current.rpe || notes != current.notes.orEmpty()),
            ) {
                Text(ai.uphill.app.core.localization.L(if (saved) "Saved" else "Save Log"))
            }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (model.canMove(current))
                OutlinedButton(onClick = onMove, enabled = enabled) { Text(P("Move / swap")) }
            OutlinedButton(onClick = onMatch, enabled = enabled) {
                Text(P(if (current.isMatched) "Change watch match" else "Link watch activity"))
            }
            current.matchedActivityId?.let { activity ->
                TextButton(onClick = { model.match(activity, null, onClose) }, enabled = enabled) {
                    Text(P("Unlink watch activity"))
                }
            }
        }
    }
    val coaching = remember(model.api) { ai.uphill.app.core.coaching.CoachingService(model.api) }
    WorkoutCoachNotes(
        coaching,
        model.athleteId ?: currentUserId,
        current.id,
        model.athleteId != null,
    )
}

@Composable
internal fun MoveSwapSheet(model: PlanViewModel, workout: Workout, onClose: () -> Unit) {
    var swap by remember { mutableStateOf(false) }
    Text(P("Move / swap"), style = MaterialTheme.typography.headlineSmall)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        FilterChip(
            selected = !swap,
            onClick = { swap = false },
            label = { Text(P("Move workout")) },
        )
        FilterChip(selected = swap, onClick = { swap = true }, label = { Text(P("Swap days")) })
    }
    Text(
        P(
            if (swap) "Swap all sessions between two days in the same week."
            else "Move this session to this week or next week."
        ),
        color = UH.secondary,
    )
    val targets =
        if (swap) Weekday.entries.filter { it != workout.weekday }.map { workout.weekNumber to it }
        else model.moveTargets(workout)
    targets.forEach { (week, day) ->
        OutlinedButton(
            onClick = { model.move(workout, week, day, swap, onClose) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("${P("Week")} $week · ${P(day.name)}")
        }
    }
}

@Composable
internal fun GenerationSheet(model: PlanViewModel, adapt: Boolean, onClose: () -> Unit) {
    val state by model.state.collectAsState()
    val offer = model.nextOffer()
    var rpe by remember { mutableStateOf<Int?>(null) }
    var fatigue by remember { mutableStateOf("medium") }
    var notes by remember { mutableStateOf("") }
    var coachNotes by remember { mutableStateOf("") }
    var override by remember { mutableStateOf(false) }
    val schedule = remember(state.snapshot?.plan?.id) { ScheduleDraft(state.snapshot?.plan) }
    var evaluation by remember { mutableStateOf<BlockEvaluation?>(null) }
    var scheduleExpanded by remember { mutableStateOf(false) }
    LaunchedEffect(adapt) { if (!adapt) evaluation = model.blockEvaluation() }
    Text(
        P(if (adapt) "Adapt week" else "Next block"),
        style = MaterialTheme.typography.headlineSmall,
    )
    if (!adapt) {
        Text("${P("Week")} ${offer?.start}–${offer?.end}")
        evaluation?.let { value ->
            Text(
                "${value.sessionsCompleted} / ${value.sessionsTotal} · ${value.completionPct.toInt()}%\n${P("Planned")} ${value.plannedKm} km · ${P("Actual")} ${value.actualKm} km"
            )
            value.coachSummary?.let { Text(it) }
            value.coachingTakeaways.forEach { Text("• $it") }
            value.coachNotes.forEach { Text(it) }
        }
    }
    Text(P("Overall effort (RPE)"))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        (1..10).forEach { value ->
            FilterChip(
                selected = rpe == value,
                onClick = { rpe = value },
                label = { Text("$value") },
            )
        }
    }
    if (adapt) {
        Text(P("Fatigue"))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            listOf(
                    "easy" to "Fresh",
                    "medium" to "Normal tiredness",
                    "hard" to "Heavy legs",
                    "exhausted" to "Exhausted",
                )
                .forEach { (key, title) ->
                    FilterChip(
                        selected = fatigue == key,
                        onClick = { fatigue = key },
                        label = { Text(P(title)) },
                    )
                }
        }
    }
    OutlinedTextField(
        value = notes,
        onValueChange = { notes = it },
        label = { Text(P("Notes for Coach Uphill")) },
        modifier = Modifier.fillMaxWidth(),
    )
    if (model.athleteId != null && !adapt)
        OutlinedTextField(
            value = coachNotes,
            onValueChange = { coachNotes = it },
            label = { Text(P("Coach guidance")) },
            modifier = Modifier.fillMaxWidth(),
        )
    TextButton(onClick = { scheduleExpanded = !scheduleExpanded }) {
        Text(P("Edit schedule and training venues"))
    }
    if (scheduleExpanded) ScheduleEditor(schedule)
    schedule.validationMessage?.let { Text(P(it), color = UH.danger) }
    if (!adapt && offer?.unlocked == false) {
        Text(P("The previous block is not complete enough yet."), color = UH.warningInk)
        Row {
            Checkbox(checked = override, onCheckedChange = { override = it })
            Text(P("Build anyway"), Modifier.padding(top = 12.dp))
        }
    }
    Button(
        onClick = {
            model.generate(adapt, rpe, fatigue, notes, schedule, override, coachNotes, onClose)
        },
        enabled =
            !state.busy &&
                schedule.validationMessage == null &&
                (adapt || offer?.unlocked == true || override),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(P(if (adapt) "Adapt week" else "Build next week"))
    }
}

@Composable
internal fun ScheduleChangeSheet(model: PlanViewModel, onClose: () -> Unit) {
    val state by model.state.collectAsState()
    val snapshot = state.snapshot ?: return
    val draft = remember(snapshot.plan.id) { ScheduleDraft(snapshot.plan) }
    var confirm by remember { mutableStateOf(false) }
    Text(P("Schedule"), style = MaterialTheme.typography.headlineSmall)
    Text(P("Weekly Schedule"), style = MaterialTheme.typography.titleMedium)
    Text(
        P("Adjust your preferred running days, long run, and training environment."),
        style = MaterialTheme.typography.bodySmall,
        color = UH.secondary,
    )
    ScheduleEditor(draft)
    draft.validationMessage?.let { Text(P(it), color = UH.danger) }
    Button(
        onClick = { confirm = true },
        enabled = !state.busy && draft.validationMessage == null && draft.changes().isNotEmpty(),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(P("Rebuild week"))
    }
    if (confirm)
        AlertDialog(
            onDismissRequest = { confirm = false },
            title = { Text(P("Rebuild this week around your new schedule?")) },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirm = false
                        model.generate(
                            true,
                            null,
                            "medium",
                            "",
                            draft,
                            false,
                            "",
                            onClose,
                            weekOverride =
                                PlanCalendar.currentWeek(snapshot.plan, snapshot.workouts),
                        )
                    }
                ) {
                    Text(P("Rebuild week"))
                }
            },
            dismissButton = { TextButton(onClick = { confirm = false }) { Text(P("Not now")) } },
        )
}

@Composable
private fun ScheduleEditor(draft: ScheduleDraft) {
    var revision by remember { mutableIntStateOf(0) }
    @Suppress("UNUSED_VARIABLE") val observe = revision
    Text(P("Run days"), style = MaterialTheme.typography.titleMedium)
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        (3..7).forEach { count ->
            FilterChip(
                selected = draft.daysPerWeek == count,
                onClick = {
                    draft.changeDaysPerWeek(count)
                    revision++
                },
                label = { Text("$count") },
            )
        }
    }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Weekday.entries.forEach { day ->
            FilterChip(
                selected = day in draft.preferredDays,
                onClick = {
                    draft.toggle(day)
                    revision++
                },
                label = { Text(P(day.short)) },
            )
        }
    }
    Text(P("Long run day"))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        draft.orderedDays.forEach { day ->
            FilterChip(
                selected = draft.longRunDay == day,
                onClick = {
                    draft.longRunDay = day
                    revision++
                },
                label = { Text(P(day.short)) },
            )
        }
    }
    Text(P("Double sessions"))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        draft.orderedDays.forEach { day ->
            FilterChip(
                selected = day in draft.doubleSessionDays,
                onClick = {
                    draft.doubleSessionDays =
                        if (day in draft.doubleSessionDays) draft.doubleSessionDays - day
                        else if (draft.doubleSessionDays.size < 2) draft.doubleSessionDays + day
                        else draft.doubleSessionDays
                    revision++
                },
                label = { Text(P(day.short)) },
            )
        }
    }
    Text(P("Terrain near home"))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        listOf("flat" to "Mostly flat", "hilly" to "Hilly", "mixed" to "A mix").forEach {
            (key, title) ->
            FilterChip(
                selected = draft.environment == key,
                onClick = {
                    draft.environment = key
                    revision++
                },
                label = { Text(P(title)) },
            )
        }
    }
    Text(P("Hill / trail days"))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Weekday.entries.forEach { day ->
            FilterChip(
                selected = day in draft.mountainDays,
                onClick = {
                    draft.mountainDays =
                        if (day in draft.mountainDays) draft.mountainDays - day
                        else draft.mountainDays + day
                    revision++
                },
                label = { Text(P(day.short)) },
            )
        }
    }
    ScheduleToggle("Gym access", draft.hasGymAccess) {
        draft.hasGymAccess = it
        revision++
    }
    ScheduleToggle("Treadmill", draft.useTreadmill) {
        draft.useTreadmill = it
        revision++
    }
    if (draft.useTreadmill)
        OutlinedTextField(
            value = draft.treadmillMaxIncline.toString(),
            onValueChange = {
                draft.treadmillMaxIncline = it.toIntOrNull() ?: 0
                revision++
            },
            label = { Text(P("Maximum incline (%)")) },
        )
    ScheduleToggle("Stair access", draft.stairAccess) {
        draft.stairAccess = it
        revision++
    }
    if (draft.gettingStarted)
        OutlinedTextField(
            value = draft.maxContinuousJogMin.toString(),
            onValueChange = {
                draft.maxContinuousJogMin = it.toIntOrNull() ?: 0
                revision++
            },
            label = { Text(P("Continuous jogging (min)")) },
        )
}

@Composable
private fun ScheduleToggle(title: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(P(title), Modifier.padding(top = 12.dp))
        Switch(checked = value, onCheckedChange = onChange)
    }
}

@Composable
internal fun WeekReviewSheet(model: PlanViewModel) {
    var review by remember { mutableStateOf<WeekReview?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(true) }
    LaunchedEffect(Unit) {
        try {
            review = model.weekReview()
        } catch (e: Exception) {
            error = e.message
        } finally {
            loading = false
        }
    }
    Text(P("Week review"), style = MaterialTheme.typography.headlineSmall)
    if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
    error?.let { Text(P(it), color = UH.danger) }
    review?.let { value ->
        Text(
            "${value.completionPct.toInt()}% · ${P("Recorded training")}",
            style = MaterialTheme.typography.headlineMedium,
        )
        value.checkboxCompletionPct?.let { Text("${it.toInt()}% · ${P("Sessions marked done")}") }
        Text(
            "${P("Planned")} ${value.planned?.distanceKm ?: 0} km · ${P("Actual")} ${value.actual?.totalActualKm ?: 0} km"
        )
        value.narrative?.summary?.let { Text(it) }
        value.narrative?.highlights?.forEach { Text("• $it") }
        value.narrative?.watch?.forEach { Text("• $it", color = UH.warningInk) }
        value.perWorkout.forEach { row ->
            HorizontalDivider()
            Text("${P(row.dayOfWeek.orEmpty())} · ${row.title.orEmpty()}")
            Text(
                "${P(row.actual.state)} · ${row.actual.distanceKm ?: 0} km · ${row.actual.durationMinutes ?: 0} min",
                color = UH.secondary,
            )
        }
    }
}

@Composable
internal fun GoalSheet(model: PlanViewModel, state: PlanState, onClose: () -> Unit) {
    var confirm by remember { mutableStateOf(false) }
    val goal = state.goal
    Text(P("Time Target"), style = MaterialTheme.typography.headlineSmall)
    Text(
        goal?.targetTimeHours?.let { minutesText(it * 60) } ?: P("No target"),
        style = MaterialTheme.typography.headlineLarge,
    )
    goal?.assessment?.let { assessment ->
        assessment.goals?.let {
            Text("A ${minutesText(it.a)} · B ${minutesText(it.b)} · C ${minutesText(it.c)}")
        }
        assessment.confidence?.let { Text("${P("Confidence")} · ${P(it)}", color = UH.secondary) }
        assessment.reasoningText.forEach { Text("• $it") }
        assessment.missingText.forEach { Text("${P("Missing")}: ${P(it)}", color = UH.warningInk) }
        assessment.anchors.forEach { Text("${P(it.method)} · ${minutesText(it.minutes)}") }
        assessment.context?.get("race")?.jsonObject?.let { race ->
            Text(
                "${P("Race")}: ${race["distance_km"]?.jsonPrimitive?.content.orEmpty()} km · ${race["gain_m"]?.jsonPrimitive?.content.orEmpty()} m D+"
            )
        }
        assessment.createdAt?.let { Text(it, color = UH.muted) }
    }
    Button(onClick = model::reassess, enabled = state.cachedAt == null && !state.busy) {
        Text(P("Check my goal"))
    }
    goal?.suggestedMinutes?.let { minutes ->
        OutlinedButton(
            onClick = { confirm = true },
            enabled = state.cachedAt == null && !state.busy,
        ) {
            Text("${P("Use suggested time")} · ${minutesText(minutes)}")
        }
    }
    if (confirm)
        AlertDialog(
            onDismissRequest = { confirm = false },
            title = { Text(P("Update Time Target?")) },
            text = { Text(P("This changes your plan target. Your workouts stay in place.")) },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirm = false
                        model.applyGoal(onClose)
                    }
                ) {
                    Text(P("Confirm"))
                }
            },
            dismissButton = { TextButton(onClick = { confirm = false }) { Text(P("Cancel")) } },
        )
}

@Composable
internal fun ManagePlanSheet(
    model: PlanViewModel,
    onClose: () -> Unit,
    onNewPlan: () -> Unit,
    onSchedule: () -> Unit,
    onSync: () -> Unit,
    onExport: () -> Unit,
    onTool: (String) -> Unit,
) {
    var plans by remember { mutableStateOf<List<Plan>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var delete by remember { mutableStateOf<Plan?>(null) }
    val state by model.state.collectAsState()
    LaunchedEffect(Unit) {
        try {
            plans = model.recent()
        } catch (e: Exception) {
            error = e.message
        }
    }
    Text(P("Manage plan"), style = MaterialTheme.typography.headlineSmall)
    error?.let { Text(P(it), color = UH.danger) }
    Text(P("Recent plans"), style = MaterialTheme.typography.titleMedium)
    plans.forEach { plan ->
        OutlinedCard {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(plan.raceName, style = MaterialTheme.typography.titleMedium)
                Text("${plan.raceDate} · ${plan.totalWeeks} ${P("weeks")}")
                if (model.athleteId == null)
                    Row {
                        TextButton(
                            onClick = { model.select(plan, onClose) },
                            enabled = !state.busy,
                        ) {
                            Text(
                                P(
                                    if (plan.id == state.snapshot?.plan?.id) "Active plan"
                                    else "Select plan"
                                )
                            )
                        }
                        TextButton(onClick = { delete = plan }, enabled = !state.busy) {
                            Text(P("Delete"), color = UH.danger)
                        }
                    }
            }
        }
    }
    if (model.athleteId == null) {
        Text(P("Plan actions"), style = MaterialTheme.typography.titleMedium)
        OutlinedButton(onClick = onNewPlan, modifier = Modifier.fillMaxWidth()) {
            Text(P("Build a new plan"))
        }
        OutlinedButton(
            onClick = onSchedule,
            modifier = Modifier.fillMaxWidth(),
            enabled = state.cachedAt == null,
        ) {
            Text(P("Edit schedule and training venues"))
        }
    }
    Text(P("Tools & Labs"), style = MaterialTheme.typography.titleMedium)
    listOf(
            "goal" to "Goal Determiner",
            "gear" to "Gear Vault",
            "nutrition" to "Nutrition Lab",
            "pace" to "Pace Strategy",
            "knowledge" to "Knowledge Hub",
        )
        .forEach { (route, title) ->
            TextButton(onClick = { onTool(route) }, modifier = Modifier.fillMaxWidth()) {
                Text(P(title))
            }
        }
    if (model.athleteId == null) {
        Text(P("Integrations"), style = MaterialTheme.typography.titleMedium)
        OutlinedButton(
            onClick = onSync,
            modifier = Modifier.fillMaxWidth(),
            enabled = state.cachedAt == null && !state.busy,
        ) {
            Text(P("Sync watch"))
        }
        OutlinedButton(
            onClick = onExport,
            modifier = Modifier.fillMaxWidth(),
            enabled = state.cachedAt == null,
        ) {
            Text(P("Export calendar"))
        }
    }
    delete?.let { plan ->
        AlertDialog(
            onDismissRequest = { delete = null },
            title = { Text(P("Delete plan?")) },
            text = { Text(plan.raceName) },
            confirmButton = {
                TextButton(
                    onClick = {
                        delete = null
                        model.delete(plan, onClose)
                    }
                ) {
                    Text(P("Delete"), color = UH.danger)
                }
            },
            dismissButton = { TextButton(onClick = { delete = null }) { Text(P("Cancel")) } },
        )
    }
}

@Composable
internal fun WatchMatchSheet(model: PlanViewModel, workout: Workout?, onClose: () -> Unit) {
    var activities by remember { mutableStateOf<List<WatchActivity>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(true) }
    LaunchedEffect(Unit) {
        try {
            activities = model.watch()
        } catch (e: Exception) {
            error = e.message
        } finally {
            loading = false
        }
    }
    Text(P("Link watch activity"), style = MaterialTheme.typography.headlineSmall)
    if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
    error?.let { Text(P(it), color = UH.danger) }
    if (!loading && activities.isEmpty() && error == null)
        Text(P("No watch activities in this plan yet."))
    activities.forEach { activity ->
        OutlinedCard(
            onClick = { model.match(activity.activityId, workout, onClose) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(Modifier.padding(14.dp)) {
                Text(activity.startTime.orEmpty())
                Text(
                    "${activity.distanceKm ?: 0} km · ${((activity.durationSeconds ?: 0.0)/60).toInt()} min · ${activity.avgHr?.toInt() ?: 0} bpm"
                )
                activity.workoutTitle?.let { Text(it, color = UH.secondary) }
                Text(P(activity.matchMethod ?: "unmatched"), color = UH.muted)
            }
        }
    }
}

@Composable
internal fun ExportCalendarSheet(model: PlanViewModel, snapshot: PlanSnapshot) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var pref by remember { mutableStateOf("all_day") }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    Text(P("Export calendar"), style = MaterialTheme.typography.headlineSmall)
    Text(P("Share a calendar file with Google Calendar, Outlook, or another calendar app."))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        listOf(
                "all_day" to "All day",
                "morning" to "Morning",
                "afternoon" to "Afternoon",
                "evening" to "Evening",
            )
            .forEach { (key, label) ->
                FilterChip(
                    selected = pref == key,
                    onClick = { pref = key },
                    label = { Text(P(label)) },
                )
            }
    }
    Button(
        enabled = !busy,
        onClick = {
            scope.launch {
                busy = true
                error = null
                try {
                    val text = model.service.ics(snapshot.plan.id, snapshot.plan.raceDate, pref)
                    val directory = File(context.cacheDir, "exports").apply { mkdirs() }
                    val file =
                        File(directory, "uphill_plan_${snapshot.plan.id}.ics").apply {
                            writeText(text)
                        }
                    val uri =
                        FileProvider.getUriForFile(
                            context,
                            "${context.packageName}.fileprovider",
                            file,
                        )
                    val intent =
                        Intent(Intent.ACTION_SEND)
                            .setType("text/calendar")
                            .putExtra(Intent.EXTRA_STREAM, uri)
                            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    context.startActivity(Intent.createChooser(intent, "Uphill AI"))
                } catch (e: Exception) {
                    error = e.message
                } finally {
                    busy = false
                }
            }
        },
    ) {
        Text(P("Share .ics file"))
    }
    error?.let { Text(P(it), color = UH.danger) }
}

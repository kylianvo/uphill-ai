package ai.uphill.app.feature.onboarding

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.generation.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.models.Weekday
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import java.time.LocalDate

@Composable
fun OnboardingScreen(
    api: APIClient,
    user: User,
    lang: String,
    onComplete: () -> Unit,
    onNavigate: (String) -> Unit = {},
    newPlan: Boolean = false,
    onClose: () -> Unit = onComplete,
) {
    val context = LocalContext.current
    val center = remember(api, user.id) { GenerationCenter.get(context, api, user.id) }
    val model: PlanSetupViewModel =
        viewModel(
            key = "setup-${user.id}-$newPlan",
            factory =
                object : ViewModelProvider.Factory {
                    override fun <T : ViewModel> create(modelClass: Class<T>): T {
                        @Suppress("UNCHECKED_CAST")
                        return PlanSetupViewModel(api, user, lang, center, !newPlan) as T
                    }
                },
        )
    SideEffect { model.changeLanguage(lang) }
    val state by model.state.collectAsState()
    val generation by center.state.collectAsState()
    LaunchedEffect(Unit) { model.refreshFitness() }
    LaunchedEffect(generation.outcome) {
        if (
            state.started &&
                (generation.outcome is JobOutcome.Done || generation.outcome is JobOutcome.Lost)
        )
            onComplete()
    }
    if (generation.running != null || state.started) {
        Column(
            Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(P("Building your plan"), style = MaterialTheme.typography.headlineMedium)
            if (generation.running != null) {
                LinearProgressIndicator(Modifier.fillMaxWidth())
                Text(P("You can leave this screen. Your plan will keep building."))
                generation.running!!.summary.forEach { Text(P(it)) }
            }
            (generation.outcome as? JobOutcome.Failed)?.let {
                Text(P(it.message), color = UH.danger)
                Button(onClick = { model.reopenReview() }) { Text(P("Try again")) }
            }
        }
        return
    }
    val draft = state.draft
    val step = model.step()
    val formScroll = rememberScrollState()
    LaunchedEffect(step) { formScroll.scrollTo(0) }
    Column(Modifier.fillMaxSize().padding(horizontal = 24.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = model::back, enabled = state.index > 0) {
                if (state.index > 0) Icon(Icons.Default.ChevronLeft, P("Back"))
            }
            val progress = (state.index + 1f) / model.steps().size
            val progressLabel =
                L("Setup progress") +
                    ": " +
                    L("Step %lld of %lld", state.index + 1, model.steps().size)
            Box(
                Modifier.weight(1f)
                    .height(4.dp)
                    .clip(RoundedCornerShape(50))
                    .background(UH.line)
                    .semantics {
                        contentDescription = progressLabel
                        progressBarRangeInfo = ProgressBarRangeInfo(progress, 0f..1f)
                    }
            ) {
                Box(Modifier.fillMaxHeight().fillMaxWidth(progress).background(UH.accent))
            }
            IconButton(onClick = onClose, enabled = !state.submitting) {
                Icon(Icons.Default.Close, L("Close"))
            }
        }
        Column(
            Modifier.weight(1f).verticalScroll(formScroll).padding(vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SetupCoachBanner(step, draft.goal)
            val title =
                when (step) {
                    SetupStep.Details ->
                        if (draft.goal == SetupGoal.Race) "Which race?"
                        else if (draft.goal == SetupGoal.Distance) "What distance?" else step.title
                    SetupStep.RaceDate -> "When is it?"
                    SetupStep.StartDate -> "When do you want to start?"
                    else -> step.title
                }
            Text(P(title), style = MaterialTheme.typography.headlineMedium)
            when (step) {
                SetupStep.Goal -> SetupGoalOptions(draft, model::selectGoal)
                SetupStep.Details ->
                    when (draft.goal) {
                        SetupGoal.Race,
                        SetupGoal.Distance -> {
                            if (draft.goal == SetupGoal.Race)
                                Field("Race name", draft.raceName, model::raceName)
                            state.candidates.forEach { race ->
                                TextButton(onClick = { model.selectRace(race) }) {
                                    Text(race.raceName)
                                }
                            }
                            state.selectedRace
                                ?.distances
                                ?.sortedBy { it.distanceKm }
                                ?.forEach { distance ->
                                    FilterChip(
                                        selected =
                                            draft.distanceKm == distance.distanceKm &&
                                                draft.distanceLabel == distance.label,
                                        onClick = {
                                            model.edit {
                                                it.distanceKm = distance.distanceKm
                                                it.elevationGainM = distance.elevationGainM
                                                it.distanceLabel = distance.label
                                            }
                                        },
                                        label = {
                                            Text(distance.label ?: "${distance.distanceKm} km")
                                        },
                                    )
                                }
                            NumberField("Distance (km)", draft.distanceKm) {
                                model.edit { d -> d.distanceKm = it }
                            }
                            NumberField("Elevation Gain (m)", draft.elevationGainM) {
                                model.edit { d -> d.elevationGainM = it }
                            }
                            Options(
                                listOf("trail" to "Trail", "road" to "Road", "mixed" to "Mixed"),
                                draft.terrain,
                            ) {
                                model.edit { d -> d.terrain = it }
                            }
                        }
                        SetupGoal.Return ->
                            Options(
                                listOf(
                                    "< 2 weeks" to "< 2 weeks",
                                    "2–6 weeks" to "2–6 weeks",
                                    "1–3 months" to "1–3 months",
                                    "3–6 months" to "3–6 months",
                                    "6+ months" to "6+ months",
                                ),
                                draft.timeAway,
                            ) {
                                model.edit { d -> d.timeAway = it }
                            }
                        SetupGoal.Recovery ->
                            Options(
                                listOf(
                                        "5k",
                                        "10k",
                                        "Half Marathon",
                                        "Marathon",
                                        "Ultra (< 60k)",
                                        "Ultra (60k+)",
                                    )
                                    .map { it to it },
                                draft.raceDistanceCompleted,
                            ) {
                                model.edit { d -> d.raceDistanceCompleted = it }
                            }
                        else -> Unit
                    }
                SetupStep.RaceDate -> {
                    SetupDatePicker(draft.raceDate, LocalDate.now().plusDays(14)) { date ->
                        model.edit { it.raceDate = date }
                    }
                    draft.raceDate?.let {
                        Text(
                            L(
                                "That's %lld weeks away",
                                java.time.temporal.ChronoUnit.WEEKS.between(LocalDate.now(), it),
                            ),
                            color = UH.accentInk,
                        )
                    }
                }
                SetupStep.RaceGoal -> {
                    Options(
                        listOf(
                            "finish" to "Finish strong",
                            "time" to "Hit a target time",
                            "optimal" to "My best possible time",
                        ),
                        draft.raceGoal,
                    ) {
                        model.edit { d -> d.raceGoal = it }
                    }
                    if (draft.raceGoal == "time")
                        Field(
                            "Target time (h:mm)",
                            draft.targetMinutes?.let { minutesText(it.toDouble()) }.orEmpty(),
                        ) { value ->
                            val parts = value.split(':')
                            model.edit {
                                it.targetMinutes =
                                    if (parts.size == 2)
                                        parts[0].toIntOrNull()?.let { h ->
                                            parts[1].toIntOrNull()?.let { m -> h * 60 + m }
                                        }
                                    else null
                            }
                        }
                    OutlinedButton(onClick = model::assess, enabled = !state.assessmentBusy) {
                        Text(P("Estimate my goal"))
                    }
                    if (state.assessmentBusy) LinearProgressIndicator(Modifier.fillMaxWidth())
                    state.goalAssessment?.let { assessment ->
                        assessment.goals?.let { tiers ->
                            Text(
                                "A ${minutesText(tiers.a)} · B ${minutesText(tiers.b)} · C ${minutesText(tiers.c)}"
                            )
                            Button(
                                onClick = {
                                    model.edit {
                                        it.raceGoal = "time"
                                        it.targetMinutes = kotlin.math.round(tiers.b).toInt()
                                    }
                                }
                            ) {
                                Text(P("Use suggested time"))
                            }
                        }
                        assessment.reasoningText.forEach { Text(it) }
                        assessment.missingText.forEach { Text(it, color = UH.muted) }
                    }
                }
                SetupStep.FitnessFeel ->
                    Options(
                        listOf(
                            "Feeling good, just need structure" to
                                "Feeling good, just need structure",
                            "A bit rusty, slightly deconditioned" to
                                "A bit rusty, slightly deconditioned",
                            "Significant deconditioning — starting nearly fresh" to
                                "Significant deconditioning — starting nearly fresh",
                        ),
                        draft.fitnessFeel,
                    ) {
                        model.edit { d -> d.fitnessFeel = it }
                    }
                SetupStep.DaysSinceRace ->
                    Field("Days since your race", draft.daysSinceRace.toString()) {
                        model.edit { d -> d.daysSinceRace = it.toIntOrNull() ?: 0 }
                    }
                SetupStep.RecoveryFeel ->
                    Options(
                        listOf(
                            "Feeling great, minimal soreness" to "Feeling great, minimal soreness",
                            "Moderate fatigue, some soreness" to "Moderate fatigue, some soreness",
                            "Very fatigued — need real rest" to "Very fatigued — need real rest",
                        ),
                        draft.recoveryFeel,
                    ) {
                        model.edit { d -> d.recoveryFeel = it }
                    }
                SetupStep.Watch -> {
                    Text(P("Watch activities can fill your weekly volume."))
                    Button(onClick = { onNavigate("integrations") }) {
                        Text(P("Connect your watch"))
                    }
                    OutlinedButton(onClick = model::refreshFitness) { Text(P("Refresh")) }
                }
                SetupStep.Schedule -> {
                    Options((3..7).map { it.toString() to "$it" }, draft.daysPerWeek.toString()) {
                        model.setRunDays(it.toInt())
                    }
                    DayChips(draft.preferredDays, model::toggleDay)
                    Text(P("Long run day"))
                    DayChips(
                        setOf(draft.longRunDay),
                        { model.edit { d -> d.longRunDay = it } },
                        draft.preferredDays,
                    )
                    NumberField(
                        "Current weekly volume (km)",
                        draft.currentWeeklyKm,
                        model::weeklyKm,
                    )
                    state.watchKm?.let { Text("COROS · $it km", color = UH.muted) }
                    Text(P("Double sessions"))
                    DayChips(
                        draft.doubleSessionDays,
                        { day ->
                            model.edit {
                                it.doubleSessionDays =
                                    if (day in it.doubleSessionDays) it.doubleSessionDays - day
                                    else if (it.doubleSessionDays.size < 2)
                                        it.doubleSessionDays + day
                                    else it.doubleSessionDays
                            }
                        },
                        draft.preferredDays,
                    )
                }
                SetupStep.Venues -> {
                    Options(
                        listOf("flat" to "Mostly flat", "hilly" to "Hilly", "mixed" to "A mix"),
                        draft.environment,
                    ) {
                        model.edit { d -> d.environment = it }
                    }
                    Text(P("Hill / trail days"))
                    DayChips(
                        draft.mountainDays,
                        { day ->
                            model.edit {
                                it.mountainDays =
                                    if (day in it.mountainDays) it.mountainDays - day
                                    else it.mountainDays + day
                            }
                        },
                    )
                    Toggle("Gym access", draft.hasGymAccess) {
                        model.edit { d -> d.hasGymAccess = it }
                    }
                    Toggle("Treadmill", draft.useTreadmill) {
                        model.edit { d -> d.useTreadmill = it }
                    }
                    if (draft.useTreadmill)
                        Field("Maximum incline (%)", draft.treadmillMaxIncline.toString()) {
                            model.edit { d -> d.treadmillMaxIncline = it.toIntOrNull() ?: 15 }
                        }
                    Toggle("Stair access", draft.stairAccess) {
                        model.edit { d -> d.stairAccess = it }
                    }
                }
                SetupStep.Body -> {
                    Field("Date of birth (YYYY-MM-DD)", draft.birthDate) {
                        model.edit { d -> d.birthDate = it }
                    }
                    Options(
                        listOf("male" to "Male", "female" to "Female", "other" to "Other"),
                        draft.gender,
                    ) {
                        model.edit { d -> d.gender = it }
                    }
                    NumberField("Height (cm)", draft.heightCm) {
                        model.edit { d -> d.heightCm = it }
                    }
                    NumberField("Weight (kg)", draft.weightKg) {
                        model.edit { d -> d.weightKg = it }
                    }
                    Field("Injury history", draft.injuryHistory) {
                        model.edit { d -> d.injuryHistory = it }
                    }
                }
                SetupStep.TrainingZones -> {
                    Field("Max HR", draft.maxHr?.toString().orEmpty()) {
                        model.edit { d -> d.maxHr = it.toIntOrNull() }
                    }
                    Field("Resting HR", draft.restingHr?.toString().orEmpty()) {
                        model.edit { d -> d.restingHr = it.toIntOrNull() }
                    }
                    Field("AeT", draft.aetHr?.toString().orEmpty()) {
                        model.edit { d -> d.aetHr = it.toIntOrNull() }
                    }
                    Field("AnT", draft.antHr?.toString().orEmpty()) {
                        model.edit { d -> d.antHr = it.toIntOrNull() }
                    }
                    Options(
                        listOf(
                            "lab" to "Lab test",
                            "field_test" to "Field test",
                            "unknown" to "Not sure",
                        ),
                        draft.thresholdSource,
                    ) {
                        model.edit { d -> d.thresholdSource = it }
                    }
                    Field("Easy pace, slower end", draft.zone2PaceMin) {
                        model.edit { d -> d.zone2PaceMin = it }
                    }
                    Field("Easy pace, faster end", draft.zone2PaceMax) {
                        model.edit { d -> d.zone2PaceMax = it }
                    }
                    Field("Threshold pace", draft.thresholdPace) {
                        model.edit { d -> d.thresholdPace = it }
                    }
                }
                SetupStep.RaceHistory -> {
                    Text(P("Past race results make goal estimates more useful."))
                    Button(onClick = { onNavigate("racehistory") }) {
                        Text(P("Link your race history"))
                    }
                }
                SetupStep.StartDate -> {
                    SetupDatePicker(
                        draft.startDate,
                        LocalDate.now(),
                        draft.latestStart(LocalDate.now()),
                    ) { date ->
                        model.edit { it.startDate = date }
                    }
                }
                SetupStep.Review -> {
                    Text(
                        P(draft.goal?.title.orEmpty()),
                        style = MaterialTheme.typography.titleLarge,
                    )
                    if (draft.goal?.isEvent == true)
                        Text(
                            "${draft.raceName} · ${draft.raceDate}\n${draft.distanceKm} km · ${draft.elevationGainM ?: 0} m D+"
                        )
                    Text(
                        "${draft.daysPerWeek} · ${draft.orderedDays.joinToString {PName(it)}}\n${draft.currentWeeklyKm} km · ${draft.startDate}"
                    )
                    Field("Notes for Coach Uphill", draft.notes) {
                        model.edit { d -> d.notes = it }
                    }
                    if (!newPlan)
                        TextButton(
                            onClick = { model.submit(true, onComplete) },
                            enabled = !state.submitting,
                        ) {
                            Text(P("Save profile only"))
                        }
                }
            }
            state.issues.forEach { Text(P(it), color = UH.danger) }
            state.error?.let { Text(P(it), color = UH.danger) }
        }
        if (step != SetupStep.Goal)
            Button(
                onClick = { if (step == SetupStep.Review) model.submit() else model.next() },
                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                enabled = !state.submitting,
            ) {
                if (state.submitting) CircularProgressIndicator(Modifier.size(20.dp))
                Text(P(if (step == SetupStep.Review) "Build my plan" else "Next"))
            }
    }
    if (state.zoneWarning)
        AlertDialog(
            onDismissRequest = { model.next(true) },
            title = { Text(P("Estimated training zones")) },
            text = {
                Text(
                    P(
                        "Missing training zones will be estimated. You can update them later in Profile."
                    )
                )
            },
            confirmButton = { TextButton(onClick = { model.next(true) }) { Text(P("Continue")) } },
        )
}

private fun PName(day: Weekday) = day.short

@Composable
private fun Field(label: String, value: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(P(label)) },
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun NumberField(label: String, value: Double?, onChange: (Double?) -> Unit) {
    var text by
        remember(value) {
            mutableStateOf(
                value
                    ?.let { if (it % 1.0 == 0.0) it.toInt().toString() else it.toString() }
                    .orEmpty()
            )
        }
    Field(label, text) {
        text = it
        onChange(it.toDoubleOrNull())
    }
}

@Composable
private fun Options(
    options: List<Pair<String, String>>,
    value: String?,
    onSelect: (String) -> Unit,
) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        options.forEach { (key, title) ->
            FilterChip(
                selected = key == value,
                onClick = { onSelect(key) },
                label = { Text(P(title)) },
            )
        }
    }
}

@Composable
private fun DayChips(
    selected: Set<Weekday>,
    onSelect: (Weekday) -> Unit,
    enabled: Set<Weekday> = Weekday.entries.toSet(),
) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        Weekday.entries.forEach { day ->
            FilterChip(
                selected = day in selected,
                onClick = { onSelect(day) },
                enabled = day in enabled,
                label = { Text(P(day.short)) },
            )
        }
    }
}

@Composable
private fun Toggle(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(P(label), Modifier.padding(top = 12.dp))
        Switch(checked = value, onCheckedChange = onChange)
    }
}

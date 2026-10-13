package ai.uphill.app.feature.goal

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.time.LocalDate
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class GoalState(
    val assessment: GoalAssessmentResponse? = null,
    val busy: Boolean = false,
    val error: String? = null,
    val activePlan: ActiveToolPlan? = null,
    val applied: Boolean = false,
)

class GoalViewModel(api: APIClient) : ViewModel() {
    private val service = GoalService(api)
    private val plans = ToolPlanService(api)
    private val mutable = MutableStateFlow(GoalState())
    val state = mutable.asStateFlow()

    init {
        viewModelScope.launch {
            val plan = plans.active()
            mutable.update { it.copy(activePlan = plan) }
        }
    }

    fun applyGoal(minutes: Double) {
        val plan = mutable.value.activePlan ?: return
        viewModelScope.launch {
            try {
                plans.applyGoal(plan.id, minutes)
                mutable.update { it.copy(applied = true, error = null) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            }
        }
    }

    fun assess(request: GoalRequest) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null, applied = false) }
            try {
                val goal = service.assess(request)
                mutable.update { it.copy(assessment = goal, busy = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message, busy = false) }
            }
        }
    }
}

@Composable
fun GoalScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("goal-${user.id}") { GoalViewModel(api) }
    val state by vm.state.collectAsState()
    var name by rememberSaveable { mutableStateOf("") }
    var distance by rememberSaveable { mutableStateOf("50") }
    var gain by rememberSaveable { mutableStateOf("2200") }
    var date by rememberSaveable { mutableStateOf(LocalDate.now().plusDays(60).toString()) }
    var excluded by rememberSaveable { mutableStateOf(listOf<String>()) }
    var manual by rememberSaveable { mutableStateOf(false) }
    var refName by rememberSaveable { mutableStateOf("") }
    var refDistance by rememberSaveable { mutableStateOf("") }
    var refGain by rememberSaveable { mutableStateOf("") }
    var refTime by rememberSaveable { mutableStateOf("") }
    var resultTab by rememberSaveable { mutableStateOf("Goals") }
    var applying by remember { mutableStateOf<Double?>(null) }
    LaunchedEffect(state.activePlan) {
        state.activePlan?.let { p ->
            name = p.raceName
            distance = (p.courseDistanceKm ?: 50.0).toString()
            gain = (p.courseElevationGainM ?: 2200.0).toString()
            if (p.raceDate.isNotBlank()) date = p.raceDate
        }
    }
    ToolPage("Goal Determiner", onNavigate) {
        ToolPanel("Race setup") {
            RaceSearch(api, name, { name = it }) {
                distance = it.distanceKm.toString()
                it.elevationGainM?.let { gain = it.toString() }
            }
            ToolField("Distance (km)", distance, { distance = it })
            ToolField("Elevation Gain (m)", gain, { gain = it })
            ToolField("Race date (YYYY-MM-DD)", date, { date = it })
        }
        ToolPanel("Your baseline") {
            Text(user.name, style = MaterialTheme.typography.titleSmall)
            Text("${user.currentWeeklyKm?:"—"} km / ${TT("week")}")
            Text("AeT ${user.aetHr?:"—"} · Max HR ${user.maxHr?:"—"}")
            listOf(
                    "race_history" to "Race history",
                    "utmb_index" to "UTMB index",
                    "watch" to "Watch data",
                    "physiology" to "Physiology",
                )
                .forEach { (key, label) ->
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(TT(label))
                        Switch(
                            key !in excluded,
                            { on -> excluded = if (on) excluded - key else excluded + key },
                        )
                    }
                }
            TextButton(onClick = { onNavigate("race-history") }) { Text(TT("Link race profile")) }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(TT("Manual reference race"))
                Switch(manual, { manual = it })
            }
            if (manual) {
                ToolField("Reference race", refName, { refName = it })
                ToolField("Reference distance (km)", refDistance, { refDistance = it })
                ToolField("Reference gain (m)", refGain, { refGain = it })
                ToolField("Finish time (H:MM:SS)", refTime, { refTime = it })
            }
        }
        ToolError(state.error)
        if (state.applied) Text(TT("Goal updated"), color = UH.accentInk)
        val valid =
            (distance.toDoubleOrNull() ?: 0.0) > 0 &&
                (gain.toDoubleOrNull() ?: -1.0) >= 0 &&
                runCatching { LocalDate.parse(date) }.isSuccess &&
                (!manual ||
                    ((refDistance.toDoubleOrNull() ?: 0.0) > 0 &&
                        GoalTime.parseTime(refTime) != null))
        ToolSubmit("Estimate my goals", state.busy, valid) {
            vm.assess(
                GoalRequest(
                    name.ifBlank { null },
                    distance.toDoubleOrNull(),
                    gain.toDoubleOrNull(),
                    date,
                    excluded,
                    if (manual)
                        GoalReference(
                            refName.ifBlank { null },
                            refDistance.toDouble(),
                            refGain.toDoubleOrNull(),
                            refTime,
                        )
                    else null,
                    lang,
                )
            )
        }
        state.assessment?.let { goal ->
            ToolOptions(
                "Results",
                listOf("Goals", "What we used", "Field curve"),
                setOf(resultTab),
            ) {
                resultTab = it
            }
            when (resultTab) {
                "Goals" -> {
                    goal.goals?.let { tiers ->
                        listOf(
                                Triple("A", "Ambitious", tiers.a),
                                Triple("B", "Realistic", tiers.b),
                                Triple("C", "Safe", tiers.c),
                            )
                            .forEach { (tier, label, mins) ->
                                ToolPanel {
                                    Text("$tier · ${TT(label)}", color = UH.accentInk)
                                    Text(
                                        GoalTime.format(mins),
                                        style = MaterialTheme.typography.headlineLarge,
                                    )
                                    Text("${"%.1f".format(mins/goal.distanceKm)} min/km")
                                    Button(
                                        onClick = {
                                            ToolHandoff.pacingTargetMinutes = mins
                                            onNavigate("pace")
                                        }
                                    ) {
                                        Text(TT("Plan pacing"))
                                    }
                                    if (state.activePlan != null)
                                        OutlinedButton(onClick = { applying = mins }) {
                                            Text(TT("Apply to plan"))
                                        }
                                }
                            }
                    }
                        ?: ToolPanel {
                            Text(TT("Not enough data to estimate a goal."))
                            TextButton(onClick = { onNavigate("race-history") }) {
                                Text(TT("Add a race result"))
                            }
                        }
                    if (!goal.missing.isNullOrEmpty())
                        ToolPanel("To sharpen this") {
                            goal.missing.forEach {
                                Text(
                                    "• ${TT(it.replace('_',' ').replaceFirstChar(Char::uppercase))}"
                                )
                            }
                        }
                    goal.reasoning
                        ?.takeIf { it.isNotEmpty() }
                        ?.let { ToolPanel("Coach reasoning") { it.forEach { Text("• $it") } } }
                }
                "What we used" ->
                    ToolPanel("What we used") {
                        Text("${TT("Confidence")}: ${TT(goal.confidence?:"Unknown")}")
                        goal.sources.orEmpty().forEach {
                            Text("${if(it.included)"✓"else"–"} ${it.label}")
                        }
                        Text(
                            "${TT("Course profile")}: ${TT(goal.context?.race?.profileSource?:"Unknown")}"
                        )
                    }
                else -> FieldCurveView(goal.benchmarks.orEmpty(), goal.goals)
            }
        }
    }
    applying?.let { mins ->
        AlertDialog(
            onDismissRequest = { applying = null },
            title = { Text(TT("Confirm time target")) },
            text = { Text("${TT("Update plan target to")} ${GoalTime.format(mins)}?") },
            confirmButton = {
                TextButton(
                    onClick = {
                        vm.applyGoal(mins)
                        applying = null
                    }
                ) {
                    Text(TT("Apply"))
                }
            },
            dismissButton = { TextButton(onClick = { applying = null }) { Text(TT("Cancel")) } },
        )
    }
}

@Composable
fun FieldCurveView(benchmarks: List<RaceBenchmark>, goals: GoalTiers?) {
    var year by remember { mutableStateOf(benchmarks.firstOrNull()?.year) }
    var gender by rememberSaveable { mutableStateOf("overall") }
    var selected by remember { mutableStateOf<Double?>(null) }
    ToolPanel("Finishers field curve") {
        if (benchmarks.isEmpty())
            Text(TT("No verified benchmark field data available for this race."))
        else {
            ToolOptions("Year", benchmarks.map { it.year.toString() }, setOf(year.toString())) {
                year = it.toInt()
            }
            ToolOptions("Gender", listOf("overall", "men", "women"), setOf(gender)) { gender = it }
            val bench = benchmarks.firstOrNull { it.year == year } ?: benchmarks.first()
            val anchors = FieldCurve.anchors(bench, gender)
            ToolLineChart(
                anchors.map { it.minutes to it.percentile },
                "Time (mins) / percentile",
                goals?.let { listOf(it.a, it.b, it.c) } ?: emptyList(),
            ) {
                selected = it
            }
            selected?.let {
                Text(
                    "${GoalTime.format(it)} · ${TT("Top")} ${"%.1f".format(FieldCurve.percentile(it,anchors))}%",
                    color = UH.accentInk,
                )
            }
            goals?.let { g ->
                Text(
                    "A ${GoalTime.format(g.a)} · B ${GoalTime.format(g.b)} · C ${GoalTime.format(g.c)}"
                )
            }
            anchors.forEach {
                Text(
                    "${TT(it.label)} · ${GoalTime.format(it.minutes)} · ${"%.1f".format(it.percentile)}%"
                )
            }
            bench.conditionsNote?.let { Text(it) }
        }
    }
}

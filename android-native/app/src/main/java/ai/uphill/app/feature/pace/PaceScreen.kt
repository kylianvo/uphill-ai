package ai.uphill.app.feature.pace

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.pace.*
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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

data class PaceState(
    val paced: List<PacedCheckpoint> = emptyList(),
    val benchmarks: List<RaceBenchmark> = emptyList(),
    val gpx: GpxCourseResult? = null,
    val gpxImportVersion: Int = 0,
    val busy: Boolean = false,
    val error: String? = null,
    val activePlan: ActiveToolPlan? = null,
    val planLoaded: Boolean = false,
)

class PaceViewModel(api: APIClient) : ViewModel() {
    private val service = PacingService(api)
    private val plans = ToolPlanService(api)
    private val mutable = MutableStateFlow(PaceState())
    val state = mutable.asStateFlow()
    private var bytes: ByteArray? = null
    private var calculationJob: Job? = null
    private var benchmarkJob: Job? = null

    init {
        viewModelScope.launch {
            val plan = plans.active()
            mutable.update { it.copy(activePlan = plan, planLoaded = true) }
        }
    }

    fun parse(data: ByteArray, name: String, interval: Double, imported: Boolean = true) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                val result =
                    withContext(Dispatchers.Default) { GpxCourseParser.parse(data, name, interval) }
                bytes = data
                mutable.update {
                    it.copy(
                        gpx = result,
                        gpxImportVersion = it.gpxImportVersion + if (imported) 1 else 0,
                        busy = false,
                    )
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message, busy = false) }
            }
        }
    }

    fun interval(value: Double) {
        val data = bytes ?: return
        parse(data, mutable.value.gpx?.fileName ?: "course.gpx", value, imported = false)
    }

    fun removeGpx() {
        bytes = null
        mutable.update { it.copy(gpx = null) }
    }

    fun calculate(
        request: PacingRequest,
        debounce: Boolean = false,
    ) {
        calculationJob?.cancel()
        calculationJob =
            viewModelScope.launch {
                if (debounce) delay(350)
                mutable.update { it.copy(busy = true, error = null) }
                try {
                    val paced = service.calculate(request)
                    ensureActive()
                    mutable.update { it.copy(paced = paced, busy = false) }
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    ensureActive()
                    mutable.update { it.copy(error = e.message, busy = false) }
                }
            }
    }

    fun loadBenchmarks(name: String, distance: Double) {
        benchmarkJob?.cancel()
        mutable.update { it.copy(benchmarks = emptyList()) }
        if (name.trim().length < 3 || !distance.isFinite() || distance <= 0) return
        benchmarkJob = viewModelScope.launch {
            delay(400)
            val results = service.benchmarks(name.trim(), distance)
            ensureActive()
            mutable.update { it.copy(benchmarks = results) }
        }
    }

    fun cancelCalculation() {
        calculationJob?.cancel()
        mutable.update { it.copy(busy = false) }
    }

    fun error(message: String) {
        mutable.update { it.copy(error = message) }
    }
}

@Composable
fun PaceScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("pace-${user.id}") { PaceViewModel(api) }
    val state by vm.state.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val incomingTarget by rememberSaveable { mutableStateOf(ToolHandoff.pacingTargetMinutes) }
    var planDefaultsApplied by rememberSaveable { mutableStateOf(false) }
    var name by rememberSaveable { mutableStateOf("") }
    var distance by rememberSaveable { mutableStateOf("50") }
    var gain by rememberSaveable { mutableStateOf("2200") }
    var interval by rememberSaveable { mutableStateOf("5") }
    var target by rememberSaveable { mutableStateOf(incomingTarget?.toString() ?: "330") }
    var weight by rememberSaveable { mutableStateOf((user.weightKg ?: 68.0).toString()) }
    var clock by rememberSaveable { mutableStateOf("05:00") }
    var bias by rememberSaveable { mutableFloatStateOf(0f) }
    var rests by rememberSaveable { mutableStateOf(mapOf<Int, Int>()) }
    var year by rememberSaveable { mutableStateOf("All years") }
    val launcher =
        rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
            if (uri != null)
                scope.launch {
                    try {
                        val loaded =
                            withContext(Dispatchers.IO) {
                                val fileName =
                                    context.contentResolver
                                        .query(
                                            uri,
                                            arrayOf(OpenableColumns.DISPLAY_NAME),
                                            null,
                                            null,
                                            null,
                                        )
                                        ?.use { if (it.moveToFirst()) it.getString(0) else null }
                                        ?: "course.gpx"
                                val data =
                                    context.contentResolver.openInputStream(uri)?.use {
                                        it.readBytes()
                                    } ?: error("Cannot read GPX file.")
                                data to fileName
                            }
                        vm.parse(loaded.first, loaded.second, interval.toDoubleOrNull() ?: 5.0)
                    } catch (e: CancellationException) {
                        throw e
                    } catch (e: Exception) {
                        vm.error(e.message ?: "Cannot read GPX file.")
                    }
                }
        }
    LaunchedEffect(Unit) {
        if (ToolHandoff.pacingTargetMinutes == incomingTarget)
            ToolHandoff.pacingTargetMinutes = null
    }
    LaunchedEffect(state.planLoaded) {
        if (state.planLoaded && !planDefaultsApplied) {
            state.activePlan?.let { p ->
                name = p.raceName
                distance = (p.courseDistanceKm ?: 50.0).toString().removeSuffix(".0")
                gain = (p.courseElevationGainM ?: 2200.0).toString().removeSuffix(".0")
            }
            if (incomingTarget == null) {
                val d = distance.toDoubleOrNull() ?: 50.0
                val g = gain.toDoubleOrNull() ?: 2200.0
                val bounds = PacingCalculator.sliderBoundsMins(d, g)
                target = (state.activePlan?.targetMinutes
                    ?: ((d + g / 100) * 6.5).coerceIn(bounds.first, bounds.second)).toString()
            }
            planDefaultsApplied = true
        }
    }
    LaunchedEffect(state.gpx) {
        state.gpx?.let {
            distance = it.totalDistanceKm.toString().removeSuffix(".0")
            gain = it.totalElevationGainM.toString().removeSuffix(".0")
            if (name.isBlank()) name = it.fileName.removeSuffix(".gpx").replace('_', ' ')
        }
    }
    LaunchedEffect(state.gpxImportVersion) {
        state.gpx?.let { course ->
            val bounds = PacingCalculator.sliderBoundsMins(course.totalDistanceKm, course.totalElevationGainM)
            target = ((course.totalDistanceKm + course.totalElevationGainM / 100) * 6.5)
                .coerceIn(bounds.first, bounds.second)
                .toString()
        }
    }
    fun pacingRequest(): PacingRequest? {
        val d = state.gpx?.totalDistanceKm ?: distance.toDoubleOrNull() ?: return null
        val g = state.gpx?.totalElevationGainM ?: gain.toDoubleOrNull() ?: return null
        val minutes = target.toDoubleOrNull() ?: return null
        val kg = weight.toDoubleOrNull() ?: return null
        val step = interval.toDoubleOrNull() ?: return null
        if (
            !d.isFinite() ||
                d <= 0 ||
                !g.isFinite() ||
                g < 0 ||
                !minutes.isFinite() ||
                minutes <= 0 ||
                !kg.isFinite() ||
                kg <= 0 ||
                !step.isFinite() ||
                step <= 0
        )
            return null
        val checkpoints =
            state.gpx?.checkpoints ?: PacingCalculator.synthesizeCourse(d, g, intervalKm = step)
        return PacingRequest(
            checkpoints,
            minutes,
            splitBias = bias.toDouble(),
            runnerWeightKg = kg,
        )
    }
    LaunchedEffect(planDefaultsApplied, target, bias, distance, gain, weight, interval, state.gpx) {
        if (planDefaultsApplied) {
            val request = pacingRequest()
            if (request == null) vm.cancelCalculation()
            else vm.calculate(request, debounce = true)
        }
    }
    LaunchedEffect(name, distance) {
        vm.loadBenchmarks(name, distance.toDoubleOrNull() ?: 0.0)
    }
    LaunchedEffect(state.benchmarks) {
        if (year != "All years" && state.benchmarks.none { it.year.toString() == year })
            year = "All years"
    }
    ToolPage("Pace strategy", onNavigate) {
        PaceCourseCard(
            api = api,
            name = name,
            distance = distance,
            gain = gain,
            interval = interval,
            gpx = state.gpx,
            onName = { name = it },
            onDistance = { distance = it },
            onGain = { gain = it },
            onRace = {
                distance = it.distanceKm.toString().removeSuffix(".0")
                it.elevationGainM?.let { gain = it.toString().removeSuffix(".0") }
            },
            onInterval = {
                interval = it
                vm.interval(it.toDouble())
            },
            onImport = {
                launcher.launch(
                    arrayOf("application/gpx+xml", "application/xml", "text/xml", "application/octet-stream", "*/*")
                )
            },
            onRemove = { vm.removeGpx() },
        )
        val courseDistance = (state.gpx?.totalDistanceKm ?: distance.toDoubleOrNull())?.takeIf { it.isFinite() && it > 0 } ?: 0.0
        val courseGain = (state.gpx?.totalElevationGainM ?: gain.toDoubleOrNull())?.takeIf { it.isFinite() && it >= 0 } ?: 0.0
        PaceControlsCard(
            target = target.toDoubleOrNull()?.takeIf { it.isFinite() } ?: 330.0,
            bounds = PacingCalculator.sliderBoundsMins(courseDistance, courseGain),
            bias = bias, weight = weight, clock = clock,
            onTarget = { target = it.toString() }, onBias = { bias = it },
            onWeight = { weight = it }, onClock = { clock = it },
        )
        ToolError(state.error)
        ToolSubmit("Calculate pacing", state.busy, pacingRequest() != null) {
            pacingRequest()?.let { vm.calculate(it) }
        }

        if (state.benchmarks.isNotEmpty())
            ToolPanel("Past results") {
                ToolOptions(
                    "Year",
                    listOf("All years") + state.benchmarks.map { it.year.toString() },
                    setOf(year),
                ) {
                    year = it
                }
                BenchmarkMarker.markers(state.benchmarks, year.toIntOrNull()).forEach { marker ->
                    TextButton(onClick = { target = marker.minutes.toString() }) {
                        Text("${TT(marker.label)} · ${GoalTime.format(marker.minutes)}")
                    }
                }
            }
        if (state.paced.isNotEmpty()) {
            val last = state.paced.last()
            val rest = rests.values.sum()
            val etas = PacingCalculator.clockEtas(state.paced, rests, clock)
            ToolPanel("Race summary") {
                Text("${TT("Moving time")}: ${GoalTime.format(last.cumulativeTimeMins)}")
                Text("${TT("With rest")}: ${GoalTime.format(last.cumulativeTimeMins+rest)}")
                Text(
                    "${state.paced.count{it.effort=="hike"}} ${TT("Hike sections")} · ${last.energyKcal?:0} kcal"
                )
            }
            ToolPanel("Elevation profile") {
                ToolLineChart(
                    state.paced.map { it.distanceKm to it.elevationM },
                    "Distance (km) / elevation (m)",
                )
            }
            Text(TT("Pacing splits"), style = MaterialTheme.typography.titleLarge)
            state.paced.forEachIndexed { i, cp ->
                ToolPanel {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(cp.name, style = MaterialTheme.typography.titleMedium)
                        Text(etas[i], color = UH.accentInk)
                    }
                    Text("${cp.distanceKm} km · ${cp.elevationM.toInt()}m · ${cp.gradePct}%")
                    Text(
                        "${TT(cp.effort)} · ${cp.targetPace} min/km · ${TT("Split")} ${cp.splitTime}"
                    )
                    Text("${TT("Elapsed")}: ${GoalTime.format(cp.cumulativeTimeMins)}")
                    if (cp.tempC != null) Text("${cp.tempC}°C · ${cp.rainMm?:0}mm")
                    if (cp.afterSunset == true) Text(TT("After sunset"))
                    if (i > 0 && i < state.paced.lastIndex)
                        ToolOptions(
                            "Rest (minutes)",
                            listOf("0", "2", "5", "10", "15", "20"),
                            setOf((rests[i] ?: 0).toString()),
                        ) {
                            rests = rests + (i to it.toInt())
                        }
                }
            }
            Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                OutlinedButton(
                    onClick = {
                        ToolHandoff.fuelingHours = (last.cumulativeTimeMins + rest) / 60
                        onNavigate("nutrition")
                    }
                ) {
                    Text(TT("Plan fueling"))
                }
                OutlinedButton(onClick = { onNavigate("gear") }) { Text(TT("Choose gear")) }
            }
        }
    }
}

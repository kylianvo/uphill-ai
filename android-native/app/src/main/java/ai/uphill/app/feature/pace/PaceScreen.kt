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
    val busy: Boolean = false,
    val error: String? = null,
    val activePlan: ActiveToolPlan? = null,
)

class PaceViewModel(api: APIClient) : ViewModel() {
    private val service = PacingService(api)
    private val plans = ToolPlanService(api)
    private val mutable = MutableStateFlow(PaceState())
    val state = mutable.asStateFlow()
    private var bytes: ByteArray? = null

    init {
        viewModelScope.launch {
            val plan = plans.active()
            mutable.update { it.copy(activePlan = plan) }
        }
    }

    fun parse(data: ByteArray, name: String, interval: Double) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                val result =
                    withContext(Dispatchers.Default) { GpxCourseParser.parse(data, name, interval) }
                bytes = data
                mutable.update { it.copy(gpx = result, busy = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message, busy = false) }
            }
        }
    }

    fun interval(value: Double) {
        val data = bytes ?: return
        parse(data, mutable.value.gpx?.fileName ?: "course.gpx", value)
    }

    fun removeGpx() {
        bytes = null
        mutable.update { it.copy(gpx = null) }
    }

    fun calculate(request: PacingRequest, name: String, distance: Double) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                val paced = service.calculate(request)
                val benchmarks = service.benchmarks(name, distance)
                mutable.update { it.copy(paced = paced, benchmarks = benchmarks, busy = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message, busy = false) }
            }
        }
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
    var name by rememberSaveable { mutableStateOf("") }
    var distance by rememberSaveable { mutableStateOf("50") }
    var gain by rememberSaveable { mutableStateOf("2200") }
    var interval by rememberSaveable { mutableStateOf("5") }
    var target by rememberSaveable { mutableStateOf("330") }
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
    LaunchedEffect(state.activePlan) {
        state.activePlan?.let { p ->
            name = p.raceName
            distance = (p.courseDistanceKm ?: 50.0).toString()
            gain = (p.courseElevationGainM ?: 2200.0).toString()
            p.targetMinutes?.let { target = it.toString() }
        }
        ToolHandoff.pacingTargetMinutes?.let {
            target = it.toString()
            ToolHandoff.pacingTargetMinutes = null
        }
    }
    LaunchedEffect(state.gpx) {
        state.gpx?.let {
            distance = it.totalDistanceKm.toString()
            gain = it.totalElevationGainM.toString()
            if (name.isBlank()) name = it.fileName.removeSuffix(".gpx").replace('_', ' ')
        }
    }
    ToolPage("Pace strategy", onNavigate) {
        ToolPanel("Course setup") {
            RaceSearch(api, name, { name = it }) {
                distance = it.distanceKm.toString()
                it.elevationGainM?.let { gain = it.toString() }
            }
            ToolField("Distance (km)", distance, { distance = it })
            ToolField("Elevation Gain (m)", gain, { gain = it })
            OutlinedButton(
                onClick = {
                    launcher.launch(
                        arrayOf(
                            "application/gpx+xml",
                            "application/xml",
                            "text/xml",
                            "application/octet-stream",
                            "*/*",
                        )
                    )
                }
            ) {
                Text(TT("Import GPX"))
            }
            state.gpx?.let { g ->
                Text("${g.fileName} · ${g.trackpointCount} ${TT("trackpoints")}")
                Text(
                    "${g.totalDistanceKm} km · D+ ${g.totalElevationGainM.toInt()}m · D− ${g.totalElevationLossM.toInt()}m"
                )
                TextButton(onClick = { vm.removeGpx() }) { Text(TT("Remove GPX")) }
            }
            ToolOptions("Split interval (km)", listOf("1", "3", "5", "10"), setOf(interval)) {
                interval = it
                vm.interval(it.toDouble())
            }
        }
        ToolPanel("Pacing controls") {
            ToolField("Target time (minutes)", target, { target = it })
            ToolField("Runner weight (kg)", weight, { weight = it })
            ToolField("Start time (HH:MM)", clock, { clock = it })
            ToolOptions(
                "Split strategy",
                listOf("Even", "Negative", "Positive"),
                setOf(if (bias < 0) "Negative" else if (bias > 0) "Positive" else "Even"),
            ) {
                bias =
                    when (it) {
                        "Negative" -> -.05f
                        "Positive" -> .05f
                        else -> 0f
                    }
            }
            Slider(bias, { bias = it }, valueRange = -0.05f..0.05f)
            Text("${TT("Split bias")}: ${"%.1f".format(bias*100)}%")
            val d = state.gpx?.totalDistanceKm ?: distance.toDoubleOrNull() ?: 0.0
            val g = state.gpx?.totalElevationGainM ?: gain.toDoubleOrNull() ?: 0.0
            if (d > 0) {
                val bounds = PacingCalculator.sliderBoundsMins(d, g)
                Text(
                    "${TT("Suggested range")}: ${GoalTime.format(bounds.first)} – ${GoalTime.format(bounds.second)}"
                )
                Slider(
                    (target.toFloatOrNull() ?: 330f).coerceIn(
                        bounds.first.toFloat(),
                        bounds.second.toFloat(),
                    ),
                    { target = it.toInt().toString() },
                    valueRange = bounds.first.toFloat()..bounds.second.toFloat(),
                )
            }
        }
        ToolError(state.error)
        ToolSubmit(
            "Calculate pacing",
            state.busy,
            (distance.toDoubleOrNull() ?: 0.0) > 0 &&
                (gain.toDoubleOrNull() ?: -1.0) >= 0 &&
                (target.toDoubleOrNull() ?: 0.0) > 0 &&
                (weight.toDoubleOrNull() ?: 0.0) > 0,
        ) {
            val d = state.gpx?.totalDistanceKm ?: distance.toDouble()
            val g = state.gpx?.totalElevationGainM ?: gain.toDouble()
            val checkpoints =
                state.gpx?.checkpoints
                    ?: PacingCalculator.synthesizeCourse(d, g, intervalKm = interval.toDouble())
            vm.calculate(
                PacingRequest(
                    checkpoints,
                    target.toDouble(),
                    splitBias = bias.toDouble(),
                    runnerWeightKg = weight.toDouble(),
                ),
                name,
                d,
            )
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
                            listOf("0", "5", "10", "15"),
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

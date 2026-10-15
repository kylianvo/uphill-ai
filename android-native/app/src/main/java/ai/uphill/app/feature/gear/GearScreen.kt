package ai.uphill.app.feature.gear

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.gear.*
import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class GearState(
    val plan: GearPlan? = null,
    val rotation: ShoeRotation = ShoeRotation(),
    val loaded: Boolean = false,
    val loading: Boolean = false,
    val busy: Boolean = false,
    val saving: Boolean = false,
    val error: String? = null,
    val feedback: Int? = null,
    val activePlan: ActiveToolPlan? = null,
)

class GearViewModel(api: APIClient) : ViewModel() {
    private val service = GearService(api)
    private val plans = ToolPlanService(api)
    private val mutable = MutableStateFlow(GearState())
    val state = mutable.asStateFlow()
    private var saveJob: Job? = null

    init {
        viewModelScope.launch {
            val plan = plans.active()
            mutable.update { it.copy(activePlan = plan) }
        }
        loadRotation()
    }

    fun loadRotation() {
        if (mutable.value.loaded || mutable.value.loading) return
        mutable.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            try {
                val rotation = service.rotation()
                mutable.update { it.copy(rotation = rotation, loaded = true, loading = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(loading = false, error = e.message) }
            }
        }
    }

    fun recommend(params: GearParams) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null, feedback = null) }
            try {
                val plan = service.recommend(params)
                mutable.update { it.copy(plan = plan, busy = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(busy = false, error = e.message) }
            }
        }
    }

    fun rotation(value: ShoeRotation) {
        if (!mutable.value.loaded) return
        mutable.update { it.copy(rotation = value, saving = true) }
        saveJob?.cancel()
        saveJob =
            viewModelScope.launch {
                delay(600)
                try {
                    if (!mutable.value.loaded) return@launch
                    service.save(value)
                    ensureActive()
                    mutable.update { it.copy(saving = false, error = null) }
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    mutable.update { it.copy(saving = false, error = e.message) }
                }
            }
    }

    fun feedback(token: String, value: Int) {
        viewModelScope.launch {
            try {
                service.feedback(token, value)
                mutable.update { it.copy(feedback = value) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            }
        }
    }
}

@Composable
fun GearScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("gear-${user.id}") { GearViewModel(api) }
    val state by vm.state.collectAsState()
    var tab by rememberSaveable { mutableStateOf("Find shoes") }
    var race by rememberSaveable { mutableStateOf("") }
    var distance by rememberSaveable { mutableStateOf("") }
    var surface by rememberSaveable { mutableStateOf("trail") }
    var cushion by rememberSaveable { mutableStateOf("balanced") }
    var width by rememberSaveable { mutableStateOf("normal") }
    var carbon by rememberSaveable { mutableStateOf("unknown") }
    var terrain by rememberSaveable { mutableStateOf(listOf("runnable")) }
    var useCase by rememberSaveable { mutableStateOf("daily training") }
    var brands by rememberSaveable { mutableStateOf("") }
    var budget by rememberSaveable { mutableStateOf("") }
    var notes by rememberSaveable { mutableStateOf("") }
    var assignDistance by rememberSaveable { mutableStateOf("0") }
    var assign by remember { mutableStateOf<ShoeRecommendation?>(null) }
    var slot by rememberSaveable { mutableStateOf("daily") }
    LaunchedEffect(state.activePlan) {
        state.activePlan?.let {
            race = it.raceName
            distance = it.courseDistanceKm?.toString() ?: ""
        }
    }
    ToolPage("Gear Vault", onNavigate) {
        ToolOptions("Gear", listOf("Find shoes", "Shoe rotation"), setOf(tab)) { tab = it }
        ToolError(state.error)
        if (!state.loaded)
            ToolPanel("Shoe rotation") {
                if (state.loading) {
                    LinearProgressIndicator(Modifier.fillMaxWidth())
                    Text(TT("Loading shoe rotation…"))
                } else TextButton(onClick = vm::loadRotation) { Text(TT("Retry")) }
            }
        if (tab == "Find shoes") {
            ToolPanel("Shoe preferences") {
                RaceSearch(api, race, { race = it }) { distance = it.distanceKm.toString() }
                state.activePlan?.let { plan ->
                    TextButton(
                        onClick = {
                            race = plan.raceName
                            distance = plan.courseDistanceKm?.toString().orEmpty()
                        }
                    ) {
                        Text(TT("Use my plan's race"))
                    }
                }
                ToolField("Race distance (km)", distance, { distance = it })
                ToolOptions("Surface", listOf("trail", "road"), setOf(surface)) { surface = it }
                if (surface == "trail")
                    ToolOptions(
                        "Terrain",
                        listOf("runnable", "technical", "muddy", "rocky"),
                        terrain.toSet(),
                    ) {
                        terrain = if (it in terrain) terrain - it else terrain + it
                    }
                else
                    ToolOptions(
                        "Use case",
                        listOf("daily training", "race", "speed work"),
                        setOf(useCase),
                    ) {
                        useCase = it
                    }
                ToolOptions("Cushioning", listOf("plush", "balanced", "firm"), setOf(cushion)) {
                    cushion = it
                }
                ToolOptions("Width", listOf("narrow", "normal", "wide"), setOf(width)) {
                    width = it
                }
                ToolOptions("Carbon Plate", listOf("yes", "no", "unknown"), setOf(carbon)) {
                    carbon = it
                }
                ToolOptions(
                    "Preferred brands",
                    listOf("Salomon", "Hoka", "Nike", "Saucony", "Altra", "Brooks", "Nnormal"),
                    brands.split(',').map { it.trim() }.toSet(),
                ) { brand ->
                    val selected = brands.split(',').map { it.trim() }.filter { it.isNotBlank() }
                    brands =
                        (if (brand in selected) selected - brand else selected + brand)
                            .joinToString(", ")
                }
                ToolField("Preferred brands", brands, { brands = it })
                ToolField("Budget", budget, { budget = it })
                ToolField("Additional context", notes, { notes = it })
            }
            ToolSubmit("Find matching shoes", state.busy) {
                vm.recommend(
                    GearParams(
                        surface,
                        cushion,
                        width,
                        carbon,
                        budget.ifBlank { null },
                        if (surface == "trail") terrain else null,
                        if (surface == "road") useCase else null,
                        brands.ifBlank { null },
                        notes.ifBlank { null },
                        distance.ifBlank { null },
                        race.ifBlank { null },
                        "Age: ${user.age?:"N/A"}, Max HR: ${user.maxHr?:"N/A"}, Resting HR: ${user.restingHr?:"N/A"}, Weekly volume: ${user.currentWeeklyKm?:"N/A"}km",
                        state.activePlan?.gearContext() ?: "None",
                    )
                )
            }
            state.plan?.let { plan ->
                plan.matchedRace?.let { Text("${TT("Matched race")}: ${it.raceName}") }
                if (plan.recommendations.isEmpty()) Text(TT("No recommendations available."))
                plan.recommendations.forEach { shoe ->
                    ToolPanel {
                        Packshot("shoe", shoe.brand, shoe.model, surface)
                        Text(shoe.brand.uppercase(), color = UH.secondary)
                        Text(shoe.model, style = MaterialTheme.typography.titleLarge)
                        Text("${shoe.price} · ${shoe.weight}")
                        Text("Drop ${shoe.drop} · Stack ${shoe.stack} · Lug ${shoe.lugDepth}")
                        Text("${shoe.foamMaterial} · ${shoe.outsoleCompound}")
                        Text("${TT("Pros")}: ${shoe.pros}")
                        Text("${TT("Cons")}: ${shoe.cons}")
                        OutlinedButton(
                            onClick = {
                                assign = shoe
                                assignDistance = "0"
                            },
                            enabled = state.loaded,
                        ) {
                            Text(TT("Assign to rotation"))
                        }
                    }
                }
                ToolPanel("Tips") {
                    plan.tips.forEach { Text("• $it") }
                    ToolFeedback(plan.feedbackToken, state.feedback) { v ->
                        vm.feedback(plan.feedbackToken!!, v)
                    }
                }
            }
        } else if (state.loaded) {
            Text(if (state.saving) TT("Saving rotation…") else TT("Shoe rotation"))
            listOf("daily", "tempo", "race", "trail").forEach { s ->
                RotationSlot(s, state.rotation, { vm.rotation(it) })
            }
        }
    }
    assign?.let { shoe ->
        AlertDialog(
            onDismissRequest = { assign = null },
            title = { Text(TT("Assign to rotation")) },
            text = {
                Column {
                    Text("${shoe.brand} ${shoe.model}")
                    ToolField(
                        "Current distance logged (km)",
                        assignDistance,
                        { assignDistance = it },
                    )
                    ToolOptions("Slot", listOf("daily", "tempo", "race", "trail"), setOf(slot)) {
                        slot = it
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        vm.rotation(
                            state.rotation.setShoe(
                                ShoeItem(slot, shoe.brand, shoe.model, assignDistance.toDouble())
                            )
                        )
                        assign = null
                    },
                    enabled =
                        state.loaded &&
                            assignDistance.toDoubleOrNull()?.let { it.isFinite() && it >= 0 } ==
                                true,
                ) {
                    Text(TT("Save"))
                }
            },
            dismissButton = { TextButton(onClick = { assign = null }) { Text(TT("Cancel")) } },
        )
    }
}

@Composable
private fun RotationSlot(slot: String, rotation: ShoeRotation, onChange: (ShoeRotation) -> Unit) {
    val shoe = rotation.shoe(slot)
    var editing by remember { mutableStateOf(false) }
    var brand by remember(slot, shoe?.brand) { mutableStateOf(shoe?.brand ?: "") }
    var model by remember(slot, shoe?.model) { mutableStateOf(shoe?.model ?: "") }
    var life by
        remember(slot, shoe?.maxDistanceKm) {
            mutableStateOf((shoe?.maxDistanceKm ?: 700.0).toString())
        }
    var distance by
        remember(slot, shoe?.distanceKm) { mutableStateOf((shoe?.distanceKm ?: 0.0).toString()) }
    var notes by remember(slot, shoe?.notes) { mutableStateOf(shoe?.notes ?: "") }
    ToolPanel(slot) {
        if (shoe != null) {
            Packshot("shoe", shoe.brand, shoe.model, slot)
            Text("${shoe.brand} ${shoe.model}", style = MaterialTheme.typography.titleMedium)
            Text(
                "${shoe.distanceKm.toInt()} / ${shoe.maxDistanceKm.toInt()} km · ${(shoe.wearRatio*100).toInt()}%"
            )
            LinearProgressIndicator(
                progress = { shoe.wearRatio.toFloat() },
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.SpaceEvenly) {
                listOf(5.0, 10.0, 15.0, 21.1).forEach { km ->
                    TextButton(onClick = { onChange(rotation.addDistance(slot, km)) }) {
                        Text("+$km")
                    }
                }
            }
            Row {
                TextButton(onClick = { onChange(rotation.setShoe(shoe.copy(isRetired = true))) }) {
                    Text(TT("Retire"))
                }
                TextButton(onClick = { onChange(rotation.remove(slot)) }) { Text(TT("Remove")) }
            }
        } else Text(TT("No shoe assigned to this slot"))
        TextButton(onClick = { editing = !editing }) { Text(TT("Configure shoe")) }
        if (editing) {
            val presets =
                when (slot) {
                    "daily" ->
                        listOf(
                            "Nike" to "Pegasus 41",
                            "Hoka" to "Clifton 10",
                            "Asics" to "Novablast 5",
                            "Brooks" to "Glycerin 23",
                            "Saucony" to "Triumph 23",
                        )
                    "tempo" ->
                        listOf(
                            "Saucony" to "Endorphin Speed 4",
                            "Hoka" to "Mach 7",
                            "Adidas" to "Adizero Boston 13",
                            "New Balance" to "FuelCell Rebel v5",
                            "Asics" to "Superblast 3",
                        )
                    "race" ->
                        listOf(
                            "Nike" to "Vaporfly 3",
                            "Nike" to "Alphafly 3",
                            "Hoka" to "Rocket X 3",
                            "Saucony" to "Endorphin Pro 5",
                            "Asics" to "Metaspeed Sky Tokyo",
                        )
                    else ->
                        listOf(
                            "Salomon" to "S/Lab Genesis",
                            "Hoka" to "Speedgoat 6",
                            "Saucony" to "Peregrine 16",
                            "Brooks" to "Cascadia 19",
                            "Altra" to "Mont Blanc Carbon",
                        )
                }
            presets.forEach { (presetBrand, presetModel) ->
                TextButton(
                    onClick = {
                        brand = presetBrand
                        model = presetModel
                        distance = "0"
                    }
                ) {
                    Text("$presetBrand $presetModel")
                }
            }
            ToolField("Brand", brand, { brand = it })
            ToolField("Model", model, { model = it })
            ToolField("Logged distance (km)", distance, { distance = it })
            ToolField("Expected life (km)", life, { life = it })
            ToolField("Notes", notes, { notes = it })
            ToolSubmit(
                "Save",
                false,
                brand.isNotBlank() &&
                    model.isNotBlank() &&
                    (life.toDoubleOrNull() ?: 0.0) > 0 &&
                    (distance.toDoubleOrNull() ?: -1.0) >= 0,
            ) {
                onChange(
                    rotation.setShoe(
                        ShoeItem(
                            slot,
                            brand,
                            model,
                            distance.toDouble(),
                            life.toDouble(),
                            notes = notes.ifBlank { null },
                        )
                    )
                )
                editing = false
            }
        }
    }
}

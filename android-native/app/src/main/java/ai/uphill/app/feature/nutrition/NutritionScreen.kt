package ai.uphill.app.feature.nutrition

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.goal.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.nutrition.*
import ai.uphill.app.designsystem.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class NutritionState(
    val plan: NutritionPlan? = null,
    val catalog: List<CatalogProduct> = emptyList(),
    val busy: Boolean = false,
    val error: String? = null,
    val feedback: Int? = null,
    val activePlan: ActiveToolPlan? = null,
)

class NutritionViewModel(api: APIClient) : ViewModel() {
    private val service = NutritionService(api)
    private val plans = ToolPlanService(api)
    private val mutable = MutableStateFlow(NutritionState())
    val state = mutable.asStateFlow()

    init {
        viewModelScope.launch {
            val plan = plans.active()
            mutable.update { it.copy(activePlan = plan) }
            try {
                val c = service.catalog()
                mutable.update { it.copy(catalog = c) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            }
        }
    }

    fun calculate(params: NutritionParams) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null, feedback = null) }
            try {
                val p = service.calculate(params)
                mutable.update { it.copy(plan = p, busy = false) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(busy = false, error = e.message) }
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
fun NutritionScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val vm = toolViewModel("nutrition-${user.id}") { NutritionViewModel(api) }
    val state by vm.state.collectAsState()
    var duration by rememberSaveable { mutableStateOf("4") }
    var distance by rememberSaveable { mutableStateOf("") }
    var gain by rememberSaveable { mutableStateOf("") }
    var temp by rememberSaveable { mutableStateOf("moderate") }
    var formats by rememberSaveable { mutableStateOf(listOf("gel")) }
    var level by rememberSaveable { mutableStateOf("Recreational") }
    var brands by rememberSaveable { mutableStateOf("") }
    var carbs by rememberSaveable { mutableStateOf("60") }
    var sodium by rememberSaveable { mutableStateOf("500") }
    var notes by rememberSaveable { mutableStateOf("") }
    var tab by rememberSaveable { mutableStateOf("Timeline") }
    var catalog by rememberSaveable { mutableStateOf(false) }
    var filter by rememberSaveable { mutableStateOf("") }
    LaunchedEffect(state.activePlan) {
        state.activePlan?.let { p ->
            distance = p.courseDistanceKm?.toString() ?: ""
            gain = p.courseElevationGainM?.toString() ?: ""
            p.targetTimeHours?.let { duration = it.toString() }
        }
        ToolHandoff.fuelingHours?.let {
            duration = it.toString()
            ToolHandoff.fuelingHours = null
        }
    }
    ToolPage("Nutrition Lab", onNavigate) {
        ToolPanel("Fueling setup") {
            ToolField("Duration (hours)", duration, { duration = it })
            ToolField("Distance (km)", distance, { distance = it })
            ToolField("Elevation Gain (m)", gain, { gain = it })
            ToolOptions("Temperature", listOf("cool", "moderate", "hot"), setOf(temp)) { temp = it }
            ToolOptions("Formats", listOf("gel", "chews", "drink_mix", "solid"), formats.toSet()) {
                formats = if (it in formats) formats - it else formats + it
            }
            ToolOptions(
                "Athlete level",
                listOf("Recreational", "Intermediate", "Advanced"),
                setOf(level),
            ) {
                level = it
            }
            ToolField("Carbs (g/hour)", carbs, { carbs = it })
            ToolField("Sodium (mg/hour)", sodium, { sodium = it })
            ToolField("Preferred brands", brands, { brands = it })
            ToolField("Additional context", notes, { notes = it })
        }
        ToolError(state.error)
        ToolSubmit(
            "Calculate fueling",
            state.busy,
            (duration.toDoubleOrNull() ?: 0.0) > 0 &&
                (carbs.toDoubleOrNull() ?: -1.0) >= 0 &&
                (sodium.toDoubleOrNull() ?: -1.0) >= 0 &&
                formats.isNotEmpty(),
        ) {
            vm.calculate(
                NutritionParams(
                    distance.toDoubleOrNull(),
                    gain.toDoubleOrNull(),
                    duration.toDouble(),
                    temp,
                    brands.ifBlank { null },
                    carbs.toDouble(),
                    sodium.toDouble(),
                    formats,
                    level,
                    notes.ifBlank { null },
                    "Age: ${user.age?:0}, Max HR: ${user.maxHr?:0}, Resting HR: ${user.restingHr?:0}",
                    state.activePlan?.gearContext(),
                )
            )
        }
        state.plan?.let { plan ->
            ToolPanel("Fueling totals") {
                Text(
                    "${plan.totalCarbs.toInt()}g Carbs · ${plan.totalSodium.toInt()}mg Sodium",
                    style = MaterialTheme.typography.titleLarge,
                )
                Text(
                    "${plan.avgCarbsPerHour.toInt()}g / h · ${plan.avgSodiumPerHour.toInt()}mg / h"
                )
            }
            ToolOptions("Results", listOf("Timeline", "Products", "Tips"), setOf(tab)) { tab = it }
            when (tab) {
                "Timeline" ->
                    plan.hourlyPlan.forEach { entry ->
                        ToolPanel {
                            Text(
                                "${TT("Hour")} ${entry.hour}",
                                color = UH.accentInk,
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Text(entry.action)
                            Text("${entry.carbs.toInt()}g Carbs · ${entry.sodium.toInt()}mg Sodium")
                        }
                    }
                "Products" ->
                    plan.products.forEach { p ->
                        ToolPanel {
                            Packshot("nutrition", p.brand, p.name, p.format)
                            Text(
                                "${p.brand} ${p.name}",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Text("× ${p.totalQuantity}")
                            Text(
                                "${p.carbsPerUnit}g Carbs · ${p.sodiumPerUnit}mg Sodium · ${p.proteinPerUnit}g ${TT("Protein")}"
                            )
                            Text(p.techNotes)
                        }
                    }
                else -> ToolPanel("Tips") { plan.tips.forEach { Text("• $it") } }
            }
            ToolPanel {
                ToolFeedback(plan.feedbackToken, state.feedback) {
                    vm.feedback(plan.feedbackToken!!, it)
                }
            }
        }
        TextButton(onClick = { catalog = !catalog }) { Text(TT("Browse product catalog")) }
        if (catalog) {
            ToolField("Search products", filter, { filter = it })
            state.catalog
                .filter { "${it.brand} ${it.name} ${it.type}".contains(filter, true) }
                .forEach { p ->
                    ToolPanel {
                        Packshot("nutrition", p.brand, p.name, p.type)
                        Text("${p.brand} ${p.name}", style = MaterialTheme.typography.titleMedium)
                        Text(
                            "${p.carbsGrams}g Carbs · ${p.sodiumMg}mg Sodium · ${p.caffeineMg?:0}mg ${TT("Caffeine")}"
                        )
                        p.waterRatioMl?.let { Text("${it.toInt()}ml ${TT("Water")}") }
                        TextButton(
                            onClick = {
                                brands = p.brand
                                formats = listOf(p.type)
                            }
                        ) {
                            Text(TT("Use this brand"))
                        }
                    }
                }
        }
    }
}

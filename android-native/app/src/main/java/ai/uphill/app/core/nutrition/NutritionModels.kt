package ai.uphill.app.core.nutrition

import kotlinx.serialization.Serializable

@Serializable
data class NutritionProduct(
    val brand: String,
    val name: String,
    val totalQuantity: Int = 0,
    val carbsPerUnit: Double = 0.0,
    val sodiumPerUnit: Double = 0.0,
    val proteinPerUnit: Double = 0.0,
    val techNotes: String = "",
) {
    val format: String
        get() {
            val s = "$name $techNotes".lowercase()
            return when {
                listOf("solid", "bar", "waffle").any { s.contains(it) } -> "solid"
                listOf("drink", "mix", "hydration", "scoop").any { s.contains(it) } -> "drink_mix"
                s.contains("chew") -> "chews"
                else -> "gel"
            }
        }
}

@Serializable
data class HourlyEntry(val hour: Int, val action: String, val carbs: Double, val sodium: Double)

@Serializable
data class NutritionPlan(
    val products: List<NutritionProduct> = emptyList(),
    val hourlyPlan: List<HourlyEntry> = emptyList(),
    val tips: List<String> = emptyList(),
    val feedbackToken: String? = null,
) {
    val totalCarbs
        get() = hourlyPlan.sumOf { it.carbs }

    val totalSodium
        get() = hourlyPlan.sumOf { it.sodium }

    val avgCarbsPerHour
        get() = if (hourlyPlan.isEmpty()) 0.0 else totalCarbs / hourlyPlan.size

    val avgSodiumPerHour
        get() = if (hourlyPlan.isEmpty()) 0.0 else totalSodium / hourlyPlan.size
}

@Serializable
data class NutritionParams(
    val distanceKm: Double? = null,
    val elevationGainM: Double? = null,
    val targetTimeHours: Double? = null,
    val weatherTemp: String? = null,
    val preferredBrands: String? = null,
    val targetCarbH: Double? = null,
    val targetSodiumH: Double? = null,
    val preferredFormat: List<String>? = null,
    val athleteLevel: String? = null,
    val additionalContext: String? = null,
    val userProfile: String? = null,
    val activePlanContext: String? = null,
)

@Serializable
data class CatalogProduct(
    val id: Int,
    val brand: String,
    val name: String,
    val type: String,
    val carbsGrams: Double,
    val sodiumMg: Double,
    val caffeineMg: Double? = null,
    val waterRatioMl: Double? = null,
)

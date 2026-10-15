package ai.uphill.app.core.gear

import kotlinx.serialization.Serializable

@Serializable
data class ShoeItem(
    val slot: String,
    val brand: String,
    val model: String,
    val distanceKm: Double = 0.0,
    val maxDistanceKm: Double = 700.0,
    val isRetired: Boolean = false,
    val notes: String? = null,
) {
    val wearRatio
        get() = if (maxDistanceKm > 0) (distanceKm / maxDistanceKm).coerceIn(0.0, 1.0) else 0.0

    val remainingKm
        get() = (maxDistanceKm - distanceKm).coerceAtLeast(0.0)
}

@Serializable
data class ShoeRotation(val shoes: List<ShoeItem> = emptyList()) {
    fun shoe(slot: String) = shoes.firstOrNull { it.slot == slot && !it.isRetired }

    fun setShoe(shoe: ShoeItem) = copy(shoes = shoes.filterNot { it.slot == shoe.slot } + shoe)

    fun remove(slot: String) = copy(shoes = shoes.filterNot { it.slot == slot })

    fun addDistance(slot: String, km: Double) =
        copy(
            shoes =
                shoes.map {
                    if (it.slot == slot && !it.isRetired) it.copy(distanceKm = it.distanceKm + km)
                    else it
                }
        )
}

@Serializable
data class ShoeRecommendation(
    val model: String,
    val brand: String,
    val foamMaterial: String = "",
    val outsoleCompound: String = "",
    val lugDepth: String = "",
    val drop: String = "",
    val stack: String = "",
    val weight: String = "",
    val price: String = "",
    val pros: String = "",
    val cons: String = "",
)

@Serializable
data class GearPlan(
    val recommendations: List<ShoeRecommendation> = emptyList(),
    val tips: List<String> = emptyList(),
    val feedbackToken: String? = null,
    val matchedRace: ai.uphill.app.core.goal.RaceMatch? = null,
)

@Serializable
data class GearParams(
    val surface: String = "trail",
    val cushioning: String = "balanced",
    val width: String = "normal",
    val carbonPlate: String = "unknown",
    val budget: String? = null,
    val terrain: List<String>? = listOf("runnable"),
    val useCase: String? = null,
    val preferredBrands: String? = null,
    val additionalContext: String? = null,
    val raceDistance: String? = null,
    val raceName: String? = null,
    val userProfile: String? = null,
    val activePlanContext: String? = null,
)

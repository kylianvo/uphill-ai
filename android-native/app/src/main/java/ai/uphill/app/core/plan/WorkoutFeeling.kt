package ai.uphill.app.core.plan

/** The iOS five-level feeling scale stores the same backend RPE values. */
enum class WorkoutFeeling(
    val rpe: Int,
    val label: String,
    val subtitle: String,
    val guidance: String,
) {
    VeryLight(
        2,
        "Very Light",
        "Effortless recovery",
        "Effortless recovery or peak freshness — coach will maintain or slightly increase volume to capitalize.",
    ),
    Light(
        4,
        "Light",
        "Fresh & easy",
        "Fresh and well recovered — coach will maintain progressive overload without cutting volume.",
    ),
    Moderate(
        6,
        "Moderate",
        "Normal fatigue",
        "Normal training fatigue — coach will keep balanced volume with steady progression.",
    ),
    Hard(
        8,
        "Hard",
        "Heavy legs / Tired",
        "Heavy legs or elevated fatigue — coach will ease off volume and reduce high-intensity sessions.",
    ),
    MaxEffort(
        10,
        "Max Effort",
        "Exhausted / Deload",
        "Deep exhaustion or overreaching risk — coach will schedule an active recovery deload week.",
    );

    companion object {
        fun from(rpe: Int?): WorkoutFeeling? =
            rpe?.let { value -> entries.firstOrNull { value <= it.rpe } ?: MaxEffort }
    }
}

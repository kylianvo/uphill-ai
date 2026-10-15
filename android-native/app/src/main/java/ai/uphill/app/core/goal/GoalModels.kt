package ai.uphill.app.core.goal

import kotlinx.serialization.Serializable

@Serializable
data class PercentileSet(
    val p5: String? = null,
    val p10: String? = null,
    val p25: String? = null,
    val p50: String? = null,
    val p75: String? = null,
    val p90: String? = null,
)

@Serializable
data class RaceBenchmark(
    val year: Int,
    val finishers: Int? = null,
    val finishersMen: Int? = null,
    val finishersWomen: Int? = null,
    val winnerTime: String? = null,
    val winnerTimeWomen: String? = null,
    val conditionsNote: String? = null,
    val percentiles: Map<String, PercentileSet>? = null,
    val topTimes: Map<String, Map<String, String>>? = null,
)

@Serializable data class GoalTiers(val a: Double, val b: Double, val c: Double)

@Serializable
data class GoalSource(val key: String, val label: String, val included: Boolean = true)

@Serializable data class GoalAthleteContext(val easyPaceMinKm: Double? = null)

@Serializable data class GoalRaceContext(val profileSource: String? = null)

@Serializable
data class GoalContext(val athlete: GoalAthleteContext? = null, val race: GoalRaceContext? = null)

@Serializable
data class GoalAssessmentResponse(
    val raceName: String? = null,
    val distanceKm: Double,
    val elevationGainM: Double? = null,
    val goals: GoalTiers? = null,
    val confidence: String? = null,
    val reasoning: List<String>? = null,
    val sources: List<GoalSource>? = null,
    val benchmarks: List<RaceBenchmark>? = null,
    val context: GoalContext? = null,
    val missing: List<String>? = null,
)

@Serializable
data class GoalReference(
    val raceName: String? = null,
    val distanceKm: Double,
    val elevationGainM: Double? = null,
    val time: String,
)

@Serializable
data class GoalRequest(
    val raceName: String? = null,
    val distanceKm: Double? = null,
    val elevationGainM: Double? = null,
    val raceDate: String? = null,
    val exclude: List<String> = emptyList(),
    val reference: GoalReference? = null,
    val lang: String = "en",
)

@Serializable
data class RaceDistance(
    val label: String? = null,
    val distanceKm: Double,
    val elevationGainM: Double? = null,
)

@Serializable
data class RaceMatch(
    val raceName: String,
    val distanceLabel: String? = null,
    val distanceKm: Double? = null,
    val elevationGainM: Double? = null,
    val distances: List<RaceDistance>? = null,
)

@Serializable
data class RaceMatchResponse(
    val matched: Boolean,
    val autoApply: Boolean? = null,
    val match: RaceMatch? = null,
    val candidates: List<RaceMatch>? = null,
)

object GoalTime {
    fun parseTime(raw: String): Double? {
        val p = raw.trim().split(":").map { it.toDoubleOrNull() ?: return null }
        return when (p.size) {
            2 -> p[0] * 60 + p[1]
            3 -> p[0] * 60 + p[1] + p[2] / 60
            else -> null
        }
    }

    fun parsePace(raw: String): Double? {
        val p = raw.trim().split(":")
        return if (p.size >= 2)
            p[0].toDoubleOrNull()?.let { a -> p[1].toDoubleOrNull()?.let { a + it / 60 } }
        else raw.trim().toDoubleOrNull()?.takeIf { it > 0 }
    }

    fun format(mins: Double): String {
        val m = (mins * 60).toInt() / 60
        return "%d:%02d".format(m / 60, m % 60)
    }
}

data class FieldAnchor(val minutes: Double, val percentile: Double, val label: String)

object FieldCurve {
    fun anchors(b: RaceBenchmark, gender: String): List<FieldAnchor> {
        val n =
            when (gender) {
                "men" -> b.finishersMen
                "women" -> b.finishersWomen
                else -> b.finishers
            } ?: b.finishers
        val winner = if (gender == "women") b.winnerTimeWomen ?: b.winnerTime else b.winnerTime
        val raw = mutableListOf<FieldAnchor>()
        winner?.let {
            GoalTime.parseTime(it)?.let { m ->
                raw += FieldAnchor(m, if (n != null && n > 0) 100.0 / n else 0.0, "Winner")
            }
        }
        if (n != null && n > 0)
            b.topTimes?.get(gender)?.forEach { (key, time) ->
                val rank = key.removePrefix("top").toIntOrNull()
                if (rank != null && rank > 1)
                    GoalTime.parseTime(time)?.let {
                        raw += FieldAnchor(it, 100.0 * rank / n, "Top $rank")
                    }
            }
        val p = b.percentiles?.get(gender) ?: b.percentiles?.get("overall")
        listOf(
                p?.p5 to 5.0,
                p?.p10 to 10.0,
                p?.p25 to 25.0,
                p?.p50 to 50.0,
                p?.p75 to 75.0,
                p?.p90 to 90.0,
            )
            .forEach { (time, pct) ->
                time?.let {
                    GoalTime.parseTime(it)?.let { m ->
                        raw += FieldAnchor(m, pct, "P${pct.toInt()}")
                    }
                }
            }
        val result = mutableListOf<FieldAnchor>()
        raw.sortedBy { it.percentile }
            .forEach {
                if (
                    result.isEmpty() ||
                        (it.minutes > result.last().minutes &&
                            it.percentile > result.last().percentile)
                )
                    result += it
            }
        return result
    }

    fun percentile(mins: Double, points: List<FieldAnchor>): Double {
        if (points.isEmpty()) return 50.0
        if (mins <= points.first().minutes) return points.first().percentile
        if (mins >= points.last().minutes) return (points.last().percentile + 5).coerceAtMost(99.0)
        points.zipWithNext().forEach { (a, b) ->
            if (mins in a.minutes..b.minutes)
                return a.percentile +
                    (mins - a.minutes) / (b.minutes - a.minutes) * (b.percentile - a.percentile)
        }
        return 50.0
    }
}

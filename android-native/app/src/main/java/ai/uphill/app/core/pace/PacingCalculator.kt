package ai.uphill.app.core.pace

import ai.uphill.app.core.goal.*
import kotlin.math.*

object PacingCalculator {
    private fun minetti(grade: Double): Double {
        val i = grade.coerceIn(-.45, .45)
        return 155.4 * i.pow(5) - 30.4 * i.pow(4) - 43.3 * i.pow(3) +
            46.3 * i.pow(2) +
            19.5 * i +
            3.6
    }

    fun gradePaceMultiplier(grade: Double): Double {
        val g = min(.30, grade)
        val ratio = minetti(g) / 3.6
        return if (g < 0) 1 + (ratio - 1) * .4 else ratio
    }

    fun sliderBoundsMins(distanceKm: Double, gainM: Double): Pair<Double, Double> {
        val eq = distanceKm + gainM / 100
        val lo = max(30.0, eq * 3.8)
        return lo to max(lo + 60, eq * 13)
    }

    fun synthesizeCourse(
        distanceKm: Double,
        gainM: Double,
        lossM: Double = gainM,
        baseElevationM: Double = 0.0,
        intervalKm: Double = 1.0,
    ): List<CourseCheckpoint> {
        require(distanceKm > 0 && intervalKm > 0)
        val n = max(1, ceil(distanceKm / intervalKm).toInt())
        val cps = mutableListOf(CourseCheckpoint("Start", 0.0, baseElevationM, 0.0, 0.0))
        var elevation = baseElevationM
        for (i in 1..n) {
            val dist = min(i * intervalKm * 1000, distanceKm * 1000)
            val fraction = (dist - cps.last().distanceMeters) / 1000
            val gain = gainM / distanceKm * fraction
            val loss = lossM / distanceKm * fraction
            elevation += gain - loss
            val bump = sin(i.toDouble() / n * PI) * min(gainM, lossM) * .25
            cps +=
                CourseCheckpoint(
                    "KM ${(dist/1000).roundToInt()}",
                    dist,
                    round(elevation + bump),
                    gain,
                    loss,
                )
        }
        return cps
    }

    fun calculate(
        checkpoints: List<CourseCheckpoint>,
        targetTimeMins: Double? = null,
        targetFlatPaceMinKm: Double? = null,
        splitBias: Double = 0.0,
        runnerWeightKg: Double = 68.0,
    ): List<PacedCheckpoint> {
        if (checkpoints.size < 2) return emptyList()
        val distance = checkpoints.last().distanceMeters / 1000
        val gain = checkpoints.sumOf { it.segmentGainMeters }
        val base =
            targetFlatPaceMinKm
                ?: targetTimeMins?.let {
                    (it / max(1.0, distance + gain / 100)).coerceIn(2.5, 14.0)
                }
                ?: 5.5
        var time = 0.0
        var eq = 0.0
        var kcal = 0.0
        return checkpoints.mapIndexed { index, cp ->
            if (index == 0)
                PacedCheckpoint(
                    cp.name,
                    0.0,
                    cp.elevationMeters,
                    "—",
                    "0:00",
                    0.0,
                    0.0,
                    0.0,
                    "run",
                    energyKcal = 0,
                )
            else {
                val dm = cp.distanceMeters - checkpoints[index - 1].distanceMeters
                val dk = dm / 1000
                val grade = if (dm > 0) (cp.segmentGainMeters - cp.segmentLossMeters) / dm else 0.0
                val gm = gradePaceMultiplier(grade)
                val fatigue = 1 + .0015 * max(0.0, eq - 15)
                val progress = if (distance > 0) cp.distanceMeters / 1000 / distance else .5
                val pace = base * gm * fatigue * (1 + (progress - .5) * 2 * splitBias)
                val segment = pace * dk
                time += segment
                eq += dk * gm
                kcal += minetti(grade) * dm * runnerWeightKg / 4184
                PacedCheckpoint(
                    cp.name,
                    round(cp.distanceMeters / 1000 * 10) / 10,
                    cp.elevationMeters,
                    formatPace(pace),
                    formatMinutes(segment),
                    time,
                    eq,
                    round(grade * 1000) / 10,
                    if (grade >= .2) "hike" else "run",
                    energyKcal = kcal.toInt(),
                )
            }
        }
    }

    fun clockEtas(
        paced: List<PacedCheckpoint>,
        rest: Map<Int, Int> = emptyMap(),
        startClock: String = "05:00",
    ): List<String> {
        val p = startClock.split(":").mapNotNull { it.toIntOrNull() }
        val start = if (p.size >= 2) p[0] * 60 + p[1] else 300
        var accumulated = 0
        return paced.mapIndexed { index, cp ->
            val arrival = cp.cumulativeTimeMins + accumulated
            accumulated += rest[index] ?: 0
            val clock = (start + arrival).toInt() % (24 * 60)
            "%02d:%02d".format(clock / 60, clock % 60)
        }
    }

    fun formatPace(mins: Double): String {
        val seconds = (mins * 60).toInt()
        return "%d:%02d".format(seconds / 60, seconds % 60)
    }

    fun formatMinutes(mins: Double): String {
        val m = (mins * 60).toInt() / 60
        return if (m >= 60) "%d:%02d".format(m / 60, m % 60) else "$m min"
    }
}

data class BenchmarkMarker(val label: String, val minutes: Double) {
    companion object {
        fun markers(benchmarks: List<RaceBenchmark>, year: Int? = null): List<BenchmarkMarker> {
            val editions = benchmarks.filter { year == null || it.year == year }
            fun avg(pick: (RaceBenchmark) -> String?): Double? {
                val values = editions.mapNotNull(pick).mapNotNull(GoalTime::parseTime)
                return values.takeIf { it.isNotEmpty() }?.average()
            }
            return listOf(
                    "Winner" to avg { it.winnerTime },
                    "Winner (F)" to avg { it.winnerTimeWomen },
                    "P10" to avg { it.percentiles?.get("overall")?.p10 },
                    "P25" to avg { it.percentiles?.get("overall")?.p25 },
                    "P50" to avg { it.percentiles?.get("overall")?.p50 },
                    "P75" to avg { it.percentiles?.get("overall")?.p75 },
                    "P90" to avg { it.percentiles?.get("overall")?.p90 },
                )
                .mapNotNull { (label, m) -> m?.let { BenchmarkMarker(label, it) } }
                .sortedBy { it.minutes }
        }
    }
}

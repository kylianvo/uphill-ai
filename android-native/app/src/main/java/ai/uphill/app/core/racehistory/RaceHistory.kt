package ai.uphill.app.core.racehistory

import ai.uphill.app.core.networking.*
import java.net.URI
import java.time.LocalDate
import java.util.Locale
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable
data class RaceClaim(
    val id: Int,
    val source: String,
    val displayName: String,
    val syncStatus: String,
    val syncError: String? = null,
    val verified: Boolean = false,
    val verificationMethods: List<String> = emptyList(),
    val meta: JsonObject? = null,
)

@Serializable
data class RaceResult(
    val id: Int,
    val source: String = "manual",
    val raceName: String,
    val raceDate: String,
    val distanceKm: Double,
    val discipline: String = "trail",
    val claimId: Int? = null,
    val elevationGainM: Double? = null,
    val finishTimeSec: Int? = null,
    val isDnf: Boolean = false,
    val bib: String? = null,
    val selected: Boolean = true,
    val hidden: Boolean = false,
    val userNote: String? = null,
    val verified: Boolean = false,
    val verificationMethods: List<String> = emptyList(),
    val rankOverall: Int? = null,
    val totalOverall: Int? = null,
    val location: String? = null,
    val resultUrl: String? = null,
    val rankGender: Int? = null,
    val totalGender: Int? = null,
    val rankAgeGroup: Int? = null,
    val totalAgeGroup: Int? = null,
) {
    val duration: String
        get() = if (isDnf) "DNF" else finishTimeSec?.let(::raceDuration) ?: "—"
}

fun raceDuration(seconds: Int): String =
    if (seconds >= 3600)
        String.format(Locale.ROOT, "%d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60)
    else String.format(Locale.ROOT, "%02d:%02d", seconds / 60, seconds % 60)

@Serializable
data class PRTime(
    val timeSec: Int,
    val stale: Boolean = false,
    val resultId: Int? = null,
    val date: String? = null,
)

@Serializable
data class HistorySummary(
    val trailFinishes: Int = 0,
    val trailDnfs: Int = 0,
    val ultras: Int = 0,
    val longestFinish: RaceResult? = null,
    val roadHmPr: PRTime? = null,
    val roadFmPr: PRTime? = null,
    val roadPrs: Map<String, PRTime?>? = null,
)

@Serializable
data class RaceHistoryResponse(
    val claims: List<RaceClaim> = emptyList(),
    val results: List<RaceResult> = emptyList(),
    val summary: HistorySummary = HistorySummary(),
)

@Serializable
data class RaceCandidate(
    val externalId: String,
    val displayName: String,
    val ageGroup: String? = null,
    val index: Double? = null,
)

@Serializable
data class ManualResultPayload(
    val raceName: String,
    val raceDate: String,
    val discipline: String,
    val distanceKm: Double,
    val elevationGainM: Double? = null,
    val finishTimeSec: Int? = null,
    val isDnf: Boolean = false,
    val rankOverall: Int? = null,
    val totalOverall: Int? = null,
    val location: String? = null,
    val resultUrl: String? = null,
    val rankGender: Int? = null,
    val totalGender: Int? = null,
    val rankAgeGroup: Int? = null,
    val totalAgeGroup: Int? = null,
    val bib: String? = null,
    val userNote: String? = null,
) {
    fun patch(): JsonObject = JSONCoding.json.encodeToJsonElement(this).jsonObject
}

fun safeRaceResultURL(value: String?): Boolean =
    runCatching {
            val u = URI(value ?: "")
            u.scheme?.lowercase() in listOf("http", "https") &&
                !u.host.isNullOrBlank() &&
                u.userInfo == null
        }
        .getOrDefault(false)

data class ManualRaceDraft(
    val raceName: String = "",
    val raceDate: String = LocalDate.now().toString(),
    val discipline: String = "trail",
    val distance: String = "",
    val elevation: String = "",
    val duration: String = "",
    val isDnf: Boolean = false,
    val location: String = "",
    val bib: String = "",
    val resultUrl: String = "",
    val userNote: String = "",
    val rankOverall: String = "",
    val totalOverall: String = "",
    val rankGender: String = "",
    val totalGender: String = "",
    val rankAgeGroup: String = "",
    val totalAgeGroup: String = "",
) {
    fun payload(): ManualResultPayload {
        fun text(v: String, max: Int): String? {
            require(v.trim().length <= max) { "Text is too long." }
            return v.trim().ifEmpty { null }
        }
        fun rank(v: String): Int? {
            if (v.isBlank()) return null
            return v.trim().toIntOrNull()?.also {
                require(it > 0) { "Ranks must be positive whole numbers." }
            } ?: error("Ranks must be positive whole numbers.")
        }
        fun pair(r: String, t: String): Pair<Int?, Int?> {
            val a = rank(r)
            val b = rank(t)
            require(a == null || b == null || a <= b) { "Rank cannot exceed finishers." }
            return a to b
        }
        val name = text(raceName, 200)
        require(name != null && discipline in listOf("trail", "road")) {
            "Enter a race name and discipline."
        }
        require(runCatching { LocalDate.parse(raceDate) }.isSuccess) { "Enter date as yyyy-mm-dd." }
        val km = distance.trim().toDoubleOrNull()
        require(km != null && km.isFinite() && km > 0 && km <= 1000) {
            "Enter a distance between 0 and 1,000 km."
        }
        val gain =
            if (elevation.isBlank()) null
            else
                elevation.trim().toDoubleOrNull().also {
                    require(it != null && it.isFinite() && it >= 0) {
                        "Elevation must be zero or positive."
                    }
                }
        val seconds =
            if (isDnf) null
            else {
                val p = duration.trim().split(':')
                val n = p.map { it.toIntOrNull() }
                require(
                    p.size in 2..3 &&
                        n.all { it != null && it >= 0 } &&
                        n.last()!! < 60 &&
                        (p.size == 2 || n[1]!! < 60) &&
                        n[0]!! <= 9999
                ) {
                    "Enter finish time as h:mm:ss or mm:ss."
                }
                val s =
                    if (n.size == 3) n[0]!! * 3600 + n[1]!! * 60 + n[2]!! else n[0]!! * 60 + n[1]!!
                require(s > 0) { "Finish time must be greater than zero." }
                s
            }
        val url = text(resultUrl, 2048)
        require(url == null || safeRaceResultURL(url)) {
            "Use an http or https link without credentials."
        }
        val o = pair(rankOverall, totalOverall)
        val g = pair(rankGender, totalGender)
        val a = pair(rankAgeGroup, totalAgeGroup)
        return ManualResultPayload(
            name!!,
            raceDate,
            discipline,
            km!!,
            gain,
            seconds,
            isDnf,
            o.first,
            o.second,
            text(location, 200),
            url,
            g.first,
            g.second,
            a.first,
            a.second,
            text(bib, 100),
            text(userNote, 2000),
        )
    }

    companion object {
        fun from(r: RaceResult) =
            ManualRaceDraft(
                r.raceName,
                r.raceDate,
                r.discipline,
                r.distanceKm.toString(),
                r.elevationGainM?.toString().orEmpty(),
                r.finishTimeSec?.let(::raceDuration).orEmpty(),
                r.isDnf,
                r.location.orEmpty(),
                r.bib.orEmpty(),
                r.resultUrl.orEmpty(),
                r.userNote.orEmpty(),
                r.rankOverall?.toString().orEmpty(),
                r.totalOverall?.toString().orEmpty(),
                r.rankGender?.toString().orEmpty(),
                r.totalGender?.toString().orEmpty(),
                r.rankAgeGroup?.toString().orEmpty(),
                r.totalAgeGroup?.toString().orEmpty(),
            )
    }
}

@Serializable
data class RaceDetailResponse(
    val result: RaceResult,
    val performance: RacePerformance,
    val previousFinish: PreviousRaceFinish? = null,
    val courseContext: RaceCourseContext,
    val historicalField: JsonObject? = null,
)

@Serializable
data class RacePerformance(
    val overallTopPct: Double? = null,
    val genderTopPct: Double? = null,
    val ageGroupTopPct: Double? = null,
    val averagePaceSecKm: Double? = null,
    val roadPbKey: String? = null,
)

@Serializable
data class PreviousRaceFinish(
    val resultId: Int,
    val raceDate: String,
    val finishTimeSec: Int,
    val deltaSec: Int,
)

@Serializable
data class RaceCourseContext(
    val status: String,
    val course: RaceCourse? = null,
    val candidates: List<RaceCourseCandidate> = emptyList(),
    val message: String? = null,
)

@Serializable
data class RaceCourseCandidate(val id: Int, val raceName: String, val distanceLabel: String)

@Serializable
data class RaceCourse(
    val id: Int,
    val raceName: String,
    val distanceLabel: String,
    val distanceKm: Double,
    val elevationGainM: Double? = null,
    val location: String? = null,
    val terrain: List<String> = emptyList(),
    val keyClimbs: List<String> = emptyList(),
    val climate: JsonObject = JsonObject(emptyMap()),
    val runnerReviews: List<String> = emptyList(),
    val sourceLabel: String? = null,
    val sourceUrls: List<String> = emptyList(),
    val verifiedAt: String? = null,
    val editionYear: Int? = null,
    val editionStatus: String = "unknown",
)

class RaceHistoryService(private val api: APIClient) {
    suspend fun history(): RaceHistoryResponse = api.send(Endpoint("GET", "/api/race-history"))

    suspend fun athleteHistory(id: Int): RaceHistoryResponse =
        api.send(Endpoint("GET", "/api/coaching/athletes/$id/race-history"))

    suspend fun detail(id: Int, courseId: Int? = null, athleteId: Int? = null): RaceDetailResponse =
        api.send(
            Endpoint(
                "GET",
                (athleteId?.let { "/api/coaching/athletes/$it/race-history" }
                    ?: "/api/race-history") + "/results/$id/detail",
                query = courseId?.let { mapOf("course_id" to "$it") } ?: emptyMap(),
            )
        )

    suspend fun search(source: String, query: String): List<RaceCandidate> =
        api.send(
            Endpoint(
                "GET",
                "/api/race-history/search",
                query = mapOf("source" to source, "q" to query),
            )
        )

    suspend fun claim(source: String, externalId: String) {
        api.text(
            Endpoint(
                "POST",
                "/api/race-history/claims",
                buildJsonObject {
                    put("source", source)
                    put("external_id", externalId)
                },
            )
        )
    }

    suspend fun deleteClaim(id: Int) {
        api.text(Endpoint("DELETE", "/api/race-history/claims/$id"))
    }

    suspend fun verifyBib(id: Int, bib: String) {
        require(bib.isNotBlank())
        api.text(
            Endpoint(
                "POST",
                "/api/race-history/claims/$id/verify-bib",
                buildJsonObject { put("bib", bib.trim()) },
            )
        )
    }

    suspend fun refreshClaim(id: Int) {
        api.text(Endpoint("POST", "/api/race-history/claims/$id/refresh"))
    }

    suspend fun add(p: ManualResultPayload): RaceResult =
        api.send(
            Endpoint("POST", "/api/race-history/results", JSONCoding.json.encodeToJsonElement(p))
        )

    suspend fun update(id: Int, changes: JsonObject): RaceResult =
        api.send(Endpoint("PATCH", "/api/race-history/results/$id", changes))

    suspend fun delete(id: Int) {
        api.text(Endpoint("DELETE", "/api/race-history/results/$id"))
    }
}

enum class DistanceCategory(val label: String) {
    FIVE_K("5km"),
    TEN_K("10km"),
    HALF("HM"),
    MARATHON("FM"),
    FIFTY_K("50km"),
    HUNDRED_K("100km"),
    HUNDRED_MILES("100 miles");

    companion object {
        fun match(km: Double): DistanceCategory? =
            when {
                km >= 4 && km < 7.5 -> FIVE_K
                km >= 7.5 && km < 15 -> TEN_K
                km >= 18 && km < 30 -> HALF
                km >= 38 && km < 48 -> MARATHON
                km >= 48 && km < 75 -> FIFTY_K
                km >= 85 && km < 130 -> HUNDRED_K
                km >= 140 -> HUNDRED_MILES
                else -> null
            }
    }
}

data class DistanceBadge(val category: DistanceCategory, val result: RaceResult?) {
    val unlocked
        get() = result != null

    companion object {
        fun derive(results: List<RaceResult>): List<DistanceBadge> {
            val usable = results.filter { it.selected && !it.isDnf && (it.finishTimeSec ?: 0) > 0 }
            return DistanceCategory.entries.map { c ->
                DistanceBadge(
                    c,
                    usable
                        .filter { DistanceCategory.match(it.distanceKm) == c }
                        .sortedWith(
                            compareByDescending<RaceResult> { it.raceDate }.thenBy { it.id }
                        )
                        .firstOrNull(),
                )
            }
        }
    }
}

package ai.uphill.app.feature.onboarding

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.generation.*
import ai.uphill.app.core.models.Weekday
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.plan.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlin.math.round
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

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
    val distances: List<RaceDistance> = emptyList(),
)

@Serializable
private data class RaceMatchResponse(
    val matched: Boolean,
    val autoApply: Boolean? = null,
    val match: RaceMatch? = null,
    val candidates: List<RaceMatch> = emptyList(),
)

@Serializable private data class WatchVolume(val weeklyKm: Double, val weeklyKmSource: String)

data class SetupState(
    val draft: PlanSetupDraft,
    val index: Int = 0,
    val issues: List<String> = emptyList(),
    val submitting: Boolean = false,
    val error: String? = null,
    val zoneWarning: Boolean = false,
    val candidates: List<RaceMatch> = emptyList(),
    val selectedRace: RaceMatch? = null,
    val goalAssessment: GoalAssessment? = null,
    val assessmentBusy: Boolean = false,
    val watchKm: Double? = null,
    val started: Boolean = false,
)

class PlanSetupViewModel(
    private val api: APIClient,
    user: User,
    private var lang: String,
    private val generation: GenerationCenter,
    val onboarding: Boolean = true,
) : ViewModel() {
    private val mutable = MutableStateFlow(SetupState(PlanSetupDraft.from(user)))
    val state = mutable.asStateFlow()

    fun changeLanguage(value: String) {
        lang = value
    }

    private var searchJob: Job? = null
    private var editedVolume = false
    private val service = GenerationService(api)

    fun steps() = SetupStep.steps(mutable.value.draft.goal, onboarding)

    fun step() = steps()[mutable.value.index.coerceAtMost(steps().lastIndex)]

    fun edit(block: (PlanSetupDraft) -> Unit) {
        val draft = mutable.value.draft.copy()
        block(draft)
        mutable.value = mutable.value.copy(draft = draft, issues = emptyList())
    }

    fun selectGoal(goal: SetupGoal, terrain: String = "trail") {
        edit {
            it.goal = goal
            it.terrain = terrain
            if (goal.isEvent && it.raceDate == null)
                it.raceDate = java.time.LocalDate.now().plusDays(14)
        }
        next()
    }

    fun next(skipZoneWarning: Boolean = false) {
        val issues = mutable.value.draft.issues(step())
        if (issues.isNotEmpty()) {
            mutable.value = mutable.value.copy(issues = issues)
            return
        }
        if (
            step() == SetupStep.TrainingZones &&
                mutable.value.draft.needsZoneWarning &&
                !skipZoneWarning
        ) {
            mutable.value = mutable.value.copy(zoneWarning = true)
            return
        }
        mutable.value =
            mutable.value.copy(
                index = (mutable.value.index + 1).coerceAtMost(steps().lastIndex),
                zoneWarning = false,
                issues = emptyList(),
            )
    }

    fun back() {
        mutable.value =
            mutable.value.copy(
                index = (mutable.value.index - 1).coerceAtLeast(0),
                issues = emptyList(),
            )
    }

    fun reopenReview() {
        mutable.value = mutable.value.copy(started = false, index = steps().lastIndex, error = null)
        generation.clearOutcome()
    }

    fun weeklyKm(value: Double?) {
        editedVolume = true
        edit {
            it.currentWeeklyKm = value
            it.weeklyKmFromWatch = value != null && value == mutable.value.watchKm
        }
    }

    fun setRunDays(count: Int) {
        edit {
            it.daysPerWeek = count
            it.preferredDays = PlanSetupDraft.defaultDays(count)
            it.doubleSessionDays = it.doubleSessionDays.intersect(it.preferredDays)
            if (it.longRunDay !in it.preferredDays) it.longRunDay = it.orderedDays.last()
        }
    }

    fun toggleDay(day: Weekday) {
        edit {
            it.preferredDays =
                if (day in it.preferredDays) it.preferredDays - day else it.preferredDays + day
            it.doubleSessionDays = it.doubleSessionDays.intersect(it.preferredDays)
            if (it.preferredDays.size in 3..7) it.daysPerWeek = it.preferredDays.size
            if (it.longRunDay !in it.preferredDays && it.preferredDays.isNotEmpty())
                it.longRunDay = it.orderedDays.last()
        }
    }

    fun refreshFitness() {
        viewModelScope.launch {
            runCatching { api.send<WatchVolume>(Endpoint("GET", "/api/auth/fitness-snapshot")) }
                .getOrNull()
                ?.takeIf { it.weeklyKmSource == "watch" || it.weeklyKmSource == "coros" }
                ?.let { volume ->
                    val km = round(volume.weeklyKm)
                    mutable.value = mutable.value.copy(watchKm = km)
                    if (!editedVolume)
                        edit {
                            it.currentWeeklyKm = km
                            it.weeklyKmFromWatch = true
                        }
                }
        }
    }

    fun raceName(name: String) {
        edit { it.raceName = name }
        searchJob?.cancel()
        mutable.value = mutable.value.copy(candidates = emptyList(), selectedRace = null)
        if (name.trim().length < 3) return
        val initialKm = mutable.value.draft.distanceKm
        val initialGain = mutable.value.draft.elevationGainM
        searchJob =
            viewModelScope.launch {
                delay(500)
                runCatching {
                        api.send<RaceMatchResponse>(
                            Endpoint(
                                "GET",
                                "/api/kb/match-race",
                                query = mapOf("name" to name.trim()),
                                requiresAuth = false,
                            )
                        )
                    }
                    .getOrNull()
                    ?.let { response ->
                        if (mutable.value.draft.raceName.trim() != name.trim()) return@let
                        if (response.autoApply == true && response.match != null) {
                            val typedKm = mutable.value.draft.distanceKm
                            val typedGain = mutable.value.draft.elevationGainM
                            selectRace(response.match)
                            edit {
                                if (typedKm != initialKm) {
                                    it.distanceKm = typedKm
                                    it.distanceLabel = null
                                }
                                if (typedGain != initialGain) it.elevationGainM = typedGain
                            }
                        } else mutable.value = mutable.value.copy(candidates = response.candidates)
                    }
            }
    }

    fun selectRace(race: RaceMatch) {
        edit {
            it.raceName = race.raceName
            if (race.distanceKm != null) {
                it.distanceKm = race.distanceKm
                it.elevationGainM = race.elevationGainM
                it.distanceLabel = race.distanceLabel
            } else if (race.distances.size == 1) {
                it.distanceKm = race.distances[0].distanceKm
                it.elevationGainM = race.distances[0].elevationGainM
                it.distanceLabel = race.distances[0].label
            }
        }
        mutable.value = mutable.value.copy(selectedRace = race, candidates = emptyList())
    }

    fun assess() {
        viewModelScope.launch {
            mutable.value = mutable.value.copy(assessmentBusy = true, error = null)
            try {
                val draft = mutable.value.draft
                val body = buildJsonObject {
                    put("lang", lang)
                    if (draft.raceName.isNotBlank()) put("race_name", draft.raceName)
                    draft.distanceKm?.let { put("distance_km", it) }
                    draft.elevationGainM?.let { put("elevation_gain_m", it) }
                    draft.raceDate?.let { put("race_date", it.toString()) }
                    put("exclude", JsonArray(emptyList()))
                }
                val result = api.send<GoalAssessment>(Endpoint("POST", "/api/goal/assess", body))
                mutable.value = mutable.value.copy(goalAssessment = result)
            } catch (e: Exception) {
                mutable.value = mutable.value.copy(error = e.message)
            } finally {
                mutable.value = mutable.value.copy(assessmentBusy = false)
            }
        }
    }

    fun submit(skipPlan: Boolean = false, onSaved: () -> Unit = {}) {
        if (mutable.value.submitting) return
        val checked =
            if (skipPlan)
                listOf(SetupStep.Goal, SetupStep.Schedule, SetupStep.Body, SetupStep.TrainingZones)
            else steps()
        checked
            .firstOrNull { mutable.value.draft.issues(it).isNotEmpty() }
            ?.let { step ->
                mutable.value =
                    mutable.value.copy(
                        index = steps().indexOf(step).coerceAtLeast(0),
                        issues = mutable.value.draft.issues(step),
                    )
                return
            }
        viewModelScope.launch {
            mutable.value = mutable.value.copy(submitting = true, error = null)
            try {
                val draft = mutable.value.draft
                val body = draft.body(lang, onboarding, skipPlan)
                val id =
                    if (onboarding) service.onboarding(body).jobId else service.generate(body).jobId
                if (skipPlan) {
                    onSaved()
                    return@launch
                }
                requireNotNull(id) { "We couldn't start building your plan. Please try again." }
                generation.track(
                    "newPlan",
                    id,
                    listOf(
                        draft.goal?.title.orEmpty(),
                        "${draft.daysPerWeek} / week",
                        "${draft.currentWeeklyKm ?: 0} km / week",
                    ),
                )
                mutable.value = mutable.value.copy(started = true)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.value = mutable.value.copy(error = e.message)
            } finally {
                mutable.value = mutable.value.copy(submitting = false)
            }
        }
    }
}

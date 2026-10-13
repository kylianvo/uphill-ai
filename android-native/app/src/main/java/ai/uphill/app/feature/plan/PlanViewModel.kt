package ai.uphill.app.feature.plan

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.generation.*
import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.persistence.OfflineCache
import ai.uphill.app.core.plan.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.io.File
import java.time.LocalDate
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*

@Serializable private data class CachedPlan(val snapshot: PlanSnapshot, val savedAt: Long)

data class NextWeekOffer(
    val block: Int,
    val start: Int,
    val end: Int,
    val completion: Double?,
    val unlocked: Boolean,
)

data class PlanState(
    val snapshot: PlanSnapshot? = null,
    val loading: Boolean = true,
    val error: String? = null,
    val notice: String? = null,
    val cachedAt: Long? = null,
    val week: Int = 1,
    val busy: Boolean = false,
    val blocks: BlockCompletionResponse? = null,
    val goal: PlanGoal? = null,
    val knowledge: JsonObject? = null,
)

class PlanViewModel(
    val api: APIClient,
    user: User,
    var lang: String,
    val generation: GenerationCenter,
    filesDir: File,
    val athleteId: Int? = null,
) : ViewModel() {
    private val mutable = MutableStateFlow(PlanState())
    val state = mutable.asStateFlow()

    fun changeLanguage(value: String) {
        lang = value
    }

    val service = PlanService(api, athleteId)
    private val cache = OfflineCache(File(filesDir, "offline"))
    private val cacheKey = "plan-${user.id}-${api.baseURL().hashCode()}"

    init {
        generation.resume()
        viewModelScope.launch {
            generation.state.collect {
                if (it.outcome is JobOutcome.Done || it.outcome is JobOutcome.Lost) load()
            }
        }
        load()
    }

    fun selectWeek(week: Int) {
        mutable.value =
            mutable.value.copy(
                week = week.coerceIn(1, mutable.value.snapshot?.plan?.totalWeeks ?: 1)
            )
    }

    fun clearError() {
        mutable.value = mutable.value.copy(error = null)
    }

    fun load() {
        viewModelScope.launch { refresh() }
    }

    suspend fun refresh() {
        val old = mutable.value
        val signedToken = api.tokenStore.read()
        if (old.snapshot == null && athleteId == null)
            cache.load<CachedPlan>(cacheKey)?.let {
                mutable.value =
                    mutable.value.copy(
                        snapshot = it.snapshot,
                        cachedAt = it.savedAt,
                        week =
                            PlanCalendar.resolveCurrentWeek(it.snapshot.plan, it.snapshot.workouts),
                        loading = false,
                    )
            }
        try {
            val fresh = service.activePlan()
            if (api.tokenStore.read() != signedToken) return
            if (fresh == null) {
                mutable.value = PlanState(loading = false)
                File(cache.directory, "$cacheKey.json").delete()
                return
            }
            mutable.value =
                mutable.value.copy(
                    snapshot = fresh,
                    loading = false,
                    cachedAt = null,
                    error = null,
                    week =
                        if (old.snapshot == null)
                            PlanCalendar.resolveCurrentWeek(fresh.plan, fresh.workouts)
                        else old.week.coerceAtMost(fresh.plan.totalWeeks),
                )
            if (athleteId == null)
                cache.save(cacheKey, CachedPlan(fresh, System.currentTimeMillis()))
            val blocks = runCatching { service.blockCompletion(fresh.plan.id) }.getOrNull()
            val goal =
                if (fresh.plan.courseDistanceKm != null)
                    runCatching { service.goal(fresh.plan.id, lang) }.getOrNull()
                else null
            val phase = weekWorkouts().firstOrNull()?.phase.orEmpty().lowercase()
            val topic =
                if (
                    (PlanCalendar.daysToRace(fresh.plan.raceDate) ?: 1000) <= 21 ||
                        phase.contains("taper") ||
                        phase.contains("peak")
                )
                    "Pacing"
                else if (phase.contains("recovery")) "Recovery" else "Training"
            mutable.value =
                mutable.value.copy(
                    blocks = blocks,
                    goal = goal,
                    knowledge = service.knowledge(topic, lang),
                )
        } catch (e: CancellationException) {
            throw e
        } catch (e: APIError.Transport) {
            mutable.value =
                mutable.value.copy(
                    loading = false,
                    cachedAt =
                        if (athleteId == null && mutable.value.snapshot != null)
                            mutable.value.cachedAt ?: System.currentTimeMillis()
                        else null,
                    error = if (mutable.value.snapshot == null) e.message else null,
                )
        } catch (e: Exception) {
            mutable.value = mutable.value.copy(loading = false, error = e.message)
        }
    }

    fun weekWorkouts() =
        mutable.value.snapshot
            ?.workouts
            .orEmpty()
            .filter { it.weekNumber == mutable.value.week }
            .sortedWith(compareBy({ it.weekday.offset }, { it.sessionSlot ?: "main" }))

    fun nextOffer(): NextWeekOffer? {
        val s = mutable.value
        val snap = s.snapshot ?: return null
        val blocks = s.blocks ?: return null
        val generated = snap.workouts.maxOfOrNull { it.weekNumber } ?: return null
        if (s.cachedAt != null || generated >= snap.plan.totalWeeks || s.week < generated)
            return null
        val last = blocks.blocks.maxByOrNull { it.blockNumber } ?: return null
        val start = blocks.maxGeneratedWeek + 1
        return NextWeekOffer(
            last.blockNumber + 1,
            start,
            minOf(start + last.weekEnd - last.weekStart, snap.plan.totalWeeks),
            last.completionPct,
            last.unlocked,
        )
    }

    fun canAdapt(): Boolean {
        val s = mutable.value
        val snapshot = s.snapshot ?: return false
        return s.cachedAt == null &&
            s.week >= PlanCalendar.currentWeek(snapshot.plan, snapshot.workouts) &&
            s.week <= (snapshot.workouts.maxOfOrNull { it.weekNumber } ?: 0)
    }

    fun canMove(workout: Workout): Boolean {
        val s = mutable.value
        val snapshot = s.snapshot ?: return false
        val current = PlanCalendar.currentWeek(snapshot.plan, snapshot.workouts)
        return athleteId == null &&
            s.cachedAt == null &&
            !workout.isDone &&
            !workout.isMissedFlag &&
            !workout.isMatched &&
            workout.weekNumber in current..current + 1
    }

    fun moveTargets(workout: Workout): List<Pair<Int, Weekday>> {
        val s = mutable.value
        val snap = s.snapshot ?: return emptyList()
        val current = PlanCalendar.currentWeek(snap.plan, snap.workouts)
        return (current..minOf(current + 1, snap.plan.totalWeeks)).flatMap { week ->
            Weekday.entries
                .filter { day ->
                    PlanCalendar.date(week, day, snap.plan, snap.workouts)?.let {
                        it >= LocalDate.now()
                    } == true && !(week == workout.weekNumber && day == workout.weekday)
                }
                .map { week to it }
        }
    }

    private fun action(block: suspend () -> Unit) {
        if (mutable.value.busy) return
        if (mutable.value.cachedAt != null) {
            mutable.value = mutable.value.copy(error = "You're offline. Changes need a connection.")
            return
        }
        viewModelScope.launch {
            mutable.value = mutable.value.copy(busy = true, error = null)
            try {
                block()
            } catch (e: CancellationException) {
                throw e
            } catch (e: APIError.ScheduleGuard) {
                mutable.value = mutable.value.copy(error = ScheduleMessages.guardText(e.code))
            } catch (e: Exception) {
                mutable.value = mutable.value.copy(error = e.message)
            } finally {
                mutable.value = mutable.value.copy(busy = false)
            }
        }
    }

    fun log(
        workout: Workout,
        completed: Int?,
        missed: Int?,
        rpe: Int?,
        notes: String,
        onSuccess: () -> Unit = {},
    ) {
        if (athleteId != null) return
        action {
            val rows = service.log(workout.id, completed, missed, rpe, notes)
            replace(rows)
            onSuccess()
            refresh()
        }
    }

    private fun replace(rows: List<Workout>) {
        mutable.value = mutable.value.copy(snapshot = mutable.value.snapshot?.copy(workouts = rows))
    }

    fun move(workout: Workout, week: Int, day: Weekday, swap: Boolean, onSuccess: () -> Unit) {
        action {
            val id = requireNotNull(mutable.value.snapshot).plan.id
            val result =
                if (swap)
                    service.swap(
                        id,
                        workout.weekNumber,
                        workout.weekday,
                        day,
                        LocalDate.now().toString(),
                    )
                else service.move(id, workout.id, week, day, LocalDate.now().toString())
            replace(result.workouts)
            mutable.value =
                mutable.value.copy(
                    notice =
                        result.warnings
                            .joinToString("\n") { ScheduleMessages.warningText(it) }
                            .takeIf { it.isNotBlank() }
                )
            onSuccess()
            refresh()
        }
    }

    suspend fun weekReview(): WeekReview =
        service.weekReview(requireNotNull(mutable.value.snapshot).plan.id, mutable.value.week)

    suspend fun blockEvaluation(): BlockEvaluation? =
        nextOffer()?.let {
            if (it.block > 1)
                runCatching {
                        service.blockEvaluation(
                            requireNotNull(mutable.value.snapshot).plan.id,
                            it.block - 1,
                        )
                    }
                    .getOrNull()
            else null
        }

    fun generate(
        adapt: Boolean,
        rpe: Int?,
        fatigue: String,
        notes: String,
        schedule: ScheduleDraft,
        override: Boolean,
        coachNotes: String,
        onSuccess: () -> Unit,
        weekOverride: Int? = null,
    ) {
        if (schedule.validationMessage != null) {
            mutable.value = mutable.value.copy(error = schedule.validationMessage)
            return
        }
        action {
            val snapshot = requireNotNull(mutable.value.snapshot)
            val offer = nextOffer()
            val body = buildJsonObject {
                put("plan_id", snapshot.plan.id)
                put("lang", lang)
                put("client_today", LocalDate.now().toString())
                rpe?.let { put("overall_rpe", it) }
                schedule.changes().forEach { (key, value) ->
                    if (adapt || key != "max_continuous_jog_min") put(key, value)
                }
                if (adapt) {
                    put("week_number", weekOverride ?: mutable.value.week)
                    put("fatigue_level", fatigue)
                    if (notes.isNotBlank()) put("fatigue_notes", notes.trim())
                } else {
                    put("block_number", requireNotNull(offer).block)
                    put("override_gate", override)
                    if (notes.isNotBlank()) put("notes", notes.trim())
                    if (athleteId != null && coachNotes.isNotBlank())
                        put("coach_notes", coachNotes.trim())
                }
            }
            val svc = GenerationService(api, athleteId)
            val start = if (adapt) svc.adapt(body) else svc.nextBlock(body)
            generation.track(
                if (adapt) "adaptWeek" else "nextWeek",
                start.jobId,
                athleteId = athleteId,
            )
            onSuccess()
        }
    }

    fun reassess() {
        action {
            val id = requireNotNull(mutable.value.snapshot).plan.id
            mutable.value = mutable.value.copy(goal = service.reassessGoal(id, lang))
        }
    }

    fun applyGoal(onSuccess: () -> Unit) {
        action {
            val s = mutable.value
            val minutes = requireNotNull(s.goal?.suggestedMinutes)
            mutable.value =
                mutable.value.copy(
                    goal = service.applyGoal(requireNotNull(s.snapshot).plan.id, minutes)
                )
            onSuccess()
            refresh()
        }
    }

    suspend fun recent(): List<Plan> = service.recentPlans()

    fun select(plan: Plan, onSuccess: () -> Unit) {
        if (athleteId != null) return
        action {
            service.selectPlan(plan.id)?.let {
                mutable.value =
                    mutable.value.copy(
                        snapshot = it,
                        week = PlanCalendar.resolveCurrentWeek(it.plan, it.workouts),
                    )
            }
            onSuccess()
            refresh()
        }
    }

    fun delete(plan: Plan, onSuccess: () -> Unit) {
        if (athleteId != null) return
        action {
            service.deletePlan(plan.id)
            onSuccess()
            refresh()
        }
    }

    fun sync() {
        if (athleteId != null) return
        action {
            val id = requireNotNull(mutable.value.snapshot).plan.id
            val count = service.syncWatch(id)
            refresh()
            mutable.value.snapshot
                ?.workouts
                ?.filter { it.isMatched && it.isCompleted != 1 }
                ?.forEach { service.log(it.id, completed = 1, missed = 0) }
            refresh()
            mutable.value = mutable.value.copy(notice = "COROS · $count")
        }
    }

    suspend fun watch(): List<WatchActivity> =
        service.watchActivities(requireNotNull(mutable.value.snapshot).plan.id).sortedByDescending {
            it.startTime
        }

    fun match(activityId: Int, workout: Workout?, onSuccess: () -> Unit) {
        if (athleteId != null) return
        action {
            val unlinked =
                if (workout == null)
                    mutable.value.snapshot?.workouts?.firstOrNull {
                        it.matchedActivityId == activityId
                    }
                else null
            val previous = workout?.matchedActivityId?.takeIf { it != activityId }
            previous?.let { service.setMatch(it, null) }
            try {
                service.setMatch(activityId, workout?.id)
            } catch (e: Exception) {
                if (previous != null && workout != null)
                    runCatching { service.setMatch(previous, workout.id) }
                throw e
            }
            if (unlinked?.isCompleted == 1) service.log(unlinked.id, completed = 0)
            if (workout != null) service.log(workout.id, completed = 1, missed = 0)
            onSuccess()
            refresh()
        }
    }
}

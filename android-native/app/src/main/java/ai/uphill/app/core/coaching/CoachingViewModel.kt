package ai.uphill.app.core.coaching

import ai.uphill.app.core.auth.User
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class CoachingState(
    val overview: CoachOverview? = null,
    val roster: List<CoachedAthleteRow> = emptyList(),
    val invites: List<CoachingInvite> = emptyList(),
    val busy: Boolean = false,
    val error: String? = null,
)

class CoachingViewModel(private val service: CoachingService, private val coach: Boolean) :
    ViewModel() {
    private val mutable = MutableStateFlow(CoachingState())
    val state = mutable.asStateFlow()

    private suspend fun refresh(days: Int, level: String) {
        val invites = service.invites()
        mutable.update { it.copy(invites = invites) }
        if (coach) {
            val overview = service.overview(days, level)
            val roster = service.roster()
            mutable.update { it.copy(overview = overview, roster = roster) }
        }
    }

    fun load(days: Int = 14, level: String = "all") = action(days, level) {}

    fun action(days: Int = 14, level: String = "all", block: suspend () -> Unit) {
        if (mutable.value.busy) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                block()
                refresh(days, level)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }
}

data class CoachedAthleteState(
    val profile: User? = null,
    val active: CoachPlanSnapshot? = null,
    val draft: CoachPlanSnapshot? = null,
    val notes: List<CoachNote> = emptyList(),
    val busy: Boolean = false,
    val error: String? = null,
)

class CoachedAthleteViewModel(private val service: CoachingService, val athleteId: Int) :
    ViewModel() {
    private val mutable = MutableStateFlow(CoachedAthleteState())
    val state = mutable.asStateFlow()

    private suspend fun refresh() {
        val profile = service.profile(athleteId)
        mutable.update { it.copy(profile = profile) }
        val active = service.activePlan(athleteId)
        mutable.update { it.copy(active = active) }
        val draft = service.draftPlan(athleteId)
        mutable.update { it.copy(draft = draft) }
        val notes = service.notes(athleteId)
        mutable.update { it.copy(notes = notes) }
    }

    fun load() = action {}

    fun action(onSuccess: () -> Unit = {}, block: suspend () -> Unit) {
        if (mutable.value.busy) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                block()
                refresh()
                onSuccess()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }
}

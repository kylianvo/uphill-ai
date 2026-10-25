package ai.uphill.app.core.coaching

import ai.uphill.app.core.auth.User
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject

data class CoachedProfileState(
    val profile: User? = null,
    val notes: List<CoachNote> = emptyList(),
    val busy: Boolean = false,
    val error: String? = null,
)

/** One athlete's profile sheet; no active-plan mutation or cache from another athlete. */
class CoachedProfileViewModel(private val service: CoachingService, private val athleteId: Int) :
    ViewModel() {
    private val mutable = MutableStateFlow(CoachedProfileState())
    val state = mutable.asStateFlow()

    fun load() = perform {
        val profile = service.profile(athleteId)
        mutable.update { it.copy(profile = profile) }
        val notes = service.notes(athleteId, "general")
        mutable.update { it.copy(notes = notes) }
    }

    fun save(patch: JsonObject, onSuccess: () -> Unit) = perform {
        val profile = service.updateProfile(athleteId, patch)
        mutable.update { it.copy(profile = profile) }
        onSuccess()
    }

    fun post(text: String, onSuccess: () -> Unit) {
        if (text.isBlank()) return
        perform {
            val note = service.addNote(athleteId, CoachNoteCreatePayload("general", text.trim()))
            mutable.update { it.copy(notes = listOf(note) + it.notes) }
            onSuccess()
        }
    }

    private fun perform(block: suspend () -> Unit) {
        if (mutable.value.busy) return
        mutable.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try {
                block()
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

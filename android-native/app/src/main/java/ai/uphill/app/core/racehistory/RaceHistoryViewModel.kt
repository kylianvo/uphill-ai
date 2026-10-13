package ai.uphill.app.core.racehistory

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class RaceHistoryState(
    val history: RaceHistoryResponse? = null,
    val busy: Boolean = false,
    val error: String? = null,
)

class RaceHistoryViewModel(private val service: RaceHistoryService) : ViewModel() {
    private val mutable = MutableStateFlow(RaceHistoryState())
    val state = mutable.asStateFlow()

    fun load() {
        if (mutable.value.busy) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                val history = service.history()
                mutable.update { it.copy(history = history) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }

    fun perform(operation: suspend () -> Unit, onSuccess: () -> Unit = {}) {
        if (mutable.value.busy) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                operation()
                onSuccess()
                val history = service.history()
                mutable.update { it.copy(history = history) }
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

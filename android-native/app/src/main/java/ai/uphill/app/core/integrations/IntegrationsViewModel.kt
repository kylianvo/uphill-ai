package ai.uphill.app.core.integrations

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class IntegrationsState(
    val status: DeviceConnectionStatus? = null,
    val push: CorosPushStatus? = null,
    val outcome: CorosPushOutcome? = null,
    val sync: DeviceSyncResult? = null,
    val fitness: FitnessSyncResult? = null,
    val busy: Boolean = false,
    val error: String? = null,
)

class IntegrationsViewModel(private val service: DeviceConnectionService) : ViewModel() {
    private val mutable = MutableStateFlow(IntegrationsState())
    val state = mutable.asStateFlow()

    suspend fun refresh() {
        try {
            val status = service.fetchStatus()
            val push = if (status.isCorosConnected) service.fetchPushStatus() else null
            mutable.update { it.copy(status = status, push = push) }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            mutable.update { it.copy(error = e.message) }
        }
    }

    fun action(block: suspend () -> Unit) {
        if (mutable.value.busy) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                block()
                refresh()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e.message) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }

    fun sync() = action {
        val res = service.syncNow()
        mutable.update { it.copy(sync = res) }
    }

    fun fitness() = action {
        val res = service.syncFitness()
        mutable.update { it.copy(fitness = res) }
    }

    fun push(lang: String) = action {
        val res = service.pushToCoros(lang)
        mutable.update { it.copy(outcome = res) }
    }

    fun disconnect() = action {
        service.disconnectCoros()
        mutable.update { IntegrationsState() }
    }
}

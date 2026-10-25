package ai.uphill.app.core.auth

import ai.uphill.app.core.networking.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface SessionState {
    data object Restoring : SessionState

    data object SignedOut : SessionState

    data class SignedIn(val user: User) : SessionState
}

class SessionStore(
    private val tokens: TokenStore,
    private val load: () -> User?,
    private val save: (User) -> Unit,
    private val clear: () -> Unit,
) {
    private val mutable =
        MutableStateFlow<SessionState>(
            if (tokens.read() == null) SessionState.SignedOut else SessionState.Restoring
        )
    val state = mutable.asStateFlow()
    private val mutableRestoreError = MutableStateFlow<Throwable?>(null)
    val restoreError = mutableRestoreError.asStateFlow()

    suspend fun restore(me: suspend () -> User) {
        mutableRestoreError.value = null
        val restoringToken = tokens.read()
        if (restoringToken == null) {
            mutable.value = SessionState.SignedOut
            return
        }
        try {
            val user = me()
            if (tokens.read() == restoringToken) updateUser(user)
        } catch (e: CancellationException) {
            throw e
        } catch (e: APIError.Unauthorized) {
            if (tokens.read() != restoringToken) return
            signOut()
        } catch (e: APIError.Transport) {
            if (tokens.read() != restoringToken) return
            val cached = load()
            if (cached != null) mutable.value = SessionState.SignedIn(cached)
            else mutableRestoreError.value = e
        } catch (e: Exception) {
            if (tokens.read() != restoringToken) return
            mutableRestoreError.value = e
        }
    }

    fun signIn(response: AuthResponse) {
        tokens.write(response.sessionToken)
        updateUser(response.user)
    }

    fun updateUser(user: User) {
        mutableRestoreError.value = null
        save(user)
        mutable.value = SessionState.SignedIn(user)
    }

    fun signOut() {
        mutableRestoreError.value = null
        tokens.write(null)
        clear()
        mutable.value = SessionState.SignedOut
    }
}

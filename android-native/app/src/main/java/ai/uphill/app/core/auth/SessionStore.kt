package ai.uphill.app.core.auth

import ai.uphill.app.core.networking.*
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

    suspend fun restore(me: suspend () -> User) {
        if (tokens.read() == null) {
            mutable.value = SessionState.SignedOut
            return
        }
        try {
            updateUser(me())
        } catch (e: APIError.Transport) {
            load()?.let { mutable.value = SessionState.SignedIn(it) } ?: signOut()
        } catch (e: APIError) {
            signOut()
        }
    }

    fun signIn(response: AuthResponse) {
        tokens.write(response.sessionToken)
        updateUser(response.user)
    }

    fun updateUser(user: User) {
        save(user)
        mutable.value = SessionState.SignedIn(user)
    }

    fun signOut() {
        tokens.write(null)
        clear()
        mutable.value = SessionState.SignedOut
    }
}

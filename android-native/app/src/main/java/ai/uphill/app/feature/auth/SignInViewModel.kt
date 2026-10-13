package ai.uphill.app.feature.auth

import ai.uphill.app.core.auth.*
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class SignInState(
    val email: String = "",
    val password: String = "",
    val name: String = "",
    val register: Boolean = false,
    val busy: Boolean = false,
    val error: Throwable? = null,
) {
    val canSubmit
        get() =
            !busy &&
                email.trim().contains('@') &&
                password.length >= 8 &&
                (!register || name.trim().isNotEmpty())
}

class SignInViewModel(private val auth: AuthService, private val session: SessionStore) :
    ViewModel() {
    private val mutable = MutableStateFlow(SignInState())
    val state = mutable.asStateFlow()

    fun edit(transform: (SignInState) -> SignInState) {
        mutable.update(transform)
    }

    fun submit() {
        val form = mutable.value
        if (!form.canSubmit) return
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                session.signIn(
                    if (form.register)
                        auth.register(form.name.trim(), form.email.trim(), form.password)
                    else auth.login(form.email.trim(), form.password)
                )
                mutable.value = SignInState()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }

    fun google(fetch: suspend () -> String) {
        viewModelScope.launch {
            mutable.update { it.copy(busy = true, error = null) }
            try {
                session.signIn(auth.google(fetch()))
                mutable.value = SignInState()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutable.update { it.copy(error = e) }
            } finally {
                mutable.update { it.copy(busy = false) }
            }
        }
    }
}

package ai.uphill.app.feature.auth

import ai.uphill.app.core.localization.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.*
import androidx.compose.ui.unit.dp
import androidx.credentials.*
import com.google.android.libraries.identity.googleid.*

@Composable
fun SignInScreen(model: SignInViewModel) {
    val state by model.state.collectAsState()
    val context = LocalContext.current
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    Column(
        Modifier.fillMaxSize().imePadding().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp),
    ) {
        Spacer(Modifier.height(8.dp))
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(L("Uphill AI"), style = MaterialTheme.typography.headlineLarge)
            Text(L("Your adaptive training plan for the mountains."), color = UH.secondary)
        }
        state.error?.let {
            Text(
                localizedError(context, it),
                color = UH.danger,
                modifier = Modifier.testTag("signin.error"),
            )
        }
        OutlinedButton(
            onClick = {
                model.google {
                    val option =
                        GetSignInWithGoogleOption.Builder(
                                "451637841654-0eoo8qsa5fgnpm4cq0br8phgkhh92c5a.apps.googleusercontent.com"
                            )
                            .build()
                    val result =
                        CredentialManager.create(context)
                            .getCredential(
                                context,
                                GetCredentialRequest.Builder().addCredentialOption(option).build(),
                            )
                    GoogleIdTokenCredential.createFrom(result.credential.data).idToken
                }
            },
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            enabled = !state.busy,
        ) {
            Text(L("Continue with Google"))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            HorizontalDivider(Modifier.weight(1f).padding(top = 10.dp), color = UH.line)
            Text(L("or"), style = MaterialTheme.typography.bodySmall, color = UH.muted)
            HorizontalDivider(Modifier.weight(1f).padding(top = 10.dp), color = UH.line)
        }
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (state.register)
                OutlinedTextField(
                    value = state.name,
                    onValueChange = { value -> model.edit { it.copy(name = value) } },
                    label = { Text(L("Name")) },
                    modifier = Modifier.fillMaxWidth().testTag("signin.name"),
                    singleLine = true,
                    enabled = !state.busy,
                )
            OutlinedTextField(
                value = state.email,
                onValueChange = { value -> model.edit { it.copy(email = value) } },
                label = { Text(L("Email")) },
                modifier = Modifier.fillMaxWidth().testTag("signin.email"),
                singleLine = true,
                enabled = !state.busy,
                colors =
                    OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = androidx.compose.ui.graphics.Color.White,
                        unfocusedContainerColor = androidx.compose.ui.graphics.Color.White,
                    ),
                keyboardOptions =
                    KeyboardOptions(
                        keyboardType = KeyboardType.Email,
                        imeAction = ImeAction.Next,
                        autoCorrectEnabled = false,
                    ),
                keyboardActions = KeyboardActions(onNext = { focus.moveFocus(FocusDirection.Down) }),
            )
            OutlinedTextField(
                value = state.password,
                onValueChange = { value -> model.edit { it.copy(password = value) } },
                label = { Text(L("Password (8+ characters)")) },
                modifier = Modifier.fillMaxWidth().testTag("signin.password"),
                singleLine = true,
                enabled = !state.busy,
                colors =
                    OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = androidx.compose.ui.graphics.Color.White,
                        unfocusedContainerColor = androidx.compose.ui.graphics.Color.White,
                    ),
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions =
                    KeyboardOptions(
                        keyboardType = KeyboardType.Password,
                        imeAction = ImeAction.Done,
                    ),
            )
            Button(
                onClick = model::submit,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("signin.submit"),
                enabled = state.canSubmit,
            ) {
                if (state.busy) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                else Text(L(if (state.register) "Create account" else "Sign in"))
            }
            TextButton(
                onClick = { model.edit { it.copy(register = !it.register, error = null) } },
                enabled = !state.busy,
            ) {
                Text(
                    L(
                        if (state.register) "Have an account? Sign in"
                        else "New to Uphill? Create an account"
                    )
                )
            }
        }
    }
}

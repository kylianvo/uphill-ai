package ai.uphill.app.app

import ai.uphill.app.core.auth.SessionState
import ai.uphill.app.designsystem.UphillTheme
import ai.uphill.app.feature.launch.LaunchScreen
import android.content.Intent
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.core.os.LocaleListCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {
    private val container
        get() = (application as UphillApplication).container

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleCallback(intent)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.RESUMED) {
                launch {
                    container.language.collect { language ->
                        if (AppCompatDelegate.getApplicationLocales().toLanguageTags() != language)
                            AppCompatDelegate.setApplicationLocales(
                                LocaleListCompat.forLanguageTags(language)
                            )
                    }
                }
                launch {
                    while (isActive) {
                        if (container.session.state.value is SessionState.SignedIn)
                            try {
                                container.corosSync.syncIfDue()
                            } catch (_: ai.uphill.app.core.networking.APIError) {}
                        delay(15 * 60 * 1000L)
                    }
                }
            }
        }
        setContent {
            UphillTheme {
                var launching by remember { mutableStateOf(savedInstanceState == null) }
                LaunchedEffect(Unit) {
                    delay(900)
                    launching = false
                }
                Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    Box(Modifier.safeDrawingPadding()) {
                        if (launching) LaunchScreen() else RootNav(container)
                    }
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleCallback(intent)
    }

    private fun handleCallback(intent: Intent) {
        val url = intent.dataString ?: return
        if (intent.data?.scheme == "uphillai" && intent.data?.host == "coros") {
            lifecycleScope.launch {
                try {
                    container.corosOAuth.handleCallback(url)
                } catch (_: Exception) {
                    android.widget.Toast.makeText(
                            this@MainActivity,
                            getString(ai.uphill.app.R.string.coros_callback_failure),
                            android.widget.Toast.LENGTH_LONG,
                        )
                        .show()
                }
            }
            intent.data = null
        }
    }
}

package ai.uphill.app

import ai.uphill.app.designsystem.UphillTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/** Mirrors MainActivity's root so screen tests use the app's system and keyboard insets. */
@Composable
internal fun AppFixture(content: @Composable () -> Unit) {
    UphillTheme {
        Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            Box(Modifier.safeDrawingPadding()) { content() }
        }
    }
}

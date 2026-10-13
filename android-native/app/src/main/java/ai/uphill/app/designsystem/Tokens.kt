package ai.uphill.app.designsystem

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

object UH {
    val accent = Color(0xFF19CE8B)
    val accentInk = Color(0xFF08764F)
    val buttonInk = Color(0xFF063E2B)
    val ink = Color(0xFF172B26)
    val secondary = Color(0xFF455C52)
    val muted = Color(0xFF5D7167)
    val line = Color(0xFFDCE5DF)
    val activeFill = accent.copy(alpha = .16f)
    val hover = Color(0xFFEDF5F0)
    val surface = Color(0xFFF8FAF8)
    val warningInk = Color(0xFF92400E)
    val warningFill = Color(0x1FF59E0B)
    val danger = Color(0xFFB42318)

    object Space {
        val compact = 8.dp
        val small = 12.dp
        val regular = 16.dp
        val medium = 20.dp
        val section = 24.dp
        val panel = 28.dp
        val reading = 32.dp
    }

    object Radius {
        val topic = 6.dp
        val control = 8.dp
        val workoutDay = 10.dp
        val panel = 12.dp
        val landing = 16.dp
    }
}

@Composable
fun UphillTheme(content: @Composable () -> Unit) {
    CompositionLocalProvider(LocalReduceMotion provides rememberReduceMotion()) {
        MaterialTheme(
            colorScheme =
                lightColorScheme(
                    primary = UH.accentInk,
                    onPrimary = Color.White,
                    secondary = UH.accentInk,
                    onSecondary = Color.White,
                    secondaryContainer = UH.activeFill,
                    onSecondaryContainer = UH.accentInk,
                    tertiary = UH.secondary,
                    onTertiary = Color.White,
                    tertiaryContainer = UH.hover,
                    onTertiaryContainer = UH.ink,
                    primaryContainer = UH.accent,
                    onPrimaryContainer = UH.buttonInk,
                    background = UH.surface,
                    onBackground = UH.ink,
                    surface = Color.White,
                    onSurface = UH.ink,
                    surfaceVariant = UH.hover,
                    onSurfaceVariant = UH.secondary,
                    surfaceTint = Color.Transparent,
                    surfaceDim = UH.surface,
                    surfaceBright = Color.White,
                    surfaceContainerLowest = Color.White,
                    surfaceContainerLow = UH.surface,
                    surfaceContainer = UH.surface,
                    surfaceContainerHigh = UH.hover,
                    surfaceContainerHighest = UH.hover,
                    outlineVariant = UH.line,
                    outline = UH.line,
                    error = UH.danger,
                ),
            typography =
                Typography(
                    headlineLarge =
                        TextStyle(
                            fontSize = 28.sp,
                            lineHeight = 34.sp,
                            fontWeight = FontWeight.Bold,
                        ),
                    headlineMedium =
                        TextStyle(
                            fontSize = 28.sp,
                            lineHeight = 34.sp,
                            fontWeight = FontWeight.Bold,
                        ),
                    headlineSmall =
                        TextStyle(
                            fontSize = 20.sp,
                            lineHeight = 26.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    titleLarge =
                        TextStyle(
                            fontSize = 20.sp,
                            lineHeight = 26.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    titleMedium =
                        TextStyle(
                            fontSize = 17.sp,
                            lineHeight = 22.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    titleSmall =
                        TextStyle(
                            fontSize = 15.sp,
                            lineHeight = 20.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    bodyLarge = TextStyle(fontSize = 17.sp, lineHeight = 22.sp),
                    bodyMedium = TextStyle(fontSize = 15.sp, lineHeight = 20.sp),
                    bodySmall = TextStyle(fontSize = 13.sp, lineHeight = 18.sp),
                    labelLarge =
                        TextStyle(
                            fontSize = 15.sp,
                            lineHeight = 20.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    labelMedium =
                        TextStyle(
                            fontSize = 13.sp,
                            lineHeight = 18.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    labelSmall =
                        TextStyle(
                            fontSize = 12.sp,
                            lineHeight = 16.sp,
                            fontWeight = FontWeight.Bold,
                        ),
                ),
            shapes =
                Shapes(
                    extraSmall = RoundedCornerShape(8.dp),
                    small = RoundedCornerShape(8.dp),
                    medium = RoundedCornerShape(12.dp),
                    large = RoundedCornerShape(16.dp),
                    extraLarge = RoundedCornerShape(16.dp),
                ),
            content = content,
        )
    }
}

package ai.uphill.app.core.plan

import ai.uphill.app.core.localization.L
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import kotlin.math.roundToInt

@Composable
fun P(key: String): String {
    val context = LocalContext.current
    val resource =
        when (key) {
            "Ultra (60k+)" -> "planui_ultra_60k_plus"
            "Ultra (< 60k)" -> "planui_ultra_under_60k"
            else -> "planui_" + key.lowercase().replace(Regex("[^a-z0-9]+"), "_").trim('_')
        }
    val id = context.resources.getIdentifier(resource, "string", context.packageName)
    return if (id != 0) context.getString(id) else L(key)
}

fun minutesText(minutes: Double): String {
    val value = minutes.roundToInt()
    return "${value/60}:${(value%60).toString().padStart(2,'0')}"
}

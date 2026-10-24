package ai.uphill.app.designsystem

import ai.uphill.app.R
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight

/** The shared bundled variable font supports the full 200–800 weight axis. */
@OptIn(ExperimentalTextApi::class)
val UphillBodyFont = FontFamily(
    (200..800 step 100).map { weight ->
        Font(
            R.font.plus_jakarta_sans,
            weight = FontWeight(weight),
            variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
        )
    }
)

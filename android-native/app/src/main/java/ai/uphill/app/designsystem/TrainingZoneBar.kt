package ai.uphill.app.designsystem

import ai.uphill.app.core.localization.L
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable
fun TrainingZoneBar(resting: Int?, aet: Int?, ant: Int?, maximum: Int?) {
    val scaled =
        resting != null &&
            aet != null &&
            ant != null &&
            maximum != null &&
            resting < aet &&
            aet < ant &&
            ant < maximum
    val boundaries =
        if (scaled) {
            val span = (maximum!! - resting!!).toFloat()
            listOf(
                    resting,
                    maxOf(resting, (aet!! * .9).toInt()),
                    aet,
                    ant!!,
                    (ant + maximum) / 2,
                    maximum,
                )
                .map { (it - resting) / span }
        } else listOf(0f, .2f, .4f, .6f, .8f, 1f)
    Column(
        Modifier.semantics(mergeDescendants = true) {},
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("AeT ${aet ?: "—"} · AnT ${ant ?: "—"}", style = MaterialTheme.typography.labelLarge)
        Row(Modifier.fillMaxWidth().height(32.dp).clearAndSetSemantics {}) {
            val colors = listOf(0xff0ea5e9, 0xff10b981, 0xfff59e0b, 0xfff97316, 0xffef4444)
            colors.forEachIndexed { index, color ->
                Box(
                    Modifier.weight(
                            (boundaries[index + 1] - boundaries[index]).coerceAtLeast(.001f)
                        )
                        .fillMaxHeight()
                        .background(Color(color))
                ) {
                    Text(
                        "Z${index + 1}",
                        color = Color.Black,
                        style = MaterialTheme.typography.labelSmall,
                        modifier = Modifier.padding(4.dp),
                    )
                }
            }
        }
        if (scaled)
            Text(
                "${L("Resting %lld bpm", resting!!)} · ${L("Max %lld bpm", maximum!!)}",
                style = MaterialTheme.typography.bodySmall,
            )
        Text(
            L(
                if (scaled) "AeT: top of Zone 2. AnT: top of Zone 3."
                else "AeT: top of Zone 2. AnT: top of Zone 3. Zone widths are schematic."
            ),
            style = MaterialTheme.typography.bodySmall,
            color = UH.secondary,
        )
    }
}

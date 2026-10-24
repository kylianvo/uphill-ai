package ai.uphill.app.feature.pace

import ai.uphill.app.R
import ai.uphill.app.core.goal.GoalTime
import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.roundToInt

@Composable
internal fun PaceControlsCard(
    target: Double, bounds: Pair<Double, Double>, bias: Float, weight: String, clock: String,
    onTarget: (Double) -> Unit, onBias: (Float) -> Unit,
    onWeight: (String) -> Unit, onClock: (String) -> Unit,
) {
    val targetLabel = L("Target Finish Time")
    val targetText = GoalTime.format(target)
    val strategyLabel = L("Split Execution Strategy")
    val strategy = stringResource(when {
        bias < -.01f -> R.string.paceui_conservative_start
        bias > .01f -> R.string.paceui_aggressive_start
        else -> R.string.paceui_even_effort
    })
    ToolPanel(radius = UH.Radius.landing, modifier = Modifier.testTag("pace.controls")) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(L("TARGET TIME & STRATEGY"), color = UH.muted, fontFamily = FontFamily.Monospace,
                fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(targetLabel, Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                    Text(targetText, style = MaterialTheme.typography.titleLarge.copy(
                        fontSize = 22.sp, fontWeight = FontWeight.Bold, fontFeatureSettings = "tnum"), color = UH.accentInk)
                }
                Slider(
                    value = target.toFloat().coerceIn(bounds.first.toFloat(), bounds.second.toFloat()),
                    onValueChange = { raw ->
                        onTarget((bounds.first + ((raw - bounds.first) / 5).roundToInt() * 5).coerceIn(bounds.first, bounds.second))
                    },
                    valueRange = bounds.first.toFloat()..bounds.second.toFloat(),
                    modifier = Modifier.testTag("pace.target").semantics {
                        contentDescription = targetLabel
                        stateDescription = targetText
                    },
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    listOf(bounds.first, bounds.second).forEach {
                        Text(GoalTime.format(it), fontFamily = FontFamily.Monospace, fontSize = 10.sp, color = UH.muted)
                    }
                }
            }
            HorizontalDivider(Modifier.padding(vertical = 2.dp), color = UH.line)
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(strategyLabel, Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Medium)
                    Text(strategy, Modifier.weight(1f), style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold, textAlign = TextAlign.End)
                }
                Slider(bias, { onBias((it * 100).roundToInt() / 100f) }, valueRange = -0.05f..0.05f,
                    steps = 9, modifier = Modifier.testTag("pace.bias").semantics {
                        contentDescription = strategyLabel
                        stateDescription = strategy
                    })
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    listOf(stringResource(R.string.paceui_conservative), L("Even"),
                        stringResource(R.string.paceui_aggressive)).forEach {
                        Text(it, fontFamily = FontFamily.Monospace, fontSize = 10.sp,
                            fontWeight = FontWeight.Medium, color = UH.muted)
                    }
                }
            }
            HorizontalDivider(Modifier.padding(vertical = 2.dp), color = UH.line)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                PaceControlField("Runner Weight (kg)", weight, onWeight, KeyboardType.Decimal, Modifier.weight(1f))
                PaceControlField("Start Time (Clock)", clock, onClock, KeyboardType.Ascii, Modifier.weight(1f))
            }
        }
    }
}

@Composable
private fun PaceControlField(label: String, value: String, onChange: (String) -> Unit, keyboard: KeyboardType, modifier: Modifier) {
    val text = L(label)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(text, style = MaterialTheme.typography.bodySmall, color = UH.secondary)
        OutlinedTextField(value, onChange, Modifier.fillMaxWidth().semantics { contentDescription = text },
            singleLine = true, textStyle = MaterialTheme.typography.bodySmall,
            keyboardOptions = KeyboardOptions(keyboardType = keyboard), shape = RoundedCornerShape(UH.Radius.control),
            colors = OutlinedTextFieldDefaults.colors(unfocusedContainerColor = UH.surface, focusedContainerColor = UH.surface))
    }
}

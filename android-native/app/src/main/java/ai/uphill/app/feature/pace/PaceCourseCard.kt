package ai.uphill.app.feature.pace

import ai.uphill.app.core.goal.RaceDistance
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.pace.GpxCourseResult
import ai.uphill.app.designsystem.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.FileDownload
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Route
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.util.Locale

/** Course controls mirror SwiftUI's courseSetupCard; GPX owns distance and gain. */
@Composable
internal fun PaceCourseCard(
    api: APIClient,
    name: String,
    distance: String,
    gain: String,
    interval: String,
    gpx: GpxCourseResult?,
    onName: (String) -> Unit,
    onDistance: (String) -> Unit,
    onGain: (String) -> Unit,
    onRace: (RaceDistance) -> Unit,
    onInterval: (String) -> Unit,
    onImport: () -> Unit,
    onRemove: () -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    val removeLabel = L("Remove GPX file")
    ToolPanel {
        Text(
            L("COURSE CONFIGURATION"),
            color = UH.muted,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
            fontSize = 11.sp,
        )
        Surface(
            modifier = Modifier.fillMaxWidth().testTag("pace.gpx"),
            shape = RoundedCornerShape(UH.Radius.control),
            color = if (gpx == null) UH.surface else UH.activeFill,
            border = BorderStroke(1.dp, if (gpx == null) UH.line else UH.accent.copy(alpha = .4f)),
        ) {
            if (gpx == null) {
                Row(
                    Modifier.clickable(onClick = onImport).testTag("pace.importGpx").padding(12.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Default.Route, null, Modifier.size(20.dp), tint = UH.accentInk)
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(L("Import GPX Course File"), style = MaterialTheme.typography.labelLarge)
                        Text(
                            L("Load exact elevation profile & waypoints from .gpx"),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                    }
                    Icon(Icons.Default.FileDownload, null, Modifier.size(18.dp), tint = UH.secondary)
                }
            } else {
                Row(
                    Modifier.padding(start = 10.dp, top = 8.dp, bottom = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(Icons.Default.Map, null, Modifier.size(20.dp), tint = UH.accentInk)
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(gpx.fileName, Modifier.weight(1f, fill = false), maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.labelLarge)
                            Text("GPX", color = UH.accentInk, fontFamily = FontFamily.Monospace, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        }
                        Text(
                            String.format(Locale.getDefault(), "%.1f km · +%d m D+ · %d CPs", gpx.totalDistanceKm, gpx.totalElevationGainM.toInt(), gpx.checkpoints.size),
                            fontFamily = FontFamily.Monospace,
                            fontSize = 11.sp,
                            color = UH.secondary,
                        )
                    }
                    IconButton(onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.SegmentTick)
                        onRemove()
                    }) { Icon(Icons.Default.Close, removeLabel, tint = UH.muted) }
                }
            }
        }
        RaceSearch(api, name, onName, onRace)
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            PaceCourseField("Distance (km)", distance, onDistance, gpx == null, Modifier.weight(1f).testTag("pace.distance"))
            PaceCourseField("Gain (m D+)", gain, onGain, gpx == null, Modifier.weight(1f).testTag("pace.gain"))
        }
        Text(L("Split Interval"), style = MaterialTheme.typography.labelLarge, color = UH.secondary)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("1", "5", "10").forEach { option ->
                val active = option == interval
                Surface(
                    modifier = Modifier.weight(1f).semantics { selected = active },
                    shape = RoundedCornerShape(UH.Radius.control),
                    color = if (active) UH.ink else UH.surface,
                    contentColor = if (active) androidx.compose.ui.graphics.Color.White else UH.ink,
                    border = BorderStroke(1.dp, UH.line),
                    onClick = {
                        haptic.performHapticFeedback(HapticFeedbackType.SegmentTick)
                        onInterval(option)
                    },
                ) {
                    Box(Modifier.heightIn(min = 48.dp).padding(8.dp), contentAlignment = Alignment.Center) {
                        Text("$option km", style = MaterialTheme.typography.labelLarge, fontWeight = if (active) FontWeight.Bold else FontWeight.Medium)
                    }
                }
            }
        }
    }
}

@Composable
private fun PaceCourseField(label: String, value: String, onChange: (String) -> Unit, enabled: Boolean, modifier: Modifier) {
    val text = L(label)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(text, style = MaterialTheme.typography.labelLarge, color = UH.secondary)
        OutlinedTextField(
            value,
            onChange,
            Modifier.fillMaxWidth().semantics { contentDescription = text },
            enabled = enabled,
            singleLine = true,
            textStyle = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            shape = RoundedCornerShape(UH.Radius.control),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = UH.surface,
                unfocusedContainerColor = UH.surface,
                disabledContainerColor = UH.surface,
                disabledBorderColor = UH.line,
                disabledTextColor = UH.ink,
            ),
        )
    }
}

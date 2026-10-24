package ai.uphill.app.feature.me

import ai.uphill.app.core.localization.L
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WatchZonesGuide(onDismiss: () -> Unit) {
    var fieldTest by remember { mutableStateOf(false) }
    val uri = LocalUriHandler.current
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = ai.uphill.app.designsystem.UH.surface,
    ) {
        Column(
            Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(L("Training zones guide"), style = MaterialTheme.typography.titleLarge)
            ProfileSegments(
                listOf("watch" to "From watch", "test" to "Field test"),
                if (fieldTest) "test" else "watch",
            ) {
                fieldTest = it == "test"
            }
            val paragraphs =
                if (fieldTest)
                    listOf(
                        "Warm up, then hold a steady speed for 60 minutes. Compare heart rate between halves; drift above 5% suggests you started above AeT. Follow Evoke's full protocol and interpretation.",
                        "Evoke uses a sustained 20–60 minute time trial, depending on experience. Average heart rate estimates AnT for that activity. This is a hard effort; test well-rested.",
                        "Record easy pace below AeT on flat ground. Use a flat running time trial for Threshold pace; uphill pace is not interchangeable.",
                        "You can skip these fields and add test results later.",
                    )
                else
                    listOf(
                        "Watch zones are estimates unless calibrated by a test. Zone numbers vary by zone model; a percentage of Max HR is not a measured AeT or AnT.",
                        "Upper limit of Zone 2 (Easy). Conversational effort, key aerobic base for ultra trail endurance.",
                        "Use a tested Lactate Threshold (LTHR) when available. Do not assume every watch Zone 4 boundary is AnT.",
                        "Open Garmin Connect app on your phone.",
                        "Tap More (...) > Settings > User Settings.",
                        "Select Heart Rate & Power Zones > Heart Rate > Zones.",
                        "Copy your tested thresholds if available, or use watch zone boundaries as estimates.",
                        "Open the COROS app on your phone.",
                        "Go to Profile tab (bottom right) > Settings > Heart Rate Zone.",
                        "Select Threshold Heart Rate Zone (or Max HR Zone).",
                        "Check your Aerobic Endurance limit and threshold heart rate. Keep watch-generated values marked as estimates.",
                        "Open the Apple Watch app on your iPhone.",
                        "Scroll down and tap Workout.",
                        "Tap Heart Rate Zones (calculated automatically or manual).",
                        "Automatic zones use a heart rate formula. Treat their boundaries as estimates, not measured thresholds.",
                        "Suunto: Suunto App > Profile > Watch Settings > Intensity Zones.",
                        "Polar: Polar Flow App > Sport Profiles > Heart Rate Zones.",
                        "Strava: You > Settings > Heart Rate > Max & Custom Zones.",
                        "Look for running Lactate Threshold pace in Garmin Connect or Threshold Pace in COROS EvoLab, if available. Use easy runs on flat ground for your easy pace range. Convert min/mile values to min/km before entering them.",
                    )
            val groups =
                if (fieldTest)
                    listOf(
                        "Aerobic threshold (AeT)" to paragraphs.take(1),
                        "Anaerobic threshold (AnT)" to paragraphs.drop(1).take(1),
                        "Paces" to paragraphs.drop(2),
                    )
                else
                    listOf(
                        "Training zones" to paragraphs.take(3),
                        "Garmin" to paragraphs.drop(3).take(4),
                        "COROS" to paragraphs.drop(7).take(4),
                        "Apple Watch" to paragraphs.drop(11).take(4),
                        "Other watches" to paragraphs.drop(15).take(3),
                        "Paces" to paragraphs.drop(18),
                    )
            groups.forEach { (title, copy) ->
                ProfilePanel {
                    Text(L(title), style = MaterialTheme.typography.titleMedium)
                    copy.forEach {
                        Text(
                            L(it),
                            style = MaterialTheme.typography.bodyMedium,
                            color = ai.uphill.app.designsystem.UH.secondary,
                        )
                    }
                }
            }
            if (fieldTest)
                TextButton(
                    onClick = {
                        uri.openUri(
                            "https://evokeendurance.com/resources/our-latest-thinking-on-aerobic-assessment-for-the-mountain-athlete/"
                        )
                    }
                ) {
                    Text(L("Read Evoke's assessment guide"))
                }
            TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) {
                Text(L("Got it"))
            }
        }
    }
}

package ai.uphill.app.feature.me

import ai.uphill.app.R
import ai.uphill.app.core.gear.ShoeRotation
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.racehistory.*
import ai.uphill.app.designsystem.Packshot
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
internal fun ProfilePanel(content: @Composable ColumnScope.() -> Unit) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, UH.line),
    ) {
        Column(
            Modifier.fillMaxWidth().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            content = content,
        )
    }
}

@Composable
internal fun ProfileGroup(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            L(title),
            style = MaterialTheme.typography.bodySmall,
            color = UH.secondary,
            modifier = Modifier.padding(start = 16.dp),
        )
        Surface(color = MaterialTheme.colorScheme.surface, shape = RoundedCornerShape(12.dp)) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp), content = content)
        }
    }
}

@Composable
internal fun ProfileLink(title: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).heightIn(min = 48.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(L(title), Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
        Icon(
            Icons.AutoMirrored.Filled.KeyboardArrowRight,
            null,
            tint = UH.muted,
            modifier = Modifier.size(18.dp),
        )
    }
}

@Composable
internal fun ProfileSegments(
    options: List<Pair<String, String>>,
    selected: String,
    onSelect: (String) -> Unit,
) {
    Surface(color = UH.line.copy(alpha = .6f), shape = RoundedCornerShape(8.dp)) {
        Row(Modifier.fillMaxWidth().padding(3.dp)) {
            options.forEach { (key, title) ->
                Surface(
                    modifier = Modifier.weight(1f).clickable { onSelect(key) },
                    shape = RoundedCornerShape(6.dp),
                    color =
                        if (key == selected) MaterialTheme.colorScheme.surface
                        else Color.Transparent,
                ) {
                    Box(Modifier.padding(vertical = 9.dp), contentAlignment = Alignment.Center) {
                        Text(
                            L(title),
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight =
                                if (key == selected) FontWeight.SemiBold else FontWeight.Normal,
                        )
                    }
                }
            }
        }
    }
}

@Composable
internal fun ProfileAchievements(history: RaceHistoryResponse?, onSelect: (Int) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (history != null) {
            Text(
                L("Road personal bests"),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
            )
            listOf(
                    listOf("5k" to "5 km", "10k" to "10 km"),
                    listOf("hm" to "Half marathon", "fm" to "Marathon"),
                )
                .forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        row.forEach { (key, label) ->
                            val record =
                                history.summary.roadPrs?.get(key)
                                    ?: if (history.summary.roadPrs == null)
                                        when (key) {
                                            "hm" -> history.summary.roadHmPr
                                            "fm" -> history.summary.roadFmPr
                                            else -> null
                                        }
                                    else null
                            Surface(
                                modifier =
                                    Modifier.weight(1f).clickable(
                                        enabled = record?.resultId != null
                                    ) {
                                        record?.resultId?.let(onSelect)
                                    },
                                color = MaterialTheme.colorScheme.surface,
                                shape = RoundedCornerShape(12.dp),
                                border = BorderStroke(1.dp, UH.line),
                            ) {
                                Column(
                                    Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp),
                                ) {
                                    Text(
                                        L(label),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = UH.secondary,
                                    )
                                    Text(
                                        record?.let { raceDuration(it.timeSec) } ?: "—",
                                        fontSize = 24.sp,
                                        fontWeight = FontWeight.Bold,
                                    )
                                    Text(
                                        record?.date
                                            ?: L(
                                                if (record == null) "No confirmed result"
                                                else "Recorded finish"
                                            ),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = UH.secondary,
                                    )
                                }
                            }
                        }
                    }
                }
        }
        val badges = DistanceBadge.derive(history?.results.orEmpty())
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                L("Distance achievements"),
                Modifier.weight(1f),
                style = MaterialTheme.typography.labelSmall,
                color = UH.muted,
            )
            Text(
                "${badges.count { it.unlocked }}/7 ${L("UNLOCKED")}",
                style = MaterialTheme.typography.labelSmall,
                color = UH.accentInk,
            )
        }
        badges.take(6).chunked(3).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { badge ->
                    Surface(
                        modifier =
                            Modifier.weight(1f).clickable(enabled = badge.unlocked) {
                                badge.result?.id?.let(onSelect)
                            },
                        color =
                            if (badge.unlocked) MaterialTheme.colorScheme.surface else UH.surface,
                        shape = RoundedCornerShape(8.dp),
                        border =
                            BorderStroke(
                                1.dp,
                                if (badge.unlocked) UH.accentInk.copy(alpha = .4f) else UH.line,
                            ),
                    ) {
                        Column(
                            Modifier.padding(10.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    badge.category.label,
                                    Modifier.weight(1f),
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = if (badge.unlocked) UH.ink else UH.muted,
                                )
                                Icon(
                                    if (badge.unlocked) Icons.Default.EmojiEvents
                                    else Icons.Default.Lock,
                                    null,
                                    tint = if (badge.unlocked) Color(0xFFB45309) else UH.muted,
                                    modifier = Modifier.size(12.dp),
                                )
                            }
                            Text(
                                if (badge.unlocked) L("Completed") else "—",
                                style = MaterialTheme.typography.labelLarge,
                                color = if (badge.unlocked) UH.ink else UH.muted,
                            )
                            Text(
                                badge.result?.raceName ?: L("Locked"),
                                fontSize = 10.sp,
                                color = UH.secondary,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                    }
                }
            }
        }
        val hundred = badges.last()
        Surface(
            modifier =
                Modifier.fillMaxWidth().clickable(enabled = hundred.unlocked) {
                    hundred.result?.id?.let(onSelect)
                },
            color = UH.surface,
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, UH.line),
        ) {
            Row(
                Modifier.padding(12.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    if (hundred.unlocked) Icons.Default.EmojiEvents else Icons.Default.Lock,
                    null,
                    tint = UH.muted,
                )
                Column {
                    Text(
                        L("100 MILES (161 KM)"),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = UH.muted,
                    )
                    Text(
                        hundred.result?.raceName ?: L("Complete a 100-mile race to unlock"),
                        style = MaterialTheme.typography.bodySmall,
                        color = UH.secondary,
                    )
                }
            }
        }
    }
}

@Composable
internal fun ProfileShoeRotation(rotation: ShoeRotation, onSelect: (String) -> Unit) {
    Column(
        Modifier.testTag("profile.rotation"),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(Modifier.fillMaxWidth()) {
            Text(
                L("SHOE ROTATION"),
                Modifier.weight(1f),
                style = MaterialTheme.typography.labelSmall,
                color = UH.muted,
            )
            Text(
                L("4 SLOTS ACTIVE"),
                style = MaterialTheme.typography.labelSmall,
                color = UH.accentInk,
            )
        }
        listOf("daily", "tempo", "race", "trail").chunked(2).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                row.forEach { slot ->
                    val shoe = rotation.shoe(slot)
                    val wearColor =
                        if ((shoe?.wearRatio ?: 0.0) >= .85) UH.danger
                        else if ((shoe?.wearRatio ?: 0.0) >= .6) UH.warningInk else UH.accentInk
                    Surface(
                        modifier =
                            Modifier.weight(1f)
                                .clickable { onSelect(slot) }
                                .testTag("profile.rotation.$slot"),
                        color = MaterialTheme.colorScheme.surface,
                        shape = RoundedCornerShape(12.dp),
                        border = BorderStroke(1.dp, UH.line),
                    ) {
                        Column(
                            Modifier.padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text(
                                L(slot.replaceFirstChar { it.uppercase() }).uppercase(),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = UH.accentInk,
                            )
                            Surface(
                                color = UH.surface,
                                shape = RoundedCornerShape(8.dp),
                                border = BorderStroke(1.dp, UH.line),
                            ) {
                                Box(
                                    Modifier.fillMaxWidth().height(72.dp).padding(8.dp),
                                    contentAlignment = Alignment.Center,
                                ) {
                                    if (shoe != null) {
                                        Box(Modifier.testTag("profile.rotation.$slot.image")) {
                                            Packshot("shoe", shoe.brand, shoe.model, slot)
                                        }
                                    } else {
                                        Icon(
                                            painterResource(R.drawable.ic_shoe_placeholder),
                                            null,
                                            Modifier.size(28.dp)
                                                .testTag("profile.rotation.$slot.empty"),
                                            tint = UH.muted,
                                        )
                                    }
                                }
                            }
                            if (shoe != null) {
                                Text(shoe.brand.uppercase(), fontSize = 10.sp, color = UH.secondary)
                                Text(
                                    shoe.model,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                Row(Modifier.fillMaxWidth()) {
                                    Text(
                                        "${shoe.distanceKm.toInt()} km",
                                        Modifier.weight(1f),
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                    )
                                    Text(
                                        "${(shoe.wearRatio * 100).toInt()}%",
                                        fontSize = 10.sp,
                                        color = wearColor,
                                    )
                                }
                                LinearProgressIndicator(
                                    progress = { shoe.wearRatio.toFloat() },
                                    modifier = Modifier.fillMaxWidth().height(4.dp),
                                    color = wearColor,
                                    trackColor = UH.line,
                                    gapSize = 0.dp,
                                    drawStopIndicator = {},
                                )
                            } else {
                                Text(L("EMPTY SLOT"), fontSize = 10.sp, color = UH.muted)
                                Text(
                                    L("Tap to assign shoe"),
                                    fontSize = 11.sp,
                                    color = UH.secondary,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ProfileShoeSheet(
    slot: String,
    rotation: ShoeRotation,
    busy: Boolean,
    error: String?,
    onDismiss: () -> Unit,
    onOpenGear: () -> Unit,
    onSave: (ShoeRotation) -> Unit,
) {
    val shoe = rotation.shoe(slot)
    var brand by
        androidx.compose.runtime.remember(slot) {
            androidx.compose.runtime.mutableStateOf(shoe?.brand.orEmpty())
        }
    var model by
        androidx.compose.runtime.remember(slot) {
            androidx.compose.runtime.mutableStateOf(shoe?.model.orEmpty())
        }
    var distance by
        androidx.compose.runtime.remember(slot) {
            androidx.compose.runtime.mutableStateOf((shoe?.distanceKm ?: 0.0).toString())
        }
    var maximum by
        androidx.compose.runtime.remember(slot) {
            androidx.compose.runtime.mutableStateOf((shoe?.maxDistanceKm ?: 700.0).toString())
        }
    ModalBottomSheet(onDismissRequest = { if (!busy) onDismiss() }, containerColor = UH.surface) {
        Column(
            Modifier.fillMaxWidth()
                .padding(16.dp)
                .verticalScroll(androidx.compose.foundation.rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                L(slot.replaceFirstChar { it.uppercase() }),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
            )
            Packshot("shoe", brand, model, slot)
            if (shoe != null)
                ProfilePanel {
                    Text(
                        L("LOG RUN DISTANCE"),
                        style = MaterialTheme.typography.labelSmall,
                        color = UH.muted,
                    )
                    Text(
                        L("Quickly add kilometers from your latest run:"),
                        style = MaterialTheme.typography.bodySmall,
                        color = UH.secondary,
                    )
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        listOf(5.0, 10.0, 15.0, 21.1).forEach { km ->
                            TextButton(
                                onClick = { onSave(rotation.addDistance(slot, km)) },
                                enabled = !busy,
                                modifier = Modifier.weight(1f),
                                contentPadding = PaddingValues(4.dp),
                            ) {
                                Text("+${km.toInt()} km", fontSize = 12.sp)
                            }
                        }
                    }
                }
            val presets =
                when (slot) {
                    "daily" ->
                        listOf(
                            "Nike" to "Pegasus 41",
                            "Hoka" to "Clifton 10",
                            "Asics" to "Novablast 5",
                            "Brooks" to "Glycerin 23",
                            "Saucony" to "Triumph 23",
                        )
                    "tempo" ->
                        listOf(
                            "Saucony" to "Endorphin Speed 4",
                            "Hoka" to "Mach 7",
                            "Adidas" to "Adizero Boston 13",
                            "New Balance" to "FuelCell Rebel v5",
                            "Asics" to "Superblast 3",
                        )
                    "race" ->
                        listOf(
                            "Nike" to "Vaporfly 3",
                            "Nike" to "Alphafly 3",
                            "Hoka" to "Rocket X 3",
                            "Saucony" to "Endorphin Pro 5",
                            "Asics" to "Metaspeed Sky Tokyo",
                        )
                    else ->
                        listOf(
                            "Salomon" to "S/Lab Genesis",
                            "Hoka" to "Speedgoat 6",
                            "Saucony" to "Peregrine 16",
                            "Brooks" to "Cascadia 19",
                            "Altra" to "Mont Blanc Carbon",
                        )
                }
            ProfilePanel {
                Text(L("Popular shoes"), style = MaterialTheme.typography.titleMedium)
                presets.forEach { (presetBrand, presetModel) ->
                    TextButton(
                        onClick = {
                            brand = presetBrand
                            model = presetModel
                            distance = "0"
                        },
                        enabled = !busy,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("$presetBrand $presetModel")
                    }
                }
            }
            OutlinedTextField(
                brand,
                { brand = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text(L("Brand")) },
                singleLine = true,
            )
            OutlinedTextField(
                model,
                { model = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text(L("Model")) },
                singleLine = true,
            )
            OutlinedTextField(
                distance,
                { distance = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text(L("Distance (km)")) },
                singleLine = true,
                keyboardOptions =
                    androidx.compose.foundation.text.KeyboardOptions(
                        keyboardType = androidx.compose.ui.text.input.KeyboardType.Decimal
                    ),
            )
            OutlinedTextField(
                maximum,
                { maximum = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text(L("Max distance (km)")) },
                singleLine = true,
                keyboardOptions =
                    androidx.compose.foundation.text.KeyboardOptions(
                        keyboardType = androidx.compose.ui.text.input.KeyboardType.Decimal
                    ),
            )
            error?.let { Text(it, color = UH.danger) }
            ai.uphill.app.designsystem.PrimaryButton(
                onClick = {
                    onSave(
                        rotation.setShoe(
                            ai.uphill.app.core.gear.ShoeItem(
                                slot,
                                brand.trim(),
                                model.trim(),
                                distance.toDouble(),
                                maximum.toDouble(),
                                notes = shoe?.notes,
                            )
                        )
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                enabled =
                    !busy &&
                        brand.isNotBlank() &&
                        model.isNotBlank() &&
                        distance.toDoubleOrNull()?.let { it.isFinite() && it >= 0 } == true &&
                        maximum.toDoubleOrNull()?.let { it.isFinite() && it > 0 } == true,
            ) {
                Text(L("Save"))
            }
            ProfilePanel {
                ProfileLink("Find Matching Shoes with AI", onOpenGear)
                Text(
                    L("Explore personalized recommendations in Gear Vault"),
                    style = MaterialTheme.typography.bodySmall,
                    color = UH.secondary,
                )
            }
            if (shoe != null)
                TextButton(
                    onClick = { onSave(rotation.remove(slot)) },
                    enabled = !busy,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(L("Remove"), color = UH.danger)
                }
        }
    }
}

@Composable
internal fun ProfileHeartRateBand(resting: Int?, aet: Int?, ant: Int?, maximum: Int?) {
    val r = resting ?: 60
    val m = maxOf(maximum ?: 185, r + 20)
    val span = (m - r).toFloat()
    val aerobic = (((aet ?: 135) - r) / span).coerceIn(.12f, .88f)
    val anaerobic = (((ant ?: 165) - r) / span).coerceIn(.20f, .95f)
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            Text(
                "AeT ${aet ?: "—"}",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = UH.accentInk,
            )
            Text(
                "AnT ${ant ?: "—"}",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = UH.warningInk,
            )
        }
        androidx.compose.foundation.Canvas(Modifier.fillMaxWidth().height(16.dp)) {
            drawRoundRect(
                brush =
                    androidx.compose.ui.graphics.Brush.horizontalGradient(
                        listOf(
                            Color(0xFF0EA5E9),
                            Color(0xFF10B981),
                            Color(0xFFF59E0B),
                            Color(0xFFF97316),
                            Color(0xFFEF4444),
                        )
                    ),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(size.height / 2),
            )
            listOf(aerobic, anaerobic).forEach { fraction ->
                drawLine(
                    Color.White,
                    androidx.compose.ui.geometry.Offset(size.width * fraction, 0f),
                    androidx.compose.ui.geometry.Offset(size.width * fraction, size.height),
                    strokeWidth = 3.dp.toPx(),
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(
                L("Resting %lld bpm", r),
                style = MaterialTheme.typography.bodySmall,
                color = UH.secondary,
            )
            Text(
                L("Max %lld bpm", maximum ?: 185),
                style = MaterialTheme.typography.bodySmall,
                color = UH.secondary,
            )
        }
    }
}

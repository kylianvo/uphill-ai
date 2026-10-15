package ai.uphill.app.feature.coaching

import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import kotlinx.serialization.json.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun CoachedAthleteProfileSheet(
    api: APIClient,
    athlete: CoachedAthleteRow,
    onClose: () -> Unit,
) {
    val service = remember(api) { CoachingService(api) }
    val model: CoachedProfileViewModel =
        viewModel(key = "coach-profile-${athlete.athleteId}") {
            CoachedProfileViewModel(service, athlete.athleteId)
        }
    val state by model.state.collectAsState()
    var editing by remember(athlete.athleteId) { mutableStateOf(false) }
    var draft by remember(athlete.athleteId) { mutableStateOf("") }
    var expanded by remember(athlete.athleteId) { mutableStateOf(true) }
    val locale = LocalConfiguration.current.locales[0]
    LaunchedEffect(model) { model.load() }
    ModalBottomSheet(
        onDismissRequest = onClose,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = UH.surface,
    ) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(.94f).padding(horizontal = 16.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    L("Athlete Profile"),
                    Modifier.weight(1f),
                    fontSize = 17.sp,
                    fontWeight = FontWeight.SemiBold,
                )
                TextButton(onClick = onClose) { Text(L("Done")) }
            }
            if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            Column(
                Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                state.error?.let {
                    Text(P6Error(it), color = UH.danger)
                    TextButton(onClick = model::load, enabled = !state.busy) { Text(L("Retry")) }
                }
                CoachCard {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Box(
                            Modifier.size(48.dp)
                                .background(UH.accent.copy(alpha = .18f), CircleShape),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(
                                athlete.displayName.take(2).uppercase(),
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Black,
                                color = UH.accentInk,
                            )
                        }
                        Column(Modifier.weight(1f)) {
                            Text(
                                athlete.displayName,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.SemiBold,
                            )
                            Text(athlete.athleteEmail, fontSize = 13.sp, color = UH.muted)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            L(if (athlete.status == "active") "Active" else "Invite pending"),
                            color = UH.accentInk,
                            fontSize = 11.sp,
                        )
                        state.profile?.gender?.let {
                            Text(L(it.replaceFirstChar { c -> c.uppercase() }), fontSize = 13.sp)
                        }
                        state.profile?.age?.let { Text(L("%lld yrs", it), fontSize = 13.sp) }
                    }
                }
                CoachCard(modifier = Modifier.testTag("coach.profile.physiology")) {
                    Row(
                        Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Icon(Icons.Default.MonitorHeart, null, Modifier.size(18.dp), tint = UH.ink)
                        Text(
                            L("Physiology & Threshold Zones"),
                            Modifier.weight(1f),
                            fontSize = 20.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        TextButton(
                            onClick = { editing = true },
                            enabled = state.profile != null && !state.busy,
                            modifier = Modifier.testTag("coach.profile.edit"),
                        ) {
                            Text(L("Edit"))
                        }
                    }
                    val profile = state.profile
                    listOf(
                            listOf(
                                Triple("Resting HR", "resting_hr", profile?.restingHr),
                                Triple("Max HR", "max_hr", profile?.maxHr),
                            ),
                            listOf(
                                Triple("AeT Threshold (Z2)", "aet_hr", profile?.aetHr),
                                Triple("AnT Threshold (Z4)", "ant_hr", profile?.antHr),
                            ),
                        )
                        .forEach { row ->
                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                row.forEach { (label, key, value) ->
                                    val source = profile?.fieldSources?.get(key) as? JsonObject
                                    val color =
                                        when (key) {
                                            "aet_hr" -> Color(0xFF2563EB)
                                            "ant_hr" -> UH.warningInk
                                            else -> UH.ink
                                        }
                                    Column(
                                        Modifier.weight(1f)
                                            .background(
                                                UH.hover.copy(alpha = .6f),
                                                RoundedCornerShape(8.dp),
                                            )
                                            .padding(10.dp)
                                    ) {
                                        Text(L(label), fontSize = 11.sp, color = UH.muted)
                                        Text(
                                            value?.let { "$it bpm" } ?: "—",
                                            fontSize = 15.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            color =
                                                if (
                                                    source
                                                        ?.get("source")
                                                        ?.jsonPrimitive
                                                        ?.contentOrNull == "default"
                                                )
                                                    UH.muted
                                                else color,
                                        )
                                        ProfileProvenance(source)
                                    }
                                }
                            }
                        }
                    if (profile?.zone2PaceMin != null && profile.zone2PaceMax != null) {
                        ProfileValue(
                            "Zone 2 Pace Range:",
                            "${profile.zone2PaceMin} – ${profile.zone2PaceMax} /km",
                            Color(0xFF2563EB),
                        )
                        val slow = profile.fieldSources?.get("zone2_pace_min") as? JsonObject
                        val fast = profile.fieldSources?.get("zone2_pace_max") as? JsonObject
                        ProfileProvenance(
                            if (fast?.get("source")?.jsonPrimitive?.contentOrNull == "coach") fast
                            else slow
                        )
                    }
                    profile?.thresholdPace?.let {
                        ProfileValue("Threshold Pace:", "$it /km", UH.warningInk)
                        ProfileProvenance(
                            profile.fieldSources?.get("threshold_pace") as? JsonObject
                        )
                    }
                }
                CoachChartCard(
                    "Training Preferences & Constraints",
                    Icons.Default.CalendarMonth,
                    modifier = Modifier.testTag("coach.profile.preferences"),
                ) {
                    state.profile?.let { profile ->
                        ProfileValue(
                            "Weekly Sessions:",
                            profile.daysPerWeek?.let { L("%lld days/week", it) } ?: "—",
                        )
                        profile.longRunDay?.let {
                            ProfileValue("Designated Long Run:", L(it), UH.accentInk)
                        }
                        profile.preferredRunDays?.let { raw ->
                            val days =
                                runCatching {
                                        Json.parseToJsonElement(raw).jsonArray.map {
                                            it.jsonPrimitive.content
                                        }
                                    }
                                    .getOrNull()
                            ProfileValue(
                                "Running Days:",
                                days?.map { L(it) }?.joinToString(", ") ?: raw,
                            )
                        }
                        profile.injuryHistory
                            ?.takeIf { it.isNotBlank() }
                            ?.let { ProfileText("Injury Notes / Limitations:", it, UH.danger) }
                        profile.athleteNotes
                            ?.takeIf { it.isNotBlank() }
                            ?.let { ProfileText("Athlete Notes:", it, UH.secondary) }
                    }
                }
                CoachCard {
                    TextButton(
                        onClick = { expanded = !expanded },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Icon(Icons.Default.Forum, null, Modifier.size(16.dp), tint = UH.accentInk)
                        Spacer(Modifier.width(8.dp))
                        Text(L("Coach Notes (%lld)", state.notes.size), Modifier.weight(1f))
                        Icon(
                            if (expanded) Icons.Default.KeyboardArrowUp
                            else Icons.Default.KeyboardArrowDown,
                            null,
                        )
                    }
                    if (expanded) {
                        if (state.notes.isEmpty() && !state.busy)
                            Text(
                                L(
                                    "No coach notes yet. Leave training feedback or execution advice here."
                                ),
                                fontSize = 13.sp,
                                color = UH.muted,
                            )
                        state.notes.forEach { note ->
                            Column(
                                Modifier.fillMaxWidth()
                                    .background(
                                        UH.hover.copy(alpha = .6f),
                                        RoundedCornerShape(8.dp),
                                    )
                                    .padding(10.dp)
                            ) {
                                Text(note.note)
                                note.createdAt?.let { raw ->
                                    runCatching {
                                            OffsetDateTime.parse(raw)
                                                .atZoneSameInstant(ZoneId.systemDefault())
                                                .format(
                                                    DateTimeFormatter.ofLocalizedDateTime(
                                                            FormatStyle.SHORT
                                                        )
                                                        .withLocale(locale)
                                                )
                                        }
                                        .getOrNull()
                                        ?.let { Text(it, fontSize = 10.sp, color = UH.muted) }
                                }
                            }
                        }
                        OutlinedTextField(
                            draft,
                            { draft = it },
                            modifier = Modifier.fillMaxWidth().testTag("coach.profile.note.input"),
                            label = { Text(L("Add a note for this %@...", L("athlete"))) },
                            maxLines = 4,
                            enabled = !state.busy,
                        )
                        PrimaryButton(
                            onClick = { model.post(draft) { draft = "" } },
                            enabled = draft.isNotBlank() && !state.busy,
                            modifier = Modifier.testTag("coach.profile.note.post"),
                        ) {
                            Text(L("Post"))
                        }
                    }
                }
            }
        }
    }
    if (editing)
        state.profile?.let { profile ->
            PhysiologyDialog(profile, state.busy, state.error, { editing = false }) { patch ->
                model.save(patch) { editing = false }
            }
        }
}

@Composable
private fun ProfileValue(label: String, value: String, color: Color = UH.ink) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(L(label), Modifier.weight(1f), color = UH.secondary, fontSize = 13.sp)
        Text(
            value,
            Modifier.weight(1f),
            color = color,
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun ProfileText(label: String, value: String, color: Color) {
    Column(
        Modifier.fillMaxWidth()
            .background(color.copy(alpha = .06f), RoundedCornerShape(8.dp))
            .padding(8.dp)
    ) {
        Text(L(label), fontSize = 13.sp, color = color)
        Text(value, fontSize = 13.sp, color = UH.ink)
    }
}

@Composable
private fun ProfileProvenance(source: JsonObject?) {
    if (source == null) return
    fun field(key: String) = source[key]?.jsonPrimitive?.contentOrNull
    val coach = field("source") == "coach"
    val label =
        when (field("source")) {
            "coach" -> {
                val name = field("by_name") ?: L("Coach")
                val locale = LocalConfiguration.current.locales[0]
                val date =
                    field("at")?.take(10)?.let {
                        runCatching {
                                LocalDate.parse(it)
                                    .format(DateTimeFormatter.ofPattern("d MMM", locale))
                            }
                            .getOrNull()
                    }
                if (date != null) L("Set by %@ · %@", name, date) else L("Set by %@", name)
            }
            "athlete" ->
                L(
                    when (field("method")) {
                        "lab" -> "Athlete · lab test"
                        "field" -> "Athlete · field test"
                        "estimated" -> "Athlete · watch/formula"
                        null -> "Entered by athlete"
                        else -> "Athlete · method unknown"
                    }
                )
            else -> L("App default, not measured")
        }
    Text(
        label,
        fontSize = 11.sp,
        color = if (coach) UH.accentInk else UH.muted,
        fontWeight = if (coach) FontWeight.SemiBold else FontWeight.Normal,
    )
}

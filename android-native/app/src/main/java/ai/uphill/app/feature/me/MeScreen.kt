package ai.uphill.app.feature.me

import ai.uphill.app.BuildConfig
import ai.uphill.app.core.auth.*
import ai.uphill.app.core.localization.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.plan.TrainingNavigation
import ai.uphill.app.core.profile.ProfileService
import ai.uphill.app.designsystem.UH
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AddCircleOutline
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.RemoveCircleOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import kotlinx.serialization.json.*

@Composable
fun MeScreen(
    api: APIClient,
    user: User,
    lang: String,
    onNavigate: (String) -> Unit,
    onLanguage: (String) -> Unit,
    onEnvironment: (String) -> Unit,
    onLogout: () -> Unit,
    onUser: (User) -> Unit,
) {
    var editor by remember { mutableStateOf<String?>(null) }
    var guide by remember { mutableStateOf(false) }
    var devMenu by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<Throwable?>(null) }
    var busy by remember { mutableStateOf(false) }
    var savedFields by remember(editor) { mutableStateOf<Map<String, String>?>(null) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val service = remember(api) { ProfileService(api) }
    val requestedSection by TrainingNavigation.profileSection.collectAsState()
    LaunchedEffect(requestedSection) {
        requestedSection?.let {
            if (it in setOf("about", "hr", "paces")) editor = it
            TrainingNavigation.profileSection.value = null
        }
    }
    var history by
        remember(api, user.id) {
            mutableStateOf<ai.uphill.app.core.racehistory.RaceHistoryResponse?>(null)
        }
    var rotation by
        remember(api, user.id) { mutableStateOf(ai.uphill.app.core.gear.ShoeRotation()) }
    var shoeSlot by remember { mutableStateOf<String?>(null) }
    var detailId by remember { mutableStateOf<Int?>(null) }
    val raceService = remember(api) { ai.uphill.app.core.racehistory.RaceHistoryService(api) }
    LaunchedEffect(api, user.id) {
        launch { runCatching { raceService.history() }.onSuccess { history = it } }
        launch {
            runCatching { ai.uphill.app.core.gear.GearService(api).rotation() }
                .onSuccess { rotation = it }
        }
    }
    if (editor == null)
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            Text(
                L("Me"),
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
            )
            ProfilePanel {
                Text(
                    user.name,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )
                Text(user.email, style = MaterialTheme.typography.bodySmall, color = UH.secondary)
            }
            if (!user.coachProfileChanges.isNullOrEmpty())
                ProfilePanel {
                    Text(L("Your coach updated your training zones."))
                    TextButton(
                        onClick = {
                            scope.launch {
                                try {
                                    onUser(service.acknowledge())
                                } catch (e: Exception) {
                                    error = e
                                }
                            }
                        }
                    ) {
                        Text(L("Got it"))
                    }
                }
            ProfileAchievements(history, onSelect = { detailId = it })
            ProfileShoeRotation(rotation) { shoeSlot = it }
            ProfileGroup("Training") {
                ProfileLink("About you") { editor = "about" }
                HorizontalDivider(color = UH.line)
                ProfileLink("Training zones") { editor = "hr" }
                HorizontalDivider(color = UH.line)
                ProfileLink("Race history") { onNavigate("racehistory") }
            }
            ProfileGroup("Tools & Labs") {
                listOf(
                        "Pace Strategy" to "pace",
                        "Goal Determiner" to "goal",
                        "Nutrition Lab" to "nutrition",
                        "Gear Vault" to "gear",
                        "Knowledge Hub" to "knowledge",
                    )
                    .forEachIndexed { index, (title, route) ->
                        if (index > 0) HorizontalDivider(color = UH.line)
                        ProfileLink(title) { onNavigate(route) }
                    }
            }
            ProfileGroup("Training profile") {
                listOf(
                        "Weekly volume" to user.currentWeeklyKm?.let { "${it.toInt()} km" },
                        "Days per week" to user.daysPerWeek?.toString(),
                        "Long run day" to user.longRunDay?.let { L(it) },
                        "Aerobic threshold HR" to user.aetHr?.let { "$it bpm" },
                        "Anaerobic threshold HR" to user.antHr?.let { "$it bpm" },
                        "Zone 2 pace" to
                            user.zone2PaceMin?.let { lo ->
                                user.zone2PaceMax?.let { hi -> "$lo–$hi /km" }
                            },
                    )
                    .forEachIndexed { index, (label, value) ->
                        if (index > 0) HorizontalDivider(color = UH.line)
                        Row(
                            Modifier.fillMaxWidth().padding(vertical = 12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                L(label),
                                Modifier.weight(1f),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Text(
                                value ?: L("Not set"),
                                style = MaterialTheme.typography.bodyMedium,
                                color = UH.secondary,
                            )
                        }
                    }
            }
            ProfileConnectedAccounts(api, user.id) { onNavigate("integrations") }
            ProfileGroup("Your coach") { ProfileLink("Your coach") { onNavigate("athletes") } }
            ProfilePanel {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(L("Language"), Modifier.weight(1f))
                    TextButton(onClick = { onLanguage("en") }) {
                        Text("English", color = if (lang == "en") UH.accentInk else UH.secondary)
                    }
                    TextButton(onClick = { onLanguage("vi") }) {
                        Text("Tiếng Việt", color = if (lang == "vi") UH.accentInk else UH.secondary)
                    }
                }
            }
            ProfileGroup("Account") {
                if (user.provider == "email") {
                    ProfileLink("Change password") { editor = "password" }
                    HorizontalDivider(color = UH.line)
                }
                TextButton(
                    onClick = onLogout,
                    enabled = !busy,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(L("Sign out"), color = UH.danger)
                }
            }
            error?.let { Text(localizedError(context, it), color = UH.danger) }
            Text(
                "Uphill AI ${BuildConfig.VERSION_NAME}",
                color = UH.muted,
                style = MaterialTheme.typography.bodySmall,
                modifier =
                    Modifier.align(Alignment.CenterHorizontally)
                        .combinedClickable(
                            onClick = {},
                            onLongClick = { if (BuildConfig.DEBUG) devMenu = true },
                        ),
            )
        }
    shoeSlot?.let { slot ->
        ProfileShoeSheet(
            slot,
            rotation,
            busy,
            error?.let { localizedError(context, it) },
            {
                shoeSlot = null
                error = null
            },
            {
                shoeSlot = null
                onNavigate("gear")
            },
        ) { changed ->
            busy = true
            scope.launch {
                try {
                    rotation = ai.uphill.app.core.gear.GearService(api).save(changed)
                    shoeSlot = null
                    error = null
                } catch (e: Exception) {
                    error = e
                } finally {
                    busy = false
                }
            }
        }
    }
    detailId?.let {
        ai.uphill.app.designsystem.RaceDetailDialog(raceService, it, { detailId = null })
    }
    if (guide) WatchZonesGuide { guide = false }
    if (devMenu && BuildConfig.DEBUG)
        AlertDialog(
            onDismissRequest = { devMenu = false },
            title = { Text(L("Environment")) },
            text = {
                Column {
                    listOf(
                            "Local" to AppEnvironment.local,
                            "Local (USB)" to "http://127.0.0.1:8000",
                            "Staging" to AppEnvironment.staging,
                            "Production" to AppEnvironment.production,
                        )
                        .forEach { (title, url) ->
                            TextButton(
                                onClick = {
                                    onEnvironment(url)
                                    devMenu = false
                                }
                            ) {
                                Text(L(title))
                            }
                        }
                }
            },
            confirmButton = {},
        )
    editor?.let { section ->
        ProfileEditor(
            section,
            user,
            service,
            busy,
            error?.let { localizedError(context, it) },
            savedFields,
            onGuide = { guide = true },
            onDismiss = {
                editor = null
                error = null
            },
        ) { fields ->
            busy = true
            error = null
            savedFields = null
            scope.launch {
                try {
                    if (section == "password") service.password(fields.getValue("password"))
                    else onUser(service.update(user, fields))
                    savedFields = if (section == "password") emptyMap() else fields
                } catch (e: Exception) {
                    error = e
                } finally {
                    busy = false
                }
            }
        }
    }
}

@Composable
private fun ProfileEditor(
    section: String,
    user: User,
    service: ProfileService,
    busy: Boolean,
    error: String?,
    savedFields: Map<String, String>?,
    onGuide: () -> Unit,
    onDismiss: () -> Unit,
    save: (Map<String, String>) -> Unit,
) {
    BackHandler(enabled = !busy, onBack = onDismiss)
    var selectedTab by
        remember(section) { mutableStateOf(if (section == "paces") "paces" else "hr") }
    val zoneEditor = section == "hr" || section == "paces"
    val labels =
        when {
            section == "about" ->
                listOf(
                    "age" to "Age",
                    "gender" to "Sex",
                    "height_cm" to "Height",
                    "weight_kg" to "Weight",
                    "athlete_notes" to "Injuries and notes for Coach Uphill",
                )
            zoneEditor ->
                listOf(
                    "resting_hr" to "Resting heart rate",
                    "aet_hr" to "Aerobic threshold (AeT)",
                    "ant_hr" to "Anaerobic threshold (AnT)",
                    "max_hr" to "Max heart rate",
                    "zone2_pace_min" to "Easy pace, slower end",
                    "zone2_pace_max" to "Easy pace, faster end",
                    "threshold_pace" to "Threshold pace",
                    "pace_zone_model" to "Pace zone model",
                )
            else -> listOf("password" to "New Password", "confirmation" to "Confirm New Password")
        }
    val original =
        mapOf(
            "age" to (user.age ?: 30).toString(),
            "gender" to user.gender.orEmpty(),
            "height_cm" to user.heightCm?.toString().orEmpty(),
            "weight_kg" to user.weightKg?.toString().orEmpty(),
            "athlete_notes" to user.athleteNotes.orEmpty(),
            "resting_hr" to (user.restingHr ?: 60).toString(),
            "aet_hr" to (user.aetHr ?: 135).toString(),
            "ant_hr" to (user.antHr ?: 165).toString(),
            "max_hr" to (user.maxHr ?: 185).toString(),
            "zone2_pace_min" to user.zone2PaceMin.orEmpty(),
            "zone2_pace_max" to user.zone2PaceMax.orEmpty(),
            "threshold_pace" to user.thresholdPace.orEmpty(),
            "pace_zone_model" to (user.paceZoneModel ?: "5_zone"),
        )
    val fields =
        remember(section) {
            mutableStateMapOf<String, String>().apply {
                labels.forEach { put(it.first, original[it.first].orEmpty()) }
            }
        }
    LaunchedEffect(savedFields) {
        if (section == "password" && savedFields != null) {
            fields["password"] = ""
            fields["confirmation"] = ""
        }
    }
    val saved =
        savedFields != null &&
            if (section == "password")
                fields["password"].isNullOrEmpty() && fields["confirmation"].isNullOrEmpty()
            else fields.toMap() == savedFields
    val valid =
        when (section) {
            "password" ->
                fields["password"].orEmpty().length >= 8 &&
                    fields["password"] == fields["confirmation"]
            "about" ->
                fields["age"]?.toIntOrNull() in 15..99 &&
                    fields["height_cm"]?.let {
                        it.isBlank() ||
                            it.toDoubleOrNull()?.let { n -> n.isFinite() && n in 120.0..230.0 } ==
                                true
                    } == true &&
                    fields["weight_kg"]?.let {
                        it.isBlank() ||
                            it.toDoubleOrNull()?.let { n -> n.isFinite() && n in 35.0..180.0 } ==
                                true
                    } == true
            "hr",
            "paces" ->
                listOf("resting_hr", "aet_hr", "ant_hr", "max_hr")
                    .map { fields[it]?.toIntOrNull() ?: 0 }
                    .let {
                        it[0] in 30..110 &&
                            it[0] < it[1] &&
                            it[1] < it[2] &&
                            it[2] <= it[3] &&
                            it[3] <= 240 &&
                            fields["pace_zone_model"] in listOf("4_zone", "5_zone") &&
                            listOf("zone2_pace_min", "zone2_pace_max", "threshold_pace").all { key
                                ->
                                fields[key].orEmpty().let { pace ->
                                    pace.isBlank() || Regex("[0-9]{1,2}:[0-5][0-9]").matches(pace)
                                }
                            }
                    }
            else -> fields["pace_zone_model"] in listOf("4_zone", "5_zone")
        }
    var zones by remember { mutableStateOf<kotlinx.serialization.json.JsonObject?>(null) }
    var zoneError by remember { mutableStateOf<Throwable?>(null) }
    var retry by remember { mutableIntStateOf(0) }
    val context = LocalContext.current
    LaunchedEffect(zoneEditor, fields["pace_zone_model"], savedFields, retry) {
        if (zoneEditor) {
            zones = null
            zoneError = null
            try {
                zones = service.zones(fields["pace_zone_model"] ?: "5_zone")
            } catch (e: Exception) {
                zoneError = e
            }
        }
    }
    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onDismiss, enabled = !busy) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = L("Back"))
            }
            Text(
                L(
                    if (section == "about") "About you"
                    else if (section == "password") "Change password" else "Training zones"
                ),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            if (zoneEditor)
                ProfileSegments(listOf("hr" to "Heart Rate", "paces" to "Paces"), selectedTab) {
                    selectedTab = it
                }
            when {
                section == "about" -> {
                    ProfilePanel {
                        Text(
                            L("Athlete Profile"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L("Calibrates calorie expenditure, pacing models, and recovery rates."),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        ProfileNumber("Age", fields, "age", 15..99, "years")
                        HorizontalDivider(color = UH.line)
                        Text(L("Sex"), style = MaterialTheme.typography.labelLarge)
                        listOf(
                                listOf("female" to "Female", "male" to "Male"),
                                listOf("other" to "Other", "" to "Private"),
                            )
                            .forEach { row ->
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    row.forEach { (key, label) ->
                                        FilterChip(
                                            selected = fields["gender"] == key,
                                            onClick = { fields["gender"] = key },
                                            label = { Text(L(label)) },
                                            modifier = Modifier.weight(1f),
                                        )
                                    }
                                }
                            }
                        HorizontalDivider(color = UH.line)
                        ProfileNumber("Height", fields, "height_cm", 120..230, "cm")
                        HorizontalDivider(color = UH.line)
                        ProfileNumber("Weight", fields, "weight_kg", 35..180, "kg")
                    }
                    ProfilePanel {
                        Text(
                            L("Injuries and notes for Coach Uphill"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L("Mention past injuries, current niggles, or training constraints."),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        OutlinedTextField(
                            fields["athlete_notes"].orEmpty(),
                            { fields["athlete_notes"] = it },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 3,
                            maxLines = 8,
                            placeholder = { Text(L("Athlete notes")) },
                        )
                    }
                }
                zoneEditor && selectedTab == "hr" -> {
                    ProfilePanel {
                        Text(
                            L("Heart Rate Spectrum"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L(
                                "Visualizing your aerobic (AeT) and anaerobic (AnT) thresholds from resting to max."
                            ),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        ProfileHeartRateBand(
                            fields["resting_hr"]?.toIntOrNull(),
                            fields["aet_hr"]?.toIntOrNull(),
                            fields["ant_hr"]?.toIntOrNull(),
                            fields["max_hr"]?.toIntOrNull(),
                        )
                        listOf(
                                listOf("resting_hr" to "RESTING", "aet_hr" to "AEROBIC (AeT)"),
                                listOf("ant_hr" to "ANAEROBIC (AnT)", "max_hr" to "MAX HR"),
                            )
                            .forEach { row ->
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    row.forEach { (key, label) ->
                                        Surface(
                                            modifier = Modifier.weight(1f),
                                            color = UH.surface,
                                            shape = RoundedCornerShape(8.dp),
                                            border = BorderStroke(1.dp, UH.line),
                                        ) {
                                            Column(Modifier.padding(8.dp)) {
                                                Text(
                                                    L(label),
                                                    fontSize = 10.sp,
                                                    color = UH.secondary,
                                                    fontWeight = FontWeight.Bold,
                                                )
                                                Text(
                                                    "${fields[key]} bpm",
                                                    fontSize = 15.sp,
                                                    fontWeight = FontWeight.Bold,
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                    }
                    ProfilePanel {
                        Text(
                            L("Heart rate anchors"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        listOf(
                                Triple("max_hr", "Max heart rate", 120..240),
                                Triple("resting_hr", "Resting heart rate", 30..110),
                                Triple("aet_hr", "Aerobic threshold (AeT)", 90..190),
                                Triple("ant_hr", "Anaerobic threshold (AnT)", 120..220),
                            )
                            .forEachIndexed { index, (key, label, range) ->
                                if (index > 0) HorizontalDivider(color = UH.line)
                                ProfileNumber(label, fields, key, range, "bpm")
                            }
                    }
                    ProfilePanel {
                        ProfileLink("How to find your zones", onGuide)
                        Text(
                            L("Step-by-step instructions for Garmin, COROS & Apple Watch"),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                    }
                }
                zoneEditor -> {
                    ProfilePanel {
                        Text(
                            L("YOUR EASY PACE"),
                            style = MaterialTheme.typography.labelSmall,
                            color = UH.accentInk,
                        )
                        Text(
                            "${fields["zone2_pace_min"].orEmpty().ifBlank { "—" }} – ${fields["zone2_pace_max"].orEmpty().ifBlank { "—" }} /km",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L(
                                "Most of your running happens here. Conversational aerobic effort that builds stamina without accumulating excess fatigue."
                            ),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                    }
                    ProfilePanel {
                        Text(
                            L("Training Zones"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L("Calibrated from your threshold & fitness profile"),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        ProfileSegments(
                            listOf("5_zone" to "5 zones", "4_zone" to "4 zones"),
                            fields["pace_zone_model"] ?: "5_zone",
                        ) {
                            fields["pace_zone_model"] = it
                        }
                        if (zones == null && zoneError == null)
                            CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
                        zoneError?.let {
                            Text(localizedError(context, it), color = UH.danger)
                            TextButton(onClick = { retry++ }) { Text(L("Retry")) }
                        }
                        zones?.let { data ->
                            val names =
                                if (fields["pace_zone_model"] == "4_zone")
                                    listOf(
                                        "Zone 1 · Easy / Aerobic",
                                        "Zone 2 · Tempo",
                                        "Zone 3 · Threshold",
                                        "Zone 4 · Anaerobic / Max",
                                    )
                                else
                                    listOf(
                                        "Zone 1 · Recovery",
                                        "Zone 2 · Easy / Aerobic",
                                        "Zone 3 · Tempo",
                                        "Zone 4 · Threshold",
                                        "Zone 5 · VO2max / Speed",
                                    )
                            names.forEachIndexed { index, name ->
                                if (index > 0) HorizontalDivider(color = UH.line)
                                Row(
                                    Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text(
                                        L(name),
                                        Modifier.weight(1f),
                                        style = MaterialTheme.typography.labelLarge,
                                    )
                                    Text(
                                        "${data["zone${index + 1}_pace"]?.jsonPrimitive?.contentOrNull ?: "—"} /km",
                                        style = MaterialTheme.typography.bodySmall,
                                        fontWeight = FontWeight.Bold,
                                    )
                                }
                                LinearProgressIndicator(
                                    progress = { (index + 1f) / names.size },
                                    modifier = Modifier.fillMaxWidth().height(4.dp),
                                    color =
                                        listOf(
                                            Color(0xFF0EA5E9),
                                            Color(0xFF10B981),
                                            Color(0xFFF59E0B),
                                            Color(0xFFF97316),
                                            Color(0xFFEF4444),
                                        )[index],
                                    trackColor = UH.line,
                                )
                            }
                        }
                    }
                    ProfilePanel {
                        Text(
                            L("Adjust"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L(
                                "Fine-tune your training anchors. Your next week adapts automatically."
                            ),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        listOf(
                                "threshold_pace" to "Threshold pace",
                                "zone2_pace_min" to "Easy pace, slower end",
                                "zone2_pace_max" to "Easy pace, faster end",
                            )
                            .forEach { (key, label) ->
                                OutlinedTextField(
                                    fields[key].orEmpty(),
                                    { fields[key] = it },
                                    modifier = Modifier.fillMaxWidth(),
                                    label = { Text(L(label)) },
                                    placeholder = { Text("m:ss") },
                                    suffix = { Text("/km") },
                                    singleLine = true,
                                    keyboardOptions =
                                        KeyboardOptions(keyboardType = KeyboardType.Ascii),
                                )
                            }
                    }
                }
                else ->
                    ProfilePanel {
                        Text(
                            L("Set New Password"),
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            L("Choose a password with at least 8 characters."),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                        labels.forEach { (key, label) ->
                            OutlinedTextField(
                                fields[key].orEmpty(),
                                { fields[key] = it },
                                modifier = Modifier.fillMaxWidth(),
                                label = { Text(L(label)) },
                                visualTransformation = PasswordVisualTransformation(),
                                singleLine = true,
                                keyboardOptions =
                                    KeyboardOptions(keyboardType = KeyboardType.Password),
                            )
                        }
                    }
            }
            error?.let { Text(it, color = UH.danger) }
            if (saved)
                Row(
                    Modifier.fillMaxWidth().semantics { liveRegion = LiveRegionMode.Polite },
                    horizontalArrangement =
                        Arrangement.spacedBy(6.dp, Alignment.CenterHorizontally),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = UH.accentInk,
                        modifier = Modifier.size(18.dp),
                    )
                    Text(
                        L(
                            if (section == "password") "Password updated successfully."
                            else "Saved. Your next week will use these."
                        ),
                        style = MaterialTheme.typography.labelLarge,
                        color = UH.accentInk,
                    )
                }
            ai.uphill.app.designsystem.PrimaryButton(
                onClick = { save(fields.filterKeys { it != "confirmation" }) },
                enabled = valid && !busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (busy) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                else Text(L(if (section == "password") "Change password" else "Save"))
            }
        }
    }
}

@Composable
private fun ProfileNumber(
    label: String,
    fields: MutableMap<String, String>,
    key: String,
    range: IntRange,
    unit: String,
) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(L(label), style = MaterialTheme.typography.labelLarge)
            Text(
                "${range.first}–${range.last} ${L(unit)}",
                style = MaterialTheme.typography.bodySmall,
                color = UH.muted,
            )
        }
        IconButton(
            onClick = {
                fields[key] =
                    ((fields[key]?.toDoubleOrNull() ?: range.first.toDouble()) - 1)
                        .coerceIn(range.first.toDouble(), range.last.toDouble())
                        .toInt()
                        .toString()
            }
        ) {
            Icon(Icons.Default.RemoveCircleOutline, contentDescription = L("Decrease"))
        }
        OutlinedTextField(
            fields[key].orEmpty(),
            { fields[key] = it },
            modifier = Modifier.width(72.dp),
            singleLine = true,
            textStyle = MaterialTheme.typography.labelLarge,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        )
        IconButton(
            onClick = {
                fields[key] =
                    ((fields[key]?.toDoubleOrNull() ?: range.first.toDouble()) + 1)
                        .coerceIn(range.first.toDouble(), range.last.toDouble())
                        .toInt()
                        .toString()
            }
        ) {
            Icon(Icons.Default.AddCircleOutline, contentDescription = L("Increase"))
        }
    }
}

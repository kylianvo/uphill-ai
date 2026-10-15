package ai.uphill.app.feature.chat

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.chat.*
import ai.uphill.app.core.gear.GearPlan
import ai.uphill.app.core.localization.*
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.nutrition.NutritionPlan
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ThumbDown
import androidx.compose.material.icons.outlined.ThumbUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.serialization.json.*

@Composable
fun ChatScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val context = LocalContext.current
    val model: ChatViewModel =
        viewModel(
            factory =
                viewModelFactory { initializer { ChatViewModel(api, user, ChatHistory(context)) } }
        )
    val state by model.state.collectAsState()
    var input by remember { mutableStateOf("") }
    var confirmClear by remember { mutableStateOf(false) }
    val scroll = rememberLazyListState()
    LaunchedEffect(state.messages.size, state.messages.lastOrNull()?.content?.length) {
        if (state.messages.isNotEmpty()) scroll.animateScrollToItem(state.messages.lastIndex)
    }
    Column(Modifier.fillMaxSize().imePadding()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(L("Coach Uphill"), style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = { confirmClear = true }, enabled = !state.busy) {
                Text(L("Clear"))
            }
        }
        LazyColumn(
            Modifier.weight(1f).fillMaxWidth().testTag("chat.messages"),
            state = scroll,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            if (state.hasMore)
                item { TextButton(onClick = model::older) { Text(L("Load older messages")) } }
            items(state.messages, key = { it.id }) { message ->
                Surface(
                    color =
                        if (message.role == "user") UH.hover else MaterialTheme.colorScheme.surface,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(
                        Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        if (message.content.isNotEmpty()) Text(message.content)
                        message.tools.forEach { tool ->
                            RichCard(
                                tool,
                                state.proposals,
                                model,
                                onNavigate,
                                state.pendingProposals,
                            )
                        }
                        if (message.interrupted)
                            Text(L("Response interrupted"), color = UH.warningInk)
                        if (message.role == "assistant" && message.numericId != null)
                            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                if (message.role == "assistant")
                                    TextButton(onClick = { model.sources(message.numericId) }) {
                                        Text(L("Sources"))
                                    }
                                TextButton(
                                    onClick = {
                                        model.feedback(
                                            message.numericId,
                                            if (message.feedback == 1) 0 else 1,
                                        )
                                    }
                                ) {
                                    Icon(
                                        Icons.Outlined.ThumbUp,
                                        L("Helpful response"),
                                        tint = if (message.feedback == 1) UH.accentInk else UH.muted,
                                    )
                                }
                                TextButton(
                                    onClick = {
                                        model.feedback(
                                            message.numericId,
                                            if (message.feedback == -1) 0 else -1,
                                        )
                                    }
                                ) {
                                    Icon(
                                        Icons.Outlined.ThumbDown,
                                        L("Unhelpful response"),
                                        tint =
                                            if (message.feedback == -1) UH.accentInk else UH.muted,
                                    )
                                }
                            }
                    }
                }
            }
        }
        if (state.status.isNotBlank())
            Text(L(state.status), Modifier.padding(horizontal = 20.dp), color = UH.muted)
        state.error?.let {
            Text(
                localizedError(context, it),
                Modifier.padding(horizontal = 16.dp),
                color = UH.danger,
            )
        }
        if (!state.busy && state.retryOf != null)
            TextButton(onClick = { model.send("", lang, state.retryOf) }) { Text(L("Retry")) }
        if (state.clarify.isNotEmpty())
            LazyRow(
                Modifier.fillMaxWidth().padding(8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(state.clarify) { option ->
                    SuggestionChip(
                        onClick = { model.send(option, lang) },
                        label = { Text(option) },
                        enabled = !state.busy,
                    )
                }
                item {
                    TextButton(onClick = model::dismissSuggestions) {
                        Text(L("Dismiss suggestions"))
                    }
                }
            }
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                input,
                { if (it.length <= 2000) input = it },
                modifier = Modifier.weight(1f).testTag("chat.input"),
                label = { Text(L("Ask Coach Uphill")) },
                maxLines = 5,
                enabled = !state.busy,
            )
            if (state.busy) TextButton(onClick = model::stop) { Text(L("Stop")) }
            else
                TextButton(
                    onClick = {
                        model.send(input, lang)
                        input = ""
                    },
                    enabled = input.isNotBlank(),
                    modifier = Modifier.testTag("chat.send"),
                ) {
                    Text(L("Send"))
                }
        }
    }
    if (confirmClear)
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text(L("Clear conversation?")) },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirmClear = false
                        model.clear()
                    }
                ) {
                    Text(L("Clear"))
                }
            },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text(L("Cancel")) } },
        )
    state.sources?.let { sources ->
        val uri = LocalUriHandler.current
        AlertDialog(
            onDismissRequest = model::closeSources,
            title = { Text(L("Sources")) },
            text = {
                Column(
                    Modifier.heightIn(max = 560.dp).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    (sources["citations"] as? JsonArray).orEmpty().forEach { element ->
                        val o = element.jsonObject
                        Text(
                            o.s("title").ifBlank { o.s("book") },
                            style = MaterialTheme.typography.titleSmall,
                        )
                        Text(
                            listOf(o.s("chapter"), o.s("section"))
                                .filter { it.isNotBlank() }
                                .joinToString(" · ")
                        )
                        if (o.s("quote").isNotBlank()) Text(o.s("quote"))
                        val url = o.s("url")
                        if (url.startsWith("https://"))
                            TextButton(onClick = { uri.openUri(url) }) { Text(L("Open source")) }
                    }
                    (sources["evidence"] as? JsonArray).orEmpty().forEach { element ->
                        val evidence = element as? JsonObject ?: return@forEach
                        Text(evidence.s("title"), style = MaterialTheme.typography.titleSmall)
                        Text(evidence.s("content"))
                    }
                    if (
                        (sources["citations"] as? JsonArray).isNullOrEmpty() &&
                            (sources["evidence"] as? JsonArray).isNullOrEmpty()
                    )
                        Text(L("No sources available."))
                }
            },
            confirmButton = { TextButton(onClick = model::closeSources) { Text(L("Done")) } },
        )
    }
}

@Composable
private fun RichCard(
    tool: ChatTool,
    proposals: Map<Int, JsonObject>,
    model: ChatViewModel,
    navigate: (String) -> Unit,
    pending: Set<Int>,
) {
    val context = LocalContext.current
    val data = tool.data ?: return
    OutlinedCard(
        colors =
            CardDefaults.outlinedCardColors(
                containerColor = androidx.compose.ui.graphics.Color.White
            )
    ) {
        Column(
            Modifier.fillMaxWidth().padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            when (tool.cardType) {
                "schedule_proposal",
                "schedule_rebuild" -> {
                    val id = data["proposal_id"]?.jsonPrimitive?.intOrNull ?: return@Column
                    val current = proposals[id] ?: data
                    val status =
                        current.s("status").ifBlank {
                            if (tool.cardType == "schedule_rebuild") "generating" else "proposed"
                        }
                    LaunchedEffect(id) {
                        if (tool.cardType == "schedule_rebuild") model.refreshProposal(id)
                    }
                    Text(
                        if (tool.cardType == "schedule_rebuild")
                            L("Proposed rebuild · Week %lld", data.s("week").toIntOrNull() ?: 0)
                        else L("Proposed schedule change"),
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(data.s("rationale"))
                    val moves = (current["diff"] as? JsonArray) ?: (data["diff"] as? JsonArray)
                    moves.orEmpty().forEach { move ->
                        val o = move.jsonObject
                        Text(
                            "${o.s("from_day")} (${o.s("from_week")}) → ${o.s("to_day")} (${o.s("to_week")})"
                        )
                        (o["workout"] as? JsonObject)?.let { Text(it.s("title")) }
                    }
                    val rebuild = current["diff"] as? JsonObject
                    (rebuild?.get("totals") as? JsonObject)?.let { totals ->
                        fun summary(key: String): String {
                            val total = totals[key] as? JsonObject ?: return "—"
                            return "${total.s("min")} min · ${total.s("km")} km · ${total.s("vert")} m"
                        }
                        Text("${L("Week total")}: ${summary("before")} → ${summary("after")}")
                    }
                    (rebuild?.get("days") as? JsonArray).orEmpty().forEach { element ->
                        val day = element as? JsonObject ?: return@forEach
                        Text(L(day.s("day")), style = MaterialTheme.typography.titleSmall)
                        fun workouts(key: String): String =
                            (day[key] as? JsonArray)
                                .orEmpty()
                                .mapNotNull { it as? JsonObject }
                                .joinToString(" · ") {
                                    "${it.s("title")} (${it.s("duration_minutes")} min)"
                                }
                        workouts("kept")
                            .takeIf { it.isNotBlank() }
                            ?.let { Text("$it (${L("kept")})", color = UH.muted) }
                        workouts("before")
                            .takeIf { it.isNotBlank() }
                            ?.let { Text(L("was: %@", it), color = UH.muted) }
                        val after = workouts("after")
                        if (after.isNotBlank()) Text(after)
                        else if (!(day["before"] as? JsonArray).isNullOrEmpty()) Text(L("Rest"))
                    }
                    if (status == "proposed")
                        ((current["warnings"] ?: data["warnings"]) as? JsonArray)
                            .orEmpty()
                            .forEach { element ->
                                val warning =
                                    runCatching {
                                            JSONCoding.json.decodeFromJsonElement<ScheduleWarning>(
                                                element
                                            )
                                        }
                                        .getOrNull()
                                warning?.let {
                                    Text(
                                        ScheduleMessages.warningText(it) { key ->
                                            localizedText(context, key)
                                        },
                                        color = UH.warningInk,
                                    )
                                }
                            }
                    Text(L(status))
                    if (status == "generating") LinearProgressIndicator(Modifier.fillMaxWidth())
                    if (status in listOf("stale", "failed"))
                        Text(
                            L(ScheduleMessages.guardText(current.s("stale_reason"))),
                            color = UH.warningInk,
                        )
                    if (
                        status == "proposed" &&
                            (tool.cardType != "schedule_rebuild" || rebuild != null)
                    )
                        Row {
                            TextButton(
                                onClick = { model.actProposal(id, true) },
                                enabled = id !in pending,
                            ) {
                                Text(L("Apply"))
                            }
                            TextButton(
                                onClick = { model.actProposal(id, false) },
                                enabled = id !in pending,
                            ) {
                                Text(L("Discard"))
                            }
                        }
                }
                "gear_recommendation",
                "shoe_recommendations",
                "gear_plan" -> {
                    Text(L("Shoe Recommendations"), style = MaterialTheme.typography.titleMedium)
                    val plan =
                        runCatching { JSONCoding.json.decodeFromJsonElement<GearPlan>(data) }
                            .getOrNull()
                    plan?.let { Text(L("%lld recommendations", it.recommendations.size)) }
                    plan?.recommendations?.take(3)?.forEach { shoe ->
                        Text(
                            "${shoe.brand} ${shoe.model}",
                            style = MaterialTheme.typography.titleSmall,
                        )
                        Text("${shoe.drop} · ${shoe.weight} · ${shoe.price}")
                        Text(shoe.pros, color = UH.accentInk)
                    }
                    plan?.tips?.firstOrNull()?.let { Text(it) }
                    TextButton(onClick = { navigate("gear") }) { Text(L("Gear Vault")) }
                }
                "nutrition_plan",
                "fueling_plan" -> {
                    Text(L("Fueling Strategy"), style = MaterialTheme.typography.titleMedium)
                    val plan =
                        runCatching { JSONCoding.json.decodeFromJsonElement<NutritionPlan>(data) }
                            .getOrNull()
                    plan?.let {
                        Text(
                            "${it.avgCarbsPerHour.toInt()}g carbs/h · ${it.totalCarbs.toInt()}g carbs · ${it.totalSodium.toInt()}mg sodium"
                        )
                    }
                    plan?.let { Text("${it.hourlyPlan.size} h") }
                    plan?.products?.take(3)?.forEach {
                        Text("${it.name} × ${it.totalQuantity} · ${it.carbsPerUnit.toInt()}g carbs")
                    }
                    plan?.tips?.firstOrNull()?.let { Text(it) }
                    TextButton(onClick = { navigate("nutrition") }) { Text(L("Nutrition Lab")) }
                }
                "goal_estimate" -> {
                    Text(
                        data.s("race_name").ifBlank { L("Race Goal Estimate") },
                        style = MaterialTheme.typography.titleMedium,
                    )
                    data["distance_km"]?.let {
                        Text("${(it as? JsonPrimitive)?.content.orEmpty()} km")
                    }
                    (data["benchmarks"] as? JsonArray)?.firstOrNull()?.let { element ->
                        (element as? JsonObject)?.let {
                            Text(
                                L(
                                    "Calibrated against %lld field (%lld finishers)",
                                    it.s("year").toIntOrNull() ?: 0,
                                    it.s("finishers").toIntOrNull() ?: 0,
                                ),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                    val goals = data["goals"] as? JsonObject
                    listOf(
                            "ambitious" to "A: Ambitious",
                            "realistic" to "B: Realistic",
                            "safe" to "C: Safe",
                        )
                        .forEach { (key, title) ->
                            val time =
                                (goals?.get(key)
                                    ?: goals?.get(
                                        when (key) {
                                            "ambitious" -> "a"
                                            "realistic" -> "b"
                                            else -> "c"
                                        }
                                    ))
                                    as? JsonPrimitive
                            time?.doubleOrNull?.let { Text("${L(title)}: ${formatMinutes(it)}") }
                        }
                    data["adjusted_time_mins"]?.jsonPrimitive?.doubleOrNull?.let {
                        Text(formatMinutes(it))
                    }
                    TextButton(onClick = { navigate("goal") }) { Text(L("Goal Determiner")) }
                }
                "week_schedule" -> {
                    Text(L("Week schedule"), style = MaterialTheme.typography.titleMedium)
                    val rows =
                        (data["workouts"] as? JsonArray).orEmpty().mapNotNull { it as? JsonObject }
                    val week = data.s("week_number").ifBlank { data.s("week") }
                    if (week.isNotBlank()) Text("${L("Week")} $week")
                    Text(
                        "%.1f km · %.0f m D+"
                            .format(
                                rows.sumOf { it.s("distance_km").toDoubleOrNull() ?: 0.0 },
                                rows.sumOf { it.s("elevation_gain_m").toDoubleOrNull() ?: 0.0 },
                            )
                    )
                    rows.forEach { workout ->
                        val rest =
                            workout.s("type").equals("rest", true) ||
                                workout.s("title").equals("Rest Day", true)
                        TextButton(
                            enabled = !rest,
                            onClick = {
                                val id = workout["id"]?.jsonPrimitive?.intOrNull
                                navigate(if (id != null) "workout/$id" else "plan")
                            },
                        ) {
                            Column(Modifier.fillMaxWidth()) {
                                Text("${L(workout.s("day_of_week"))} · ${workout.s("title")}")
                                Text(
                                    "${workout.s("type")} · ${workout.s("duration_minutes")} min · ${workout.s("target_zone")}",
                                    style = MaterialTheme.typography.bodySmall,
                                )
                                if (workout.s("is_completed") in listOf("1", "true"))
                                    Text(L("Done"))
                                if (workout.s("is_priority") in listOf("1", "true"))
                                    Text(L("Priority session"))
                            }
                        }
                    }
                }
                "week_review" -> {
                    Text(L("Week review"), style = MaterialTheme.typography.titleMedium)
                    val review =
                        runCatching { JSONCoding.json.decodeFromJsonElement<WeekReview>(data) }
                            .getOrNull()
                    if (review != null) {
                        Text(
                            "${L("Week")} ${review.weekNumber} · ${L("%@%% Done", "%.0f".format(review.completionPct))}"
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                            review.planned?.distanceKm?.let {
                                Text("${L("Planned")}: %.1f km".format(it))
                            }
                            review.actual?.totalActualKm?.let {
                                Text("${L("Actual")}: %.1f km".format(it))
                            }
                        }
                        review.narrative?.let { narrative ->
                            narrative.summary?.let { Text(it) }
                            narrative.highlights.forEach { Text(it) }
                            narrative.watch.forEach { Text(it, color = UH.warningInk) }
                        }
                    } else {
                        listOf("summary", "headline", "coach_note", "recommendation").forEach { key
                            ->
                            if (data.s(key).isNotBlank()) Text(data.s(key))
                        }
                        (data["highlights"] as? JsonArray).orEmpty().forEach {
                            Text((it as? JsonPrimitive)?.content.orEmpty())
                        }
                    }
                }
                "pacing_splits" -> {
                    Text(
                        data.s("race_name").ifBlank { L("Pace Strategy") },
                        style = MaterialTheme.typography.titleMedium,
                    )
                    data["total_distance_km"]?.let {
                        Text("${(it as? JsonPrimitive)?.content.orEmpty()} km")
                    }
                    (data["splits"] as? JsonArray).orEmpty().forEach { element ->
                        val split = element.jsonObject
                        Text(
                            "${split.s("name")} · ${split.s("distance_km")} km · ${split.s("target_pace")} · ${split.s("split_time")}"
                        )
                    }
                    TextButton(onClick = { navigate("pace") }) { Text(L("View strategy")) }
                }
            }
        }
    }
}

private fun formatMinutes(value: Double): String = minutesText(value)

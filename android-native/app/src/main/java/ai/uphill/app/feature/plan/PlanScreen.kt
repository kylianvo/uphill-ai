package ai.uphill.app.feature.plan

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.generation.*
import ai.uphill.app.core.integrations.DeviceConnectionService
import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.core.plan.*
import ai.uphill.app.core.racehistory.RaceHistoryService
import ai.uphill.app.designsystem.LocalReduceMotion
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.UH
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PageSize
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import java.time.*
import java.time.format.DateTimeFormatter
import kotlinx.serialization.json.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlanScreen(
    api: APIClient,
    user: User,
    lang: String,
    onNavigate: (String) -> Unit,
    athleteId: Int? = null,
) {
    val context = LocalContext.current
    val center = remember(api, user.id) { GenerationCenter.get(context, api, user.id) }
    val model: PlanViewModel =
        viewModel(
            key = "plan-${user.id}-$athleteId-${api.baseURL()}",
            factory =
                object : ViewModelProvider.Factory {
                    override fun <T : ViewModel> create(modelClass: Class<T>): T {
                        @Suppress("UNCHECKED_CAST")
                        return PlanViewModel(api, user, lang, center, context.filesDir, athleteId)
                            as T
                    }
                },
        )
    SideEffect { model.changeLanguage(lang) }
    LaunchedEffect(Unit) { model.load() }
    val state by model.state.collectAsState()
    val generation by center.state.collectAsState()
    var sheet by remember { mutableStateOf<String?>(null) }
    var calendarMode by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<Workout?>(null) }
    val snapshot = state.snapshot
    val requestedWorkout by TrainingNavigation.workoutId.collectAsState()
    LaunchedEffect(snapshot, requestedWorkout) {
        requestedWorkout?.let { id ->
            snapshot
                ?.workouts
                ?.firstOrNull { it.id == id }
                ?.let { workout ->
                    model.selectWeek(workout.weekNumber)
                    selected = workout
                    sheet = "workout"
                    TrainingNavigation.workoutId.value = null
                }
        }
    }
    LazyColumn(
        Modifier.fillMaxSize().background(UH.surface),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    P("Plan"),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f),
                )
                IconButton(onClick = model::load) {
                    Icon(Icons.Default.Refresh, P("Refresh"), tint = UH.accentInk)
                }
                TextButton(
                    onClick = { sheet = "manage" },
                    enabled = snapshot != null && state.cachedAt == null,
                ) {
                    Text(P("Manage"))
                }
            }
        }
        if (generation.running != null)
            item {
                OutlinedCard {
                    Column(
                        Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text(P("Building your plan"))
                        LinearProgressIndicator(Modifier.fillMaxWidth())
                        Text(P("You can leave this screen. Your plan will keep building."))
                    }
                }
            }
        (generation.outcome as? JobOutcome.Failed)?.let { failure ->
            item { Text(P(failure.message), color = UH.danger) }
        }
        if (state.cachedAt != null) item { Text(P("Offline · Read only"), color = UH.warningInk) }
        if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        state.error?.let { error -> item { Text(P(error), color = UH.danger) } }
        state.notice?.let { item { Text(P(it), color = UH.warningInk) } }
        if (snapshot == null && !state.loading)
            item {
                Column(
                    Modifier.fillMaxWidth().padding(vertical = 48.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Icon(Icons.Default.Terrain, null, Modifier.size(48.dp), tint = UH.accentInk)
                    Text(P("No plan yet"), style = MaterialTheme.typography.headlineLarge)
                    Text(
                        P("Your weekly workouts show up here once Coach Uphill builds your plan."),
                        style = MaterialTheme.typography.bodyMedium,
                        color = UH.secondary,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    )
                    Button(
                        onClick = { onNavigate("newPlan") },
                        modifier = Modifier.widthIn(max = 280.dp),
                    ) {
                        Text(P("Build my plan"))
                    }
                }
            }
        if (snapshot != null) {
            item {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            snapshot.plan.raceName.ifBlank { P(snapshot.plan.goalType) },
                            fontSize = 19.sp,
                            fontWeight = FontWeight.Bold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(
                                snapshot.plan.raceDate,
                                style = MaterialTheme.typography.bodySmall,
                                color = UH.secondary,
                            )
                            PlanCalendar.daysToRace(snapshot.plan.raceDate)?.let {
                                Text(
                                    "· ${it / 7} ${P("weeks to go")}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = UH.accentInk,
                                )
                            }
                        }
                    }
                    TextButton(onClick = { sheet = "goal" }) {
                        Text(
                            P(goalStatus(state)),
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color =
                                if (state.goal?.status?.state == "behind") UH.danger
                                else UH.accentInk,
                        )
                    }
                }
            }
            item {
                SummaryCarousel(
                    model,
                    state,
                    onGoal = { sheet = "goal" },
                    onReview = { sheet = "review" },
                    onAdapt = { sheet = "adapt" },
                    canAdapt = model.canAdapt() && generation.running == null,
                )
            }
            item { CoachReview(model, state, onReview = { sheet = "review" }) }
            if (athleteId == null) item { SharpenChecklist(api, user, onNavigate) }
            if (model.canAdapt())
                item {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                        TextButton(
                            onClick = { sheet = "adapt" },
                            enabled = generation.running == null,
                        ) {
                            Icon(Icons.Default.AutoAwesome, null, Modifier.size(14.dp))
                            Spacer(Modifier.width(5.dp))
                            Text("${P("Adapt week")} ${state.week}", fontSize = 12.sp)
                        }
                    }
                }
            item {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    if (!calendarMode) {
                        IconButton(
                            onClick = { model.selectWeek(state.week - 1) },
                            enabled = state.week > 1,
                        ) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, P("Previous week"))
                        }
                        Column(
                            Modifier.weight(1f),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Text(
                                "${P("Week")} ${state.week}",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            if (
                                state.week ==
                                    PlanCalendar.currentWeek(snapshot.plan, snapshot.workouts)
                            )
                                Text(P("This week"), fontSize = 11.sp, color = UH.accentInk)
                        }
                        IconButton(
                            onClick = { model.selectWeek(state.week + 1) },
                            enabled = state.week < snapshot.plan.totalWeeks,
                        ) {
                            Icon(Icons.AutoMirrored.Filled.ArrowForward, P("Next week"))
                        }
                    } else
                        Text(
                            P("Month Calendar"),
                            Modifier.weight(1f),
                            style = MaterialTheme.typography.titleMedium,
                        )
                    Row(Modifier.background(UH.hover, RoundedCornerShape(8.dp))) {
                        IconButton(
                            onClick = { calendarMode = false },
                            modifier = Modifier.size(44.dp),
                        ) {
                            Icon(
                                Icons.AutoMirrored.Filled.List,
                                P("List"),
                                tint = if (!calendarMode) UH.accentInk else UH.muted,
                            )
                        }
                        IconButton(
                            onClick = { calendarMode = true },
                            modifier = Modifier.size(44.dp),
                        ) {
                            Icon(
                                Icons.Default.CalendarMonth,
                                P("Calendar"),
                                tint = if (calendarMode) UH.accentInk else UH.muted,
                            )
                        }
                    }
                }
            }
            if (calendarMode)
                item {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        CalendarGrid(
                            snapshot,
                            onWorkout = {
                                selected = it
                                sheet = "workout"
                            },
                            onWeek = {
                                model.selectWeek(it)
                                calendarMode = false
                            },
                        )
                    }
                }
            if (!calendarMode)
                items(Weekday.entries.toList()) { day ->
                    val workouts = model.weekWorkouts().filter { it.weekday == day }
                    val date = PlanCalendar.date(state.week, day, snapshot.plan, snapshot.workouts)
                    DayRow(
                        day,
                        date,
                        workouts,
                        onClick = {
                            selected = it
                            sheet = "workout"
                        },
                        onToggle =
                            if (athleteId == null && state.cachedAt == null && !state.busy)
                                ({ workout ->
                                    model.log(
                                        workout,
                                        if (workout.isDone) 0 else 1,
                                        0,
                                        workout.rpe,
                                        workout.notes.orEmpty(),
                                    ) {}
                                })
                            else null,
                    )
                }
            state.knowledge?.let { card ->
                item {
                    OutlinedCard(onClick = { onNavigate("knowledge") }) {
                        Column(Modifier.padding(16.dp)) {
                            Text(
                                P("COACH'S PICK THIS WEEK"),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = UH.muted,
                            )
                            Text(card["title"]?.jsonPrimitive?.content.orEmpty())
                            Text(
                                card["content"]?.jsonPrimitive?.content.orEmpty().take(200),
                                color = UH.secondary,
                            )
                        }
                    }
                }
            }
            model.nextOffer()?.let { offer ->
                item {
                    OutlinedCard {
                        Column(
                            Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text(
                                "${P("Next block")} · ${P("Week")} ${offer.start}–${offer.end}",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Text("${P("Completion")} ${offer.completion?.toInt() ?: 0}%")
                            Button(
                                onClick = { sheet = "next" },
                                enabled = offer.unlocked && generation.running == null,
                            ) {
                                Text(P("Build next week"))
                            }
                        }
                    }
                }
            }
        }
    }
    if (sheet != null && snapshot != null)
        ModalBottomSheet(onDismissRequest = { sheet = null }) {
            Column(
                Modifier.fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
                    .padding(bottom = 32.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                state.error?.let { Text(P(it), color = UH.danger) }
                when (sheet) {
                    "workout" ->
                        selected?.let {
                            WorkoutDetail(
                                model,
                                it,
                                state,
                                onMove = { sheet = "move" },
                                onMatch = { sheet = "watch" },
                                onClose = { sheet = null },
                            )
                        }
                    "move" -> selected?.let { MoveSwapSheet(model, it, onClose = { sheet = null }) }
                    "adapt",
                    "next" ->
                        GenerationSheet(model, adapt = sheet != "next", onClose = { sheet = null })
                    "schedule" -> ScheduleChangeSheet(model, onClose = { sheet = null })
                    "review" -> WeekReviewSheet(model)
                    "goal" -> GoalSheet(model, state, onClose = { sheet = null })
                    "manage" ->
                        ManagePlanSheet(
                            model,
                            onClose = { sheet = null },
                            onNewPlan = {
                                sheet = null
                                onNavigate("newPlan")
                            },
                            onSchedule = { sheet = "schedule" },
                            onSync = model::sync,
                            onExport = { sheet = "export" },
                            onTool = {
                                sheet = null
                                onNavigate(it)
                            },
                        )
                    "calendar" ->
                        CalendarGrid(
                            snapshot,
                            onWorkout = {
                                selected = it
                                sheet = "workout"
                            },
                            onWeek = {
                                model.selectWeek(it)
                                sheet = null
                            },
                        )
                    "watch" -> WatchMatchSheet(model, selected, onClose = { sheet = null })
                    "export" -> ExportCalendarSheet(model, snapshot)
                }
            }
        }
}

private fun goalStatus(state: PlanState): String =
    when (state.goal?.status?.state) {
        "on_track" -> "On track"
        "ahead" -> "Ahead of target"
        "behind" -> "Behind target"
        "no_target" -> "No target"
        else -> "Not assessed yet"
    }

@Composable
private fun SummaryCarousel(
    model: PlanViewModel,
    state: PlanState,
    onGoal: () -> Unit,
    onReview: () -> Unit,
    onAdapt: () -> Unit,
    canAdapt: Boolean,
) {
    val snapshot = state.snapshot ?: return
    val rows = model.weekWorkouts()
    var trend by remember { mutableStateOf(false) }
    val pager = rememberPagerState(pageCount = { 4 })
    val planned = rows.sumOf { it.distanceKm ?: 0.0 }
    val actual = rows.sumOf { it.matchedDistanceKm ?: if (it.isDone) it.distanceKm ?: 0.0 else 0.0 }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        HorizontalPager(state = pager, pageSpacing = 12.dp, pageSize = PageSize.Fixed(315.dp)) {
            page ->
            OutlinedCard(
                Modifier.fillMaxWidth().heightIn(min = 184.dp),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
            ) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    when (page) {
                        0 -> {
                            Row(
                                Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(
                                    "${P("Week")} ${state.week} ${P("Volume")}".uppercase(),
                                    Modifier.weight(1f),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = UH.secondary,
                                )
                                listOf(false to "Days", true to "Trend").forEach { (value, title) ->
                                    Text(
                                        P(title),
                                        Modifier.background(
                                                if (trend == value) UH.hover else Color.Transparent,
                                                CircleShape,
                                            )
                                            .clickable { trend = value }
                                            .padding(horizontal = 8.dp, vertical = 8.dp),
                                        fontSize = 10.sp,
                                        color = if (trend == value) UH.accentInk else UH.secondary,
                                    )
                                }
                            }
                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Bottom) {
                                Text(
                                    "%.1f".format(planned),
                                    fontSize = 26.sp,
                                    fontWeight = FontWeight.Bold,
                                )
                                Text(" km", color = UH.secondary)
                                Spacer(Modifier.weight(1f))
                                Text(
                                    "%.1f h · %d m D+"
                                        .format(
                                            rows.sumOf { it.durationMinutes } / 60,
                                            rows.sumOf { it.elevationGainM ?: 0.0 }.toInt(),
                                        ),
                                    fontSize = 12.sp,
                                    color = UH.secondary,
                                )
                            }
                            Text(
                                "${P("Planned")} %.1f km · ${P("Actual")} %.1f km"
                                    .format(planned, actual),
                                fontSize = 11.sp,
                                color = UH.secondary,
                            )
                            val values =
                                if (trend)
                                    (1..snapshot.plan.totalWeeks).map { week ->
                                        snapshot.workouts
                                            .filter { it.weekNumber == week }
                                            .sumOf { it.distanceKm ?: 0.0 }
                                    }
                                else
                                    Weekday.entries.map { day ->
                                        rows
                                            .filter { it.weekday == day }
                                            .sumOf { it.distanceKm ?: 0.0 }
                                    }
                            val label =
                                P(if (trend) "Every week volume trend" else "Week days volume")
                            Canvas(
                                Modifier.fillMaxWidth().height(54.dp).semantics {
                                    contentDescription = "$label: ${values.joinToString()}"
                                }
                            ) {
                                val maximum = values.maxOrNull()?.coerceAtLeast(1.0) ?: 1.0
                                val width = size.width / values.size.coerceAtLeast(1)
                                values.forEachIndexed { index, value ->
                                    val height =
                                        (value.coerceAtLeast(0.4) / maximum * size.height)
                                            .toFloat()
                                            .coerceAtMost(size.height)
                                    drawRoundRect(
                                        if (value == 0.0) UH.line else UH.accentInk,
                                        Offset(index * width + 3, size.height - height),
                                        Size((width - 6).coerceAtLeast(1f), height),
                                        androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()),
                                    )
                                }
                            }
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceAround,
                            ) {
                                values.indices.forEach { index ->
                                    Text(
                                        if (trend) "W${index + 1}"
                                        else P(Weekday.entries[index].short),
                                        fontSize = 9.sp,
                                        color = UH.secondary,
                                    )
                                }
                            }
                        }
                        1 -> {
                            val active = rows.count { !it.isRest }
                            val done = rows.count { it.isDone && !it.isRest }
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(
                                    P("This week").uppercase(),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = UH.secondary,
                                )
                                Text(
                                    "${if (active == 0) 0 else done * 100 / active}% ${P("adherence")}",
                                    fontSize = 11.sp,
                                    color = UH.accentInk,
                                )
                            }
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceAround,
                            ) {
                                Weekday.entries.forEach { day ->
                                    val workouts = rows.filter { it.weekday == day && !it.isRest }
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        Text(P(day.short), fontSize = 10.sp, color = UH.muted)
                                        Icon(
                                            if (workouts.any { it.isDone })
                                                Icons.Default.CheckCircle
                                            else if (workouts.any { it.isMissedFlag })
                                                Icons.Default.Cancel
                                            else Icons.Default.RadioButtonUnchecked,
                                            null,
                                            Modifier.padding(top = 4.dp).size(20.dp),
                                            tint =
                                                if (workouts.any { it.isDone }) UH.accentInk
                                                else if (workouts.any { it.isMissedFlag }) UH.danger
                                                else UH.line,
                                        )
                                    }
                                }
                            }
                            Text("$done / $active ${P("Sessions completed")}", fontSize = 12.sp)
                            Row {
                                TextButton(onClick = onReview) {
                                    Text(P("Week review"), fontSize = 11.sp)
                                }
                                if (canAdapt)
                                    TextButton(onClick = onAdapt) {
                                        Text(P("Adapt week"), fontSize = 11.sp)
                                    }
                            }
                        }
                        2 -> {
                            Text(
                                P("Race Target").uppercase(),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = UH.secondary,
                            )
                            Text(
                                snapshot.plan.raceName,
                                style = MaterialTheme.typography.titleMedium,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Text(
                                snapshot.plan.raceDate,
                                style = MaterialTheme.typography.bodySmall,
                                color = UH.secondary,
                            )
                            Row(
                                Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(
                                    "${PlanCalendar.daysToRace(snapshot.plan.raceDate) ?: "—"} ${P("days to go")}",
                                    fontSize = 13.sp,
                                    color = UH.accentInk,
                                )
                                Spacer(Modifier.weight(1f))
                                TextButton(onClick = onGoal) {
                                    Text(P(goalStatus(state)), fontSize = 11.sp)
                                }
                            }
                        }
                        else -> {
                            Text(
                                P("Training phase").uppercase(),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = UH.secondary,
                            )
                            Text(
                                P(
                                    rows.firstOrNull()?.phase?.ifBlank { "Base Phase" }
                                        ?: "Base Phase"
                                ),
                                fontSize = 26.sp,
                                fontWeight = FontWeight.Bold,
                            )
                            Text(
                                "${P("Week")} ${state.week} / ${snapshot.plan.totalWeeks}",
                                fontSize = 13.sp,
                                color = UH.secondary,
                            )
                            Text(
                                P(
                                    "Focus: build consistent aerobic capacity and fatigue resistance."
                                ),
                                fontSize = 12.sp,
                                color = UH.secondary,
                            )
                        }
                    }
                }
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
            repeat(4) { index ->
                Box(
                    Modifier.padding(3.dp)
                        .size(5.dp)
                        .background(
                            if (pager.currentPage == index) UH.accentInk else UH.line,
                            CircleShape,
                        )
                )
            }
        }
    }
}

@Composable
private fun CoachReview(model: PlanViewModel, state: PlanState, onReview: () -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    val reducedMotion = LocalReduceMotion.current
    val block = state.blocks?.blocks?.firstOrNull { state.week in it.weekStart..it.weekEnd }
    val priority = model.weekWorkouts().firstOrNull { it.isPriority }
    OutlinedCard(
        Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(
                Modifier.fillMaxWidth().clickable { expanded = !expanded }.heightIn(min = 44.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Default.FormatQuote, null, Modifier.size(26.dp), tint = UH.accentInk)
                Column(Modifier.weight(1f).padding(horizontal = 10.dp)) {
                    Text(
                        P("COACH'S REVIEW"),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = UH.accentInk,
                    )
                    if (!expanded)
                        Text(
                            block?.aiThisWeekDescription?.ifBlank { null }
                                ?: P("Tap to read coach takeaways and weekly focus"),
                            fontSize = 12.sp,
                            color = UH.secondary,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                }
                Icon(
                    if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    P("Coach review"),
                    tint = UH.muted,
                )
            }
            AnimatedVisibility(
                expanded,
                enter =
                    if (reducedMotion) androidx.compose.animation.EnterTransition.None
                    else
                        androidx.compose.animation.fadeIn() +
                            androidx.compose.animation.expandVertically(),
                exit =
                    if (reducedMotion) androidx.compose.animation.ExitTransition.None
                    else
                        androidx.compose.animation.fadeOut() +
                            androidx.compose.animation.shrinkVertically(),
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    HorizontalDivider(color = UH.line)
                    Text(
                        P("Training phase") +
                            " · " +
                            P(model.weekWorkouts().firstOrNull()?.phase.orEmpty()),
                        fontSize = 10.sp,
                        color = UH.muted,
                    )
                    block
                        ?.aiLastWeekReview
                        ?.takeIf { it.isNotBlank() }
                        ?.let {
                            Text(P("LAST WEEK REVIEW"), fontSize = 10.sp, color = UH.secondary)
                            Text(it, fontSize = 13.sp)
                        }
                    block
                        ?.aiThisWeekDescription
                        ?.takeIf { it.isNotBlank() }
                        ?.let {
                            Text(P("THIS WEEK FOCUS"), fontSize = 10.sp, color = UH.accentInk)
                            Text(it, fontSize = 13.sp)
                        }
                    priority?.let {
                        Text(P("COACH'S PICK THIS WEEK"), fontSize = 10.sp, color = UH.accentInk)
                        Text(
                            "${it.title} (${it.durationMinutes.toInt()} min)",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                    TextButton(onClick = onReview) { Text(P("Read complete weekly review")) }
                }
            }
        }
    }
}

@Composable
private fun DayRow(
    day: Weekday,
    date: LocalDate?,
    workouts: List<Workout>,
    onClick: (Workout) -> Unit,
    onToggle: ((Workout) -> Unit)?,
) {
    val rest = workouts.isEmpty() || workouts.all { it.isRest && !it.isDone && !it.isMissedFlag }
    val today = date == LocalDate.now()
    val color =
        when {
            workouts.any { it.targetZone.contains("4") || it.targetZone.contains("5") } ->
                Color(0xFFBD514C)
            workouts.any { it.targetZone.contains("3") } -> Color(0xFFC07C25)
            workouts.any { it.type.contains("strength", true) } -> Color(0xFF8765AF)
            else -> UH.accentInk
        }
    val dateText = "${P(day.short)} ${date?.format(DateTimeFormatter.ofPattern("dd/MM")) ?: ""}"
    OutlinedCard(
        Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        border =
            BorderStroke(
                if (today) 1.5.dp else 1.dp,
                if (rest) UH.line else color.copy(alpha = 0.35f),
            ),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
    ) {
        Row(
            Modifier.background(
                if (rest) Brush.horizontalGradient(listOf(Color.White, Color.White))
                else
                    Brush.horizontalGradient(
                        listOf(color.copy(alpha = if (today) 0.16f else 0.09f), Color.White)
                    )
            )
        ) {
            if (!rest)
                Box(
                    Modifier.padding(start = 7.dp, top = 7.dp, bottom = 7.dp)
                        .width(4.dp)
                        .heightIn(min = 76.dp)
                        .background(color, RoundedCornerShape(3.dp))
                )
            Column(
                Modifier.weight(1f).padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (rest)
                    Row(
                        Modifier.heightIn(min = 30.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(dateText, fontSize = 12.sp, color = UH.secondary)
                        Spacer(Modifier.weight(1f))
                        Text(P("Rest"), fontSize = 13.sp, color = UH.muted)
                    }
                else
                    workouts.forEachIndexed { index, workout ->
                        if (index > 0) HorizontalDivider(color = UH.line)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(
                                Modifier.weight(1f).clickable { onClick(workout) },
                                verticalArrangement = Arrangement.spacedBy(3.dp),
                            ) {
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text(
                                        if (workouts.size > 1) P(workout.sessionSlot ?: "Session")
                                        else dateText,
                                        fontSize = 11.sp,
                                        color = UH.secondary,
                                    )
                                    if (today)
                                        Text(
                                            P("TODAY"),
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = UH.accentInk,
                                        )
                                    if (workout.isPriority)
                                        Text(
                                            P("PRIORITY"),
                                            fontSize = 9.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = UH.accentInk,
                                        )
                                    Text(
                                        P(workout.type),
                                        Modifier.background(
                                                color.copy(alpha = 0.12f),
                                                RoundedCornerShape(6.dp),
                                            )
                                            .padding(horizontal = 6.dp, vertical = 2.dp),
                                        fontSize = 10.sp,
                                        color = color,
                                        maxLines = 1,
                                    )
                                }
                                Text(
                                    workout.title,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                Text(
                                    "${workout.durationMinutes.toInt()} min · ${workout.distanceKm ?: 0} km · ${workout.targetPace ?: workout.targetZone}",
                                    fontSize = 12.sp,
                                    color = UH.secondary,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                            }
                            IconButton(
                                onClick = { onToggle?.invoke(workout) },
                                enabled = onToggle != null,
                            ) {
                                Icon(
                                    if (workout.isDone) Icons.Default.CheckCircle
                                    else if (workout.isMissedFlag) Icons.Default.Cancel
                                    else Icons.Default.RadioButtonUnchecked,
                                    P(if (workout.isDone) "Undo done" else "Mark done"),
                                    Modifier.size(24.dp),
                                    tint = if (workout.isDone) UH.accentInk else UH.line,
                                )
                            }
                        }
                        if (workout.isMatched)
                            Row(
                                Modifier.fillMaxWidth()
                                    .background(UH.surface, RoundedCornerShape(6.dp))
                                    .clickable { onClick(workout) }
                                    .padding(7.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Icon(
                                    Icons.Default.Watch,
                                    null,
                                    Modifier.size(13.dp),
                                    tint = UH.accentInk,
                                )
                                Text(
                                    " COROS · ${workout.matchedDistanceKm ?: 0} km · ${((workout.matchedDurationSeconds ?: 0.0) / 60).toInt()} min",
                                    fontSize = 11.sp,
                                    color = UH.secondary,
                                )
                                Spacer(Modifier.weight(1f))
                                Text(P("Matched"), fontSize = 10.sp, color = UH.accentInk)
                            }
                    }
            }
        }
    }
}

@Composable
private fun SharpenChecklist(api: APIClient, user: User, onNavigate: (String) -> Unit) {
    val context = LocalContext.current
    val preferences = remember {
        context.getSharedPreferences("plan-checklist", android.content.Context.MODE_PRIVATE)
    }
    val snoozeKey = "snoozed-${user.id}"
    var snoozed by
        remember(user.id) {
            mutableStateOf(
                System.currentTimeMillis() - preferences.getLong(snoozeKey, 0) < 14L * 86_400_000
            )
        }
    var watchConnected by remember { mutableStateOf(false) }
    var raceLinked by remember { mutableStateOf(false) }
    LaunchedEffect(api, user.id) {
        watchConnected =
            runCatching { DeviceConnectionService(api).fetchStatus().isCorosConnected }
                .getOrDefault(false)
        raceLinked =
            runCatching { RaceHistoryService(api).history().claims.isNotEmpty() }
                .getOrDefault(false)
    }
    if (snoozed) return
    fun entered(key: String) =
        user.fieldSources?.get(key)?.jsonObject?.get("source")?.jsonPrimitive?.content in
            setOf("athlete", "coach", "watch")
    val checklist =
        listOf(
            Triple("Connect your watch", "integrations", watchConnected),
            Triple("Link your race history", "racehistory", raceLinked),
            Triple(
                "Add your AeT and AnT heart rates",
                "profile/hr",
                user.aetHr != null && user.antHr != null && entered("aet_hr") && entered("ant_hr"),
            ),
            Triple(
                "Add your pace zones",
                "profile/paces",
                (!user.zone2PaceMin.isNullOrBlank() && entered("zone2_pace_min")) ||
                    !user.thresholdPace.isNullOrBlank(),
            ),
            Triple(
                "Tell Coach Uphill about injuries",
                "profile/about",
                !user.injuryHistory.isNullOrBlank() || !user.athleteNotes.isNullOrBlank(),
            ),
        )
    if (checklist.all { it.third }) return
    OutlinedCard(
        Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(
                    P("Get the most from your plan"),
                    Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    "${checklist.count { it.third }} / ${checklist.size}",
                    style = MaterialTheme.typography.bodySmall,
                    color = UH.accentInk,
                )
            }
            Text(
                P("Each one helps Coach Uphill fit your next weeks to you instead of an estimate."),
                style = MaterialTheme.typography.bodySmall,
                color = UH.secondary,
            )
            checklist.forEach { (title, route, done) ->
                val icon =
                    when (route) {
                        "integrations" -> Icons.Default.Watch
                        "racehistory" -> Icons.Default.EmojiEvents
                        "profile/hr" -> Icons.Default.Favorite
                        "profile/paces" -> Icons.Default.Speed
                        else -> Icons.Default.MedicalServices
                    }
                Row(
                    Modifier.fillMaxWidth().clickable { onNavigate(route) }.heightIn(min = 56.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        icon,
                        null,
                        Modifier.size(36.dp)
                            .background(UH.hover, RoundedCornerShape(8.dp))
                            .padding(8.dp),
                        tint = if (done) UH.muted else UH.accentInk,
                    )
                    Text(
                        P(title),
                        Modifier.weight(1f).padding(horizontal = 10.dp),
                        style = MaterialTheme.typography.labelLarge,
                        color = if (done) UH.secondary else UH.ink,
                    )
                    Icon(
                        if (done) Icons.Default.CheckCircle else Icons.Default.ChevronRight,
                        if (done) P("Done") else null,
                        tint = if (done) UH.accentInk else UH.muted,
                    )
                }
                HorizontalDivider(color = UH.line)
            }
            TextButton(
                onClick = {
                    preferences.edit().putLong(snoozeKey, System.currentTimeMillis()).apply()
                    snoozed = true
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(P("Not now"), color = UH.secondary)
            }
        }
    }
}

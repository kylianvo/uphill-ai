package ai.uphill.app.feature.plan

import ai.uphill.app.core.localization.L
import ai.uphill.app.core.models.*
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.*
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.text.TextAutoSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Flag
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import java.time.*
import java.time.format.DateTimeFormatter
import java.time.format.TextStyle
import kotlin.math.abs
import kotlin.math.roundToInt

@Composable
internal fun CalendarGrid(
    snapshot: PlanSnapshot,
    onDay: (CalendarDayCell) -> Unit,
    onWeek: (Int) -> Unit,
    week: Int = PlanCalendar.resolveCurrentWeek(snapshot.plan, snapshot.workouts),
) {
    var month by
        remember(snapshot.plan.id) {
            mutableStateOf(YearMonth.from(PlanCalendar.focusDate(week, snapshot)))
        }
    val data = remember(month, snapshot) { CalendarMonth.make(month, snapshot) }
    val locale = LocalConfiguration.current.locales[0]
    val reduceMotion = LocalReduceMotion.current
    val haptic = LocalHapticFeedback.current
    fun title(value: YearMonth) =
        value
            .format(
                DateTimeFormatter.ofPattern(
                    if (locale.language == "vi") "LLLL 'năm' yyyy" else "LLLL yyyy",
                    locale,
                )
            )
            .replaceFirstChar { it.titlecase(locale) }
    fun goTo(value: YearMonth) {
        if (value != month) {
            month = value
            haptic.performHapticFeedback(
                androidx.compose.ui.hapticfeedback.HapticFeedbackType.TextHandleMove
            )
        }
    }
    OutlinedCard(
        modifier = Modifier.testTag("calendar.card"),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, UH.line),
    ) {
        Column(
            Modifier.fillMaxWidth().padding(10.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        title(month),
                        Modifier.weight(1f).semantics {
                            heading()
                            liveRegion = LiveRegionMode.Polite
                        },
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = UH.ink,
                    )
                    if (!data.isCurrentMonth)
                        TextButton(
                            onClick = { goTo(YearMonth.now()) },
                            modifier = Modifier.testTag("calendar.today"),
                        ) {
                            Text(L("Today"))
                        }
                    IconButton(
                        onClick = { goTo(month.minusMonths(1)) },
                        modifier = Modifier.testTag("calendar.previous"),
                    ) {
                        Icon(Icons.Default.ChevronLeft, L("Previous month"))
                    }
                    IconButton(
                        onClick = { goTo(month.plusMonths(1)) },
                        modifier = Modifier.testTag("calendar.next"),
                    ) {
                        Icon(Icons.Default.ChevronRight, L("Next month"))
                    }
                }
                Text(
                    if (data.sessionsTotal == 0) L("No sessions planned this month")
                    else
                        L(
                            "%lld km · %@ h · %lld of %lld sessions done",
                            data.km.roundToInt(),
                            String.format(locale, "%.1f", data.hours),
                            data.sessionsDone,
                            data.sessionsTotal,
                        ),
                    color = UH.muted,
                    fontSize = 13.sp,
                    modifier = Modifier.testTag("calendar.summary"),
                )
            }
            val density = LocalDensity.current
            CompositionLocalProvider(
                LocalDensity provides Density(density.density, density.fontScale.coerceAtMost(1.4f))
            ) {
                Crossfade(
                    month,
                    animationSpec = tween(if (reduceMotion) 0 else 200),
                    label = "calendar month",
                ) { shownMonth ->
                    val shown = CalendarMonth.make(shownMonth, snapshot)
                    Column(
                        Modifier.testTag("calendar.grid").pointerInput(shownMonth) {
                            var drag = 0f
                            detectHorizontalDragGestures(
                                onDragStart = { drag = 0f },
                                onDragEnd = {
                                    if (abs(drag) > 60.dp.toPx())
                                        goTo(month.plusMonths(if (drag < 0) 1 else -1))
                                },
                            ) { _, amount ->
                                drag += amount
                            }
                        }
                    ) {
                        Row(Modifier.fillMaxWidth()) {
                            Weekday.entries.forEach { day ->
                                Text(
                                    DayOfWeek.of(day.offset + 1)
                                        .getDisplayName(TextStyle.NARROW_STANDALONE, locale),
                                    Modifier.weight(1f),
                                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                                    fontSize = 11.sp,
                                    color = UH.muted,
                                )
                            }
                            BasicText(
                                L("km/wk"),
                                Modifier.width(44.dp).testTag("calendar.weekHeader"),
                                style =
                                    androidx.compose.ui.text.TextStyle(
                                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                                        fontSize = 11.sp,
                                        color = UH.muted,
                                    ),
                                maxLines = 1,
                                softWrap = false,
                                autoSize =
                                    TextAutoSize.StepBased(
                                        minFontSize = 7.7.sp,
                                        maxFontSize = 11.sp,
                                        stepSize = .25.sp,
                                    ),
                            )
                        }
                        shown.weeks.forEach { row ->
                            Row(Modifier.fillMaxWidth().height(62.dp)) {
                                row.cells.forEach { cell ->
                                    CalendarCell(cell, shown, Modifier.weight(1f), onDay)
                                }
                                val weekLabel =
                                    row.weekNumber
                                        ?.let { L("Week %lld, %lld km", it, row.km.roundToInt()) }
                                        .orEmpty()
                                Column(
                                    Modifier.width(44.dp)
                                        .fillMaxHeight()
                                        .then(
                                            if (row.weekNumber != null)
                                                Modifier.clickable { onWeek(row.weekNumber!!) }
                                                    .testTag("calendar.week.${row.weekNumber}")
                                                    .semantics { contentDescription = weekLabel }
                                            else Modifier
                                        )
                                        .padding(top = 3.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.spacedBy(4.dp),
                                ) {
                                    Text(
                                        if (row.km > 0) row.km.roundToInt().toString() else "–",
                                        Modifier.heightIn(min = 24.dp),
                                        fontSize = 13.sp,
                                        fontWeight = FontWeight.SemiBold,
                                        color = if (row.containsToday) UH.accentInk else UH.ink,
                                    )
                                    Box(
                                        Modifier.width(30.dp).height(26.dp),
                                        contentAlignment = Alignment.BottomStart,
                                    ) {
                                        if (row.km > 0) {
                                            Box(
                                                Modifier.fillMaxWidth()
                                                    .height(4.dp)
                                                    .background(UH.line, RoundedCornerShape(2.dp))
                                            )
                                            Box(
                                                Modifier.fillMaxWidth(
                                                        (row.km /
                                                                shown.maxWeekKm.coerceAtLeast(
                                                                    row.km
                                                                ))
                                                            .toFloat()
                                                    )
                                                    .height(4.dp)
                                                    .background(
                                                        UH.accentInk,
                                                        RoundedCornerShape(2.dp),
                                                    )
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                val kinds =
                    data.weeks
                        .flatMap { it.cells }
                        .flatMap { it.sessions }
                        .distinctBy(::workoutChipLabel)
                if (kinds.isNotEmpty()) {
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        kinds.forEach { workout ->
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp),
                            ) {
                                Box(
                                    Modifier.size(8.dp)
                                        .background(workoutEffortColor(workout), CircleShape)
                                )
                                Text(workoutChipLabel(workout), fontSize = 11.sp, color = UH.muted)
                            }
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("Done", "Planned", "Missed").forEach { state ->
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp),
                            ) {
                                SessionBar(UH.ink, state, Modifier.width(7.dp).height(11.dp))
                                Text(L(state), fontSize = 11.sp, color = UH.muted)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CalendarCell(
    cell: CalendarDayCell,
    month: CalendarMonth,
    modifier: Modifier,
    onDay: (CalendarDayCell) -> Unit,
) {
    val locale = LocalConfiguration.current.locales[0]
    val today = L("Today")
    val rest = L("Rest")
    val race = L("Race day")
    val descriptions =
        cell.sessions.map { w ->
            "${w.title}, ${w.durationMinutes.toInt()} min, ${w.distanceKm ?: 0} km, ${L(sessionFill(w))}"
        }
    val description =
        listOfNotNull(
            today.takeIf { cell.isToday },
            cell.date.format(DateTimeFormatter.ofPattern("EEEE, d MMMM", locale)),
            race.takeIf { cell.isRaceDay },
            rest.takeIf { cell.weekNumber != null && cell.sessions.isEmpty() },
        ) + descriptions
    Column(
        modifier
            .fillMaxHeight()
            .background(
                if (cell.isToday) UH.accent.copy(alpha = .12f) else Color.Transparent,
                RoundedCornerShape(8.dp),
            )
            .then(if (cell.weekNumber != null) Modifier.clickable { onDay(cell) } else Modifier)
            .testTag("calendar.day.${cell.date}")
            .semantics(mergeDescendants = true) {
                contentDescription = description.joinToString(", ")
            }
            .padding(top = 3.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                cell.date.dayOfMonth.toString(),
                Modifier.size(24.dp)
                    .background(if (cell.isToday) UH.accentInk else Color.Transparent, CircleShape)
                    .wrapContentSize(),
                fontSize = 13.sp,
                fontWeight = if (cell.isToday) FontWeight.Bold else FontWeight.Medium,
                color =
                    if (cell.isToday) Color.White else if (cell.isCurrentMonth) UH.ink else UH.muted,
            )
            if (cell.isRaceDay)
                Icon(
                    Icons.Default.Flag,
                    null,
                    Modifier.size(10.dp).align(Alignment.CenterEnd).offset(x = 10.dp),
                    tint = UH.danger,
                )
        }
        Box(Modifier.fillMaxWidth().height(26.dp), contentAlignment = Alignment.BottomCenter) {
            Box(Modifier.fillMaxWidth().height(1.dp).background(UH.line))
            val sessions = cell.sessions.take(3)
            Row(
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.spacedBy(2.dp),
                modifier = Modifier.graphicsLayer { alpha = if (cell.isCurrentMonth) 1f else .5f },
            ) {
                sessions.forEach { workout ->
                    val share =
                        if (month.maxSessionLoad > 0) workout.calendarLoad / month.maxSessionLoad
                        else 0.0
                    SessionBar(
                        workoutEffortColor(workout),
                        sessionFill(workout),
                        Modifier.width(if (sessions.size > 1) 9.dp else 11.dp)
                            .height((24 * share).coerceIn(5.0, 24.0).dp),
                    )
                }
            }
        }
    }
}

private fun sessionFill(workout: Workout) =
    if (workout.isDone) "Done" else if (workout.isMissedFlag) "Missed" else "Planned"

@Composable
private fun SessionBar(color: Color, state: String, modifier: Modifier) {
    Canvas(modifier) {
        val path =
            Path().apply {
                val radius = minOf(3.dp.toPx(), size.width / 2)
                moveTo(0f, size.height)
                lineTo(0f, radius)
                quadraticTo(0f, 0f, radius, 0f)
                lineTo(size.width - radius, 0f)
                quadraticTo(size.width, 0f, size.width, radius)
                lineTo(size.width, size.height)
                close()
            }
        drawPath(
            path,
            color.copy(
                alpha =
                    when (state) {
                        "Done" -> 1f
                        "Missed" -> .08f
                        else -> .22f
                    }
            ),
        )
        if (state != "Done")
            drawPath(
                path,
                color,
                style =
                    Stroke(
                        1.5.dp.toPx(),
                        pathEffect =
                            if (state == "Missed")
                                PathEffect.dashPathEffect(floatArrayOf(2.5.dp.toPx(), 2.dp.toPx()))
                            else null,
                    ),
            )
    }
}

@Composable
internal fun CalendarDayContent(
    model: PlanViewModel,
    cell: CalendarDayCell,
    state: PlanState,
    onWorkout: (Workout) -> Unit,
    onWeek: (Int) -> Unit,
    onClose: () -> Unit,
) {
    val week = cell.weekNumber ?: return
    val locale = LocalConfiguration.current.locales[0]
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(
            cell.date.format(DateTimeFormatter.ofPattern("EEEE, d MMMM", locale)),
            Modifier.weight(1f),
            fontWeight = FontWeight.SemiBold,
        )
        TextButton(onClick = onClose) { Text(L("Done")) }
    }
    val workouts =
        state.snapshot?.workouts.orEmpty().filter {
            it.weekNumber == week && it.weekday.offset == cell.date.dayOfWeek.value - 1
        }
    DayRow(
        Weekday.entries[cell.date.dayOfWeek.value - 1],
        cell.date,
        workouts,
        onWorkout,
        if (model.athleteId == null && state.cachedAt == null && !state.busy)
            { w -> model.log(w, if (w.isDone) 0 else 1, 0, w.rpe, w.notes.orEmpty()) }
        else null,
    )
    SecondaryButton(
        onClick = { onWeek(week) },
        modifier = Modifier.fillMaxWidth().testTag("calendar.openWeek"),
        colors =
            ButtonDefaults.outlinedButtonColors(
                containerColor = UH.accentInk.copy(alpha = .08f),
                contentColor = UH.accentInk,
            ),
    ) {
        Icon(Icons.AutoMirrored.Filled.List, null, Modifier.size(18.dp))
        Spacer(Modifier.width(8.dp))
        Text(L("Open week %lld in list", week))
    }
}

package ai.uphill.app.feature.coaching

import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.UphillBodyFont
import ai.uphill.app.designsystem.UH
import android.graphics.Paint
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ShowChart
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.EventBusy
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalFontFamilyResolver
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
internal fun CoachCharts(overview: CoachOverview) {
    val chartTypeface = LocalFontFamilyResolver.current.resolve(UphillBodyFont).value as android.graphics.Typeface
    Column(
        Modifier.fillMaxWidth().testTag("coach.charts"),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        CoachChartCard("Adherence Trend", Icons.AutoMirrored.Filled.ShowChart, L("Target: 80%")) {
            val trend = overview.adherenceTrend
            if (trend.isEmpty()) Text(L("No adherence data recorded yet"), color = UH.muted)
            else {
                val description =
                    trend.joinToString(", ") {
                        "W${it.weekNumber}: ${coachPercent(it.adherencePct)}"
                    }
                Canvas(
                    Modifier.fillMaxWidth()
                        .height(120.dp)
                        .testTag("coach.adherence.chart")
                        .semantics { contentDescription = description }
                ) {
                    val left = 32.dp.toPx()
                    val bottom = size.height - 19.dp.toPx()
                    val height = bottom - 5.dp.toPx()
                    val width = size.width - left - 8.dp.toPx()
                    val paint =
                        Paint(Paint.ANTI_ALIAS_FLAG).apply {
                            typeface = chartTypeface
                            color = UH.muted.toArgb()
                            textSize = 10.sp.toPx()
                        }
                    listOf(0, 50, 80, 100).forEach { value ->
                        val y = bottom - height * value / 100f
                        drawLine(UH.line, Offset(left, y), Offset(size.width, y), 1.dp.toPx())
                        drawContext.canvas.nativeCanvas.drawText(
                            "$value%",
                            0f,
                            y + 3.dp.toPx(),
                            paint,
                        )
                    }
                    val points =
                        trend.mapIndexed { i, entry ->
                            Offset(
                                left +
                                    width *
                                        (if (trend.size == 1) .5f
                                        else i.toFloat() / (trend.size - 1)),
                                bottom - height * entry.adherencePct.toFloat().coerceIn(0f, 1f),
                            )
                        }
                    val path =
                        Path().apply {
                            points.forEachIndexed { i, p ->
                                if (i == 0) moveTo(p.x, p.y) else lineTo(p.x, p.y)
                            }
                        }
                    if (points.size > 1) {
                        val area =
                            Path().apply {
                                addPath(path)
                                lineTo(points.last().x, bottom)
                                lineTo(points.first().x, bottom)
                                close()
                            }
                        drawPath(
                            area,
                            Brush.verticalGradient(
                                listOf(UH.accent.copy(alpha = .35f), UH.accent.copy(alpha = .05f))
                            ),
                        )
                        drawPath(path, UH.accent, style = Stroke(2.5.dp.toPx()))
                    }
                    val target = bottom - height * .8f
                    drawLine(
                        Color(0xFF34C759).copy(alpha = .4f),
                        Offset(left, target),
                        Offset(size.width, target),
                        1.dp.toPx(),
                        pathEffect =
                            PathEffect.dashPathEffect(floatArrayOf(4.dp.toPx(), 4.dp.toPx())),
                    )
                    points.forEachIndexed { i, point ->
                        drawCircle(UH.accent, 3.dp.toPx(), point)
                        paint.textAlign = Paint.Align.CENTER
                        drawContext.canvas.nativeCanvas.drawText(
                            "W${trend[i].weekNumber}",
                            point.x,
                            size.height - 3.dp.toPx(),
                            paint,
                        )
                    }
                }
            }
        }
        val order =
            listOf("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        val counts =
            order.map { day ->
                overview.missedByDay.firstOrNull { it.dayOfWeek == day }?.count ?: 0
            }
        val labels = listOf("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun").map { L(it) }
        CoachChartCard(
            "Missed by Day",
            Icons.Default.EventBusy,
            L("%lld total misses", overview.missedByDay.sumOf { it.count }),
        ) {
            val description = labels.zip(counts).joinToString(", ") { "${it.first}: ${it.second}" }
            Canvas(
                Modifier.fillMaxWidth().height(120.dp).testTag("coach.missed.chart").semantics {
                    contentDescription = description
                }
            ) {
                val left = 20.dp.toPx()
                val bottom = size.height - 19.dp.toPx()
                val height = bottom - 5.dp.toPx()
                val max = (counts.maxOrNull() ?: 0).coerceAtLeast(1)
                val column = (size.width - left) / 7
                val paint =
                    Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        typeface = chartTypeface
                        color = UH.secondary.toArgb()
                        textSize = 10.sp.toPx()
                        textAlign = Paint.Align.CENTER
                    }
                listOf(0, max).distinct().forEach { value ->
                    val y = bottom - height * value / max
                    drawLine(UH.line, Offset(left, y), Offset(size.width, y), 1.dp.toPx())
                    drawContext.canvas.nativeCanvas.drawText(
                        value.toString(),
                        8.dp.toPx(),
                        y + 3.dp.toPx(),
                        paint,
                    )
                }
                counts.forEachIndexed { i, count ->
                    val x = left + column * i
                    val barHeight = height * count / max
                    if (count > 0)
                        drawRoundRect(
                            Color(0xFFFF3B30).copy(alpha = .85f),
                            Offset(x + column * .2f, bottom - barHeight),
                            Size(column * .6f, barHeight),
                            androidx.compose.ui.geometry.CornerRadius(4.dp.toPx()),
                        )
                    drawContext.canvas.nativeCanvas.drawText(
                        labels[i],
                        x + column / 2,
                        size.height - 3.dp.toPx(),
                        paint,
                    )
                }
            }
        }
        CoachChartCard("Workout Type Mix", Icons.Default.BarChart) {
            if (overview.workoutTypeMix.isEmpty())
                Text(L("No completed workouts in window"), color = UH.muted)
            overview.workoutTypeMix.take(6).forEach { entry ->
                val color = workoutMixColor(entry.type)
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Box(Modifier.size(8.dp).background(color, CircleShape))
                    Text(
                        entry.type,
                        Modifier.width(110.dp),
                        maxLines = 1,
                        color = UH.ink,
                        fontSize = 13.sp,
                    )
                    Box(
                        Modifier.weight(1f)
                            .height(8.dp)
                            .background(UH.line.copy(alpha = .3f), RoundedCornerShape(3.dp))
                    ) {
                        Box(
                            Modifier.fillMaxWidth(entry.pct.toFloat().coerceIn(0f, 1f))
                                .height(8.dp)
                                .background(color, RoundedCornerShape(3.dp))
                        )
                    }
                    Text(
                        coachPercent(entry.pct),
                        Modifier.width(36.dp),
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = UH.secondary,
                    )
                    Text(
                        "(${entry.count})",
                        Modifier.width(30.dp),
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        color = UH.muted,
                    )
                }
            }
        }
    }
}

@Composable
internal fun CoachChartCard(
    title: String,
    icon: ImageVector,
    summary: String? = null,
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    CoachCard(modifier) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(icon, null, Modifier.size(18.dp), tint = UH.ink)
            Text(
                L(title),
                Modifier.weight(1f),
                fontSize = 20.sp,
                fontWeight = FontWeight.SemiBold,
                color = UH.ink,
            )
            summary?.let { Text(it, fontSize = 13.sp, color = UH.secondary) }
        }
        content()
    }
}

@Composable
internal fun CoachCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    OutlinedCard(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.outlinedCardColors(containerColor = Color.White),
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

private fun workoutMixColor(type: String): Color {
    val t = type.lowercase()
    return when {
        t.contains("easy") || t.contains("recovery") -> Color(0xFF007AFF)
        t.contains("long") -> Color(0xFF34C759)
        t.contains("tempo") || t.contains("threshold") -> Color(0xFFFF9500)
        t.contains("interval") -> Color(0xFFFF3B30)
        t.contains("endurance") || t.contains("strength") || t.contains("me") -> Color(0xFFAF52DE)
        t.contains("cross") -> Color(0xFF30B0C7)
        else -> Color(0xFF8E8E93)
    }
}

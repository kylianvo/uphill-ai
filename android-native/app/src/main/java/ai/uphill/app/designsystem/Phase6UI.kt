package ai.uphill.app.designsystem

import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.racehistory.*
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

@Composable
fun P6(key: String, vararg args: Any): String {
    val context = LocalContext.current
    val id = context.resources.getIdentifier("p6_$key", "string", context.packageName)
    return if (id != 0) stringResource(id, *args) else key
}

@Composable
fun P6Card(content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(
            Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            content = content,
        )
    }
}

@Composable
fun P6Field(label: String, value: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value,
        onChange,
        label = { Text(P6(label)) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = label != "note" && label != "description",
        keyboardOptions =
            KeyboardOptions(
                keyboardType =
                    when (label) {
                        "distance",
                        "elevation",
                        "duration" -> KeyboardType.Decimal
                        "resting_hr",
                        "aet_hr",
                        "ant_hr",
                        "max_hr",
                        "overall_rank",
                        "overall_finishers",
                        "gender_rank",
                        "gender_finishers",
                        "age_rank",
                        "age_finishers" -> KeyboardType.Number
                        "athlete_email" -> KeyboardType.Email
                        "result_url" -> KeyboardType.Uri
                        else -> KeyboardType.Text
                    }
            ),
    )
}

@Composable
fun P6Choice(label: String, value: String, values: List<String>, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column {
        Text(P6(label), style = MaterialTheme.typography.labelMedium)
        Box {
            OutlinedButton(onClick = { expanded = true }) { Text(P6Option(value)) }
            DropdownMenu(expanded, { expanded = false }) {
                values.forEach { v ->
                    DropdownMenuItem(
                        text = { Text(P6Option(v)) },
                        onClick = {
                            onChange(v)
                            expanded = false
                        },
                    )
                }
            }
        }
    }
}

@Composable
fun P6Dialog(title: String, onDismiss: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = MaterialTheme.shapes.large) {
            Column(
                Modifier.fillMaxWidth()
                    .heightIn(max = 650.dp)
                    .verticalScroll(rememberScrollState())
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(P6(title), style = MaterialTheme.typography.titleLarge)
                content()
            }
        }
    }
}

@Composable
fun RaceDetailDialog(
    service: RaceHistoryService,
    id: Int,
    onDismiss: () -> Unit,
    athleteId: Int? = null,
) {
    var detail by remember(id) { mutableStateOf<RaceDetailResponse?>(null) }
    var courseId by remember(id) { mutableStateOf<Int?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    val context = LocalContext.current
    LaunchedEffect(id, courseId) {
        try {
            detail = service.detail(id, courseId, athleteId)
            error = null
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            error = e.message
        }
    }
    P6Dialog("race_detail", onDismiss) {
        error?.let { Text(P6Error(it), color = UH.danger) }
        val d = detail
        if (d == null && error == null) CircularProgressIndicator()
        d?.let {
            Text(it.result.raceName, style = MaterialTheme.typography.titleMedium)
            Text("${it.result.raceDate} · ${it.result.distanceKm} km · ${it.result.duration}")
            it.result.location?.let { Text(it) }
            listOf(
                    "overall_top" to it.performance.overallTopPct,
                    "gender_top" to it.performance.genderTopPct,
                    "age_top" to it.performance.ageGroupTopPct,
                )
                .forEach { (key, value) -> value?.let { Text(P6(key, it)) } }
            it.performance.averagePaceSecKm?.let {
                Text(P6("average_pace", raceDuration(it.toInt())))
            }
            it.previousFinish?.let { previous ->
                Text(P6("previous_finish", previous.raceDate, raceDuration(previous.finishTimeSec)))
                Text(
                    P6(
                        if (previous.deltaSec < 0) "faster" else "slower",
                        raceDuration(kotlin.math.abs(previous.deltaSec)),
                    )
                )
            }
            it.result.userNote?.let { Text(it) }
            if (safeRaceResultURL(it.result.resultUrl))
                TextButton(
                    onClick = {
                        runCatching {
                            context.startActivity(
                                Intent(Intent.ACTION_VIEW, Uri.parse(it.result.resultUrl))
                            )
                        }
                    }
                ) {
                    Text(P6("open_results"))
                }
            Text(P6("course_context"), style = MaterialTheme.typography.titleMedium)
            it.courseContext.message?.let { Text(it) }
            it.courseContext.candidates.forEach { course ->
                OutlinedButton(onClick = { courseId = course.id }) {
                    Text("${course.raceName} · ${course.distanceLabel}")
                }
            }
            it.courseContext.course?.let { course ->
                Text("${course.raceName} · ${course.distanceLabel}")
                Text(
                    P6(
                        "edition_status",
                        course.editionYear?.toString() ?: "—",
                        course.editionStatus,
                    )
                )
                Text(course.terrain.joinToString(" · "))
                course.keyClimbs.forEach { Text(it) }
                course.runnerReviews.forEach { Text(it) }
                course.climate.forEach { (key, value) ->
                    Text("$key: ${(value as? JsonPrimitive)?.contentOrNull ?: value}")
                }
                course.sourceLabel?.let { Text(it, color = UH.secondary) }
                course.sourceUrls.filter(::safeRaceResultURL).forEach { url ->
                    TextButton(
                        onClick = {
                            runCatching {
                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            }
                        }
                    ) {
                        Text(P6("source"))
                    }
                }
            }
        }
        TextButton(onClick = onDismiss) { Text(P6("close")) }
    }
}

@Composable
fun P6Option(value: String): String =
    when (value) {
        "Monday" -> P6("option_monday")
        "Tuesday" -> P6("option_tuesday")
        "Wednesday" -> P6("option_wednesday")
        "Thursday" -> P6("option_thursday")
        "Friday" -> P6("option_friday")
        "Saturday" -> P6("option_saturday")
        "Sunday" -> P6("option_sunday")
        "all" -> P6("option_all")
        "beginner" -> P6("option_beginner")
        "intermediate" -> P6("option_intermediate")
        "advanced" -> P6("option_advanced")
        "pending" -> P6("option_pending")
        "syncing" -> P6("option_syncing")
        "synced" -> P6("option_synced")
        "failed" -> P6("option_failed")
        "idle" -> P6("option_idle")
        else -> value
    }

@Composable
fun P6Error(message: String): String =
    when (message) {
        "Text is too long." -> P6("error_text_long")
        "Ranks must be positive whole numbers." -> P6("error_rank_positive")
        "Rank cannot exceed finishers." -> P6("error_rank_finishers")
        "Enter a race name and discipline." -> P6("error_name_discipline")
        "Enter a distance between 0 and 1,000 km." -> P6("error_distance")
        "Elevation must be zero or positive." -> P6("error_elevation")
        "Enter finish time as h:mm:ss or mm:ss." -> P6("error_finish_format")
        "Finish time must be greater than zero." -> P6("error_finish_positive")
        "Use an http or https link without credentials." -> P6("error_link")
        "Heart rate must be a whole number." -> P6("error_hr_whole")
        "Heart rate is outside the supported range." -> P6("error_hr_range")
        "Enter date as yyyy-mm-dd." -> P6("error_date")
        "Resting HR, AeT, AnT and Max HR must increase in that order." -> P6("error_hr_order")
        "Enter pace as 5:30." -> P6("error_pace")
        "Zone 2 slow end must be slower than the fast end." -> P6("error_zone_order")
        "Threshold pace must be faster than Zone 2." -> P6("error_threshold")
        "Enter duration between 0 and 1,440 minutes." -> P6("error_duration")
        "Enter a positive distance." -> P6("error_distance_positive")
        "AI workout duration must be positive." -> P6("error_ai_duration")
        "Enter a title." -> P6("error_title")
        "Invalid COROS authorization URL." -> P6("error_oauth_url")
        "Missing COROS authorization state." -> P6("error_oauth_state")
        "Invalid callback response from COROS." -> P6("error_oauth_callback")
        "Authorization security check failed or the connection expired." ->
            P6("error_oauth_security")
        "Enter an email address." -> P6("error_email")
        "COROS_not_connected" -> P6("push_not_connected")
        "NOTHING_to_push" -> P6("push_nothing")
        "RACE_too_far" -> P6("push_too_far")
        "RACE_too_close" -> P6("push_too_close")
        "PUSH_in_progress" -> P6("push_in_progress")
        "PUSH_limit" -> P6("push_limit")
        "COROS_rejected" -> P6("push_rejected")
        else -> L(message)
    }

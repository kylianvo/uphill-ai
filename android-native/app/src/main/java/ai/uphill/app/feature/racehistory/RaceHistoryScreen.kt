package ai.uphill.app.feature.racehistory

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.networking.*
import ai.uphill.app.core.racehistory.*
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import java.time.Instant
import java.time.ZoneOffset
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

@Composable
fun RaceHistoryScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val service = remember(api) { RaceHistoryService(api) }
    val vm: RaceHistoryViewModel =
        viewModel(key = "race-${user.id}") { RaceHistoryViewModel(service) }
    val state by vm.state.collectAsState()
    var add by remember { mutableStateOf(false) }
    var edit by remember { mutableStateOf<RaceResult?>(null) }
    var link by remember { mutableStateOf(false) }
    var detailId by remember { mutableStateOf<Int?>(null) }
    var bibClaim by remember { mutableStateOf<RaceClaim?>(null) }
    var delete by remember { mutableStateOf<RaceResult?>(null) }
    var unlink by remember { mutableStateOf<RaceClaim?>(null) }
    LaunchedEffect(vm) { vm.load() }
    LaunchedEffect(state.history?.claims?.map { it.syncStatus }) {
        while (
            state.history?.claims?.any { it.syncStatus in listOf("pending", "syncing") } == true
        ) {
            delay(3000)
            vm.load()
        }
    }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(P6("race_history"), style = MaterialTheme.typography.headlineMedium)
        Text(P6("race_intro"), color = UH.secondary)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { add = true }, enabled = !state.busy) { Text(P6("add_race")) }
            OutlinedButton(onClick = { link = true }, enabled = !state.busy) {
                Text(P6("link_profile"))
            }
        }
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.error?.let {
            Text(P6Error(it), color = UH.danger)
            TextButton(onClick = vm::load) { Text(P6("retry")) }
        }
        val h = state.history
        if (h != null) {
            P6Card {
                Text(P6("trail_summary"), style = MaterialTheme.typography.titleMedium)
                Text(
                    P6(
                        "trail_stats",
                        h.summary.trailFinishes,
                        h.summary.trailDnfs,
                        h.summary.ultras,
                    )
                )
                h.summary.longestFinish?.let {
                    Text(P6("longest_finish", it.distanceKm, it.raceName))
                }
            }
            P6Card {
                Text(P6("road_pbs"), style = MaterialTheme.typography.titleMedium)
                listOf(
                        "5k" to "5 km",
                        "10k" to "10 km",
                        "hm" to "Half marathon",
                        "fm" to "Marathon",
                    )
                    .forEach { (key, title) ->
                        val pb =
                            if (h.summary.roadPrs != null) h.summary.roadPrs[key]
                            else if (key == "hm") h.summary.roadHmPr
                            else if (key == "fm") h.summary.roadFmPr else null
                        TextButton(
                            onClick = { detailId = pb?.resultId },
                            enabled = pb?.resultId != null,
                        ) {
                            Text("$title · ${pb?.timeSec?.let(::raceDuration) ?: "—"}")
                        }
                        pb?.let {
                            Text(
                                it.date.orEmpty() + (if (it.stale) " · " + P6("stale_pb") else ""),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
            }
            P6Card {
                Text(P6("distance_badges"), style = MaterialTheme.typography.titleMedium)
                DistanceBadge.derive(h.results).chunked(2).forEach { badges ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        badges.forEach { badge ->
                            OutlinedButton(
                                onClick = { detailId = badge.result?.id },
                                enabled = badge.unlocked,
                                modifier = Modifier.weight(1f),
                            ) {
                                Column {
                                    Text(badge.category.label)
                                    Text(badge.result?.duration ?: "—")
                                    badge.result?.let {
                                        Text(
                                            it.raceDate,
                                            style = MaterialTheme.typography.labelSmall,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (h.claims.isNotEmpty())
                Text(P6("linked_profiles"), style = MaterialTheme.typography.titleMedium)
            h.claims.forEach { claim ->
                P6Card {
                    Text(
                        "${claim.source.uppercase()} · ${claim.displayName}",
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(P6Option(claim.syncStatus), color = UH.secondary)
                    claim.syncError?.let { Text(P6Error(it), color = UH.danger) }
                    if (claim.verified) Text(P6("verified"), color = UH.accentInk)
                    Row {
                        TextButton(
                            onClick = { vm.perform({ service.refreshClaim(claim.id) }) },
                            enabled = !state.busy,
                        ) {
                            Text(P6("refresh"))
                        }
                        TextButton(onClick = { bibClaim = claim }, enabled = !state.busy) {
                            Text(P6("verify_bib"))
                        }
                        TextButton(onClick = { unlink = claim }, enabled = !state.busy) {
                            Text(P6("unlink"))
                        }
                    }
                }
            }
            if (h.results.isEmpty()) P6Card { Text(P6("no_results")) }
            h.results
                .filter { !it.hidden }
                .sortedByDescending { it.raceDate }
                .forEach { result ->
                    P6Card {
                        TextButton(onClick = { detailId = result.id }) {
                            Text(result.raceName, style = MaterialTheme.typography.titleMedium)
                        }
                        Text("${result.raceDate} · ${result.distanceKm} km · ${result.duration}")
                        result.elevationGainM?.let {
                            Text("D+ ${it.toInt()} m", color = UH.secondary)
                        }
                        Row {
                            Checkbox(
                                result.selected,
                                { selected ->
                                    vm.perform({
                                        service.update(
                                            result.id,
                                            buildJsonObject { put("selected", selected) },
                                        )
                                    })
                                },
                                enabled = !state.busy,
                            )
                            Text(P6("confirmed"), Modifier.padding(top = 12.dp))
                        }
                        if (result.source == "manual")
                            Row {
                                TextButton(onClick = { edit = result }, enabled = !state.busy) {
                                    Text(P6("edit"))
                                }
                                TextButton(onClick = { delete = result }, enabled = !state.busy) {
                                    Text(P6("delete"), color = UH.danger)
                                }
                            }
                    }
                }
        }
    }
    if (add || edit != null)
        ManualRaceDialog(
            edit,
            state.busy,
            state.error,
            onDismiss = {
                add = false
                edit = null
            },
        ) { payload ->
            val id = edit?.id
            vm.perform(
                { if (id == null) service.add(payload) else service.update(id, payload.patch()) },
                {
                    add = false
                    edit = null
                },
            )
        }
    if (link)
        LinkProfileDialog(service, state.busy, state.error, { link = false }) { source, id ->
            vm.perform({ service.claim(source, id) }, { link = false })
        }
    bibClaim?.let { claim ->
        var bib by remember(claim.id) { mutableStateOf("") }
        P6Dialog("verify_bib", { bibClaim = null }) {
            Text(claim.displayName)
            P6Field("bib", bib) { bib = it }
            Text(P6("bib_help"))
            Button(
                onClick = { vm.perform({ service.verifyBib(claim.id, bib) }, { bibClaim = null }) },
                enabled = bib.isNotBlank() && !state.busy,
            ) {
                Text(P6("verify"))
            }
            TextButton(onClick = { bibClaim = null }) { Text(P6("cancel")) }
            state.error?.let { Text(P6Error(it), color = UH.danger) }
        }
    }
    delete?.let { r ->
        AlertDialog(
            onDismissRequest = { delete = null },
            title = { Text(P6("delete_race")) },
            text = { Text(r.raceName) },
            confirmButton = {
                TextButton(
                    onClick = { vm.perform({ service.delete(r.id) }, { delete = null }) },
                    enabled = !state.busy,
                ) {
                    Text(P6("delete"))
                }
            },
            dismissButton = { TextButton(onClick = { delete = null }) { Text(P6("cancel")) } },
        )
    }
    unlink?.let { c ->
        AlertDialog(
            onDismissRequest = { unlink = null },
            title = { Text(P6("unlink_profile")) },
            text = { Text(c.displayName) },
            confirmButton = {
                TextButton(
                    onClick = { vm.perform({ service.deleteClaim(c.id) }, { unlink = null }) },
                    enabled = !state.busy,
                ) {
                    Text(P6("unlink"))
                }
            },
            dismissButton = { TextButton(onClick = { unlink = null }) { Text(P6("cancel")) } },
        )
    }
    detailId?.let { id -> RaceDetailDialog(service, id, { detailId = null }) }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ManualRaceDialog(
    result: RaceResult?,
    busy: Boolean,
    serverError: String?,
    onDismiss: () -> Unit,
    onSave: (ManualResultPayload) -> Unit,
) {
    var d by
        remember(result?.id) {
            mutableStateOf(result?.let(ManualRaceDraft::from) ?: ManualRaceDraft())
        }
    var error by remember { mutableStateOf<String?>(null) }
    var pickDate by remember { mutableStateOf(false) }
    if (pickDate) {
        val dateState =
            rememberDatePickerState(
                initialSelectedDateMillis =
                    runCatching {
                            java.time.LocalDate.parse(d.raceDate)
                                .atStartOfDay(ZoneOffset.UTC)
                                .toInstant()
                                .toEpochMilli()
                        }
                        .getOrNull()
            )
        DatePickerDialog(
            onDismissRequest = { pickDate = false },
            confirmButton = {
                TextButton(
                    onClick = {
                        dateState.selectedDateMillis?.let {
                            d =
                                d.copy(
                                    raceDate =
                                        Instant.ofEpochMilli(it)
                                            .atZone(ZoneOffset.UTC)
                                            .toLocalDate()
                                            .toString()
                                )
                        }
                        pickDate = false
                    }
                ) {
                    Text(P6("save"))
                }
            },
            dismissButton = { TextButton(onClick = { pickDate = false }) { Text(P6("cancel")) } },
        ) {
            DatePicker(state = dateState)
        }
    }
    P6Dialog(if (result == null) "add_race" else "edit_race", onDismiss) {
        (error ?: serverError)?.let { Text(P6Error(it), color = UH.danger) }
        P6Field("race_name", d.raceName) { d = d.copy(raceName = it) }
        Text(P6("date"), style = MaterialTheme.typography.labelMedium)
        OutlinedButton(onClick = { pickDate = true }) { Text(d.raceDate) }
        P6Choice("discipline", d.discipline, listOf("trail", "road")) {
            d = d.copy(discipline = it)
        }
        P6Field("distance", d.distance) { d = d.copy(distance = it) }
        P6Field("elevation", d.elevation) { d = d.copy(elevation = it) }
        Row {
            Checkbox(d.isDnf, { d = d.copy(isDnf = it) })
            Text("DNF", Modifier.padding(top = 12.dp))
        }
        if (!d.isDnf) P6Field("finish_time", d.duration) { d = d.copy(duration = it) }
        P6Field("location", d.location) { d = d.copy(location = it) }
        P6Field("bib", d.bib) { d = d.copy(bib = it) }
        P6Field("result_url", d.resultUrl) { d = d.copy(resultUrl = it) }
        P6Field("overall_rank", d.rankOverall) { d = d.copy(rankOverall = it) }
        P6Field("overall_finishers", d.totalOverall) { d = d.copy(totalOverall = it) }
        P6Field("gender_rank", d.rankGender) { d = d.copy(rankGender = it) }
        P6Field("gender_finishers", d.totalGender) { d = d.copy(totalGender = it) }
        P6Field("age_rank", d.rankAgeGroup) { d = d.copy(rankAgeGroup = it) }
        P6Field("age_finishers", d.totalAgeGroup) { d = d.copy(totalAgeGroup = it) }
        P6Field("note", d.userNote) { d = d.copy(userNote = it) }
        Button(
            onClick = {
                runCatching { d.payload() }.onSuccess(onSave).onFailure { error = it.message }
            },
            enabled = !busy,
        ) {
            Text(P6("save"))
        }
        TextButton(onClick = onDismiss, enabled = !busy) { Text(P6("cancel")) }
    }
}

@Composable
private fun LinkProfileDialog(
    service: RaceHistoryService,
    busy: Boolean,
    serverError: String?,
    onDismiss: () -> Unit,
    onClaim: (String, String) -> Unit,
) {
    var source by remember { mutableStateOf("utmb") }
    var query by remember { mutableStateOf("") }
    var candidates by remember { mutableStateOf<List<RaceCandidate>>(emptyList()) }
    var searching by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var selected by remember { mutableStateOf<RaceCandidate?>(null) }
    LaunchedEffect(source, query) {
        candidates = emptyList()
        selected = null
        if (query.trim().length >= 2) {
            delay(500)
            searching = true
            try {
                candidates = service.search(source, query.trim())
                error = null
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                error = e.message
            } finally {
                searching = false
            }
        }
    }
    P6Dialog("link_profile", onDismiss) {
        P6Choice("source", source, listOf("utmb", "vbm")) { source = it }
        P6Field("search_name", query) { query = it }
        serverError?.let { Text(P6Error(it), color = UH.danger) }
        if (searching) LinearProgressIndicator(Modifier.fillMaxWidth())
        error?.let { Text(P6Error(it), color = UH.danger) }
        if (!searching && query.length >= 2 && candidates.isEmpty()) Text(P6("no_matches"))
        candidates.forEach { candidate ->
            OutlinedButton(onClick = { selected = candidate }, modifier = Modifier.fillMaxWidth()) {
                Column {
                    Text(candidate.displayName)
                    Text(
                        listOfNotNull(candidate.ageGroup, candidate.index?.let { "UTMB $it" })
                            .joinToString(" · "),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
        selected?.let { candidate ->
            Text(P6("claim_confirm", candidate.displayName))
            Button(onClick = { onClaim(source, candidate.externalId) }, enabled = !busy) {
                Text(P6("claim_profile"))
            }
        }
        TextButton(onClick = onDismiss) { Text(P6("cancel")) }
    }
}

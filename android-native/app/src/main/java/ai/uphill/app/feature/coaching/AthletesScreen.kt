package ai.uphill.app.feature.coaching

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun AthletesScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val service = remember(api) { CoachingService(api) }
    val vm: CoachingViewModel =
        viewModel(key = "roster-${user.id}") { CoachingViewModel(service, user.isCoach) }
    val state by vm.state.collectAsState()
    var invite by remember { mutableStateOf(false) }
    var email by remember { mutableStateOf("") }
    var remove by remember { mutableStateOf<CoachedAthleteRow?>(null) }
    var days by remember { mutableIntStateOf(14) }
    var level by remember { mutableStateOf("all") }
    LaunchedEffect(vm, days, level) { vm.load(days, level) }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            P6(if (user.isCoach) "athletes" else "coaching_invites"),
            style = MaterialTheme.typography.headlineMedium,
        )
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.error?.let {
            Text(P6Error(it), color = UH.danger)
            TextButton(onClick = { vm.load(days, level) }) { Text(P6("retry")) }
        }
        state.invites.forEach { inv ->
            P6Card {
                Text(P6("invited_by", inv.displayName))
                Row {
                    Button(
                        onClick = { vm.action(days, level) { service.accept(inv.id) } },
                        enabled = !state.busy,
                    ) {
                        Text(P6("accept"))
                    }
                    TextButton(
                        onClick = { vm.action(days, level) { service.decline(inv.id) } },
                        enabled = !state.busy,
                    ) {
                        Text(P6("decline"))
                    }
                }
            }
        }
        if (user.isCoach) {
            Button(onClick = { invite = true }, enabled = !state.busy) {
                Text(P6("invite_athlete"))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                P6Choice("period", "$days", listOf("7", "14", "28")) { days = it.toInt() }
                P6Choice(
                    "runner_level",
                    level,
                    listOf("all", "beginner", "intermediate", "advanced"),
                ) {
                    level = it
                }
            }
            state.overview?.let { overview ->
                overview.rosterTotals?.let { totals ->
                    P6Card {
                        Text(P6("roster_totals"), style = MaterialTheme.typography.titleMedium)
                        Text(
                            P6(
                                "roster_stats",
                                totals.distanceKm ?: 0.0,
                                totals.durationHours ?: 0.0,
                                totals.workoutCount ?: 0,
                            )
                        )
                        totals.elevationGainM?.let { Text("D+ ${it.toInt()} m") }
                    }
                }
                if (
                    overview.actionItems.draftPlans.isNotEmpty() ||
                        overview.actionItems.pendingWorkoutApprovals.isNotEmpty()
                )
                    P6Card {
                        Text(P6("needs_review"), style = MaterialTheme.typography.titleMedium)
                        overview.actionItems.draftPlans.forEach { draft ->
                            TextButton(onClick = { onNavigate("athlete/${draft.athleteId}") }) {
                                Text(P6("draft_plan", draft.athleteName, draft.raceName))
                            }
                        }
                        overview.actionItems.pendingWorkoutApprovals.forEach { w ->
                            Text(w.athleteName + " · " + w.title)
                            Row {
                                Button(
                                    onClick = {
                                        vm.action(days, level) {
                                            service.approve(w.athleteId, w.planId, w.workoutId)
                                        }
                                    },
                                    enabled = !state.busy,
                                ) {
                                    Text(P6("approve"))
                                }
                                TextButton(onClick = { onNavigate("athlete/${w.athleteId}") }) {
                                    Text(P6("view_plan"))
                                }
                            }
                        }
                    }
                overview.phaseAlerts.forEach { alert ->
                    P6Card {
                        Text(P6("phase_alert", alert.athleteName, alert.phase, alert.starts))
                        TextButton(onClick = { onNavigate("athlete/${alert.athleteId}") }) {
                            Text(P6("view_plan"))
                        }
                    }
                }
                if (overview.workoutTypeMix.isNotEmpty())
                    P6Card {
                        Text(P6("workout_mix"), style = MaterialTheme.typography.titleMedium)
                        overview.workoutTypeMix.forEach { mix ->
                            Text("${mix.type} · ${coachPercent(mix.pct)}")
                            LinearProgressIndicator(
                                progress = { mix.pct.toFloat().coerceIn(0f, 1f) },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                if (overview.adherenceTrend.isNotEmpty())
                    P6Card {
                        Text(P6("adherence_trend"), style = MaterialTheme.typography.titleMedium)
                        overview.adherenceTrend.forEach { week ->
                            Text(
                                P6(
                                    "week_adherence",
                                    week.weekNumber,
                                    coachPercent(week.adherencePct),
                                )
                            )
                            LinearProgressIndicator(
                                progress = { week.adherencePct.toFloat().coerceIn(0f, 1f) },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                if (overview.missedByDay.isNotEmpty())
                    P6Card {
                        Text(P6("missed_by_day"), style = MaterialTheme.typography.titleMedium)
                        overview.missedByDay.forEach { Text("${it.dayOfWeek} · ${it.count}") }
                    }
                if (overview.races.isNotEmpty())
                    P6Card {
                        Text(P6("upcoming_races"), style = MaterialTheme.typography.titleMedium)
                        overview.races.forEach { race ->
                            Text("${race.raceName} · ${race.raceDate.orEmpty()}")
                            race.athletes.forEach { a ->
                                TextButton(onClick = { onNavigate("athlete/${a.athleteId}") }) {
                                    Text(a.name)
                                }
                            }
                        }
                    }
            }
            Text(P6("roster"), style = MaterialTheme.typography.titleLarge)
            if (state.roster.isEmpty() && !state.busy) P6Card { Text(P6("empty_roster")) }
            state.roster.forEach { athlete ->
                val stats =
                    state.overview?.athletes?.firstOrNull { it.athleteId == athlete.athleteId }
                P6Card {
                    Text(athlete.displayName, style = MaterialTheme.typography.titleMedium)
                    Text(athlete.athleteEmail, color = UH.secondary)
                    Text(
                        P6(if (athlete.status == "active") "active" else "invited"),
                        color = UH.accentInk,
                    )
                    stats?.adherencePct?.let { Text(P6("adherence", coachPercent(it))) }
                    if (stats?.needsAttention == true)
                        Text(P6("needs_attention"), color = UH.warningInk)
                    stats?.activePlan?.let {
                        Text(P6("plan_progress", it.raceName, it.currentWeek, it.totalWeeks))
                    }
                    Row {
                        TextButton(
                            onClick = { onNavigate("athlete/${athlete.athleteId}") },
                            enabled = athlete.status == "active",
                        ) {
                            Text(P6("view_athlete"))
                        }
                        TextButton(onClick = { remove = athlete }, enabled = !state.busy) {
                            Text(P6("remove"), color = UH.danger)
                        }
                    }
                }
            }
        } else if (state.invites.isEmpty() && !state.busy) Text(P6("no_invites"))
    }
    if (invite)
        P6Dialog("invite_athlete", { invite = false }) {
            P6Field("athlete_email", email) { email = it }
            state.error?.let { Text(P6Error(it), color = UH.danger) }
            Button(
                onClick = {
                    vm.action(days, level) {
                        service.invite(email)
                        invite = false
                        email = ""
                    }
                },
                enabled = !state.busy && email.contains('@'),
            ) {
                Text(P6("send_invite"))
            }
            TextButton(onClick = { invite = false }) { Text(P6("cancel")) }
        }
    remove?.let { athlete ->
        AlertDialog(
            onDismissRequest = { remove = null },
            title = { Text(P6("remove_athlete")) },
            text = { Text(athlete.displayName) },
            confirmButton = {
                TextButton(
                    onClick = {
                        vm.action(days, level) {
                            service.removeAthlete(athlete.id)
                            remove = null
                        }
                    },
                    enabled = !state.busy,
                ) {
                    Text(P6("remove"))
                }
            },
            dismissButton = { TextButton(onClick = { remove = null }) { Text(P6("cancel")) } },
        )
    }
}

package ai.uphill.app.feature.coaching

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun AthletesScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val service = remember(api) { CoachingService(api) }
    val vm: CoachingViewModel =
        viewModel(key = "roster-${user.id}-${user.isCoach}") {
            CoachingViewModel(service, user.isCoach)
        }
    val state by vm.state.collectAsState()
    var email by rememberSaveable { mutableStateOf("") }
    var invitedEmail by remember { mutableStateOf<String?>(null) }
    var remove by remember { mutableStateOf<CoachedAthleteRow?>(null) }
    var profileAthlete by remember { mutableStateOf<CoachedAthleteRow?>(null) }
    var days by rememberSaveable { mutableIntStateOf(14) }
    var level by rememberSaveable { mutableStateOf("all") }
    var section by rememberSaveable { mutableStateOf("Overview") }
    var search by rememberSaveable { mutableStateOf("") }
    val scroll = rememberScrollState()
    LaunchedEffect(section) { scroll.scrollTo(0) }
    LaunchedEffect(vm, days, level) { vm.load(days, level) }
    Column(
        Modifier.fillMaxSize().verticalScroll(scroll).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(
                if (user.isCoach) L("Coach Hub") else P6("coaching_invites"),
                Modifier.weight(1f),
                style = MaterialTheme.typography.titleMedium,
            )
            IconButton(onClick = { vm.load(days, level) }, enabled = !state.busy) {
                Icon(androidx.compose.material.icons.Icons.Default.Refresh, L("Refresh"))
            }
        }
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.error?.let {
            if (section != "Roster") {
                Text(P6Error(it), color = UH.danger)
                TextButton(onClick = { vm.load(days, level) }) { Text(P6("retry")) }
            }
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
            Row(
                Modifier.fillMaxWidth()
                    .background(UH.hover, RoundedCornerShape(8.dp))
                    .padding(3.dp)
                    .selectableGroup(),
                horizontalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                listOf("Overview", "Roster").forEach { item ->
                    Box(
                        Modifier.weight(1f)
                            .background(
                                if (section == item) Color.White else Color.Transparent,
                                RoundedCornerShape(6.dp),
                            )
                            .selectable(
                                section == item,
                                role = Role.Tab,
                                onClick = { section = item },
                            )
                            .testTag("coach.section.${item.lowercase()}")
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            L(item),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = UH.ink,
                        )
                    }
                }
            }
            if (section == "Overview") {
                CoachCard {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text(L("Window:"), color = UH.secondary, fontSize = 13.sp)
                        listOf(7, 14, 30).forEach { value ->
                            CoachFilterChip("${value}d", value == days, !state.busy) {
                                days = value
                            }
                        }
                    }
                    Text(L("Level:"), color = UH.secondary, fontSize = 13.sp)
                    Row(
                        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        listOf("all", "beginner", "intermediate", "advanced", "elite").forEach {
                            value ->
                            CoachFilterChip(
                                L(value.replaceFirstChar { it.uppercase() }),
                                value == level,
                                !state.busy,
                            ) {
                                level = value
                            }
                        }
                    }
                }
                state.overview?.let { overview ->
                    CoachOverviewSections(overview) { onNavigate("athlete/$it") }
                    CoachCharts(overview)
                    CoachRaceBreakdown(overview.races) { race ->
                        search = race
                        section = "Roster"
                    }
                }
            } else {
                CoachRosterSection(
                    state.roster,
                    state.overview,
                    search,
                    { search = it },
                    email,
                    {
                        email = it
                        invitedEmail = null
                    },
                    state.busy,
                    state.error?.let { P6Error(it) },
                    invitedEmail,
                    onInvite = {
                        val address = email.trim()
                        invitedEmail = null
                        vm.action(days, level) {
                            service.invite(address)
                            email = ""
                            invitedEmail = address
                        }
                    },
                    onAthlete = { onNavigate("athlete/$it") },
                    onProfile = { profileAthlete = it },
                    onRemove = { remove = it },
                )
            }
        } else if (state.invites.isEmpty() && !state.busy) Text(P6("no_invites"))
    }
    profileAthlete?.let { athlete ->
        CoachedAthleteProfileSheet(api, athlete) { profileAthlete = null }
    }
    remove?.let { athlete ->
        AlertDialog(
            onDismissRequest = { remove = null },
            title = { Text(L("Remove Athlete from Roster?")) },
            text = {
                Text(
                    L(
                        "Are you sure you want to remove %@? They will no longer share their plan and data with you.",
                        athlete.displayName,
                    )
                )
            },
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

@Composable
private fun CoachFilterChip(
    label: String,
    selected: Boolean,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Text(
        label,
        Modifier.background(
                if (selected) UH.accent.copy(alpha = .18f) else UH.hover,
                RoundedCornerShape(50),
            )
            .selectable(selected, enabled = enabled, role = Role.RadioButton, onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        fontSize = 12.sp,
        fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
        color = if (selected) UH.accentInk else UH.secondary,
    )
}

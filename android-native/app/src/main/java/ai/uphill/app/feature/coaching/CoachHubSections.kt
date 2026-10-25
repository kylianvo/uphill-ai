package ai.uphill.app.feature.coaching

import ai.uphill.app.core.coaching.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
internal fun CoachOverviewSections(overview: CoachOverview, onAthlete: (Int) -> Unit) {
    if (overview.phaseAlerts.isNotEmpty()) {
        CoachChartCard("Phase Alerts", Icons.Default.Warning) {
            overview.phaseAlerts.forEach { alert ->
                HubLink(onClick = { onAthlete(alert.athleteId) }) {
                    Text(
                        L(
                            "%@ enters %@ %@",
                            alert.athleteName,
                            alert.phase,
                            L(if (alert.starts == "this_week") "this week" else "next week"),
                        ),
                        Modifier.weight(1f),
                        color = UH.warningInk,
                        fontSize = 15.sp,
                    )
                }
            }
        }
    }
    CoachChartCard("Action Items", Icons.Default.Checklist) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            listOf(
                    overview.actionItems.draftPlans.size to "Draft plans to finish",
                    overview.actionItems.pendingWorkoutApprovals.size to "Workouts pending approval",
                )
                .forEachIndexed { index, (count, label) ->
                    Column(
                        Modifier.weight(1f)
                            .background(UH.hover, RoundedCornerShape(8.dp))
                            .padding(10.dp)
                    ) {
                        Text(
                            "$count",
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Black,
                            color = if (index == 0) UH.ink else UH.warningInk,
                        )
                        Text(L(label), fontSize = 13.sp, color = UH.secondary)
                    }
                }
        }
        overview.actionItems.draftPlans.forEach { item ->
            HubLink(onClick = { onAthlete(item.athleteId) }) {
                Text(
                    L("%@: Draft plan \"%@\"", item.athleteName, item.raceName),
                    Modifier.weight(1f),
                    fontSize = 13.sp,
                    color = UH.secondary,
                )
            }
        }
        overview.actionItems.pendingWorkoutApprovals.forEach { item ->
            HubLink(onClick = { onAthlete(item.athleteId) }) {
                Text(
                    L("%@: Session \"%@\" needs approval", item.athleteName, item.title),
                    Modifier.weight(1f),
                    fontSize = 13.sp,
                    color = UH.warningInk,
                )
            }
        }
    }
    CoachChartCard(
        "Roster Progress",
        Icons.Default.Groups,
        L("%lld runners", overview.athletes.size),
    ) {
        if (overview.athletes.isEmpty()) {
            Text(
                L("No athletes on your roster yet. Switch to Roster tab to invite runners."),
                fontSize = 13.sp,
                color = UH.muted,
            )
        }
        overview.athletes.forEach { athlete ->
            Row(
                Modifier.fillMaxWidth()
                    .background(UH.hover.copy(alpha = .5f), RoundedCornerShape(8.dp))
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Column(Modifier.weight(1f)) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Text(
                            athlete.name,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold,
                            modifier = Modifier.weight(1f, false),
                        )
                        if (athlete.needsAttention)
                            Box(Modifier.size(6.dp).background(UH.warningInk, CircleShape))
                    }
                    Text(
                        athlete.activePlan?.let {
                            "W${it.currentWeek}/${it.totalWeeks} · ${it.raceName}"
                        } ?: L("No active plan"),
                        fontSize = 13.sp,
                        color = UH.secondary,
                    )
                }
                athlete.adherencePct?.let { fraction ->
                    val color =
                        if (fraction >= .8) Color(0xFF19833F)
                        else if (fraction >= .6) UH.warningInk else UH.danger
                    Text(
                        coachPercent(fraction),
                        Modifier.background(color.copy(alpha = .15f), RoundedCornerShape(50))
                            .padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = color,
                    )
                }
                PrimaryButton(
                    onClick = { onAthlete(athlete.athleteId) },
                    contentPadding = PaddingValues(horizontal = 10.dp),
                    shape = CircleShape,
                ) {
                    Text(L("View"), fontSize = 12.sp)
                    Icon(Icons.Default.ChevronRight, null, Modifier.size(14.dp))
                }
            }
        }
    }
}

@Composable
internal fun CoachRaceBreakdown(races: List<RaceBreakdownEntry>, onRace: (String) -> Unit) {
    CoachChartCard("Athletes by Target Race", Icons.Default.Flag) {
        if (races.isEmpty())
            Text(L("No target races configured yet"), color = UH.muted, fontSize = 13.sp)
        races.forEachIndexed { index, race ->
            Row(
                Modifier.fillMaxWidth()
                    .background(UH.hover.copy(alpha = .5f), RoundedCornerShape(8.dp))
                    .clickable { onRace(race.raceName) }
                    .testTag("coach.race.$index")
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Column(Modifier.weight(1f)) {
                    Text(race.raceName, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
                    race.raceDate?.let { Text(it, fontSize = 13.sp, color = UH.muted) }
                }
                Row(
                    Modifier.background(UH.accent.copy(alpha = .12f), CircleShape)
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Icon(Icons.Default.People, null, Modifier.size(14.dp), tint = UH.accentInk)
                    Text(
                        "${race.count}",
                        color = UH.accentInk,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

@Composable
internal fun CoachRosterSection(
    roster: List<CoachedAthleteRow>,
    overview: CoachOverview?,
    search: String,
    onSearch: (String) -> Unit,
    email: String,
    onEmail: (String) -> Unit,
    busy: Boolean,
    error: String?,
    successEmail: String?,
    onInvite: () -> Unit,
    onAthlete: (Int) -> Unit,
    onProfile: (CoachedAthleteRow) -> Unit,
    onRemove: (CoachedAthleteRow) -> Unit,
) {
    CoachChartCard("Add an Athlete", Icons.Default.PersonAdd) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            OutlinedTextField(
                email,
                onEmail,
                placeholder = {
                    Text(
                        L("Athlete's Uphill email..."),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                },
                modifier = Modifier.weight(1f).testTag("coach.invite.email"),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                shape = RoundedCornerShape(8.dp),
            )
            PrimaryButton(
                onClick = onInvite,
                enabled = !busy && email.trim().contains('@'),
                modifier = Modifier.testTag("coach.invite.send"),
            ) {
                Text(L("Invite"))
            }
        }
        error?.let { Text(it, fontSize = 13.sp, color = UH.danger) }
        successEmail?.let {
            Text(L("Invitation sent to %@!", it), fontSize = 13.sp, color = UH.accentInk)
        }
        Text(
            L("The athlete must already have an Uphill AI account."),
            fontSize = 13.sp,
            color = UH.muted,
        )
    }
    OutlinedTextField(
        search,
        onSearch,
        placeholder = {
            Text(
                L("Search athletes by name or email..."),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        },
        leadingIcon = { Icon(Icons.Default.Search, null, Modifier.size(18.dp)) },
        trailingIcon = {
            if (search.isNotEmpty())
                IconButton(onClick = { onSearch("") }) {
                    Icon(Icons.Default.Cancel, L("Clear search"), Modifier.size(18.dp))
                }
        },
        modifier = Modifier.fillMaxWidth().testTag("coach.roster.search"),
        singleLine = true,
        shape = RoundedCornerShape(8.dp),
    )
    val filtered =
        roster.filter { athlete ->
            val race =
                overview
                    ?.athletes
                    ?.firstOrNull { it.athleteId == athlete.athleteId }
                    ?.activePlan
                    ?.raceName
                    .orEmpty()
            search.isBlank() ||
                listOf(athlete.displayName, athlete.athleteEmail, race).any {
                    it.contains(search.trim(), true)
                }
        }
    CoachChartCard("Your Athletes", Icons.Default.People, L("%lld total", filtered.size)) {
        if (filtered.isEmpty() && !busy)
            Text(
                if (roster.isEmpty()) L("No athletes yet — send an invite above to begin coaching.")
                else L("No athletes match \"%@\".", search),
                fontSize = 13.sp,
                color = UH.muted,
            )
        filtered.forEach { athlete ->
            val active = athlete.status == "active"
            val color = if (active) Color(0xFF19833F) else UH.warningInk
            Column(
                Modifier.fillMaxWidth()
                    .background(UH.hover.copy(alpha = .5f), RoundedCornerShape(8.dp))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Box(
                        Modifier.size(36.dp).background(color.copy(alpha = .15f), CircleShape),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(
                            athlete.displayName.take(2).uppercase(),
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = color,
                        )
                    }
                    Column(Modifier.weight(1f)) {
                        Text(
                            athlete.displayName,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(
                                L(if (active) "Active" else "Invite pending"),
                                fontSize = 11.sp,
                                color = color,
                            )
                            Text("·", fontSize = 11.sp, color = UH.muted)
                            Text(athlete.athleteEmail, fontSize = 11.sp, color = UH.muted)
                        }
                    }
                    IconButton(onClick = { onRemove(athlete) }, enabled = !busy) {
                        Icon(
                            Icons.Default.Close,
                            L("Remove %@", athlete.displayName),
                            Modifier.size(16.dp),
                            tint = UH.muted,
                        )
                    }
                }
                if (active)
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        TextButton(
                            onClick = { onProfile(athlete) },
                            modifier = Modifier.testTag("coach.profile.${athlete.athleteId}"),
                        ) {
                            Icon(Icons.Default.Badge, null, Modifier.size(16.dp), tint = UH.ink)
                            Spacer(Modifier.width(4.dp))
                            Text(L("Profile"), fontSize = 12.sp, color = UH.ink)
                        }
                        Spacer(Modifier.weight(1f))
                        PrimaryButton(
                            onClick = { onAthlete(athlete.athleteId) },
                            shape = CircleShape,
                        ) {
                            Text(L("View Plan"), fontSize = 12.sp)
                            Spacer(Modifier.width(4.dp))
                            Icon(Icons.AutoMirrored.Filled.ArrowForward, null, Modifier.size(14.dp))
                        }
                    }
            }
        }
    }
}

@Composable
private fun HubLink(onClick: () -> Unit, content: @Composable RowScope.() -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable(onClick = onClick).heightIn(min = 48.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        content()
        Icon(Icons.Default.ChevronRight, null, Modifier.size(14.dp), tint = UH.secondary)
    }
}

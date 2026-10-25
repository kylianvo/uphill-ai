package ai.uphill.app.feature.onboarding

import ai.uphill.app.core.localization.L
import ai.uphill.app.core.plan.*
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
internal fun SetupCoachBanner(step: SetupStep, goal: SetupGoal?) {
    val text =
        when (step) {
            SetupStep.Goal -> "This sets the shape of your whole plan."
            SetupStep.Details ->
                when (goal) {
                    SetupGoal.Race -> "If I know the race, I know its distance and climbing."
                    SetupGoal.Distance -> "Distance and climbing set how long your key runs get."
                    else -> "So I don't start you too hard."
                }
            SetupStep.FitnessFeel,
            SetupStep.DaysSinceRace,
            SetupStep.RecoveryFeel -> "So I don't start you too hard."
            SetupStep.RaceDate -> "I'll count the weeks back from race day."
            SetupStep.RaceGoal -> "A clear goal sets how hard your key sessions are."
            SetupStep.Schedule -> "Your first week starts close to what you already do."
            SetupStep.Venues -> "Hill sessions and strength work go where you can actually do them."
            SetupStep.TrainingZones -> "Your thresholds and easy pace help set workout intensity."
            SetupStep.Body -> "Injury history sets how fast I add volume."
            SetupStep.RaceHistory -> "Past results tell me what you can already do."
            SetupStep.Watch -> "Your runs show me what you really do, not just what you remember."
            SetupStep.StartDate -> "Pick today or any day in the next two weeks."
            SetupStep.Review -> "You can change any of this later from your plan."
        }
    Surface(
        color = Color.White,
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, UH.line),
    ) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Icon(Icons.Default.DirectionsRun, null, Modifier.size(20.dp), tint = UH.accentInk)
            Text(L(text), fontSize = 13.sp, color = UH.secondary)
        }
    }
}

private data class GoalChoice(
    val title: String,
    val goal: SetupGoal,
    val icon: ImageVector,
    val terrain: String = "trail",
    val subtitle: String? = null,
)

@Composable
internal fun SetupGoalOptions(draft: PlanSetupDraft, onSelect: (SetupGoal, String) -> Unit) {
    val haptic = LocalHapticFeedback.current
    val choices =
        listOf(
            GoalChoice("A trail race", SetupGoal.Race, Icons.Default.Terrain),
            GoalChoice("A road race", SetupGoal.Race, Icons.Default.Flag, "road"),
            GoalChoice(
                "A distance",
                SetupGoal.Distance,
                Icons.Default.Route,
                subtitle = "No race yet, like your first 21 km or 50 km.",
            ),
            GoalChoice("Getting started", SetupGoal.StartRunning, Icons.Default.DirectionsWalk),
        )
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        choices.forEach { choice ->
            val selected =
                draft.goal == choice.goal &&
                    (choice.goal != SetupGoal.Race || draft.terrain == choice.terrain)
            Surface(
                modifier =
                    Modifier.fillMaxWidth()
                        .selectable(
                            selected,
                            role = Role.Button,
                            onClick = {
                                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                                onSelect(choice.goal, choice.terrain)
                            },
                        )
                        .testTag("setup.goal.${choice.goal.wire}.${choice.terrain}"),
                color = if (selected) UH.activeFill else Color.White,
                shape = RoundedCornerShape(16.dp),
                border =
                    BorderStroke(
                        if (selected) 1.5.dp else 1.dp,
                        if (selected) UH.accent else UH.line,
                    ),
            ) {
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 64.dp).padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    Box(
                        Modifier.size(44.dp)
                            .background(
                                if (selected) UH.accentInk else UH.accent.copy(alpha = .12f),
                                RoundedCornerShape(8.dp),
                            ),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            choice.icon,
                            null,
                            Modifier.size(24.dp),
                            tint = if (selected) Color.White else UH.accentInk,
                        )
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                        Text(
                            L(choice.title),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = UH.ink,
                        )
                        choice.subtitle?.let { Text(L(it), fontSize = 13.sp, color = UH.secondary) }
                    }
                    if (selected) Icon(Icons.Default.CheckCircle, null, tint = UH.accentInk)
                }
            }
        }
    }
}

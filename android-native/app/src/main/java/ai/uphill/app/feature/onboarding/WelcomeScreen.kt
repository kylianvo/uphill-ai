package ai.uphill.app.feature.onboarding

import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Terrain
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun WelcomeScreen(onStart: () -> Unit, onNotNow: () -> Unit) {
    Column(Modifier.fillMaxSize().background(UH.surface).verticalScroll(rememberScrollState())) {
        Box(
            Modifier.fillMaxWidth().height(280.dp).background(UH.accent).clipToBounds(),
            contentAlignment = Alignment.BottomStart,
        ) {
            Icon(
                Icons.Filled.Terrain,
                contentDescription = null,
                tint = UH.buttonInk,
                modifier = Modifier.size(220.dp).offset(x = 24.dp, y = 28.dp),
            )
        }
        Column(
            Modifier.padding(24.dp).padding(top = 12.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp),
        ) {
            Text(
                L("Let's build your training plan"),
                fontSize = 34.sp,
                lineHeight = 41.sp,
                fontWeight = FontWeight.ExtraBold,
                letterSpacing = (-.8).sp,
            )
            Text(
                L(
                    "Answer a few questions and Coach Uphill builds a plan around your goal, your week and how you feel today."
                ),
                color = UH.secondary,
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Outlined.Schedule, contentDescription = null)
                Text(L("About 1 minute"), style = MaterialTheme.typography.labelLarge)
            }
            PrimaryButton(onClick = onStart, modifier = Modifier.fillMaxWidth()) {
                Text(L("Get started"))
            }
            TextButton(onClick = onNotNow, modifier = Modifier.fillMaxWidth()) {
                Text(L("Not now"))
            }
        }
    }
}

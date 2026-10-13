package ai.uphill.app.feature.integrations

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.integrations.*
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.*
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay

@Composable
fun IntegrationsScreen(api: APIClient, user: User, lang: String, onNavigate: (String) -> Unit) {
    val context = LocalContext.current
    val service = remember(api) { DeviceConnectionService(api) }
    val oauth = remember(context, service) { CorosOAuthCoordinator(context, service) }
    val vm: IntegrationsViewModel =
        viewModel(key = "integrations-${user.id}") { IntegrationsViewModel(service) }
    val state by vm.state.collectAsState()
    var disconnect by remember { mutableStateOf(false) }
    var confirmPush by remember { mutableStateOf(false) }
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    LaunchedEffect(vm, lifecycle) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
            while (true) {
                vm.refresh()
                delay(10000)
            }
        }
    }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(P6("connected_accounts"), style = MaterialTheme.typography.headlineMedium)
        Text(P6("watch_intro"), color = UH.secondary)
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.error?.let { Text(P6Error(it), color = UH.danger) }
        P6Card {
            Text("COROS", style = MaterialTheme.typography.titleLarge)
            Text(
                P6(if (state.status?.isCorosConnected == true) "connected" else "not_connected"),
                color = UH.accentInk,
            )
            if (state.status?.isCorosConnected == true) {
                state.status?.coros?.deviceModel?.let { Text(it) }
                state.status?.coros?.lastSyncAt?.let { Text(P6("last_sync", it)) }
                Text(
                    P6("coros_attribution"),
                    style = MaterialTheme.typography.bodySmall,
                    color = UH.secondary,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = vm::sync, enabled = !state.busy) { Text(P6("sync_now")) }
                    OutlinedButton(onClick = vm::fitness, enabled = !state.busy) {
                        Text(P6("sync_evolab"))
                    }
                }
                state.sync?.let {
                    Text(P6("sync_result", it.activities, it.dailyMetrics), color = UH.accentInk)
                }
                state.fitness?.let {
                    Text(
                        P6(
                            "fitness_result",
                            it.thresholdPace ?: "—",
                            it.corosVo2Max?.toString() ?: "—",
                        ),
                        color = UH.accentInk,
                    )
                }
                TextButton(onClick = { disconnect = true }, enabled = !state.busy) {
                    Text(P6("disconnect"), color = UH.danger)
                }
            } else
                Button(onClick = { vm.action { oauth.begin() } }, enabled = !state.busy) {
                    Text(P6("connect_coros"))
                }
        }
        if (state.status?.isCorosConnected == true)
            P6Card {
                Text(P6("watch_plan"), style = MaterialTheme.typography.titleMedium)
                Text(P6("push_intro"), color = UH.secondary)
                state.push?.lastPushedAt?.let { Text(P6("last_push", it)) }
                if (state.push?.outOfDate == true) Text(P6("push_stale"), color = UH.warningInk)
                if (state.push?.partial == true) Text(P6("push_partial"), color = UH.warningInk)
                val summary = state.outcome?.summary ?: state.push?.lastSummary
                summary?.let {
                    Text(
                        P6(
                            "push_summary",
                            it.workoutsSent,
                            it.daysSent,
                            it.leftInUphill,
                            it.lockedDays,
                            it.invalid,
                        )
                    )
                    if (it.windowEnd.isNotBlank()) Text(P6("window_end", it.windowEnd))
                }
                state.outcome?.let {
                    Text(
                        if (it.isSuccess) P6("push_success")
                        else it.errorCode?.let { code -> P6Error(code) } ?: P6("push_failed"),
                        color = if (it.isSuccess) UH.accentInk else UH.danger,
                    )
                }
                Button(onClick = { confirmPush = true }, enabled = !state.busy) {
                    Text(P6("send_to_coros"))
                }
            }
        Text(P6("disconnect_policy"), style = MaterialTheme.typography.bodySmall, color = UH.muted)
    }
    if (disconnect)
        AlertDialog(
            onDismissRequest = { disconnect = false },
            title = { Text(P6("disconnect_coros")) },
            text = { Text(P6("disconnect_help")) },
            confirmButton = {
                TextButton(
                    onClick = {
                        disconnect = false
                        vm.disconnect()
                    }
                ) {
                    Text(P6("disconnect"))
                }
            },
            dismissButton = { TextButton(onClick = { disconnect = false }) { Text(P6("cancel")) } },
        )
    if (confirmPush)
        AlertDialog(
            onDismissRequest = { confirmPush = false },
            title = { Text(P6("send_to_coros")) },
            text = { Text(P6("push_confirm")) },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirmPush = false
                        vm.push(lang)
                    }
                ) {
                    Text(P6("send"))
                }
            },
            dismissButton = { TextButton(onClick = { confirmPush = false }) { Text(P6("cancel")) } },
        )
}

package ai.uphill.app.feature.me

import ai.uphill.app.core.integrations.CorosOAuthCoordinator
import ai.uphill.app.core.integrations.DeviceConnectionService
import ai.uphill.app.core.integrations.DeviceConnectionStatus
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.localization.localizedError
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.SecondaryButton
import ai.uphill.app.designsystem.UH
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Watch
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

private data class ConnectionNotice(val key: String, val arguments: List<Any> = emptyList())

@Composable
internal fun ProfileConnectedAccounts(api: APIClient, userId: Int, onOpenAccounts: () -> Unit) {
    val context = LocalContext.current
    val service = remember(api, userId) { DeviceConnectionService(api) }
    val oauth = remember(context, service) { CorosOAuthCoordinator(context, service) }
    val scope = rememberCoroutineScope()
    val mutex = remember(service) { Mutex() }
    var status by remember(service) { mutableStateOf<DeviceConnectionStatus?>(null) }
    var checking by remember(service) { mutableStateOf(true) }
    var operation by remember(service) { mutableStateOf<String?>(null) }
    var notice by remember(service) { mutableStateOf<ConnectionNotice?>(null) }
    var error by remember(service) { mutableStateOf<Throwable?>(null) }
    var confirmDisconnect by remember(service) { mutableStateOf(false) }
    val lifecycle = LocalLifecycleOwner.current.lifecycle

    suspend fun refresh() {
        mutex.withLock {
            checking = true
            try {
                status = service.fetchStatus()
                error = null
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                error = e
            } finally {
                checking = false
            }
        }
    }

    fun perform(name: String, action: suspend () -> ConnectionNotice?) {
        if (operation != null) return
        operation = name
        notice = null
        error = null
        scope.launch {
            try {
                mutex.withLock {
                    notice = action()
                    status = service.fetchStatus()
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                error = e
            } finally {
                operation = null
            }
        }
    }

    LaunchedEffect(service, lifecycle) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
            while (true) {
                // MainActivity completes the existing OAuth callback; refresh observes its result.
                if (operation == null) refresh()
                delay(10000)
            }
        }
    }

    val connected = status?.isCorosConnected == true
    val busy = operation != null || checking
    ProfilePanel {
        Row(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                Icons.Default.Watch,
                contentDescription = null,
                tint = UH.accentInk,
                modifier = Modifier.size(16.dp),
            )
            Text(
                L("CONNECTED ACCOUNTS"),
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = UH.muted,
            )
        }
        Text(
            L("Connect your watch so completed runs are matched to your plan automatically."),
            style = MaterialTheme.typography.bodySmall,
            color = UH.secondary,
        )
        Surface(
            color = UH.surface,
            shape = RoundedCornerShape(8.dp),
            border = BorderStroke(1.dp, UH.line),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "COROS",
                        Modifier.weight(1f),
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Black,
                    )
                    Text(
                        L(
                            when {
                                status == null && checking -> "Checking connection…"
                                connected && status?.coros?.lastSyncAt != null -> "Synced"
                                connected -> "Connected"
                                else -> "Not connected"
                            }
                        ),
                        fontSize = 11.sp,
                        color = if (connected) UH.accentInk else UH.muted,
                    )
                }
                if (connected) {
                    status?.coros?.lastSyncAt?.let { value ->
                        val resourcesLocale = LocalConfiguration.current.locales[0]
                        val formatted =
                            remember(value, resourcesLocale) {
                                runCatching {
                                        OffsetDateTime.parse(value)
                                            .atZoneSameInstant(ZoneId.systemDefault())
                                            .format(
                                                DateTimeFormatter.ofLocalizedDateTime(
                                                        FormatStyle.MEDIUM,
                                                        FormatStyle.SHORT,
                                                    )
                                                    .withLocale(resourcesLocale)
                                            )
                                    }
                                    .getOrElse { value }
                            }
                        Text(
                            L("Last synced %@", formatted),
                            style = MaterialTheme.typography.bodySmall,
                            color = UH.secondary,
                        )
                    }
                    val device = status?.coros?.deviceModel
                    Text(
                        if (device.isNullOrBlank()) L("Data provided by COROS")
                        else L("Data provided by COROS · %@", device),
                        fontSize = 11.sp,
                        color = UH.secondary,
                    )
                    HorizontalDivider(color = UH.line)
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        SecondaryButton(
                            onClick = {
                                perform("fitness") {
                                    val result = service.syncFitness()
                                    ConnectionNotice(
                                        "EvoLab synced successfully: threshold pace %@/km, VO2max %@.",
                                        listOf(
                                            result.thresholdPace ?: "—",
                                            result.corosVo2Max?.toInt()?.toString() ?: "—",
                                        ),
                                    )
                                }
                            },
                            enabled = !busy,
                            modifier = Modifier.weight(1f),
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp),
                        ) {
                            Text(L("Sync EvoLab"), fontSize = 11.sp)
                        }
                        SecondaryButton(
                            onClick = {
                                perform("sync") {
                                    val result = service.syncNow()
                                    ConnectionNotice(
                                        "Sync successful: fetched %lld workouts and %lld days of health data.",
                                        listOf(result.activities, result.dailyMetrics),
                                    )
                                }
                            },
                            enabled = !busy,
                            modifier = Modifier.weight(1f),
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp),
                        ) {
                            Text(
                                L(if (operation == "sync") "Syncing…" else "Sync now"),
                                fontSize = 11.sp,
                            )
                        }
                        TextButton(
                            onClick = { confirmDisconnect = true },
                            enabled = !busy,
                            contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp),
                        ) {
                            Text(L("Disconnect"), color = UH.danger, fontSize = 11.sp)
                        }
                    }
                } else
                    PrimaryButton(
                        onClick = {
                            perform("connect") {
                                oauth.begin()
                                null
                            }
                        },
                        enabled = !busy && status != null,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(L("Connect COROS Account"), fontSize = 12.sp)
                    }
                if (operation != null) LinearProgressIndicator(Modifier.fillMaxWidth())
            }
        }
        notice?.let { message ->
            Row(
                Modifier.fillMaxWidth().semantics { liveRegion = LiveRegionMode.Polite },
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    Icons.Default.CheckCircle,
                    null,
                    tint = UH.accentInk,
                    modifier = Modifier.size(16.dp),
                )
                Text(
                    L(message.key, *message.arguments.toTypedArray()),
                    style = MaterialTheme.typography.bodySmall,
                    color = UH.accentInk,
                )
            }
        }
        error?.let {
            Text(
                localizedError(context, it),
                color = UH.danger,
                style = MaterialTheme.typography.bodySmall,
            )
            TextButton(onClick = { scope.launch { refresh() } }, enabled = !busy) {
                Text(L("Retry"))
            }
        }
        Text(
            L(
                "When disconnecting, data received from COROS is permanently deleted within 24 hours."
            ),
            fontSize = 10.sp,
            color = UH.muted,
        )
        ProfileLink("Connected accounts", onOpenAccounts)
    }
    if (confirmDisconnect)
        AlertDialog(
            onDismissRequest = { confirmDisconnect = false },
            title = { Text(L("Disconnect COROS?")) },
            text = {
                Text(
                    L(
                        "Your past workouts and health metrics from COROS will no longer automatically sync."
                    )
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        confirmDisconnect = false
                        perform("disconnect") {
                            service.disconnectCoros()
                            status = DeviceConnectionStatus()
                            ConnectionNotice("Disconnected from COROS.")
                        }
                    }
                ) {
                    Text(L("Disconnect COROS"), color = UH.danger)
                }
            },
            dismissButton = {
                TextButton(onClick = { confirmDisconnect = false }) { Text(L("Cancel")) }
            },
        )
}

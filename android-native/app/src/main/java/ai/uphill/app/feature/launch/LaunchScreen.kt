package ai.uphill.app.feature.launch

import ai.uphill.app.R
import ai.uphill.app.core.localization.L
import ai.uphill.app.designsystem.PrimaryButton
import ai.uphill.app.designsystem.LocalReduceMotion
import ai.uphill.app.designsystem.UH
import android.net.Uri
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable
fun LaunchScreen(error: String? = null, onRetry: () -> Unit = {}) {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val reduceMotion = LocalReduceMotion.current
    val player = remember {
        ExoPlayer.Builder(context).build().apply {
            setMediaItem(
                MediaItem.fromUri(
                    Uri.parse("android.resource://${context.packageName}/${R.raw.launch_bg}")
                )
            )
            repeatMode = Player.REPEAT_MODE_ONE
            volume = 0f
            prepare()
            playWhenReady = !reduceMotion
        }
    }
    DisposableEffect(player, lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME && !reduceMotion) player.play()
            else if (event == Lifecycle.Event.ON_PAUSE) player.pause()
        }
        lifecycle.addObserver(observer)
        onDispose {
            lifecycle.removeObserver(observer)
            player.release()
        }
    }
    var shown by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { shown = true }
    LaunchedEffect(reduceMotion) { player.playWhenReady = !reduceMotion }
    val opacity by
        animateFloatAsState(
            if (shown) 1f else 0f,
            tween(if (reduceMotion) 0 else 800),
            label = "launch fade",
        )
    Box(Modifier.fillMaxSize().background(UH.surface)) {
        AndroidView(
            factory = {
                PlayerView(it).apply {
                    this.player = player
                    useController = false
                    resizeMode = AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                }
            },
            modifier = Modifier.fillMaxSize().alpha(opacity),
        )
        Box(
            Modifier.fillMaxWidth()
                .fillMaxHeight(.5f)
                .background(
                    Brush.verticalGradient(
                        listOf(UH.surface.copy(alpha = .85f), UH.surface.copy(alpha = 0f))
                    )
                )
        )
        Column(Modifier.fillMaxWidth().padding(horizontal = 32.dp).padding(top = 96.dp)) {
            Canvas(Modifier.size(64.dp)) {
                val k = size.width / 256f
                drawRoundRect(Color(0xff0d0c0d), cornerRadius = CornerRadius(56 * k))
                val path =
                    Path().apply {
                        moveTo(206 * k, 68 * k)
                        lineTo(126 * k, 168 * k)
                        lineTo(96 * k, 128 * k)
                        lineTo(58 * k, 176 * k)
                        moveTo(158 * k, 68 * k)
                        lineTo(206 * k, 68 * k)
                        lineTo(206 * k, 116 * k)
                    }
                drawPath(
                    path,
                    UH.accent,
                    style = Stroke(width = 20 * k, cap = StrokeCap.Round, join = StrokeJoin.Round),
                )
            }
            Spacer(Modifier.height(24.dp))
            Text(
                L("Uphill AI"),
                fontFamily = FontFamily(Font(R.font.plus_jakarta_sans)),
                fontSize = 46.sp,
                fontWeight = FontWeight.Black,
                letterSpacing = (-1.6).sp,
                color = UH.ink,
            )
            Spacer(Modifier.height(12.dp))
            Text(
                L("Your adaptive training plan for the mountains."),
                style = MaterialTheme.typography.titleLarge,
                color = UH.secondary,
            )
            Spacer(Modifier.height(24.dp))
            if (error != null) {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text(
                        error,
                        modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
                        style = MaterialTheme.typography.bodyLarge,
                        color = UH.danger,
                    )
                    PrimaryButton(onClick = onRetry, modifier = Modifier.widthIn(max = 220.dp).fillMaxWidth()) {
                        Text(L("Try again"), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                    }
                }
            } else {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp)
                    Text(
                        L("Loading your training"),
                        style = MaterialTheme.typography.bodySmall,
                        color = UH.secondary,
                    )
                }
            }
        }
    }
}

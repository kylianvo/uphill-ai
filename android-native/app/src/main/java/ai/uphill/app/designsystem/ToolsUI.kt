package ai.uphill.app.designsystem

import ai.uphill.app.core.goal.*
import ai.uphill.app.core.localization.L
import ai.uphill.app.core.networking.APIClient
import ai.uphill.app.designsystem.PrimaryButton as Button
import ai.uphill.app.designsystem.SecondaryButton as OutlinedButton
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import coil3.compose.AsyncImage
import kotlinx.coroutines.delay

@Composable
fun TT(key: String): String {
    val context = LocalContext.current
    val name = "tools_" + key.lowercase().replace(Regex("[^a-z0-9]+"), "_").trim('_')
    val id = context.resources.getIdentifier(name, "string", context.packageName)
    return if (id == 0) L(key) else context.getString(id)
}

@Composable
inline fun <reified T : ViewModel> toolViewModel(key: String, crossinline build: () -> T): T =
    viewModel(
        key = key,
        factory =
            object : ViewModelProvider.Factory {
                override fun <M : ViewModel> create(modelClass: Class<M>): M {
                    @Suppress("UNCHECKED_CAST")
                    return build() as M
                }
            },
    )

@Composable
fun ToolPage(
    title: String,
    onNavigate: (String) -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        Modifier.fillMaxSize()
            .background(UH.surface)
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = { onNavigate("back") }) { Text(TT("Back")) }
            Text(TT(title), style = MaterialTheme.typography.headlineSmall)
        }
        content()
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
fun ToolPanel(title: String? = null, content: @Composable ColumnScope.() -> Unit) {
    OutlinedCard(
        Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            title?.let {
                Text(TT(it), style = MaterialTheme.typography.titleMedium, color = UH.ink)
            }
            content()
        }
    }
}

@Composable
fun ToolField(
    label: String,
    value: String,
    onChange: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    OutlinedTextField(
        value,
        onChange,
        modifier.fillMaxWidth(),
        label = { Text(TT(label)) },
        singleLine = true,
    )
}

@Composable
fun ToolOptions(
    label: String,
    options: List<String>,
    selected: Set<String>,
    onPick: (String) -> Unit,
) {
    Text(TT(label), style = MaterialTheme.typography.labelLarge, color = UH.secondary)
    Row(
        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        options.forEach {
            FilterChip(
                selected = it in selected,
                onClick = { onPick(it) },
                label = { Text(TT(it)) },
            )
        }
    }
}

@Composable
fun ToolError(error: String?) {
    error?.let { Text(it, color = UH.danger, style = MaterialTheme.typography.bodyMedium) }
}

@Composable
fun ToolSubmit(label: String, busy: Boolean, enabled: Boolean = true, onClick: () -> Unit) {
    Button(onClick, Modifier.fillMaxWidth(), enabled = enabled && !busy) {
        if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
        else Text(TT(label))
    }
}

@Composable
fun ToolFeedback(token: String?, sent: Int?, busy: Boolean = false, onSend: (Int) -> Unit) {
    if (token != null) {
        Text(TT("Was this useful?"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { onSend(1) }, enabled = sent == null && !busy) {
                Text(if (sent == 1) TT("Thanks") else TT("Helpful"))
            }
            OutlinedButton(onClick = { onSend(-1) }, enabled = sent == null && !busy) {
                Text(if (sent == -1) TT("Thanks") else TT("Needs work"))
            }
        }
    }
}

@Composable
fun Packshot(prefix: String, brand: String, name: String, fallback: String) {
    val context = LocalContext.current
    val assets = remember(prefix) { ProductAssets.names.filter { it.startsWith(prefix + "_") } }
    val combined = (brand + " " + name).lowercase().replace("/", " ").replace("-", " ")
    val tokens =
        combined.split(Regex("[^a-z0-9]+")).filter { it.length > 2 && !it.all(Char::isDigit) }
    val match =
        assets
            .filter { a ->
                brand.lowercase().split(" ").firstOrNull()?.let { a.contains(it) } == true
            }
            .maxByOrNull { a -> tokens.count { a.contains(it) } }
    val resource =
        match?.takeIf { a -> tokens.count { a.contains(it) } >= 2 } ?: "${prefix}_$fallback"
    val id = context.resources.getIdentifier("tools_$resource", "drawable", context.packageName)
    if (id != 0)
        AsyncImage(
            model = id,
            contentDescription = "$brand $name",
            modifier = Modifier.fillMaxWidth().height(140.dp),
        )
}

@Composable
fun RaceSearch(
    api: APIClient,
    name: String,
    onName: (String) -> Unit,
    onPick: (RaceDistance) -> Unit,
) {
    var candidates by remember { mutableStateOf<List<RaceMatch>>(emptyList()) }
    var selected by remember { mutableStateOf<RaceMatch?>(null) }
    fun select(race: RaceMatch) {
        selected = race
        candidates = emptyList()
        onName(race.raceName)
        race.distanceKm?.let { onPick(RaceDistance(race.distanceLabel, it, race.elevationGainM)) }
        if (race.distanceKm == null && race.distances?.size == 1) onPick(race.distances.single())
    }
    LaunchedEffect(name) {
        if (selected?.raceName == name) return@LaunchedEffect
        selected = null
        if (name.trim().length < 3) {
            candidates = emptyList()
            return@LaunchedEffect
        }
        delay(450)
        try {
            val res = GoalService(api).match(name.trim())
            if (res.autoApply == true && res.match != null) select(res.match)
            else candidates = res.candidates ?: listOfNotNull(res.match)
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e
        } catch (_: Exception) {
            candidates = emptyList()
        }
    }
    ToolField("Race name", name, { onName(it) })
    candidates.take(5).forEach { race ->
        TextButton(onClick = { select(race) }) { Text(race.raceName) }
    }
    selected
        ?.distances
        ?.takeIf { it.size > 1 }
        ?.let { distances ->
            Text(TT("Which distance?"))
            Row(
                Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                distances
                    .sortedBy { it.distanceKm }
                    .forEach { d ->
                        OutlinedButton(onClick = { onPick(d) }) {
                            Text(d.label ?: "${d.distanceKm} km")
                        }
                    }
            }
        }
}

@Composable
fun ToolLineChart(
    points: List<Pair<Double, Double>>,
    description: String,
    markers: List<Double> = emptyList(),
    onSelect: ((Double) -> Unit)? = null,
) {
    val label = TT(description)
    if (points.size < 2) return
    val minX = minOf(points.minOf { it.first }, markers.minOrNull() ?: Double.MAX_VALUE)
    val maxX = maxOf(points.maxOf { it.first }, markers.maxOrNull() ?: Double.MIN_VALUE)
    val minY = points.minOf { it.second }
    val maxY = points.maxOf { it.second }
    val spanX = (maxX - minX).coerceAtLeast(1.0)
    val spanY = (maxY - minY).coerceAtLeast(1.0)
    Canvas(
        Modifier.fillMaxWidth()
            .height(220.dp)
            .semantics { contentDescription = label }
            .pointerInput(points) {
                detectTapGestures { p ->
                    onSelect?.invoke(minX + (p.x / size.width).coerceIn(0f, 1f) * spanX)
                }
            }
            .pointerInput(points) {
                detectDragGestures { change, _ ->
                    onSelect?.invoke(
                        minX + (change.position.x / size.width).coerceIn(0f, 1f) * spanX
                    )
                }
            }
    ) {
        fun point(x: Double, y: Double) =
            Offset(
                ((x - minX) / spanX * size.width).toFloat(),
                (size.height - (y - minY) / spanY * size.height).toFloat(),
            )
        repeat(5) {
            val y = size.height * it / 4
            drawLine(UH.line, Offset(0f, y), Offset(size.width, y), 1f)
        }
        val path = Path()
        points.forEachIndexed { i, p ->
            val v = point(p.first, p.second)
            if (i == 0) path.moveTo(v.x, v.y) else path.lineTo(v.x, v.y)
        }
        drawPath(path, UH.accentInk, style = Stroke(3f))
        points.forEach { drawCircle(UH.accentInk, 4f, point(it.first, it.second)) }
        markers.forEach {
            val x = point(it, minY).x
            drawLine(UH.warningInk, Offset(x, 0f), Offset(x, size.height), 2f)
        }
    }
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("%.1f".format(minX), style = MaterialTheme.typography.labelSmall)
        Text(label, style = MaterialTheme.typography.labelSmall)
        Text("%.1f".format(maxX), style = MaterialTheme.typography.labelSmall)
    }
}

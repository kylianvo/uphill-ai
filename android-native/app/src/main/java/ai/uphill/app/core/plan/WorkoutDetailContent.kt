package ai.uphill.app.core.plan

import ai.uphill.app.core.models.Workout
import java.util.Locale

internal data class ExecutionStepItem(
    val phase: String,
    val duration: String?,
    val target: String,
    val recovery: String? = null,
    val steps: List<String>,
)

internal data class WorkoutDetailContent(
    val overview: String?,
    val intent: String?,
    val reason: String?,
    val benefit: String?,
    val warning: String?,
    val coachNotes: String?,
    val steps: List<ExecutionStepItem>,
) {
    companion object {
        private val labels =
            linkedMapOf(
                "coach uphill note" to "coach",
                "coach note" to "coach",
                "coach" to "coach",
                "what it builds" to "benefit",
                "benefit" to "benefit",
                "builds" to "benefit",
                "reason" to "reason",
                "why" to "reason",
                "common mistake" to "warning",
                "warning" to "warning",
                "mistake" to "warning",
                "how to execute" to "process",
                "process" to "process",
                "execution" to "process",
                "steps" to "process",
                "overall" to "intent",
                "overview" to "intent",
            )
        private val keywords = labels.keys.joinToString("|")

        private fun segments(text: String) =
            text
                .replace(Regex("(?i)(?<=[.!?;]|\\s)\\s*(?=(?:$keywords)\\s*[:\\-])"), "\n")
                .replace(Regex("\\s+/\\s+"), "\n")
                .lines()
                .map(String::trim)
                .filter(String::isNotEmpty)

        private fun label(text: String): Pair<String, String>? {
            for ((keyword, section) in labels) {
                val found =
                    Regex("(?i)^${Regex.escape(keyword)}\\s*[:\\-]\\s*(.*)$").matchEntire(text)
                        ?: continue
                return section to found.groupValues[1].trim()
            }
            return null
        }

        private fun stepLike(text: String): Boolean {
            val lower = text.lowercase()
            return listOf("warm", "main set", "cool", "target pace").any(lower::startsWith) ||
                Regex("^\\d+(?:[–\\-]\\d+)?\\s*(?:min(?:ute)?s?|km|m|sec|s|x|×)\\b")
                    .containsMatchIn(lower)
        }

        private fun prescription(text: String) =
            Regex("(?i)\\b\\d+\\s*sets?\\b").containsMatchIn(text) &&
                (Regex("(?i)\\b(reps?|repetitions?)\\b").containsMatchIn(text) ||
                    Regex("(?i)\\b\\d+[\\s-]*seconds?\\b").containsMatchIn(text))

        private data class Process(val warm: String?, val main: List<String>, val cool: String?)

        private fun splitProcess(text: String): Process {
            var warm: String? = null
            var cool: String? = null
            val main = mutableListOf<String>()
            val arrow = text.contains('→')
            var inNote = false
            val pieces =
                if (arrow) text.split('→').map(String::trim).filter(String::isNotEmpty)
                else segments(text)
            for (segment in pieces) {
                var step = segment
                if (!arrow) {
                    val tagged = label(segment)
                    if (tagged != null) {
                        if (tagged.first == "process") {
                            step = tagged.second
                            inNote = false
                        } else {
                            inNote = true
                            continue
                        }
                    } else if (inNote) {
                        if (stepLike(segment)) inNote = false else continue
                    }
                }
                val lower = step.lowercase()
                if (
                    warm == null &&
                        (lower.startsWith("warm") ||
                            lower.contains("warm up") ||
                            lower.contains("warm-up") ||
                            lower.startsWith("khởi động") ||
                            (arrow && lower.contains("easy jog")))
                )
                    warm = step
                else if (
                    lower.startsWith("cool") ||
                        lower.contains("cool down") ||
                        lower.contains("cool-down") ||
                        (arrow && lower.contains("stretch")) ||
                        lower.startsWith("thả lỏng") ||
                        lower.startsWith("hạ nhiệt")
                )
                    cool = step
                else if (step.isNotBlank()) main.add(step)
            }
            return Process(warm, main, cool)
        }

        private fun minutes(text: String?) =
            text?.let { Regex("(?i)\\d+(?:[–\\-]\\d+)?\\s*(?:min|phút)").find(it)?.value }

        private fun firstNumber(text: String?) =
            text?.let { Regex("\\d+").find(it)?.value?.toIntOrNull() }

        private fun clean(text: String, prefix: String) =
            text
                .replace(
                    Regex(
                        "(?i)\\s*(?:\\b(?:overall|overview|reason|why|benefit|builds|what it builds|warning|common mistake|mistake|coach note|coach uphill note)\\s*[:\\-]).*$"
                    ),
                    "",
                )
                .trim()
                .replace(Regex("(?i)^${Regex.escape(prefix)}\\s*"), "")
                .trim()

        fun make(workout: Workout, treadmill: Boolean = false): WorkoutDetailContent {
            val raw = workout.description.orEmpty().trim()
            val values = mutableMapOf<String, MutableList<String>>()
            val free = mutableListOf<String>()
            var section: String? = null
            for (segment in segments(raw)) {
                val tagged = label(segment)
                if (tagged != null) {
                    section = tagged.first
                    if (tagged.second.isNotEmpty())
                        values.getOrPut(tagged.first) { mutableListOf() }.add(tagged.second)
                } else if (section != null && (section == "process" || !stepLike(segment)))
                    values.getOrPut(section) { mutableListOf() }.add(segment)
                else {
                    section = null
                    free.add(segment)
                }
            }
            val tagged = values.isNotEmpty()
            fun text(key: String) =
                values[key]?.joinToString("\n")?.trim()?.takeIf(String::isNotEmpty)
            var process = text("process") ?: if (tagged) free.joinToString("\n") else raw
            val rescued = mutableListOf<String>()
            for (key in listOf("intent", "reason", "benefit", "warning")) {
                val value = text(key) ?: continue
                val clauses = value.split(Regex("(?<=[.!?;])\\s+")).map(String::trim)
                val exercises = clauses.filter(::prescription)
                if (exercises.isNotEmpty()) {
                    rescued.addAll(exercises.map { it.trimEnd('.', ';') })
                    values[key] = clauses.filterNot(::prescription).toMutableList()
                }
            }
            if (rescued.isNotEmpty()) {
                val old = splitProcess(process)
                if (old.main.none(::prescription))
                    process =
                        (listOfNotNull(old.warm) + rescued + listOfNotNull(old.cool)).joinToString(
                            " → "
                        )
            }
            val parts = splitProcess(process)
            val warm =
                parts.warm
                    ?: if (
                        listOf("interval", "hill", "tempo").any {
                            workout.type.lowercase().contains(it)
                        }
                    )
                        "15 min easy Zone 1/2 jog + 4 dynamic drills"
                    else "10 min easy jog to build into effort"
            val cool = parts.cool ?: "5–10 min easy jog and light mobility"
            val detected =
                Regex("(?i)(\\d+\\s*[x×]\\s*\\d+\\s*min[^\\n,]*)(?:with\\s*([^\\n.]*))?")
                    .find(parts.main.firstOrNull().orEmpty())
            val interval = (workout.intervalReps ?: 0) > 0 || detected != null
            val target: String
            val recovery: String?
            if (treadmill) {
                val settings = treadmillSettings(workout)
                target = "${settings.first} km/h · ${settings.second}% grade"
                recovery = "Maintain stable uphill cadence"
            } else if (
                (workout.intervalReps ?: 0) > 0 &&
                    workout.intervalRepValue != null &&
                    workout.intervalRepUnit != null
            ) {
                target =
                    "${workout.intervalReps} × ${workout.intervalRepValue.toInt()} ${workout.intervalRepUnit}" +
                        (workout.targetPace?.let { " @ $it" } ?: "")
                recovery =
                    if ((workout.walkIntervalValue ?: 0.0) > 0)
                        "Recovery: ${workout.walkIntervalValue!!.toInt()} ${workout.intervalRepUnit} jog / walk"
                    else "Recovery: easy jog between intervals"
            } else if (detected != null) {
                target = detected.groupValues[1].trim()
                recovery =
                    detected.groupValues.getOrNull(2)?.takeIf(String::isNotBlank)?.let {
                        "Recovery: $it"
                    }
            } else {
                target =
                    if (!workout.isStrengthOrME && !workout.targetPace.isNullOrBlank())
                        "Target pace: ${workout.targetPace}"
                    else workout.title
                recovery = null
            }
            val explicit =
                parts.main
                    .firstOrNull()
                    ?.takeIf {
                        Regex("(?i)^\\s*(?:main set:?\\s*)?\\d+(?:[–\\-]\\d+)?\\s*(?:min|phút)\\b")
                            .containsMatchIn(it)
                    }
                    ?.let(::minutes)
            val duration =
                if (!interval && explicit != null) explicit
                else if (workout.durationMinutes > 0)
                    "${maxOf(5, workout.durationMinutes.toInt() - (firstNumber(minutes(warm)) ?: 10) - (firstNumber(minutes(parts.cool)) ?: 5))} min"
                else null
            val mainSteps =
                parts.main
                    .map { clean(it, "main set:") }
                    .filter(String::isNotEmpty)
                    .ifEmpty { listOf(target) }
            val steps = buildList {
                if (!workout.isRest)
                    add(
                        ExecutionStepItem(
                            "Warm-up",
                            minutes(warm) ?: "10–15 min",
                            if (treadmill) "Treadmill warm-up at easy jog (0% grade)"
                            else clean(warm, "warm-up:"),
                            steps = listOf(clean(warm, "warm-up:")),
                        )
                    )
                add(ExecutionStepItem("Main Set", duration, target, recovery, mainSteps))
                if (!workout.isRest)
                    add(
                        ExecutionStepItem(
                            "Cool-down",
                            minutes(cool) ?: "5–10 min",
                            if (treadmill) "0% grade easy walk to lower HR"
                            else clean(cool, "cool-down:"),
                            steps = listOf(clean(cool, "cool-down:")),
                        )
                    )
            }
            return WorkoutDetailContent(
                raw.takeIf { !tagged && it.isNotEmpty() },
                text("intent"),
                text("reason"),
                text("benefit"),
                text("warning"),
                text("coach"),
                steps,
            )
        }

        private fun treadmillSettings(workout: Workout): Pair<String, String> {
            if (
                !workout.treadmillSpeed.isNullOrBlank() &&
                    workout.treadmillSpeed != "0" &&
                    !workout.treadmillIncline.isNullOrBlank()
            )
                return workout.treadmillSpeed to workout.treadmillIncline
            val pace = Regex("(\\d+):(\\d{2})").find(workout.targetPace.orEmpty())
            if (pace == null) return "12.6" to "6.0"
            val mins = pace.groupValues[1].toDouble() + pace.groupValues[2].toDouble() / 60.0
            val grade = workout.gradePercent ?: 6.0
            val speed = 60.0 / mins / (1.0 + 0.045 * maxOf(0.0, grade))
            return String.format(Locale.US, "%.1f", speed) to
                String.format(Locale.US, "%.1f", maxOf(1.0, grade))
        }
    }
}

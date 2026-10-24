package ai.uphill.app.core.plan

import ai.uphill.app.core.models.*
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.serialization.json.*

class ScheduleDraft(private val initial: Plan?) {
    var daysPerWeek by mutableStateOf(initial?.daysPerWeek ?: 4)
    var preferredDays by mutableStateOf(PlanSetupDraft.days(initial?.preferredRunDays))
    var longRunDay by mutableStateOf(initial?.longRunDay?.let { Weekday.parse(it) })
    var doubleSessionDays by mutableStateOf(PlanSetupDraft.days(initial?.doubleSessionDays))
    var hasGymAccess by mutableStateOf(initial?.hasGymAccess ?: false)
    var useTreadmill by mutableStateOf(initial?.useTreadmill ?: false)
    var environment by mutableStateOf(initial?.trainingEnvironment ?: "flat")
    var mountainDays by mutableStateOf(PlanSetupDraft.days(initial?.mountainDays))
    var stairAccess by mutableStateOf(initial?.stairAccess ?: false)
    var treadmillMaxIncline by mutableStateOf(initial?.treadmillMaxIncline ?: 15)
    var maxContinuousJogMin by mutableStateOf(initial?.maxContinuousJogMin ?: 0)
    val gettingStarted
        get() = initial?.goalType == "start_running"

    val orderedDays
        get() = Weekday.entries.filter { it in preferredDays }

    val validationMessage: String?
        get() {
            val unspecified =
                preferredDays.isEmpty() && PlanSetupDraft.days(initial?.preferredRunDays).isEmpty()
            if (daysPerWeek !in 3..7 || (!unspecified && preferredDays.size != daysPerWeek))
                return "Pick your run days."
            if (longRunDay != null && !unspecified && longRunDay !in preferredDays)
                return "Choose a long run day from your run days."
            if (doubleSessionDays.size > 2 || !preferredDays.containsAll(doubleSessionDays))
                return "Pick up to 2 run days for double sessions."
            if (gettingStarted && maxContinuousJogMin !in 0..120) return "Enter 0 to 120 minutes."
            return null
        }

    fun changeDaysPerWeek(count: Int) {
        daysPerWeek = count.coerceIn(3, 7)
        preferredDays = PlanSetupDraft.defaultDays(daysPerWeek)
        reconcile()
    }

    fun toggle(day: Weekday) {
        preferredDays = if (day in preferredDays) preferredDays - day else preferredDays + day
        daysPerWeek = preferredDays.size.coerceIn(3, 7)
        reconcile()
    }

    private fun reconcile() {
        doubleSessionDays = doubleSessionDays.intersect(preferredDays)
        if (longRunDay !in preferredDays)
            longRunDay =
                if (Weekday.Saturday in preferredDays) Weekday.Saturday
                else orderedDays.lastOrNull()
    }

    fun changes(): JsonObject {
        val before = ScheduleDraft(initial)
        return buildJsonObject {
            fun list(key: String, value: Set<Weekday>, old: Set<Weekday>) {
                if (value != old)
                    put(
                        key,
                        JsonArray(
                            Weekday.entries.filter { it in value }.map { JsonPrimitive(it.name) }
                        ),
                    )
            }
            list("preferred_days", preferredDays, before.preferredDays)
            list("double_session_days", doubleSessionDays, before.doubleSessionDays)
            list("mountain_days", mountainDays, before.mountainDays)
            if (longRunDay != before.longRunDay) longRunDay?.let { put("long_run_day", it.name) }
            if (daysPerWeek != before.daysPerWeek) put("days_per_week", daysPerWeek)
            if (hasGymAccess != before.hasGymAccess) put("has_gym_access", hasGymAccess)
            if (useTreadmill != before.useTreadmill) put("use_treadmill", useTreadmill)
            if (environment != before.environment) put("training_environment", environment)
            if (stairAccess != before.stairAccess) put("stair_access", stairAccess)
            if (treadmillMaxIncline != before.treadmillMaxIncline)
                put("treadmill_max_incline", treadmillMaxIncline)
            if (gettingStarted && maxContinuousJogMin != before.maxContinuousJogMin)
                put("max_continuous_jog_min", maxContinuousJogMin)
        }
    }
}

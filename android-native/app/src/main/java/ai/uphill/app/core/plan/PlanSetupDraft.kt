package ai.uphill.app.core.plan

import ai.uphill.app.core.auth.User
import ai.uphill.app.core.models.*
import ai.uphill.app.core.networking.JSONCoding
import java.time.LocalDate
import kotlinx.serialization.json.*

enum class SetupGoal(val wire: String, val title: String) {
    Race("race", "A specific race"),
    Distance("distance", "A distance"),
    StartRunning("start_running", "Start running"),
    Return("return", "Come back after a break"),
    Recovery("recovery", "Recover from a race");

    val isEvent
        get() = this == Race || this == Distance
}

enum class SetupStep(val title: String) {
    Goal("What are you training for?"),
    Details("Your goal"),
    RaceDate("Race date"),
    RaceGoal("Race goal"),
    FitnessFeel("How do you feel?"),
    DaysSinceRace("Days since your race"),
    RecoveryFeel("How is recovery going?"),
    Watch("Connect your watch"),
    Schedule("Your training week"),
    Venues("Where you train"),
    Body("About you"),
    TrainingZones("Training zones"),
    RaceHistory("Race history"),
    StartDate("Start date"),
    Review("Review your plan");

    companion object {
        fun steps(goal: SetupGoal?, profile: Boolean): List<SetupStep> {
            if (goal == null) return listOf(Goal)
            val details =
                when (goal) {
                    SetupGoal.Race,
                    SetupGoal.Distance -> listOf(Details, RaceDate, RaceGoal)
                    SetupGoal.Return -> listOf(Details, FitnessFeel)
                    SetupGoal.Recovery -> listOf(Details, DaysSinceRace, RecoveryFeel)
                    else -> emptyList()
                }
            return listOf(Goal) +
                details +
                (if (profile) listOf(Watch) else emptyList()) +
                listOf(Schedule, Venues) +
                (if (profile) listOf(Body, TrainingZones, RaceHistory) else emptyList()) +
                listOf(StartDate, Review)
        }
    }
}

data class PlanSetupDraft(
    var goal: SetupGoal? = null,
    var raceName: String = "",
    var raceDate: LocalDate? = null,
    var distanceKm: Double? = null,
    var elevationGainM: Double? = null,
    var terrain: String = "trail",
    var raceGoal: String = "finish",
    var targetMinutes: Int? = null,
    var distanceLabel: String? = null,
    var timeAway: String? = null,
    var fitnessFeel: String? = null,
    var raceDistanceCompleted: String? = null,
    var daysSinceRace: Int = 7,
    var recoveryFeel: String? = null,
    var daysPerWeek: Int = 4,
    var preferredDays: Set<Weekday> = defaultDays(4),
    var longRunDay: Weekday = Weekday.Saturday,
    var currentWeeklyKm: Double? = 30.0,
    var weeklyKmFromWatch: Boolean = false,
    var environment: String = "flat",
    var mountainDays: Set<Weekday> = emptySet(),
    var stairAccess: Boolean = false,
    var hasGymAccess: Boolean = false,
    var useTreadmill: Boolean = false,
    var treadmillMaxIncline: Int = 15,
    var doubleSessionDays: Set<Weekday> = emptySet(),
    var startDate: LocalDate = LocalDate.now(),
    var birthDate: String = "",
    var gender: String = "",
    var heightCm: Double? = null,
    var weightKg: Double? = null,
    var maxHr: Int? = null,
    var restingHr: Int? = null,
    var aetHr: Int? = null,
    var antHr: Int? = null,
    var thresholdSource: String = "unknown",
    var zone2PaceMin: String = "",
    var zone2PaceMax: String = "",
    var thresholdPace: String = "",
    var injuryHistory: String = "",
    var notes: String = "",
) {
    val orderedDays
        get() = Weekday.entries.filter { it in preferredDays }

    val hasZones
        get() =
            listOf(maxHr, restingHr, aetHr, antHr).any { it != null } ||
                listOf(zone2PaceMin, zone2PaceMax, thresholdPace).any { it.isNotBlank() }

    val needsZoneWarning
        get() =
            listOf(maxHr, restingHr, aetHr, antHr).any { it == null } ||
                thresholdSource == "unknown"

    fun zonesError(): String? {
        if (maxHr != null && maxHr !in 120..240) return "Enter Max HR between 120 and 240 bpm."
        if (restingHr != null && restingHr !in 30..120)
            return "Enter Resting HR between 30 and 120 bpm."
        if (aetHr != null && aetHr !in 80..220) return "Enter AeT between 80 and 220 bpm."
        if (antHr != null && antHr !in 90..225) return "Enter AnT between 90 and 225 bpm."
        if (
            listOfNotNull(restingHr, aetHr, antHr, maxHr).zipWithNext().any {
                it.first >= it.second
            }
        )
            return "Heart rates must increase from Resting to AeT to AnT to Max."
        val paces = listOf(zone2PaceMin, zone2PaceMax, thresholdPace).filter { it.isNotBlank() }
        fun seconds(value: String) = value.split(':').let { it[0].toInt() * 60 + it[1].toInt() }
        if (paces.any { !it.matches(Regex("\\d{1,2}:[0-5]\\d")) || seconds(it) == 0 })
            return "Enter pace as m:ss per km, for example 6:30."
        if (
            zone2PaceMin.isNotBlank() &&
                zone2PaceMax.isNotBlank() &&
                seconds(zone2PaceMin) < seconds(zone2PaceMax)
        )
            return "Easy pace, slower end must be slower than the faster end."
        if (
            thresholdPace.isNotBlank() &&
                listOf(zone2PaceMin, zone2PaceMax)
                    .filter { it.isNotBlank() }
                    .any { seconds(thresholdPace) >= seconds(it) }
        )
            return "Threshold pace must be faster than easy pace."
        return null
    }

    fun issues(step: SetupStep, today: LocalDate = LocalDate.now()): List<String> = buildList {
        when (step) {
            SetupStep.Goal -> if (goal == null) add("Choose what you're training for.")
            SetupStep.Details ->
                if (goal?.isEvent == true) {
                    if (goal == SetupGoal.Race && raceName.isBlank()) add("Add the race name.")
                    if (distanceKm == null || distanceKm!! !in 1.0..400.0)
                        add("Enter a distance between 1 and 400 km.")
                }
            SetupStep.RaceDate ->
                if (raceDate == null || raceDate!! < today.plusDays(14))
                    add("Pick a date at least 2 weeks away so the plan has room to build.")
            SetupStep.RaceGoal ->
                if (raceGoal == "time" && (targetMinutes ?: 0) !in 1..6000)
                    add("Set your target finish time.")
            SetupStep.Schedule -> {
                if (preferredDays.size != daysPerWeek) add("Pick your run days.")
                if (currentWeeklyKm == null || currentWeeklyKm!! !in 0.0..250.0)
                    add("Enter 0 to 250 km.")
            }
            SetupStep.TrainingZones -> zonesError()?.let { add(it) }
            SetupStep.StartDate ->
                if (startDate < today || startDate > latestStart(today))
                    add(
                        if (goal?.isEvent == true) "Start at least 2 weeks before your goal date."
                        else "Start today or later."
                    )
            else -> Unit
        }
    }

    fun latestStart(today: LocalDate): LocalDate =
        if (goal?.isEvent == true && raceDate != null)
            maxOf(today, minOf(today.plusDays(14), raceDate!!.minusDays(14)))
        else today.plusDays(14)

    fun body(lang: String, onboarding: Boolean, skipPlan: Boolean = false): JsonObject =
        buildJsonObject {
            val event = goal?.isEvent == true
            val days =
                if (preferredDays.size == daysPerWeek) orderedDays
                else Weekday.entries.filter { it in defaultDays(daysPerWeek) }
            val long = longRunDay.takeIf { it in days } ?: days.last()
            put("lang", lang)
            put(
                "goal_type",
                if (onboarding) goal?.wire ?: "start_running"
                else if (event) raceGoal else goal?.wire ?: "start_running",
            )
            if (event) {
                put(
                    "race_name",
                    raceName.trim().takeIf { it.isNotEmpty() } ?: "$distanceKm km goal",
                )
                raceDate?.let { put("race_date", it.toString()) }
                distanceKm?.let { put("course_distance_km", it) }
                elevationGainM?.let { put("course_elevation_gain_m", it) }
                if (onboarding) put("race_goal", raceGoal)
                if (raceGoal == "time")
                    targetMinutes?.let {
                        if (onboarding)
                            put(
                                "expected_finish_time",
                                "${it/60}:${(it%60).toString().padStart(2,'0')}",
                            )
                        else put("target_time_hours", it / 60.0)
                    }
            }
            put("terrain", terrain)
            put("days_per_week", daysPerWeek)
            put(
                if (onboarding) "preferred_run_days" else "preferred_days",
                JsonArray(days.map { JsonPrimitive(it.name) }),
            )
            put("long_run_day", long.name)
            put("current_weekly_km", currentWeeklyKm ?: 0.0)
            if (!onboarding) put("weekly_km_from_watch", weeklyKmFromWatch)
            put("has_gym_access", hasGymAccess)
            put("use_treadmill", useTreadmill)
            put("training_environment", environment)
            put(
                "mountain_days",
                JsonArray(
                    Weekday.entries.filter { it in mountainDays }.map { JsonPrimitive(it.name) }
                ),
            )
            put("stair_access", stairAccess)
            if (useTreadmill) put("treadmill_max_incline", treadmillMaxIncline)
            put(
                "double_session_days",
                JsonArray(days.filter { it in doubleSessionDays }.map { JsonPrimitive(it.name) }),
            )
            put("plan_start_date", startDate.toString())
            if (notes.isNotBlank()) put("athlete_notes", notes.trim())
            if (goal == SetupGoal.Return) {
                timeAway?.let { put("time_away", it) }
                fitnessFeel?.let { put("fitness_feel", it) }
            }
            if (goal == SetupGoal.Recovery) {
                raceDistanceCompleted?.let { put("race_distance_completed", it) }
                put("days_since_race", daysSinceRace)
                recoveryFeel?.let { put("recovery_feel", it) }
            }
            if (onboarding) {
                put("skip_plan", skipPlan)
                if (birthDate.isNotBlank()) put("dob", birthDate)
                if (gender.isNotBlank()) put("gender", gender)
                heightCm?.let { put("height_cm", it) }
                weightKg?.let { put("weight_kg", it) }
                maxHr?.let { put("max_hr", it) }
                restingHr?.let { put("resting_hr", it) }
                aetHr?.let { put("aet_hr", it) }
                antHr?.let { put("ant_hr", it) }
                put(
                    "threshold_source",
                    if (aetHr != null && antHr != null) thresholdSource else "unknown",
                )
                if (zone2PaceMin.isNotBlank()) put("zone2_pace_min", zone2PaceMin.trim())
                if (zone2PaceMax.isNotBlank()) put("zone2_pace_max", zone2PaceMax.trim())
                if (thresholdPace.isNotBlank()) put("threshold_pace", thresholdPace.trim())
                if (injuryHistory.isNotBlank()) put("injury_history", injuryHistory.trim())
            }
        }

    companion object {
        fun defaultDays(count: Int): Set<Weekday> =
            when (count) {
                3 -> setOf(Weekday.Tuesday, Weekday.Thursday, Weekday.Saturday)
                4 -> setOf(Weekday.Tuesday, Weekday.Thursday, Weekday.Saturday, Weekday.Sunday)
                5 ->
                    setOf(
                        Weekday.Monday,
                        Weekday.Tuesday,
                        Weekday.Thursday,
                        Weekday.Saturday,
                        Weekday.Sunday,
                    )
                6 -> Weekday.entries.toSet() - Weekday.Friday
                else -> Weekday.entries.toSet()
            }

        fun from(user: User): PlanSetupDraft {
            fun entered(field: String) =
                user.fieldSources?.get(field)?.jsonObject?.get("source")?.jsonPrimitive?.content !=
                    "default"
            val draft =
                PlanSetupDraft(
                    daysPerWeek = user.daysPerWeek?.coerceIn(3, 7) ?: 4,
                    currentWeeklyKm =
                        if (
                            !user.onboardingComplete &&
                                user.goalType == null &&
                                user.currentWeeklyKm == 30.0
                        )
                            null
                        else user.currentWeeklyKm,
                )
            val parsed = days(user.preferredRunDays)
            draft.preferredDays =
                parsed.takeIf { it.size == draft.daysPerWeek } ?: defaultDays(draft.daysPerWeek)
            draft.longRunDay =
                Weekday.parse(user.longRunDay).takeIf { it in draft.preferredDays }
                    ?: if (Weekday.Saturday in draft.preferredDays) Weekday.Saturday
                    else draft.orderedDays.last()
            draft.birthDate = user.dob.orEmpty()
            draft.gender = user.gender.orEmpty()
            draft.heightCm = user.heightCm
            draft.weightKg = user.weightKg
            draft.maxHr = user.maxHr.takeIf { entered("max_hr") }
            draft.restingHr = user.restingHr.takeIf { entered("resting_hr") }
            draft.aetHr = user.aetHr.takeIf { entered("aet_hr") }
            draft.antHr = user.antHr.takeIf { entered("ant_hr") }
            draft.zone2PaceMin =
                user.zone2PaceMin.orEmpty().takeIf { entered("zone2_pace_min") }.orEmpty()
            draft.zone2PaceMax =
                user.zone2PaceMax.orEmpty().takeIf { entered("zone2_pace_max") }.orEmpty()
            draft.thresholdPace =
                user.thresholdPace.orEmpty().takeIf { entered("threshold_pace") }.orEmpty()
            draft.injuryHistory = user.injuryHistory.orEmpty()
            draft.thresholdSource =
                user.fieldSources?.get("aet_hr")?.jsonObject?.get("method")?.jsonPrimitive?.content
                    ?: "unknown"
            return draft
        }

        fun days(raw: String?): Set<Weekday> =
            runCatching {
                    raw?.let {
                        JSONCoding.json
                            .decodeFromString<List<String>>(it)
                            .mapNotNull { v -> Weekday.entries.firstOrNull { d -> d.name == v } }
                            .toSet()
                    }
                }
                .getOrNull()
                .orEmpty()
    }
}

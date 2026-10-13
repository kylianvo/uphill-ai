package ai.uphill.app.core.plan

object ScheduleMessages {
    fun guardText(code: String): String =
        when (code) {
            "G1_not_owner" -> "This workout isn't in your active plan."
            "G2_history" ->
                "This workout is already completed or matched to an activity, so it can't be moved."
            "G3_past_target" -> "You can't move a workout to a day that has already passed."
            "G4_window" -> "Workouts can only move between this week and next week."
            "G5_out_of_plan" -> "That week is outside your plan."
            "G6_coach_linked" -> "You have a coach — ask them to change your schedule."
            "G7_no_dates" ->
                "This plan has no start date, so only same-week day swaps are possible."
            "STALE_changed" -> "Your plan changed since this was proposed."
            "NOTHING_to_move" -> "Nothing would change."
            "INVALID_operation" -> "That change isn't valid."
            else -> "That change couldn't be made."
        }

    fun warningText(warning: ScheduleWarning): String {
        val params = warning.values.toMutableMap()
        val text =
            when (warning.code) {
                "W1_hard_stacking",
                "W1_same_day",
                "W1_before_long_run" ->
                    if (params["kind"] == "before_long_run" || warning.code == "W1_before_long_run")
                        "Hard session on {day} (week {week}) right before the long run."
                    else "Two hard sessions on {day} (week {week})."
                "W2_volume_shift" -> {
                    params["before"] = params["before_minutes"].orEmpty()
                    params["after"] = params["after_minutes"].orEmpty()
                    "Week {week} volume changes from {before} to {after} min."
                }
                "W3_pending_draft" -> "“{title}” is still pending coach review."
                else -> return warning.code
            }
        return params.entries.fold(text) { value, (key, param) -> value.replace("{$key}", param) }
    }
}

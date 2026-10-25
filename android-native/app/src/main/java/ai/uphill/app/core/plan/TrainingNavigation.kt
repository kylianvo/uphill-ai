package ai.uphill.app.core.plan

import kotlinx.coroutines.flow.MutableStateFlow

/** Explicit jumps from coach cards and the plan checklist. */
object TrainingNavigation {
    val workoutId = MutableStateFlow<Int?>(null)
    val profileSection = MutableStateFlow<String?>(null)

    fun clear() {
        workoutId.value = null
        profileSection.value = null
    }
}

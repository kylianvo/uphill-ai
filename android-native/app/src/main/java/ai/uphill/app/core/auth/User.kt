package ai.uphill.app.core.auth

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class User(
    val id: Int,
    val email: String,
    val name: String,
    val role: String = "athlete",
    val onboardingComplete: Boolean = false,
    val provider: String = "email",
    val hasPassword: Boolean = false,
    val age: Int? = null,
    val dob: String? = null,
    val gender: String? = null,
    val heightCm: Double? = null,
    val weightKg: Double? = null,
    val goalType: String? = null,
    val currentWeeklyKm: Double? = null,
    val maxHr: Int? = null,
    val restingHr: Int? = null,
    val aetHr: Int? = null,
    val antHr: Int? = null,
    val daysPerWeek: Int? = null,
    val preferredRunDays: String? = null,
    val longRunDay: String? = null,
    val injuryHistory: String? = null,
    val zone2PaceMin: String? = null,
    val zone2PaceMax: String? = null,
    val thresholdPace: String? = null,
    val paceZoneModel: String? = null,
    val athleteNotes: String? = null,
    val isCoach: Boolean = false,
    val fieldSources: Map<String, JsonElement>? = null,
    val coachProfileChanges: List<JsonElement>? = null,
)

@Serializable data class AuthResponse(val sessionToken: String, val user: User)

import Foundation

/// Mirrors backend `format_user_response`. `gemini_api_key` is deliberately
/// absent: the app never reads, stores or shows it.
struct User: Codable, Sendable, Equatable, Identifiable {
    let id: Int
    let email: String
    let name: String
    let role: String
    let onboardingComplete: Bool
    let provider: String
    let hasPassword: Bool
    let age: Int?
    let dob: String?
    let gender: String?
    let heightCm: Double?
    let weightKg: Double?
    let goalType: String?
    let currentWeeklyKm: Double?
    let maxHr: Int?
    let restingHr: Int?
    let aetHr: Int?
    let antHr: Int?
    let daysPerWeek: Int?
    /// JSON-encoded array string, e.g. "[\"Tuesday\"]".
    let preferredRunDays: String?
    let longRunDay: String?
    let injuryHistory: String?
    let zone2PaceMin: String?
    let zone2PaceMax: String?
    let thresholdPace: String?
    let paceZoneModel: String?
    let isCoach: Bool

    var isAdmin: Bool { role == "admin" }
}

/// Response of every sign-in endpoint (login, register, google, apple, mock-login).
struct AuthResponse: Codable, Sendable {
    let sessionToken: String
    let user: User
}

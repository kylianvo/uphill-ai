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
    var athleteNotes: String? = nil
    let isCoach: Bool
    /// Keyed by backend column name (max_hr, aet_hr, zone2_pace_min, ...).
    var fieldSources: [String: ProfileFieldSource]? = nil
    /// Coach edits the athlete hasn't acknowledged yet.
    var coachProfileChanges: [CoachProfileChange]? = nil

    var isAdmin: Bool { role == "admin" }
}

/// Response of every sign-in endpoint (login, register, google, apple, mock-login).
struct AuthResponse: Codable, Sendable {
    let sessionToken: String
    let user: User
}

/// Where one physiology/pace number came from.
struct ProfileFieldSource: Codable, Sendable, Equatable {
    /// "coach" | "athlete" | "default"
    let source: String
    var byName: String? = nil
    var at: String? = nil
    /// AeT/AnT only: lab | field | estimated | unknown.
    var method: String? = nil
}

struct CoachProfileChange: Codable, Sendable, Equatable, Identifiable {
    let field: String
    let previous: ProfileValue?
    let value: ProfileValue?
    let byName: String?
    let at: String?
    var id: String { field }
}

/// A profile number that is an Int (heart rates) or a "m:ss" String (paces).
enum ProfileValue: Codable, Sendable, Equatable {
    case int(Int), string(String)

    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if let i = try? c.decode(Int.self) { self = .int(i) } else { self = .string(try c.decode(String.self)) }
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .int(let i): try c.encode(i)
        case .string(let s): try c.encode(s)
        }
    }

    var display: String {
        switch self {
        case .int(let i): "\(i)"
        case .string(let s): s
        }
    }
}

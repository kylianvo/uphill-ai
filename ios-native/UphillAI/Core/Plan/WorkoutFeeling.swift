import SwiftUI

/// 5-level feeling scale mirroring the web FeelingSelector (frontend/src/components/FeelingSelector.tsx).
/// Maps directly to the RPE values stored by the backend (2, 4, 6, 8, 10).
public enum WorkoutFeeling: String, CaseIterable, Identifiable, Sendable {
    case veryLight = "very_light"
    case light = "light"
    case moderate = "moderate"
    case hard = "hard"
    case maxEffort = "max_effort"

    public var id: String { rawValue }

    public var label: String {
        switch self {
        case .veryLight: "Very Light"
        case .light: "Light"
        case .moderate: "Moderate"
        case .hard: "Hard"
        case .maxEffort: "Max Effort"
        }
    }

    public var subLabel: String {
        switch self {
        case .veryLight: "Effortless recovery"
        case .light: "Fresh & easy"
        case .moderate: "Normal fatigue"
        case .hard: "Heavy legs / Tired"
        case .maxEffort: "Exhausted / Deload"
        }
    }

    public var coachDescription: String {
        switch self {
        case .veryLight:
            "Effortless recovery or peak freshness — coach will maintain or slightly increase volume to capitalize."
        case .light:
            "Fresh and well recovered — coach will maintain progressive overload without cutting volume."
        case .moderate:
            "Normal training fatigue — coach will keep balanced volume with steady progression."
        case .hard:
            "Heavy legs or elevated fatigue — coach will ease off volume and reduce high-intensity sessions."
        case .maxEffort:
            "Deep exhaustion or overreaching risk — coach will schedule an active recovery deload week."
        }
    }

    public var rpe: Int {
        switch self {
        case .veryLight: 2
        case .light: 4
        case .moderate: 6
        case .hard: 8
        case .maxEffort: 10
        }
    }

    public var color: Color {
        switch self {
        case .veryLight: Color(red: 6/255, green: 182/255, blue: 212/255)
        case .light: Color(red: 16/255, green: 185/255, blue: 129/255)
        case .moderate: Color(red: 59/255, green: 130/255, blue: 246/255)
        case .hard: Color(red: 245/255, green: 158/255, blue: 11/255)
        case .maxEffort: Color(red: 239/255, green: 68/255, blue: 68/255)
        }
    }

    public var iconName: String {
        switch self {
        case .veryLight: "leaf.fill"
        case .light: "figure.walk"
        case .moderate: "figure.run"
        case .hard: "flame.fill"
        case .maxEffort: "bolt.fill"
        }
    }

    /// Map a 1-10 backend RPE value into the 5-level feeling scale.
    public static func from(rpe: Int?) -> WorkoutFeeling? {
        guard let rpe else { return nil }
        if rpe <= 2 { return .veryLight }
        if rpe <= 4 { return .light }
        if rpe <= 6 { return .moderate }
        if rpe <= 8 { return .hard }
        return .maxEffort
    }
}

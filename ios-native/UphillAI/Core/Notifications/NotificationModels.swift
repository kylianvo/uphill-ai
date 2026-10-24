import Foundation

struct NotificationPreferences: Codable, Sendable, Equatable {
    var workoutsEnabled = false
    var coachingEnabled = false
    var resultsEnabled = false
    var workoutTime = "07:00"
    var coachingTime = "18:00"
    var quietStart = "21:00"
    var quietEnd = "07:00"
    var timezone: String?
    var language = "en"
    var distanceUnit = "km"
    var pausedUntil: String?
    var checklistSnoozedUntil: String?
    var available: Bool?
    var mutedKinds: [String]?
}

struct NotificationRoute: Codable, Sendable, Equatable {
    let kind: String
    var intent: String?
    var planId: Int?
    var workoutId: Int?
    var weekNumber: Int?
    var blockNumber: Int?
    var itemId: String?
    var cardId: Int?
    var lang: String?
    var namespace: String?

    init?(payload: [AnyHashable: Any]) {
        guard payload["v"] as? Int == 1,
              let destination = payload["destination"] as? [String: Any],
              let data = try? JSONSerialization.data(withJSONObject: destination),
              let route = try? JSONCoding.decoder.decode(Self.self, from: data) else { return nil }
        let valid: Bool
        switch route.kind {
        case "workout": valid = (route.planId ?? 0) > 0 && (route.workoutId ?? 0) > 0
        case "plan": valid = (route.planId ?? 0) > 0
        case "review": valid = (route.planId ?? 0) > 0 && (route.weekNumber ?? 0) > 0
        case "knowledge": valid = (route.cardId ?? 0) > 0 && route.namespace == "server" && ["en", "vi"].contains(route.lang ?? "")
        case "checklist": valid = ["watch", "races", "hr", "pace", "injuries"].contains(route.itemId ?? "")
        default: valid = false
        }
        guard valid else { return nil }
        self = route
    }

    var trainingDestination: TrainingDestination? {
        switch itemId {
        case "watch": .watch
        case "races": .raceHistory
        case "hr": .heartRate
        case "pace": .paces
        case "injuries": .aboutYou
        default: nil
        }
    }
}

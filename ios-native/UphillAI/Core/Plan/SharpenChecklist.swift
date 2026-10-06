import Foundation

enum TrainingDestination: String, Identifiable, Hashable {
    case aboutYou, trainingZones, heartRate, paces, schedule, raceHistory, nutritionLab, gearVault, goalDeterminer, paceStrategy, knowledgeHub
    var id: String { rawValue }
}

struct SharpenItem: Identifiable, Equatable {
    let id: String
    let title: String
    let done: Bool
    let destination: TrainingDestination
}

enum SharpenChecklist {
    static func items(user: User, plan: Plan) -> [SharpenItem] {
        func present(_ value: String?) -> Bool {
            !(value?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ?? true)
        }
        return [
            SharpenItem(id: "hr", title: "Add your heart rate zones", done: user.aetHr != nil && user.maxHr != nil, destination: .trainingZones),
            SharpenItem(id: "pace", title: "Add your easy pace", done: present(user.zone2PaceMin) || present(user.thresholdPace), destination: .trainingZones),
            SharpenItem(id: "notes", title: "Tell me about injuries", done: present(user.athleteNotes), destination: .aboutYou),
            SharpenItem(id: "schedule", title: "Set your long-run day", done: present(plan.longRunDay), destination: .schedule),
            SharpenItem(id: "profile", title: "Add your age and weight", done: user.age != nil && user.weightKg != nil, destination: .aboutYou),
        ]
    }
}

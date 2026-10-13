import Foundation

enum TrainingDestination: String, Identifiable, Hashable {
    case aboutYou, watch, trainingZones, heartRate, paces, schedule, raceHistory, nutritionLab, gearVault, goalDeterminer, paceStrategy, knowledgeHub
    var id: String { rawValue }
}

struct SharpenItem: Identifiable, Equatable {
    let id: String
    let title: String
    let done: Bool
    let destination: TrainingDestination
}

/// What the athlete can still add so each new week fits them better. Done means
/// measured or entered by them, never an app estimate.
enum SharpenChecklist {
    static func items(user: User, corosConnected: Bool, raceHistoryLinked: Bool) -> [SharpenItem] {
        func present(_ value: String?) -> Bool {
            !(value?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ?? true)
        }
        func entered(_ field: String) -> Bool {
            (user.fieldSources?[field]?.source ?? "athlete") != "default"
        }
        let thresholds = user.aetHr != nil && user.antHr != nil && entered("aet_hr") && entered("ant_hr")
        let paces = (present(user.zone2PaceMin) && entered("zone2_pace_min")) || present(user.thresholdPace)
        return [
            SharpenItem(id: "watch", title: L("Connect your watch"), done: corosConnected, destination: .watch),
            SharpenItem(id: "races", title: L("Link your race history"), done: raceHistoryLinked, destination: .raceHistory),
            SharpenItem(id: "hr", title: L("Add your AeT and AnT heart rates"), done: thresholds, destination: .heartRate),
            SharpenItem(id: "pace", title: L("Add your pace zones"), done: paces, destination: .paces),
            SharpenItem(id: "injuries", title: L("Tell Coach Uphill about injuries"),
                        done: present(user.injuryHistory) || present(user.athleteNotes), destination: .aboutYou),
        ]
    }
}

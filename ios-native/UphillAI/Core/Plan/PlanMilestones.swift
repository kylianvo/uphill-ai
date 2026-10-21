import Foundation

/// What a beginner's plan builds toward. Raw values match the backend's `milestone_target`.
enum MilestoneTarget: String, CaseIterable, Codable, Sendable {
    case fiveK = "5k", tenK = "10k"

    var title: String { self == .fiveK ? L("First 5K") : L("First 10K") }
}

/// The `beginner_milestones` object on the plan payload (`services/beginner_milestones.py`).
/// The server owns the ladder and achievement; the app labels and shows it.
struct PlanMilestones: Codable, Sendable, Equatable {
    struct Item: Codable, Sendable, Equatable, Identifiable {
        let key: String
        let kind: String
        let threshold: Double
        let stage: String
        let typicalWeeks: [Int]
        let achievedAt: String?
        let source: String?

        var id: String { key }
        var isReached: Bool { achievedAt != nil }
        var title: String { BeginnerMilestones.label(key) }
        var typicalWeeksText: String {
            typicalWeeks.count == 2 ? L("usually around week %lld–%lld", typicalWeeks[0], typicalWeeks[1]) : ""
        }
    }

    let target: String
    let hasEvent: Bool
    let items: [Item]
    let nextKey: String?

    var reachedCount: Int { items.filter(\.isReached).count }
    var next: Item? { items.first { $0.key == nextKey } }
    var targetTitle: String { (MilestoneTarget(rawValue: target) ?? .fiveK).title }
    var canUpgrade: Bool { target == MilestoneTarget.fiveK.rawValue && items.contains { $0.key == "first_5k" && $0.isReached } }

    /// "First 5K · 3 of 6 milestones", plus "· 6 weeks to event" when the plan has one.
    func headerText(weeksToEvent: Int?) -> String {
        var text = L("%@ · %lld of %lld milestones", targetTitle, reachedCount, items.count)
        if hasEvent, let weeksToEvent { text += " · " + L("%lld weeks to event", weeksToEvent) }
        return text
    }

    /// The latest milestone earned in the app (not the onboarding baseline) that this device has not shown yet.
    func unseenEarned(seen: Set<String>) -> Item? {
        items.last { $0.isReached && $0.source != "baseline" && !seen.contains($0.key) }
    }
}

enum BeginnerMilestones {
    /// Mirrors backend `beginner_milestones.LADDER`. The plan response is the source of truth once a plan exists;
    /// this copy only previews the path during onboarding.
    static let ladder: [(key: String, jog: Int?, weeks: ClosedRange<Int>)] = [
        ("first_session", nil, 1...1), ("jog_5", 5, 3...5), ("jog_10", 10, 4...6), ("jog_20", 20, 5...8),
        ("jog_30", 30, 7...10), ("first_5k", nil, 9...12), ("jog_45", 45, 13...17), ("jog_60", 60, 16...21),
        ("first_10k", nil, 18...24),
    ]

    static func preview(for target: MilestoneTarget) -> [(key: String, jog: Int?, weeks: ClosedRange<Int>)] {
        Array(ladder.prefix(target == .fiveK ? 6 : 9))
    }

    static func label(_ key: String) -> String {
        switch key {
        case "first_session": L("First run/walk session")
        case "jog_5": L("5 min unbroken jog")
        case "jog_10": L("10 min unbroken jog")
        case "jog_20": L("20 min unbroken jog")
        case "jog_30": L("30 min non-stop")
        case "first_5k": L("First 5 km")
        case "jog_45": L("45 min non-stop")
        case "jog_60": L("60 min non-stop")
        case "first_10k": L("First 10 km")
        default: key
        }
    }

    /// Mirrors backend `minimum_weeks`: no reduction without a baseline.
    static func minimumWeeks(target: MilestoneTarget, currentJogMin: Int) -> Int {
        let base = target == .fiveK ? 9 : 17
        guard currentJogMin > 0, ladder.contains(where: { ($0.jog ?? Int.max) <= currentJogMin }) else { return base }
        let firstOpen = ladder.first { entry in
            guard entry.key != "first_session" else { return false }
            return (entry.jog ?? Int.max) > currentJogMin || entry.jog == nil
        }
        let openWeek = (firstOpen?.weeks.lowerBound) ?? 9
        return max(3, base - (openWeek - 1))
    }

    /// Whole Monday-aligned weeks from `start` to `event`, like the backend, or nil when the event is not after the start.
    static func weeksUntil(event: Date, start: Date, calendar: Calendar) -> Int? {
        guard event > start else { return nil }
        func monday(_ d: Date) -> Date {
            let day = calendar.startOfDay(for: d)
            let offset = (calendar.component(.weekday, from: day) + 5) % 7
            return calendar.date(byAdding: .day, value: -offset, to: day)!
        }
        let days = calendar.dateComponents([.day], from: monday(start), to: monday(event)).day ?? 0
        return days / 7 + 1
    }
}

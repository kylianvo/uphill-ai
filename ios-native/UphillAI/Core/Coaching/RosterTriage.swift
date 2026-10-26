import Foundation

/// What the coach narrowed the Athletes tab to. nil = no filter on that field.
struct RosterFilter: Equatable, Sendable {
    var planType: String? = nil
    var race: String? = nil
    var level: String? = nil
    var phase: String? = nil
}

enum TriageSection: CaseIterable, Sendable {
    case actNow, reviewBuild, checkIn, onTrack
}

enum GroupKey: CaseIterable, Sendable {
    case race, level, planType
}

/// The one-tap action a runner's most urgent signal calls for.
enum CoachAction: Equatable, Sendable {
    case adaptWeek, reviewPlan, buildPlan, openDraft, buildNextWeek, reviewChanges, note
}

extension CoachOverviewAthlete {
    var effectivePlanType: String { planType ?? "review" }

    var section: TriageSection {
        let sev = signals?.first { $0.severity != .highlight }?.severity
        switch sev {
        case .actNow: return .actNow
        case .reviewBuild: return .reviewBuild
        case .checkIn: return .checkIn
        default: return .onTrack
        }
    }

    var primaryAction: CoachAction? {
        guard let top = signals?.first(where: { $0.severity != .highlight }) else { return nil }
        switch top.code {
        case "reported_pain", "reported_sick", "overload", "missed_many": return .adaptWeek
        case "plan_to_review": return .reviewPlan
        case "needs_plan": return .buildPlan
        case "draft_unpublished": return .openDraft
        case "next_block_due": return .buildNextWeek
        case "changes_to_approve": return .reviewChanges
        default: return .note
        }
    }

    /// This plan week (offset 0) or one of the three before it.
    func stats(weekOffset: Int) -> CoachWeekStats? {
        weekOffset == 0 ? week : prevWeeks?.dropFirst(weekOffset - 1).first
    }

    func groupKey(_ key: GroupKey) -> String {
        switch key {
        case .race: activePlan?.raceName ?? "none"
        case .level: runnerLevel
        case .planType: effectivePlanType
        }
    }
}

/// Filters, sections and roster numbers for the Athletes tab, computed on the device from one overview fetch.
struct RosterTriage {
    let all: [CoachOverviewAthlete]
    let visible: [CoachOverviewAthlete]
    let weekOffset: Int

    init(athletes: [CoachOverviewAthlete], filter: RosterFilter, weekOffset: Int) {
        all = athletes
        self.weekOffset = weekOffset
        visible = athletes.filter { a in
            (filter.planType == nil || a.effectivePlanType == filter.planType)
                && (filter.race == nil || a.activePlan?.raceName == filter.race)
                && (filter.level == nil || a.runnerLevel == filter.level)
                && (filter.phase == nil || a.phase == filter.phase)
        }
    }

    func athletes(in section: TriageSection) -> [CoachOverviewAthlete] {
        visible.filter { $0.section == section }
    }

    var highlights: [(athlete: CoachOverviewAthlete, signal: CoachSignal)] {
        visible.flatMap { a in (a.signals ?? []).filter { $0.severity == .highlight }.map { (a, $0) } }
    }

    var counts: (all: Int, review: Int, coached: Int) {
        let coached = all.filter { $0.effectivePlanType == "coached" }.count
        return (all.count, all.count - coached, coached)
    }

    var sessionsDonePct: Double? { ratio(visible, \.sessionsDone, \.sessionsPlanned) }
    var keyDonePct: Double? { ratio(visible, \.keyDone, \.keyPlanned) }
    var volumePct: Double? { ratio(visible, \.minutesDone, \.minutesPlanned) }

    func groups(by key: GroupKey) -> [(label: String, count: Int, donePct: Double?)] {
        var order: [String] = []
        var members: [String: [CoachOverviewAthlete]] = [:]
        for a in visible {
            let k = a.groupKey(key)
            if members[k] == nil { order.append(k) }
            members[k, default: []].append(a)
        }
        // Biggest group first; ties keep roster order.
        return order.enumerated()
            .sorted { (members[$0.element]!.count, -$0.offset) > (members[$1.element]!.count, -$1.offset) }
            .map { k in (k.element, members[k.element]!.count, ratio(members[k.element]!, \.sessionsDone, \.sessionsPlanned)) }
    }

    /// Share of completed minutes this week by kind; nil when nothing was done.
    var mix: (easy: Double, long: Double, quality: Double)? {
        let m = visible.compactMap(\.mixMinutes)
        let easy = m.map(\.easy).reduce(0, +), long = m.map(\.long).reduce(0, +), quality = m.map(\.quality).reduce(0, +)
        let total = easy + long + quality
        return total > 0 ? (easy / total, long / total, quality / total) : nil
    }

    private func ratio(_ athletes: [CoachOverviewAthlete], _ done: KeyPath<CoachWeekStats, Int>,
                       _ planned: KeyPath<CoachWeekStats, Int>) -> Double? {
        let weeks = athletes.compactMap { $0.stats(weekOffset: weekOffset) }
        let p = weeks.map { $0[keyPath: planned] }.reduce(0, +)
        return p > 0 ? Double(weeks.map { $0[keyPath: done] }.reduce(0, +)) / Double(p) : nil
    }
}

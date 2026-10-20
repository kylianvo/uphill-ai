import Foundation

/// What changed in a week's plan versus the week before. Port of frontend/src/utils/weekDiff.ts.
enum WeekDiffChip: Equatable, Sendable {
    case time(delta: Int)
    case long(from: Int, to: Int)
    case added(type: String, count: Int)
    case removed(type: String, count: Int)
}

enum WeekDiff {
    /// Total-time change, long-run change, and session types gained or lost (max 2). Empty without both weeks.
    static func chips(prev: [Workout], cur: [Workout]) -> [WeekDiffChip] {
        let p = prev.filter { $0.type != "Rest" }
        let c = cur.filter { $0.type != "Rest" }
        guard !p.isEmpty, !c.isEmpty else { return [] }
        func mins(_ w: [Workout]) -> Double { w.reduce(0) { $0 + $1.durationMinutes } }
        func isLong(_ w: Workout) -> Bool { w.type.trimmingCharacters(in: .whitespaces).lowercased() == "long run" }

        var chips: [WeekDiffChip] = []
        let delta = Int((mins(c) - mins(p)).rounded())
        if delta != 0 { chips.append(.time(delta: delta)) }
        let from = Int(mins(p.filter(isLong)).rounded())
        let to = Int(mins(c.filter(isLong)).rounded())
        if from != to { chips.append(.long(from: from, to: to)) }

        func counts(_ w: [Workout]) -> [String: Int] { w.reduce(into: [:]) { $0[$1.type, default: 0] += 1 } }
        let before = counts(p), after = counts(c)
        let types = Set(before.keys).union(after.keys).filter { !$0.isEmpty && $0.lowercased() != "long run" }.sorted()
        var typeChips: [WeekDiffChip] = []
        for type in types {
            let d = after[type, default: 0] - before[type, default: 0]
            if d > 0 { typeChips.append(.added(type: type, count: d)) }
            else if d < 0 { typeChips.append(.removed(type: type, count: -d)) }
        }
        // Gains first, like the web.
        typeChips.sort { lhs, rhs in
            if case .added = lhs, case .removed = rhs { return true }
            return false
        }
        return chips + typeChips.prefix(2)
    }
}

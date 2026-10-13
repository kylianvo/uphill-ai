import Foundation

/// Mirrors the generator's five-zone formulas for a preview before the profile is saved.
enum OnboardingPacePreview {
    static func ranges(draft: PlanSetupDraft) -> [String]? {
        guard draft.trainingZonesError == nil else { return nil }
        let bounds: [(Double, Double)]
        if let threshold = seconds(draft.thresholdPace) {
            bounds = [(1.40, 1.25), (1.25, 1.15), (1.15, 1.05), (1.05, 0.98), (0.98, 0.88)]
                .map { ($0 * threshold, $1 * threshold) }
        } else if let slow = seconds(draft.zone2PaceMin), let fast = seconds(draft.zone2PaceMax) {
            let gap = draft.aetHr.flatMap { aet in draft.antHr.map { Double($0) / Double(aet) / 1.15 } } ?? 1
            let scale = min(1.4, max(0.7, gap))
            let z3 = fast * (1 - 0.10 * scale)
            let z4 = fast * (1 - 0.18 * scale)
            let z5 = fast * (1 - 0.27 * scale)
            bounds = [(slow * (1 + 0.15 * scale), slow), (slow, fast), (fast, z3), (z3, z4), (z4, z5)]
        } else { return nil }
        return bounds.map { "\(format($0)) - \(format($1))" }
    }

    private static func seconds(_ text: String) -> Double? {
        let text = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard text.range(of: #"^\d{1,2}:[0-5]\d$"#, options: .regularExpression) != nil else { return nil }
        let parts = text.split(separator: ":").compactMap { Double($0) }
        let value = parts[0] * 60 + parts[1]
        return value > 0 ? value : nil
    }

    private static func format(_ seconds: Double) -> String {
        let rounded = Int(seconds.rounded(.toNearestOrEven))
        return "\(rounded / 60):\(String(format: "%02d", rounded % 60))"
    }
}

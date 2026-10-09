import SwiftUI

/// Names, units and "where this came from" wording for the physiology/pace
/// numbers a coach can set. Keys are the backend column names.
enum ProfileField {
    static func label(_ field: String) -> String {
        switch field {
        case "resting_hr": L("Resting HR")
        case "max_hr": L("Max HR")
        case "aet_hr": L("AeT Threshold (Z2)")
        case "ant_hr": L("AnT Threshold (Z4)")
        case "zone2_pace_min": L("Zone 2 slow end")
        case "zone2_pace_max": L("Zone 2 fast end")
        case "threshold_pace": L("Threshold Pace")
        default: field
        }
    }

    static func unit(_ field: String) -> String {
        field.hasSuffix("_hr") ? "bpm" : "/km"
    }

    /// "9 Oct" from the backend's ISO timestamp; nil when it can't be read.
    static func shortDate(_ iso: String?) -> String? {
        guard let iso, iso.count >= 10 else { return nil }
        let parser = DateFormatter()
        parser.locale = Locale(identifier: "en_US_POSIX")
        parser.dateFormat = "yyyy-MM-dd"
        guard let date = parser.date(from: String(iso.prefix(10))) else { return nil }
        return date.formatted(.dateTime.day().month(.abbreviated))
    }
}

/// One quiet line under a number: who set it, or that it is only the app's
/// fallback. Coach-set values are emphasised because they override the athlete.
struct ProvenanceLine: View {
    let source: ProfileFieldSource?

    var body: some View {
        if let source {
            Label {
                Text(text(for: source))
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
            } icon: {
                Image(systemName: icon(for: source))
            }
            .labelStyle(.titleAndIcon)
            .font(.caption2.weight(source.source == "coach" ? .semibold : .regular))
            .foregroundStyle(source.source == "coach" ? UH.Palette.accentInk : UH.Palette.muted)
            .accessibilityLabel(text(for: source))
        }
    }

    private func icon(for s: ProfileFieldSource) -> String {
        switch s.source {
        case "coach": "person.badge.shield.checkmark"
        case "athlete": "person"
        default: "questionmark.circle"
        }
    }

    private func text(for s: ProfileFieldSource) -> String {
        switch s.source {
        case "coach":
            let who = s.byName ?? L("Coach")
            if let day = ProfileField.shortDate(s.at) { return L("Set by %@ · %@", who, day) }
            return L("Set by %@", who)
        case "athlete":
            switch s.method {
            case "lab": return L("Athlete · lab test")
            case "field": return L("Athlete · field test")
            case "estimated": return L("Athlete · watch/formula")
            case .some: return L("Athlete · method unknown")
            case nil: return L("Entered by athlete")
            }
        default:
            return L("App default, not measured")
        }
    }
}

import SwiftUI

/// Why this week looks the way it does: change chips against last week and the coach's reasons.
/// Mirrors web WeekBrief.
struct WeekBriefView: View {
    let chips: [WeekDiffChip]
    let brief: WeekBrief?

    var body: some View {
        if !chips.isEmpty || brief != nil {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                if !chips.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            Text("vs last week")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.muted)
                            ForEach(Array(chips.enumerated()), id: \.offset) { _, chip in
                                Text(verbatim: Self.text(chip))
                                    .font(.system(size: 11.5, weight: .semibold, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                                    .padding(.horizontal, 9)
                                    .padding(.vertical, 3)
                                    .background(UH.Palette.tint, in: Capsule())
                                    .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1))
                            }
                        }
                    }
                }
                if let brief {
                    HStack(alignment: .top, spacing: UH.Space.compact) {
                        Image(systemName: "sparkle")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(UH.Palette.accentInk)
                            .padding(.top, 3)
                            .accessibilityHidden(true)
                        (Text(verbatim: L("Why this week") + ": ").bold() + Text(verbatim: brief.why)).fixedSize(horizontal: false, vertical: true)
                    }
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.ink)
                    ForEach(brief.benefits, id: \.self) { benefit in
                        Text(verbatim: "• " + benefit)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .padding(.leading, UH.Space.regular)
                    }
                    if let watch = brief.watch, !watch.isEmpty {
                        HStack(alignment: .top, spacing: UH.Space.compact) {
                            Image(systemName: "exclamationmark.circle.fill")
                                .font(.system(size: 12))
                                .foregroundStyle(UH.Palette.warningInk)
                                .padding(.top, 2)
                                .accessibilityHidden(true)
                            (Text(verbatim: L("Watch out") + ": ").bold() + Text(verbatim: watch)).fixedSize(horizontal: false, vertical: true)
                        }
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.ink)
                    }
                }
            }
            .padding(UH.Space.small)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("plan.weekBrief")
        }
    }

    static func text(_ chip: WeekDiffChip) -> String {
        switch chip {
        case .time(let delta):
            return "\(delta > 0 ? "+" : "−")\(abs(delta)) \(L("min"))"
        case .long(let from, let to):
            return "Long Run \(from) → \(to) \(L("min"))"
        case .added(let type, let count):
            return "+\(count) \(type)"
        case .removed(let type, let count):
            return "−\(count) \(type)"
        }
    }
}

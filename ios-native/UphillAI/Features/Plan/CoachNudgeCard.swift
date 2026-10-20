import SwiftUI

/// The single coach message: recognition, a gentle nudge, or a plain heads-up. Absent when there is nothing to say.
struct CoachNudgeCard: View {
    let nudge: CoachNudge

    private var symbol: String {
        switch nudge.kind {
        case .encourage: "checkmark.circle"
        case .push: "arrow.forward.circle"
        case .headsUp: "exclamationmark.circle"
        }
    }

    private var tint: Color { nudge.kind == .headsUp ? UH.Palette.warningInk : nudge.kind == .push ? UH.Palette.ink : UH.Palette.accentInk }

    /// Praise is green, a heads-up amber; a nudge is neutral so it never reads as either.
    private var fill: Color {
        switch nudge.kind {
        case .encourage: UH.Palette.activeFill
        case .push: UH.Palette.card
        case .headsUp: UH.Palette.warningFill
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: UH.Space.small) {
            Image(systemName: symbol)
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(tint)
                .accessibilityHidden(true)
            Text(verbatim: nudge.text)
                .font(.subheadline)
                .foregroundStyle(UH.Palette.ink)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(fill, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay { if nudge.kind == .push { RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1) } }
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("plan.coachNudge")
    }
}

import SwiftUI

/// The six "why was it missed" choices; mirrors web MissedReasonChips.
enum MissedReason: String, CaseIterable, Identifiable {
    case busy, sick, pain, tired, weather, other

    var id: String { rawValue }

    var title: String {
        switch self {
        case .busy: L("Busy")
        case .sick: L("Sick")
        case .pain: L("Pain")
        case .tired: L("Tired")
        case .weather: L("Weather")
        case .other: L("Other")
        }
    }
}

struct MissedReasonChips: View {
    let selected: String?
    let onSelect: (MissedReason) -> Void

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 84), spacing: UH.Space.compact)], alignment: .leading, spacing: UH.Space.compact) {
            ForEach(MissedReason.allCases) { reason in
                let isSelected = selected == reason.rawValue
                Button { onSelect(reason) } label: {
                    Text(reason.title)
                        .font(UH.TextStyle.caption.weight(.semibold))
                        .foregroundStyle(isSelected ? UH.Palette.danger : UH.Palette.secondary)
                        .frame(maxWidth: .infinity, minHeight: 36)
                        .background(isSelected ? UH.Palette.danger.opacity(0.12) : Color.clear, in: Capsule())
                        .overlay(Capsule().stroke(isSelected ? UH.Palette.danger : UH.Palette.line, lineWidth: 1))
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(isSelected ? .isSelected : [])
                .accessibilityIdentifier("missed.reason.\(reason.rawValue)")
            }
        }
    }
}

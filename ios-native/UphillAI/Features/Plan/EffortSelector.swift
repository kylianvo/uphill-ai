import SwiftUI

/// Athlete-friendly effort choices; the API still receives the existing numeric RPE values.
struct EffortSelector: View {
    @Binding var selection: Int?
    let identifier: String

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 130))], spacing: UH.Space.small) {
            ForEach(WorkoutFeeling.allCases) { effort in
                let selected = WorkoutFeeling.from(rpe: selection) == effort
                Button { selection = effort.rpe } label: {
                    HStack(spacing: UH.Space.compact) {
                        Text(effort.label)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                            .multilineTextAlignment(.leading)
                        Spacer(minLength: 0)
                        Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                            .foregroundStyle(selected ? UH.Palette.accentInk : UH.Palette.muted)
                    }
                    .padding(UH.Space.small)
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .background(selected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(selected ? UH.Palette.accent : UH.Palette.line))
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(selected ? .isSelected : [])
                .accessibilityIdentifier("\(identifier).\(effort.rawValue)")
            }
        }
        .sensoryFeedback(.selection, trigger: selection)
    }
}

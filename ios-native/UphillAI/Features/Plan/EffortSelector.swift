import SwiftUI

/// Five named effort levels; color shows the scale while the API retains numeric RPE.
struct EffortSelector: View {
    @Binding var selection: Int?
    let identifier: String
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    var body: some View {
        Group {
            if dynamicTypeSize.isAccessibilitySize {
                VStack(spacing: UH.Space.compact) {
                    ForEach(WorkoutFeeling.allCases) { effort in
                        choice(effort, stacked: true)
                    }
                }
            } else {
                HStack(alignment: .top, spacing: 4) {
                    ForEach(WorkoutFeeling.allCases) { effort in
                        choice(effort, stacked: false)
                    }
                }
            }
        }
        .sensoryFeedback(.selection, trigger: selection)
    }

    private func choice(_ effort: WorkoutFeeling, stacked: Bool) -> some View {
        let selected = WorkoutFeeling.from(rpe: selection) == effort
        return Button { selection = effort.rpe } label: {
            Group {
                if stacked {
                    HStack(spacing: UH.Space.small) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(effort.color)
                            .frame(width: 36, height: 12)
                        Text(effort.label).font(UH.TextStyle.label)
                        Spacer(minLength: 0)
                        if selected { Image(systemName: "checkmark.circle.fill") }
                    }
                    .padding(UH.Space.small)
                } else {
                    VStack(spacing: UH.Space.compact) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(effort.color)
                            .frame(height: 14)
                            .overlay {
                                if selected {
                                    Image(systemName: "checkmark.circle.fill")
                                        .symbolRenderingMode(.palette)
                                        .foregroundStyle(Color.white, UH.Palette.ink)
                                        .font(.system(size: 22, weight: .semibold))
                                }
                            }
                            .padding(.vertical, 4)
                        VStack(spacing: 0) {
                            ForEach(effort.label.split(separator: " "), id: \.self) { word in
                                Text(String(word))
                                    .font(.caption)
                                    .fontWeight(selected ? .bold : .medium)
                                    .lineLimit(1)
                                    .minimumScaleFactor(0.8)
                            }
                        }
                        .frame(minHeight: 36, alignment: .top)
                    }
                    .padding(.horizontal, 3)
                    .padding(.vertical, UH.Space.compact)
                }
            }
            .foregroundStyle(UH.Palette.ink)
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .top)
            .background(selected ? effort.color.opacity(0.1) : Color.clear, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(selected ? UH.Palette.ink : Color.clear, lineWidth: 1.5))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(effort.label)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .accessibilityIdentifier("\(identifier).\(effort.rawValue)")
    }
}

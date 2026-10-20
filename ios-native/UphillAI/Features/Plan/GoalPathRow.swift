import SwiftUI

/// Whether training is on the path to the B and A goals, from measured aerobic speed. Absent until there is data.
struct GoalPathRow: View {
    let path: GoalPath?

    var body: some View {
        if let path {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                HStack(spacing: UH.Space.compact) {
                    chip("B", path.b)
                    chip("A", path.a)
                }
                Text(verbatim: path.line).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
                if let note = path.note {
                    Text(verbatim: note).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .trainingCard()
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("goal.path")
        }
    }

    private func chip(_ goal: String, _ status: String) -> some View {
        let behind = status == "behind"
        return Label {
            Text(verbatim: goal + " · " + GoalPath.word(status)).font(UH.TextStyle.label)
        } icon: {
            Image(systemName: behind ? "arrow.down.right.circle" : "arrow.up.right.circle")
        }
        .foregroundStyle(behind ? UH.Palette.warningInk : UH.Palette.accentInk)
        .padding(.horizontal, UH.Space.small)
        .padding(.vertical, 6)
        .background(behind ? UH.Palette.warningFill : UH.Palette.activeFill, in: Capsule())
    }
}

import SwiftUI

/// The Goal sheet's one notice about the plan carrying the goal: what the week holds against what the goal
/// needs, up to two ways to close the gap, and when the plan cannot back the assumed improvement. Quiet
/// (absent) when the plan can carry the goal.
struct GoalPlanCheckCard: View {
    let feasibility: GoalFeasibility?
    let assessment: GoalAssessment?

    var body: some View {
        let check = feasibility?.check
        let support = assessment?.planSupportNotice
        if check != nil || support != nil {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                if let check {
                    Label {
                        Text(check.title).font(UH.TextStyle.label)
                    } icon: {
                        Image(systemName: check.tone == .short ? "exclamationmark.triangle.fill" : "exclamationmark.circle")
                    }
                    .foregroundStyle(UH.Palette.warningInk)
                    Text(check.line).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
                    ForEach(check.levers, id: \.self) { lever in
                        Text(lever).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                    if let note = check.note {
                        Text(note).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                    }
                }
                if let support {
                    if check != nil { Divider() }
                    Text(support).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
            }
            .padding(UH.Space.regular)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .accessibilityElement(children: .combine)
        }
    }
}

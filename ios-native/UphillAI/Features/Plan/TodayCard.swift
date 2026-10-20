import SwiftUI

/// The session to do now (or next), in one line of facts. Tapping opens the session.
struct TodayCard: View {
    let focus: TodayFocus
    let onOpen: (Workout) -> Void

    private var detail: String {
        guard let w = focus.workout else { return "" }
        var parts = [focus.isToday ? L("Today") : (focus.isRestToday ? L("Rest day · next") : L("Next")), PlanViewModel.formatMinutes(w.durationMinutes), w.targetZone]
        if let gain = w.elevationGainM, gain >= 50 { parts.append("+\(Int(gain.rounded())) m") }
        return parts.joined(separator: " · ")
    }

    var body: some View {
        if let workout = focus.workout {
            Button { onOpen(workout) } label: {
                HStack(spacing: UH.Space.small) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(verbatim: workout.title)
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(2)
                        Text(verbatim: detail)
                            .font(.subheadline.monospacedDigit())
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    Spacer(minLength: UH.Space.compact)
                    stateMark
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .trainingCard()
            .accessibilityIdentifier("plan.today")
        } else {
            Text("Nothing left this week. Rest and recover.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .trainingCard()
        }
    }

    @ViewBuilder private var stateMark: some View {
        switch focus.state {
        case .done:
            Label("Done", systemImage: "checkmark.circle.fill")
                .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
        case .missed:
            Label("Missed", systemImage: "minus.circle")
                .font(UH.TextStyle.label).foregroundStyle(UH.Palette.warningInk)
        case .todo:
            Image(systemName: "chevron.right").font(.footnote.weight(.semibold)).foregroundStyle(UH.Palette.muted)
                .accessibilityHidden(true)
        }
    }
}

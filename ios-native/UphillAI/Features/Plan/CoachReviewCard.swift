import SwiftUI

/// One coach message for the selected week, and a way into the full review.
struct CoachReviewCard: View {
    let model: PlanViewModel
    let onOpenReview: () -> Void

    private var priorityWorkout: Workout? {
        model.snapshot?.workouts.first { $0.weekNumber == model.selectedWeek && $0.isPriority }
    }

    /// Which single message the card shows: the coach's nudge, the week's reason, the week-1 welcome, then the pick.
    static func message(nudge: String?, why: String?, welcome: [String]?, pick: String?) -> String? {
        if let nudge, !nudge.isEmpty { return nudge }
        if let why { return why }
        if let welcome, !welcome.isEmpty { return welcome.joined(separator: " ") }
        if let pick { return L("If you do one session well this week, make it %@.", pick) }
        return nil
    }

    private var nudge: CoachNudge? {
        model.selectedWeek == model.currentWeek ? model.coachNudge : nil
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("Coach's review")
                .font(UH.TextStyle.eyebrow)
                .foregroundStyle(UH.Palette.accentInk)

            if let text = Self.message(nudge: nudge?.text, why: whyThisWeek, welcome: welcome, pick: priorityWorkout?.title) {
                Text(verbatim: text)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(nudge?.kind == .headsUp ? UH.Palette.warningInk : UH.Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier(welcome != nil && nudge == nil && whyThisWeek == nil ? "plan.coachCard.welcome" : "plan.coachCard.message")
            }

            Button("Read the full review", action: onOpenReview)
                .font(UH.TextStyle.disclosure)
                .foregroundStyle(UH.Palette.accentInk)
                .frame(minHeight: 44)
                .buttonStyle(.plain)
                .accessibilityIdentifier("plan.coachCard.reviewLink")
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line))
    }

    /// Week 1 with nothing reviewed yet: a short welcome built from the plan, so the card is never empty.
    private var welcome: [String]? {
        guard model.selectedWeek == 1, whyThisWeek == nil, model.weekBrief == nil, model.coachNudge == nil,
              let plan = model.snapshot?.plan else { return nil }
        var lines = [L("Welcome to your plan for %@. This is where it starts.", plan.raceName)]
        if let days = model.daysToRace, days >= 7 {
            lines.append(L("You have %lld weeks. Week 1 is about easy, consistent running so your body settles into the routine.", Int((Double(days) / 7).rounded(.up))))
        }
        if let pick = priorityWorkout {
            lines.append(L("If you do one session well this week, make it %@.", pick.title))
        }
        lines.append(L("Run easy, sleep well, and tell me how each session felt. I'll adjust from there."))
        return lines
    }

    /// The week brief's reason, else the block narrative's focus for the week.
    private var whyThisWeek: String? {
        let why = model.weekBrief?.why ?? model.selectedWeekNarrative?.aiThisWeekDescription
        return why?.isEmpty == false ? why : nil
    }
}

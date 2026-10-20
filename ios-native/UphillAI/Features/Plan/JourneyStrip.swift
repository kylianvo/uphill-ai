import SwiftUI

/// Where the athlete is between today and race day: phases as segments, milestones as marks, one "you are here".
struct JourneyStrip: View {
    let journey: PlanJourney

    private let trackHeight: CGFloat = 6

    private func fraction(of week: Double) -> CGFloat {
        guard journey.totalWeeks > 0 else { return 0 }
        return CGFloat(min(max(week / Double(journey.totalWeeks), 0), 1))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            GeometryReader { proxy in
                let width = proxy.size.width
                ZStack(alignment: .leading) {
                    ForEach(journey.phases) { phase in
                        let start = fraction(of: Double(phase.startWeek - 1))
                        let end = fraction(of: Double(phase.endWeek))
                        let passed = phase.endWeek < journey.currentWeek
                        Capsule()
                            .fill(passed ? UH.Palette.accent : (phase.startWeek <= journey.currentWeek ? UH.Palette.accent.opacity(0.45) : UH.Palette.line))
                            .frame(width: max((end - start) * width - 3, 4), height: trackHeight)
                            .offset(x: start * width)
                    }
                    ForEach(journey.milestones) { milestone in
                        Circle()
                            .fill(milestone.done ? UH.Palette.accent : UH.Palette.card)
                            .overlay(Circle().stroke(milestone.done ? UH.Palette.accentInk : UH.Palette.muted, lineWidth: 1.5))
                            .frame(width: 10, height: 10)
                            .offset(x: fraction(of: Double(milestone.week) - 0.5) * width - 5, y: -11)
                    }
                    Circle()
                        .fill(UH.Palette.ink)
                        .frame(width: 12, height: 12)
                        .overlay(Circle().stroke(UH.Palette.card, lineWidth: 2))
                        .offset(x: fraction(of: Double(journey.currentWeek) - 0.5) * width - 6)
                }
                .frame(height: trackHeight)
            }
            .frame(height: 18)
            .padding(.top, 8)
            HStack(spacing: UH.Space.compact) {
                Text("Week \(journey.currentWeek) of \(journey.totalWeeks)")
                    .font(UH.TextStyle.caption.monospacedDigit())
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                if let next = journey.nextMilestone {
                    Text(verbatim: L("%@ · week %lld", next.title, next.week))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .lineLimit(1)
                }
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("plan.journey")
    }
}

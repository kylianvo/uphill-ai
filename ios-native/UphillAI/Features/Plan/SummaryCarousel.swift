import Charts
import SwiftUI

struct SummaryCarousel: View {
    @ScaledMetric(relativeTo: .body) private var cardHeight: CGFloat = 212
    @State private var page: Int? = 0
    private let pageNames = ["Volume", "Race", "This week", "Phase"]
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let model: PlanViewModel
    var adapting: Int? = nil
    var onReview: () -> Void = {}
    var onAdapt: () -> Void = {}
    var onGoal: () -> Void = {}

    var body: some View {
        VStack(spacing: UH.Space.compact) {
            ScrollView(.vertical) {
                VStack(spacing: 0) {
                    volumeCard.id(0)
                    raceCard.id(1)
                    weekCard.id(2)
                    phaseCard.id(3)
                }
                .scrollTargetLayout()
            }
            .scrollTargetBehavior(.paging)
            .scrollPosition(id: $page)
            .scrollIndicators(.hidden)
            .frame(height: cardHeight)
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line))
            .overlay(alignment: .trailing) { pageDots }
            .padding(.horizontal, UH.Space.regular)

            HStack(spacing: UH.Space.small) {
                if let adapting {
                    ProgressView()
                    Text("Adapting week \(adapting)\u{2026}").font(UH.TextStyle.label)
                } else {
                    Button(action: onReview) {
                        Text("Review week").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                            .padding(.horizontal, UH.Space.medium).frame(minHeight: 44)
                            .overlay(Capsule().stroke(UH.Palette.ink.opacity(0.35), lineWidth: 1.5))
                    }
                    .accessibilityIdentifier("plan.review")
                    if model.canAdapt(week: model.selectedWeek) {
                        Button(action: onAdapt) {
                            Text("Adapt this week").font(UH.TextStyle.label).foregroundStyle(UH.Palette.buttonInk)
                                .padding(.horizontal, UH.Space.medium).frame(minHeight: 44)
                                .background(UH.Palette.accent, in: Capsule())
                        }
                        .accessibilityIdentifier("plan.adapt")
                    }
                }
            }
            .buttonStyle(.plain).frame(minHeight: 44)
        }
    }

    private func card(_ content: some View) -> some View {
        content
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(UH.Space.regular)
            .padding(.trailing, UH.Space.small)
            .frame(height: cardHeight)
            .background(UH.Palette.card)
    }

    private var pageDots: some View {
        VStack(spacing: 0) {
            ForEach(0..<4, id: \.self) { index in
                Button {
                    withAnimation(reduceMotion ? nil : UH.Motion.standard) { page = index }
                } label: {
                    Circle()
                        .fill(index == (page ?? 0) ? UH.Palette.accentInk : UH.Palette.line)
                        .frame(width: 6, height: 6)
                        .frame(width: 28, height: 44)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("\(pageNames[index]) summary")
                .accessibilityAddTraits(index == (page ?? 0) ? .isSelected : [])
            }
        }
    }

    private func eyebrow(_ text: String) -> some View {
        Text(text.uppercased()).font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.muted)
    }

    private var volumeCard: some View {
        let volume = model.selectedVolume
        return card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Week \(model.selectedWeek) volume")
                HStack(alignment: .firstTextBaseline, spacing: UH.Space.compact) {
                    Text(volume.km, format: .number.precision(.fractionLength(0...1)))
                        .font(UH.TextStyle.metric)
                    Text("km").font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                }
                .foregroundStyle(UH.Palette.ink)
                Text("\(volume.hours, format: .number.precision(.fractionLength(0...1))) h · \(Int(volume.gainM)) m gain")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                Chart(model.weeklyVolumes.filter(\.generated), id: \.week) { week in
                    BarMark(x: .value("Week", week.week), y: .value("km", week.km))
                        .foregroundStyle(week.week == model.selectedWeek ? UH.Palette.accent : UH.Palette.line)
                        .cornerRadius(UH.Radius.topic)
                }
                .frame(height: 40)
                .chartXAxis(.hidden)
                .chartYAxis(.hidden)
                .accessibilityHidden(true)
            }
        )
        .accessibilityElement(children: .combine)
    }

    private var raceCard: some View {
        let plan = model.snapshot?.plan
        let raceDay = PlanCalendar.day(from: plan?.raceDate)
        return card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Race")
                Text(plan?.raceName ?? "")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                    .lineLimit(2)
                if let raceDay {
                    Text(raceDay, format: .dateTime.weekday(.abbreviated).day().month(.abbreviated))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                Spacer(minLength: 0)
                if let days = model.daysToRace {
                    Text(days < 7 ? "Race week" : "\(days) days to go")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                }
                if let pill = model.goalPillText {
                    Button(action: onGoal) {
                        Text(pill).font(UH.TextStyle.label)
                            .foregroundStyle(model.goal?.status.kind == .behind ? UH.Palette.danger : UH.Palette.accentInk)
                            .padding(.horizontal, UH.Space.small).frame(minHeight: 44)
                            .contentShape(Capsule())
                            .background(UH.Palette.hover, in: Capsule())
                    }
                    .accessibilityIdentifier("plan.goalpill")
                } else if let goal = model.goalText {
                    Text(goal).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
            }
        )
        .accessibilityElement(children: .contain)
    }

    private var weekCard: some View {
        card(
            VStack(alignment: .leading, spacing: UH.Space.small) {
                eyebrow(model.selectedWeek == model.currentWeek ? "This week" : "Week \(model.selectedWeek)")
                HStack(spacing: 0) {
                    ForEach(model.dayStates, id: \.weekday) { item in
                        VStack(spacing: UH.Space.compact) {
                            Text(String(item.weekday.rawValue.prefix(1)))
                                .font(UH.TextStyle.eyebrow)
                                .foregroundStyle(UH.Palette.muted)
                            dot(item.state)
                        }
                        .frame(maxWidth: .infinity)
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel("\(item.weekday.rawValue), \(label(item.state))")
                    }
                }
                let done = model.dayStates.filter { $0.state == .done }.count
                let active = model.dayStates.filter { $0.state != .rest }.count
                Text("\(done) of \(active) sessions done")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        )
    }

    @ViewBuilder
    private func dot(_ state: DayState) -> some View {
        switch state {
        case .done:
            Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk).font(.title3)
        case .missed:
            Image(systemName: "xmark.circle").foregroundStyle(UH.Palette.danger).font(.title3)
        case .planned:
            Image(systemName: "circle").foregroundStyle(UH.Palette.secondary).font(.title3)
        case .rest:
            Circle().fill(UH.Palette.line).frame(width: 6, height: 6).frame(height: 22)
        }
    }

    private func label(_ state: DayState) -> String {
        switch state {
        case .done: "done"
        case .missed: "missed"
        case .planned: "planned"
        case .rest: "rest"
        }
    }

    private var phaseCard: some View {
        card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                eyebrow("Phase")
                Text(model.phase ?? "Not generated yet")
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.ink)
                Text("Week \(model.selectedWeek) of \(model.snapshot?.plan.totalWeeks ?? 0)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            })
        .accessibilityElement(children: .combine)
    }
}

import SwiftUI
import Charts

struct SummaryCarousel: View {
    let model: PlanViewModel
    let adapting: Int?
    let onReview: () -> Void
    let onAdapt: () -> Void
    let onGoal: () -> Void
    @State private var page: Int? = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private let cardHeight: CGFloat = 190
    private let pageNames = ["Volume", "Sessions", "Race", "Phase"]

    var body: some View {
        VStack(spacing: UH.Space.compact) {
            ZStack(alignment: .trailing) {
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(spacing: 0) {
                        volumeCard.id(0)
                        weekCard.id(1)
                        raceCard.id(2)
                        phaseCard.id(3)
                    }
                    .scrollTargetLayout()
                }
                .scrollTargetBehavior(.paging)
                .scrollPosition(id: $page)

                pageDots
                    .padding(.trailing, UH.Space.small)
            }
            .frame(height: cardHeight)

            HStack {
                Text(pageNames[page ?? 0].uppercased())
                    .font(UH.TextStyle.eyebrow)
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                if let adapting, adapting == model.selectedWeek {
                    Label("Adapting week…", systemImage: "sparkles")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.accentInk)
                } else {
                    Button(action: onReview) {
                        Text("Weekly review").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                            .padding(.horizontal, UH.Space.small).frame(minHeight: 44)
                            .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1.5))
                    }
                    .accessibilityIdentifier("plan.review")

                    if model.canAdapt(week: model.selectedWeek) {
                        Button(action: onAdapt) {
                            Text("Adapt week").font(UH.TextStyle.label).foregroundStyle(UH.Palette.buttonInk)
                                .padding(.horizontal, UH.Space.small).frame(minHeight: 44)
                                .background(UH.Palette.accent, in: Capsule())
                        }
                        .accessibilityIdentifier("plan.adapt")
                    }
                }
            }
            .buttonStyle(.plain)
            .padding(.horizontal, UH.Space.regular)
        }
    }

    private func card(_ content: some View) -> some View {
        content
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .padding(UH.Space.regular)
            .padding(.trailing, UH.Space.section)
            .frame(height: cardHeight)
            .background(UH.Palette.card)
            .containerRelativeFrame(.horizontal)
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
                        .frame(width: 24, height: 32)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("\(pageNames[index]) summary")
                .accessibilityAddTraits(index == (page ?? 0) ? .isSelected : [])
            }
        }
    }

    private func eyebrow(_ text: String) -> some View {
        Text(text.uppercased())
            .font(.system(size: 10, weight: .bold, design: .monospaced))
            .tracking(0.6)
            .foregroundStyle(UH.Palette.muted)
    }

    // MARK: - Volume Card (Hours comparison, Planned vs Actual)

    private var volumeCard: some View {
        let volume = model.selectedVolume
        let comp = model.weekComparison

        return card(
            VStack(alignment: .leading, spacing: 5) {
                HStack {
                    eyebrow("Week \(model.selectedWeek) volume")
                    Spacer()
                    // Hours vs last week comparison
                    if let prev = comp.previousHours {
                        let diff = comp.currentHours - prev
                        let sign = diff >= 0 ? "+" : ""
                        Text("\(sign)\(String(format: "%.1f", diff)) h vs last wk")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }

                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text(String(format: "%.1f", volume.km))
                        .font(.system(size: 26, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.ink)
                    Text("km")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.secondary)

                    Spacer()

                    Text("\(String(format: "%.1f", volume.hours)) h · \(Int(volume.gainM)) m D+")
                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }

                // Planned vs Actual
                HStack(spacing: 4) {
                    Text("Planned \(String(format: "%.1f", comp.plannedKm)) km · Actual \(String(format: "%.1f", comp.actualKm)) km")
                        .font(.system(size: 11.5, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }

                Spacer(minLength: 2)

                Chart(model.weeklyVolumes.filter(\.generated), id: \.week) { week in
                    BarMark(x: .value("Week", week.week), y: .value("km", week.km))
                        .foregroundStyle(week.week == model.selectedWeek ? UH.Palette.accent : UH.Palette.line)
                        .cornerRadius(UH.Radius.topic)
                }
                .frame(height: 38)
                .chartXAxis(.hidden)
                .chartYAxis(.hidden)
                .accessibilityHidden(true)
            }
        )
        .accessibilityElement(children: .combine)
    }

    // MARK: - Sessions Card (Adherence %)

    private var weekCard: some View {
        let comp = model.weekComparison
        let done = model.dayStates.filter { $0.state == .done }.count
        let active = model.dayStates.filter { $0.state != .rest }.count

        return card(
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    eyebrow(model.selectedWeek == model.currentWeek ? "This week" : "Week \(model.selectedWeek)")
                    Spacer()
                    // Adherence % pill
                    Text("\(comp.adherencePct)% adherence")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 3)
                        .background(UH.Palette.activeFill, in: Capsule())
                }

                HStack(spacing: 0) {
                    ForEach(model.dayStates, id: \.weekday) { item in
                        VStack(spacing: 4) {
                            Text(String(item.weekday.rawValue.prefix(1)))
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.muted)
                            dot(item.state)
                        }
                        .frame(maxWidth: .infinity)
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel("\(item.weekday.rawValue), \(label(item.state))")
                    }
                }
                .padding(.vertical, 4)

                Spacer(minLength: 2)

                HStack {
                    Text("\(done) of \(active) sessions completed")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    Text("Planned vs Actual")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }
            }
        )
    }

    @ViewBuilder
    private func dot(_ state: DayState) -> some View {
        switch state {
        case .done:
            Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk).font(.system(size: 20))
        case .missed:
            Image(systemName: "xmark.circle").foregroundStyle(UH.Palette.danger).font(.system(size: 20))
        case .planned:
            Image(systemName: "circle").foregroundStyle(UH.Palette.line).font(.system(size: 20))
        case .rest:
            Circle().fill(UH.Palette.line.opacity(0.8)).frame(width: 6, height: 6).frame(height: 20)
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

    // MARK: - Race Card

    private var raceCard: some View {
        let plan = model.snapshot?.plan
        let raceDay = PlanCalendar.day(from: plan?.raceDate)
        return card(
            VStack(alignment: .leading, spacing: 4) {
                eyebrow("Race Target")
                Text(plan?.raceName ?? "")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                    .lineLimit(1)

                if let raceDay {
                    Text(raceDay, format: .dateTime.weekday(.abbreviated).day().month(.abbreviated).year())
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                Spacer(minLength: 0)

                HStack {
                    if let days = model.daysToRace {
                        Text(days < 7 ? "Race week" : "\(days) days to go")
                            .font(.system(size: 13, weight: .semibold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                    }

                    Spacer()

                    if let pill = model.goalPillText {
                        Button(action: onGoal) {
                            Text(pill)
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(model.goal?.status.kind == .behind ? UH.Palette.danger : UH.Palette.accentInk)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .contentShape(Capsule())
                                .background(UH.Palette.hover, in: Capsule())
                                .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1))
                        }
                        .accessibilityIdentifier("plan.goalpill")
                    } else if let goal = model.goalText {
                        Text(goal).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
        )
        .accessibilityElement(children: .contain)
    }

    // MARK: - Phase Card

    private var phaseCard: some View {
        card(
            VStack(alignment: .leading, spacing: 5) {
                eyebrow("Training Phase")
                Text(model.phase ?? "Base Phase")
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.ink)

                Text("Week \(model.selectedWeek) of \(model.snapshot?.plan.totalWeeks ?? 0)")
                    .font(.system(size: 13, weight: .medium, design: .monospaced))
                    .foregroundStyle(UH.Palette.secondary)

                Spacer(minLength: 2)

                Text("Focus: build consistent aerobic capacity and fatigue resistance.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        )
        .accessibilityElement(children: .combine)
    }
}

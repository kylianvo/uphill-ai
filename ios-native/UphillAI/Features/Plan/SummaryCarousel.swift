import SwiftUI
import Charts

enum VolumeChartMode: String, CaseIterable, Identifiable {
    case weekDays = "Days"
    case weekTrend = "Trend"

    var id: String { rawValue }

    var accessibilityTitle: String {
        switch self {
        case .weekDays: "Week days volume"
        case .weekTrend: "Every week volume trend"
        }
    }
}

struct SummaryCarousel: View {
    let model: PlanViewModel
    var adapting: Int? = nil
    let onReview: () -> Void
    let onAdapt: () -> Void
    let onGoal: () -> Void

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var volumeChartMode: VolumeChartMode = .weekDays

    init(
        model: PlanViewModel,
        adapting: Int? = nil,
        onReview: @escaping () -> Void,
        onAdapt: @escaping () -> Void,
        onGoal: @escaping () -> Void,
        initialVolumeMode: VolumeChartMode = .weekDays
    ) {
        self.model = model
        self.adapting = adapting
        self.onReview = onReview
        self.onAdapt = onAdapt
        self.onGoal = onGoal
        _volumeChartMode = State(initialValue: initialVolumeMode)
    }

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: UH.Space.compact) {
                volumeCard
                weekCard
                raceCard
                phaseCard
            }
            .padding(.horizontal, UH.Space.regular)
        }
    }

    private func card<Content: View>(_ content: Content) -> some View {
        content
            .padding(14)
            .frame(width: 315, height: 184, alignment: .topLeading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.landing)
                    .stroke(UH.Palette.line, lineWidth: 1)
            )
    }

    private func eyebrow(_ text: String) -> some View {
        Text(text.uppercased())
            .font(UH.TextStyle.eyebrow)
            .tracking(0.5)
            .foregroundStyle(UH.Palette.secondary)
    }

    // MARK: - Volume Card (Week Days & Every Week Trend)

    private var volumeCard: some View {
        let volume = model.selectedVolume
        let comp = model.weekComparison
        let dayVols = model.dayVolumes

        return card(
            VStack(alignment: .leading, spacing: 3) {
                // Header: Eyebrow + Mode Switcher [Days | Trend]
                HStack(alignment: .center) {
                    eyebrow("Week \(model.selectedWeek) Volume")

                    Spacer()

                    // Segmented pill switcher
                    HStack(spacing: 2) {
                        ForEach(VolumeChartMode.allCases) { mode in
                            Button {
                                withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.18)) {
                                    volumeChartMode = mode
                                }
                            } label: {
                                Text(mode.rawValue)
                                    .font(.system(size: 10, weight: volumeChartMode == mode ? .bold : .medium, design: .monospaced))
                                    .foregroundStyle(volumeChartMode == mode ? UH.Palette.accentInk : UH.Palette.secondary)
                                    .padding(.horizontal, 7)
                                    .padding(.vertical, 2.5)
                                    .background(volumeChartMode == mode ? UH.Palette.hover : Color.clear, in: Capsule())
                            }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("volume.mode.\(mode == .weekDays ? "days" : "trend")")
                            .accessibilityLabel(mode.accessibilityTitle)
                        }
                    }
                    .padding(2)
                    .background(UH.Palette.line.opacity(0.35), in: Capsule())
                }

                // Middle: Big Numbers
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text(String(format: "%.1f", volume.km))
                        .font(.system(size: 26, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.ink)
                    Text("km")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.secondary)

                    Spacer()

                    Text("\(String(format: "%.1f", volume.hours)) h · \(Int(volume.gainM)) m D+")
                        .font(.system(size: 12.5, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }

                // Subline: Planned vs Actual or Trend progression
                HStack(spacing: 4) {
                    if volumeChartMode == .weekDays {
                        Text("Planned \(String(format: "%.1f", comp.plannedKm)) km · Actual \(String(format: "%.1f", comp.actualKm)) km")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    } else {
                        if let diff = comp.diffHours, let prev = comp.previousHours, prev > 0 {
                            let pct = Int((diff / prev * 100).rounded())
                            let sign = pct >= 0 ? "+" : ""
                            Text("\(sign)\(pct)% vs last wk · Total \(model.snapshot?.plan.totalWeeks ?? 0) weeks")
                                .font(.system(size: 11, weight: .medium, design: .monospaced))
                                .foregroundStyle(pct >= 0 ? UH.Palette.accentInk : UH.Palette.secondary)
                        } else {
                            Text("Total \(model.snapshot?.plan.totalWeeks ?? 0) weeks progression")
                                .font(.system(size: 11, weight: .medium, design: .monospaced))
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }
                }

                Spacer(minLength: 4)

                // Chart: Week Days Breakdown or Every Week Trend
                if volumeChartMode == .weekDays {
                    weekDaysChart(dayVols)
                } else {
                    weekTrendChart
                }
            }
        )
        .accessibilityElement(children: .contain)
    }

    @ViewBuilder
    private func weekDaysChart(_ days: [DayVolume]) -> some View {
        Chart(days) { day in
            let val = max(day.km, day.isRest ? 0.8 : 1.2)
            BarMark(
                x: .value("Day", day.weekday.rawValue),
                y: .value("km", val)
            )
            .foregroundStyle(day.isRest ? UH.Palette.line.opacity(0.6) : day.color)
            .cornerRadius(3.5)
            .annotation(position: .top, spacing: 2) {
                if day.km > 0 {
                    Text(String(format: "%.0f", day.km))
                        .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                        .foregroundStyle(day.color)
                } else if day.isRest {
                    Text("–")
                        .font(.system(size: 8.5, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                }
            }
        }
        .frame(height: 54)
        .chartXAxis {
            AxisMarks(values: .automatic) { value in
                AxisValueLabel {
                    if let raw = value.as(String.self), let wd = Weekday(rawValue: raw) {
                        Text(String(wd.rawValue.prefix(1)))
                            .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(wd.rawValue == "Saturday" || wd.rawValue == "Sunday" ? UH.Palette.ink : UH.Palette.secondary)
                    }
                }
            }
        }
        .chartYAxis(.hidden)
        .accessibilityLabel("Volume by day of week")
    }

    @ViewBuilder
    private var weekTrendChart: some View {
        let vols = model.weeklyVolumes
        Chart {
            ForEach(vols, id: \.week) { week in
                let val = max(week.km, 1.0)
                BarMark(
                    x: .value("Week", "W\(week.week)"),
                    y: .value("km", val)
                )
                .foregroundStyle(
                    week.week == model.selectedWeek
                        ? UH.Palette.accentInk
                        : (week.generated ? UH.Palette.accent.opacity(0.45) : UH.Palette.line.opacity(0.45))
                )
                .cornerRadius(3)

                if week.generated {
                    LineMark(
                        x: .value("Week", "W\(week.week)"),
                        y: .value("km", week.km)
                    )
                    .foregroundStyle(UH.Palette.accentInk.opacity(0.85))
                    .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round))

                    PointMark(
                        x: .value("Week", "W\(week.week)"),
                        y: .value("km", week.km)
                    )
                    .foregroundStyle(week.week == model.selectedWeek ? UH.Palette.accentInk : UH.Palette.accent.opacity(0.7))
                    .symbolSize(week.week == model.selectedWeek ? 32 : 14)
                }
            }
        }
        .frame(height: 54)
        .chartXAxis {
            AxisMarks(values: .automatic) { value in
                AxisValueLabel {
                    if let str = value.as(String.self) {
                        Text(str)
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
        }
        .chartYAxis(.hidden)
        .accessibilityLabel("Weekly volume trend")
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
                    if model.canAdaptWeek(model.selectedWeek) {
                        Button(action: onAdapt) {
                            HStack(spacing: 4) {
                                Image(systemName: "sparkles")
                                    .font(.system(size: 10, weight: .bold))
                                Text("Adapt Week \(model.selectedWeek)")
                                    .font(.system(size: 11, weight: .bold))
                            }
                            .foregroundStyle(UH.Palette.accentInk)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(UH.Palette.activeFill, in: Capsule())
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("plan.summary.adaptWeek")
                    } else {
                        Text("Planned vs Actual")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
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

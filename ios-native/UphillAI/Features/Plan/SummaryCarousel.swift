import SwiftUI
import Charts

enum VolumeChartMode: String, CaseIterable, Identifiable {
    case weekDays = "Days"
    case weekTrend = "Trend"

    var id: String { rawValue }

    var accessibilityTitle: String {
        switch self {
        case .weekDays: L("Week days volume")
        case .weekTrend: L("Every week volume trend")
        }
    }
}

struct SummaryCarousel: View {
    let model: PlanViewModel
    let onGoal: () -> Void

    @State private var volumeChartMode: VolumeChartMode = .weekDays

    init(
        model: PlanViewModel,
        onGoal: @escaping () -> Void,
        initialVolumeMode: VolumeChartMode = .weekDays
    ) {
        self.model = model
        self.onGoal = onGoal
        _volumeChartMode = State(initialValue: initialVolumeMode)
    }

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: UH.Space.compact) {
                weekCard
                if let progress = model.goalProgress { goalProgressCard(progress) }
            }
            .scrollTargetLayout()
            .padding(.horizontal, UH.Space.regular)
        }
        .scrollTargetBehavior(.viewAligned)
    }

    private func card<Content: View>(_ content: Content) -> some View {
        content
            .padding(14)
            .frame(width: 315, alignment: .topLeading)
            .frame(minHeight: 184, alignment: .topLeading)  // grows with Dynamic Type instead of clipping
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

    // MARK: - This Week Card (sessions and volume, days or every-week trend)

    private var weekCard: some View {
        let comp = model.weekComparison
        let done = model.dayStates.filter { $0.state == .done }.count
        let active = model.dayStates.filter { $0.state != .rest }.count

        return card(
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .center) {
                        eyebrow(model.selectedWeek == model.currentWeek ? L("This week") : L("Week %lld", model.selectedWeek))
                        Spacer()
                        chartModePicker
                    }
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        eyebrow(model.selectedWeek == model.currentWeek ? L("This week") : L("Week %lld", model.selectedWeek))
                        chartModePicker
                    }
                }

                Spacer(minLength: 0)

                if volumeChartMode == .weekDays {
                    weekDaysChart(model.dayVolumes)
                } else {
                    weekTrendChart
                }

                Text(verbatim: L("%lld of %lld sessions done", done, active) + " · "
                     + L("%@ of %@ km", comp.actualKm.formatted(.number.precision(.fractionLength(0...1))),
                         comp.plannedKm.formatted(.number.precision(.fractionLength(0...1)))))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .monospacedDigit()
            }
        )
        .accessibilityElement(children: .contain)
    }

    private var chartModePicker: some View {
        Picker(L("Volume chart"), selection: $volumeChartMode) {
            ForEach(VolumeChartMode.allCases) { mode in
                Text(L(mode.rawValue))
                    .tag(mode)
                    .accessibilityLabel(mode.accessibilityTitle)
                    .accessibilityIdentifier("volume.mode.\(mode == .weekDays ? "days" : "trend")")
            }
        }
        .pickerStyle(.segmented)
        .fixedSize()
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
                        .font(UH.TextStyle.eyebrow.monospacedDigit())
                        .foregroundStyle(day.color)
                } else if day.isRest {
                    Text("–")
                        .font(UH.TextStyle.caption.monospacedDigit())
                        .foregroundStyle(UH.Palette.muted)
                }
            }
        }
        .frame(height: 54)
        .chartXAxis {
            AxisMarks(values: .automatic) { value in
                AxisValueLabel {
                    if let raw = value.as(String.self), let wd = Weekday(rawValue: raw) {
                        Text(AppLanguage.current == .vi ? L(String(wd.rawValue.prefix(3))) : String(wd.rawValue.prefix(1)))
                            .font(UH.TextStyle.eyebrow.monospacedDigit())
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
                            .font(UH.TextStyle.eyebrow.monospacedDigit())
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
        }
        .chartYAxis(.hidden)
        .accessibilityLabel("Weekly volume trend")
    }

    // MARK: - Goal Progress Card

    func goalProgressCard(_ progress: GoalProgress) -> some View {
        Button(action: onGoal) {
            card(
                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        eyebrow(L("Goal progress"))
                        Spacer()
                        if let pill = model.goalPillText {
                            Text(verbatim: pill)
                                .font(UH.TextStyle.eyebrow.monospacedDigit())
                                .foregroundStyle(goalTint)
                                .padding(.horizontal, 7)
                                .padding(.vertical, 3)
                                .background(UH.Palette.hover, in: Capsule())
                        }
                    }
                    if let hours = model.goal?.targetTimeHours {
                        HStack(alignment: .firstTextBaseline, spacing: 6) {
                            Text(verbatim: PlanViewModel.formatMinutes(hours * 60))
                                .font(UH.TextStyle.metric.monospacedDigit())
                                .foregroundStyle(UH.Palette.ink)
                            Text("target").font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    if let tiers = model.goal?.assessment?.goals {
                        HStack(spacing: 6) {
                            tierChip("A", L("Ambitious"), tiers.a)
                            tierChip("B", L("Realistic"), tiers.b)
                            tierChip("C", L("Safe"), tiers.c)
                        }
                    }
                    Spacer(minLength: 0)
                    if let bar = progress.longRun {
                        progressRow(L("Longest run"), bar, L("%@ of %@", PlanViewModel.formatMinutes(bar.done), PlanViewModel.formatMinutes(bar.target)))
                    }
                }
            )
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("plan.goalProgress")
    }

    private var goalTint: Color {
        model.goalIsOutOfReach ? UH.Palette.danger : model.goal?.status.kind == .behind ? UH.Palette.warningInk : UH.Palette.accentInk
    }

    /// The tier the target matches is filled; the others are outlined.
    private func tierChip(_ tier: String, _ name: String, _ minutes: Double) -> some View {
        let target = model.goal?.targetTimeHours.map { Int(($0 * 60).rounded()) }
        let active = model.goal?.status.tier?.uppercased() == tier || target == Int(minutes.rounded())
        return VStack(spacing: 1) {
            Text(verbatim: name).font(UH.TextStyle.eyebrow)
            Text(verbatim: PlanViewModel.formatMinutes(minutes)).font(UH.TextStyle.disclosure.monospacedDigit())
        }
            .foregroundStyle(active ? UH.Palette.accentInk : UH.Palette.secondary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
            .background(active ? UH.Palette.activeFill : .clear, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(active ? UH.Palette.accentInk.opacity(0.4) : UH.Palette.line))
    }

    private func progressRow(_ title: String, _ bar: GoalProgress.Bar, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(verbatim: title).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.ink)
                Spacer()
                Text(verbatim: value).font(UH.TextStyle.caption.monospacedDigit()).foregroundStyle(UH.Palette.secondary)
            }
            GeometryReader { proxy in
                ZStack(alignment: .leading) {
                    Capsule().fill(UH.Palette.line)
                    Capsule().fill(UH.Palette.accent).frame(width: max(proxy.size.width * bar.fraction, 4))
                }
            }
            .frame(height: 5)
        }
    }

}

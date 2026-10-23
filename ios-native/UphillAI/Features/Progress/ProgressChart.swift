import Charts
import SwiftUI

/// One chart for every card: bars for weekly counts, a line for daily values, and the athlete's
/// usual range as a pale emerald band. Compact on the summary card, with axes on the detail screen.
struct ProgressChart: View {
    let card: ProgressCard
    var detailed = false
    /// A day to show selected on appear (screenshot tests).
    var initialSelection: Date?

    /// Drag on the detail chart to read one day or week; the compact card chart stays a tap target.
    @State private var selectedDate: Date?
    @State private var selectedWeek: String?

    private var points: [ProgressPoint] { card.points }
    private var selected: ProgressPoint? {
        if let selectedDate {
            return points.min { a, b in
                guard case .day(let da) = a.x, case .day(let db) = b.x else { return false }
                return abs(da.timeIntervalSince(selectedDate)) < abs(db.timeIntervalSince(selectedDate))
            }
        }
        guard let selectedWeek else { return nil }
        return points.first { if case .week(let w) = $0.x { "W\(w)" == selectedWeek } else { false } }
    }
    private var usesBars: Bool { ["consistency", "volume", "load", "sleep"].contains(card.key) }
    /// Load's story is the last week against the weeks before it.
    private func emphasis(_ point: ProgressPoint) -> Double {
        guard card.key == "load", case .day(let date) = point.x, let last = points.last, case .day(let end) = last.x else { return 1 }
        return end.timeIntervalSince(date) < 7 * 86_400 ? 1 : 0.35
    }
    /// What the plan asked for, drawn faded behind the actual bar (Volume km, Consistency sessions).
    private func planned(_ point: ProgressPoint) -> Double? {
        (point.row["km_planned"] ?? point.row["planned"])?.doubleValue
    }

    var body: some View {
        Chart {
            if let band = card.band, band.count == 2 {
                RectangleMark(yStart: .value("Low", band[0]), yEnd: .value("High", band[1]))
                    .foregroundStyle(UH.Palette.accent.opacity(0.14))
            }
            ForEach(points) { point in
                switch point.x {
                case .day(let date):
                    if usesBars {
                        BarMark(x: .value("Date", date, unit: .day), y: .value("Value", point.y))
                            .foregroundStyle(UH.Palette.accent.opacity(emphasis(point)))
                    } else {
                        LineMark(x: .value("Date", date, unit: .day), y: .value("Value", point.y))
                            .foregroundStyle(UH.Palette.accent)
                            .interpolationMethod(.linear)  // never invent shape between a few points
                        PointMark(x: .value("Date", date, unit: .day), y: .value("Value", point.y))
                            .foregroundStyle(UH.Palette.accent)
                            .symbolSize(detailed ? 24 : 12)
                    }
                case .week(let week):
                    if usesBars {
                        if let target = planned(point) {
                            BarMark(x: .value("Week", "W\(week)"), y: .value("Value", target), stacking: .unstacked)
                                .foregroundStyle(UH.Palette.accent.opacity(0.22))
                        }
                        BarMark(x: .value("Week", "W\(week)"), y: .value("Value", point.y), stacking: .unstacked)
                            .foregroundStyle(UH.Palette.accent)
                    } else {
                        // Aerobic speed moves a few percent: a line on a fitted scale shows it, bars from zero hide it.
                        LineMark(x: .value("Week", "W\(week)"), y: .value("Value", point.y))
                            .foregroundStyle(UH.Palette.accent)
                        PointMark(x: .value("Week", "W\(week)"), y: .value("Value", point.y))
                            .foregroundStyle(UH.Palette.accent)
                    }
                }
            }
            if let selected {
                switch selected.x {
                case .day(let date):
                    RuleMark(x: .value("Date", date, unit: .day))
                        .foregroundStyle(UH.Palette.muted.opacity(0.5))
                        .annotation(position: .top, overflowResolution: .init(x: .fit(to: .chart), y: .disabled)) {
                            ChartCallout(value: ProgressText.pointValue(card, selected.y),
                                         label: date.formatted(.dateTime.day().month(.abbreviated).locale(AppLanguage.current.locale)))
                        }
                case .week(let week):
                    RuleMark(x: .value("Week", "W\(week)"))
                        .foregroundStyle(UH.Palette.muted.opacity(0.5))
                        .annotation(position: .top, overflowResolution: .init(x: .fit(to: .chart), y: .disabled)) {
                            ChartCallout(value: ProgressText.pointValue(card, selected.y), label: L("Week %lld", week))
                        }
                }
            }
        }
        .chartYScale(domain: .automatic(includesZero: usesBars))
        .chartXAxis(detailed ? .automatic : .hidden)
        .chartYAxis(detailed ? .automatic : .hidden)
        .modifier(ChartSelection(enabled: detailed, weekly: points.first.map { if case .week = $0.x { true } else { false } } ?? false,
                                 date: $selectedDate, week: $selectedWeek))
        .sensoryFeedback(.selection, trigger: selected?.id)
        .onAppear { if let initialSelection { selectedDate = initialSelection } }
        .frame(height: detailed ? 220 : 64)
        .accessibilityChartDescriptor(ProgressChartDescriptor(card: card))
    }
}

/// Scrubbing on the detail charts only. Weekly charts select by their "W3" category, daily ones by date.
struct ChartSelection: ViewModifier {
    let enabled: Bool
    var weekly = false
    @Binding var date: Date?
    @Binding var week: String?

    func body(content: Content) -> some View {
        if !enabled {
            content
        } else if weekly {
            content.chartXSelection(value: $week)
        } else {
            content.chartXSelection(value: $date)
        }
    }
}

/// The value under the finger: the number first, then the day or week it belongs to.
struct ChartCallout: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 2) {
            Text(value).font(.system(.subheadline, design: .rounded).weight(.semibold).monospacedDigit())
                .foregroundStyle(UH.Palette.ink)
            Text(label).font(.caption2).foregroundStyle(UH.Palette.muted)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
    }
}

struct ProgressChartDescriptor: AXChartDescriptorRepresentable {
    let card: ProgressCard

    func makeChartDescriptor() -> AXChartDescriptor {
        let values = card.points.map(\.y)
        let x = AXCategoricalDataAxisDescriptor(title: card.points.first.map { if case .week = $0.x { L("Week") } else { L("Day") } } ?? L("Day"), categoryOrder: card.points.indices.map { "\($0 + 1)" })
        let y = AXNumericDataAxisDescriptor(
            title: ProgressText.title(card.key), range: (values.min() ?? 0)...(values.max() ?? 1), gridlinePositions: []
        ) { "\($0.formatted(.number.precision(.fractionLength(0...1))))" }
        let series = AXDataSeriesDescriptor(
            name: ProgressText.title(card.key), isContinuous: true,
            dataPoints: card.points.enumerated().map { .init(x: "\($0.offset + 1)", y: $0.element.y) }
        )
        return AXChartDescriptor(title: ProgressText.title(card.key), summary: ProgressText.note(card),
                                 xAxis: x, yAxis: y, additionalAxes: [], series: [series])
    }
}

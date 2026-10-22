import Charts
import SwiftUI

/// One chart for every card: bars for weekly counts, a line for daily values, and the athlete's
/// usual range as a pale emerald band. Compact on the summary card, with axes on the detail screen.
struct ProgressChart: View {
    let card: ProgressCard
    var detailed = false

    private var points: [ProgressPoint] { card.points }
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
        }
        .chartYScale(domain: .automatic(includesZero: usesBars))
        .chartXAxis(detailed ? .automatic : .hidden)
        .chartYAxis(detailed ? .automatic : .hidden)
        .frame(height: detailed ? 220 : 64)
        .accessibilityChartDescriptor(ProgressChartDescriptor(card: card))
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

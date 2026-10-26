import Charts
import SwiftUI

/// The Training response card: this week's HRV and resting HR against the four weeks before, read
/// against the plan's phase (backend progress_cards.training_response). The map puts the week on two
/// axes -- right is HRV above usual, up is resting HR below usual -- and shades where this phase should land.
struct TrainingResponseCardView: View {
    let card: ProgressCard

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label(ProgressText.title(card.key), systemImage: ProgressText.symbol(card.key))
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
                Spacer()
                if let phase = TrainingResponse.phaseLine(card) {
                    Text(phase).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                }
                Image(systemName: "chevron.right")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(.tertiary)
                    .accessibilityHidden(true)
            }
            Text(TrainingResponse.headline(card))
                .font(.system(.title2, design: .rounded).weight(.semibold))
                .foregroundStyle(TrainingResponse.isExpected(card) ? UH.Palette.ink : UH.Palette.warningInk)
            Text(TrainingResponse.takeaway(card))
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)
            ResponseMap(card: card)
                .frame(height: 150)
            SignalRow(card: card)
        }
        .uhCard()
        .accessibilityElement(children: .combine)
    }
}

/// Both signals as chips: the change, coloured by what it means (better / worse), never by direction alone.
struct SignalRow: View {
    let card: ProgressCard

    var body: some View {
        HStack(spacing: UH.Space.compact) {
            chip(L("HRV"), TrainingResponse.hrvText(card), good: (card.noteNumber("hrv_z") ?? 0) >= 0)
            chip(L("Resting HR"), TrainingResponse.rhrText(card), good: (card.noteNumber("rhr_z") ?? 0) <= 0)
        }
    }

    private func chip(_ name: String, _ value: String, good: Bool) -> some View {
        HStack(spacing: 4) {
            Text(name).foregroundStyle(UH.Palette.secondary)
            Text(value).monospacedDigit().foregroundStyle(good ? UH.Palette.accentInk : UH.Palette.warningInk)
        }
        .font(UH.TextStyle.caption.weight(.semibold))
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(UH.Palette.tint, in: Capsule())
    }
}

/// Two axes in baseline spreads, clamped to ±3: x = HRV shift, y = minus resting-HR shift (up = better).
struct ResponseMap: View {
    let card: ProgressCard
    private let limit = 3.0

    var body: some View {
        GeometryReader { geo in
            let size = geo.size
            let x = { (v: Double) in (min(max(v, -limit), limit) + limit) / (2 * limit) * size.width }
            let y = { (v: Double) in (1 - (min(max(v, -limit), limit) + limit) / (2 * limit)) * size.height }
            let zone = TrainingResponse.expectedZone(card)
            let hrv = card.noteNumber("hrv_z") ?? 0
            let rhr = -(card.noteNumber("rhr_z") ?? 0)
            ZStack(alignment: .topLeading) {
                RoundedRectangle(cornerRadius: UH.Radius.control).fill(UH.Palette.tint)
                // Where this phase should land.
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .fill(UH.Palette.accent.opacity(0.18))
                    .frame(width: x(zone.maxX) - x(zone.minX), height: y(zone.minY) - y(zone.maxY))
                    .offset(x: x(zone.minX), y: y(zone.maxY))
                Text(L("Expected for %@", TrainingResponse.phase(card)))
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(6)
                    .offset(x: x(zone.minX), y: y(zone.maxY))
                // Your usual: the crosshair.
                Path { p in
                    p.move(to: CGPoint(x: x(0), y: 0)); p.addLine(to: CGPoint(x: x(0), y: size.height))
                    p.move(to: CGPoint(x: 0, y: y(0))); p.addLine(to: CGPoint(x: size.width, y: y(0)))
                }
                .stroke(UH.Palette.line, style: StrokeStyle(lineWidth: 1, dash: [3, 3]))
                corner(L("Absorbing"), .topTrailing, size)
                corner(L("Under load"), .bottomLeading, size)
                Circle()
                    .fill(TrainingResponse.isExpected(card) ? UH.Palette.accent : Color(hex: "#f59e0b"))
                    .overlay(Circle().stroke(UH.Palette.card, lineWidth: 3))
                    .frame(width: 18, height: 18)
                    .offset(x: x(hrv) - 9, y: y(rhr) - 9)
            }
        }
        .overlay(alignment: .bottom) {
            Text(L("→ HRV above usual   ↑ resting HR below usual"))
                .font(.caption2)
                .foregroundStyle(UH.Palette.muted)
                .offset(y: 18)
        }
        .padding(.bottom, 18)
        .accessibilityElement()
        .accessibilityLabel(L("This week against your usual"))
        .accessibilityValue("\(TrainingResponse.hrvText(card)), \(TrainingResponse.rhrText(card))")
    }

    private func corner(_ text: String, _ alignment: Alignment, _ size: CGSize) -> some View {
        Text(text)
            .font(.caption2)
            .foregroundStyle(UH.Palette.muted)
            .padding(6)
            .frame(width: size.width, height: size.height, alignment: alignment)
    }
}

/// The detail screen: a bigger map, then each signal's daily line on its usual band, with the plan's
/// phases as a strip so the athlete sees which weeks were loading weeks.
struct TrainingResponseDetailView: View {
    let card: ProgressCard

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text(TrainingResponse.headline(card))
                        .font(.system(.title, design: .rounded).weight(.semibold))
                        .foregroundStyle(TrainingResponse.isExpected(card) ? UH.Palette.ink : UH.Palette.warningInk)
                    Text(TrainingResponse.takeaway(card)).foregroundStyle(UH.Palette.secondary)
                    ResponseMap(card: card).frame(height: 230)
                    SignalRow(card: card)
                }
                .uhCard()
                SignalChart(title: L("HRV"), unit: "ms", days: days("hrv"), band: card.band)
                SignalChart(title: L("Resting HR"), unit: "bpm", days: days("rhr"),
                            band: card.note["rhr_band"]?.arrayValue?.compactMap(\.doubleValue))
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text(L("What this means")).font(UH.TextStyle.sectionTitle)
                    Text(ProgressText.explanation(card.key)).foregroundStyle(UH.Palette.secondary)
                    if let source = card.source {
                        Text(L("Source: %@", deviceSourceName(source)))
                            .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                    }
                }
            }
            .padding(UH.Space.regular)
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(ProgressText.title(card.key))
        .navigationBarTitleDisplayMode(.inline)
    }

    private func days(_ field: String) -> [SignalChart.Day] {
        card.series.compactMap { row in
            guard let s = row["date"]?.stringValue, let date = ProgressPoint.day.date(from: s) else { return nil }
            return SignalChart.Day(date: date, value: row[field]?.doubleValue, phase: row["phase"]?.stringValue ?? "")
        }
    }
}

/// One signal's daily line on its usual band, this week shaded, the plan's phases underneath.
/// Drag to read a day: a rule, the value and the phase that day belonged to.
struct SignalChart: View {
    struct Day: Identifiable {
        let date: Date
        let value: Double?
        let phase: String
        var id: Date { date }
    }

    let title: String
    let unit: String
    let days: [Day]
    let band: [Double]?
    /// A day to show selected on appear (screenshot tests).
    var initialSelection: Date?

    @State private var selectedDate: Date?

    private var selected: Day? {
        guard let selectedDate else { return nil }
        return days.filter { $0.value != nil }.min {
            abs($0.date.timeIntervalSince(selectedDate)) < abs($1.date.timeIntervalSince(selectedDate))
        }
    }

    var body: some View {
        let rows = days
        let thisWeek = rows.last.map { Calendar(identifier: .gregorian).date(byAdding: .day, value: -6, to: $0.date)! }
        return VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("\(title) · \(unit)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
            Chart {
                if let band, band.count == 2 {
                    RectangleMark(yStart: .value("Low", band[0]), yEnd: .value("High", band[1]))
                        .foregroundStyle(UH.Palette.accent.opacity(0.14))
                }
                if let thisWeek, let last = rows.last {
                    RectangleMark(xStart: .value("From", thisWeek, unit: .day), xEnd: .value("To", last.date, unit: .day))
                        .foregroundStyle(UH.Palette.tint)
                        .annotation(position: .top, alignment: .leading) {
                            Text(L("This week")).font(.caption2).foregroundStyle(UH.Palette.muted)
                        }
                }
                ForEach(rows.filter { $0.value != nil }) { day in
                    LineMark(x: .value("Date", day.date, unit: .day), y: .value(title, day.value!))
                        .foregroundStyle(UH.Palette.accent)
                        .interpolationMethod(.linear)
                    PointMark(x: .value("Date", day.date, unit: .day), y: .value(title, day.value!))
                        .foregroundStyle(UH.Palette.accent)
                        .symbolSize(18)
                }
                if let selected, let value = selected.value {
                    RuleMark(x: .value("Date", selected.date, unit: .day))
                        .foregroundStyle(UH.Palette.muted.opacity(0.5))
                        .annotation(position: .top, overflowResolution: .init(x: .fit(to: .chart), y: .disabled)) {
                            ChartCallout(
                                value: "\(Int(value.rounded())) \(unit)",
                                label: [selected.date.formatted(.dateTime.day().month(.abbreviated).locale(AppLanguage.current.locale)),
                                        selected.phase].filter { !$0.isEmpty }.joined(separator: " · "))
                        }
                }
            }
            .chartYScale(domain: .automatic(includesZero: false))
            .chartXSelection(value: $selectedDate)
            .sensoryFeedback(.selection, trigger: selected?.id)
            .onAppear { if let initialSelection { selectedDate = initialSelection } }
            .frame(height: 160)
            PhaseStrip(days: rows.map { ($0.date, $0.phase) })
        }
        .uhCard()
    }
}

/// One thin band per day, darker for loading phases, so the chart above reads against the plan.
struct PhaseStrip: View {
    let days: [(Date, String)]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 1) {
                ForEach(Array(days.enumerated()), id: \.offset) { _, day in
                    Rectangle().fill(TrainingResponse.phaseColor(day.1))
                }
            }
            .frame(height: 8)
            .clipShape(Capsule())
            let runs = TrainingResponse.phaseRuns(days.map(\.1))
            HStack {
                ForEach(Array(runs.enumerated()), id: \.offset) { i, name in
                    Text(name).font(.caption2).foregroundStyle(UH.Palette.muted)
                    if i < runs.count - 1 { Spacer() }
                }
            }
        }
        .accessibilityElement()
        .accessibilityLabel(L("Plan phases: %@", TrainingResponse.phaseRuns(days.map(\.1)).joined(separator: ", ")))
    }
}

/// The card's wording and geometry. Phase names stay English, like the rest of the app (CoachSignalText).
enum TrainingResponse {
    static func state(_ card: ProgressCard) -> String { card.noteKey.split(separator: ".").last.map(String.init) ?? "" }
    static func isLight(_ card: ProgressCard) -> Bool { card.noteKey.hasPrefix("response.down") }
    static func phase(_ card: ProgressCard) -> String { card.noteString("phase") ?? "" }

    static func phaseLine(_ card: ProgressCard) -> String? {
        guard let week = card.noteNumber("week") else { return nil }
        return L("%@ · week %lld", phase(card), Int(week))
    }

    /// Heavy weeks may feel heavy; light weeks should lift. Only the two mismatches read as a warning.
    static func isExpected(_ card: ProgressCard) -> Bool {
        isLight(card) ? ["adapting", "steady"].contains(state(card)) : state(card) != "strained"
    }

    static func headline(_ card: ProgressCard) -> String {
        switch (isLight(card), state(card)) {
        case (false, "adapting"): L("Absorbing the work")
        case (false, "steady"): L("Holding steady")
        case (false, "loading"): L("Feeling the load, as planned")
        case (false, "strained"): L("Well outside your usual")
        case (true, "adapting"): L("Rebounding")
        case (true, "steady"): L("Not rebounding yet")
        default: L("Still under strain")
        }
    }

    static func takeaway(_ card: ProgressCard) -> String {
        let p = phase(card)
        switch (isLight(card), state(card)) {
        case (false, "adapting"):
            return L("HRV is up and resting HR is down in a %@ phase: you're adapting to the work. Keep building as planned.", p)
        case (false, "steady"):
            return L("Your body is handling this %@ phase without strain. Stick to the plan.", p)
        case (false, "loading"):
            return L("Expected in a %@ phase. Keep easy days truly easy and protect your sleep so you bounce back in the next lighter week.", p)
        case (false, "strained"):
            return L("HRV and resting HR are both well outside your usual. Make the next session easy and look at sleep and stress before pushing on.")
        case (true, "adapting"):
            return L("HRV is up and resting HR is down in this %@ week: the hard weeks are turning into fitness.", p)
        case (true, "steady"):
            return L("This %@ week hasn't lifted your numbers yet. That often comes late in the week; keep the easy days easy.", p)
        default:
            return L("Your numbers are down in a lighter week, so training is unlikely to be the cause. Look at sleep, stress and travel.")
        }
    }

    static func hrvText(_ card: ProgressCard) -> String {
        let pct = Int(card.noteNumber("hrv_pct") ?? 0)
        return pct == 0 ? L("at usual") : String(format: "%+d%%", pct)
    }

    static func rhrText(_ card: ProgressCard) -> String {
        let delta = Int(card.noteNumber("rhr_delta") ?? 0)
        return delta == 0 ? L("at usual") : L("%@ bpm", String(format: "%+d", delta))
    }

    /// Map coordinates (x = HRV shift, y = resting-HR shift with up = lower) of where the phase should land:
    /// loading phases from a little worse to a little better than usual; light phases at usual or better.
    static func expectedZone(_ card: ProgressCard) -> (minX: Double, maxX: Double, minY: Double, maxY: Double) {
        isLight(card) ? (-0.5, 3, -0.5, 3) : (-1.5, 1, -1.5, 1)
    }

    static func phaseColor(_ phase: String) -> Color {
        switch phase {
        case "Peak": UH.Palette.accentInk
        case "Build": UH.Palette.accent
        case "Base": UH.Palette.accent.opacity(0.5)
        default: UH.Palette.line
        }
    }

    /// Phase names in order, each once per run: ["Base", "Build", "Recovery", "Build"].
    static func phaseRuns(_ phases: [String]) -> [String] {
        phases.reduce(into: []) { runs, p in if !p.isEmpty && runs.last != p { runs.append(p) } }
    }
}

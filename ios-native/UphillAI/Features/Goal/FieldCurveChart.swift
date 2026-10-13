import SwiftUI
import Charts

struct FieldCurvePoint: Identifiable {
    var id: Double { minutes }
    let minutes: Double
    let percentile: Double
    let label: String
}

struct GoalMarkerPoint: Identifiable {
    var id: String { label }
    let label: String
    let minutes: Double
    let percentile: Double
    let color: Color
}

struct FieldCurveChart: View {
    let benchmarks: [RaceBenchmark]
    let goals: GoalEstimateTiers?

    @State private var selectedYear: Int? = nil // nil means All/Avg
    @State private var selectedGender: String = "overall" // overall, men, women
    @State private var touchedMinutes: Double? = nil
    @State private var chartHeight: CGFloat = 300

    private var availableYears: [Int] {
        Array(Set(benchmarks.map { $0.year })).sorted(by: >)
    }

    private var activeBenchmark: RaceBenchmark? {
        if let year = selectedYear {
            return benchmarks.first { $0.year == year }
        }
        return benchmarks.first
    }

    private var finisherCount: Int? {
        guard let bench = activeBenchmark else { return nil }
        switch selectedGender {
        case "men": return bench.finishersMen ?? bench.finishers
        case "women": return bench.finishersWomen ?? bench.finishers
        default: return bench.finishers
        }
    }

    private var winnerTime: String? {
        guard let bench = activeBenchmark else { return nil }
        return selectedGender == "women" ? (bench.winnerTimeWomen ?? bench.winnerTime) : bench.winnerTime
    }

    /// Ranked top-N times ("top3", "top10"…) for the selected group, fastest first.
    private var topTimes: [(rank: Int, time: String)] {
        let dict = activeBenchmark?.topTimes?[selectedGender] ?? [:]
        return dict.compactMap { key, value in
            Int(key.replacingOccurrences(of: "top", with: "")).map { (rank: $0, time: value) }
        }.sorted { $0.rank < $1.rank }
    }

    /// Verified anchors only (winner, top-N ranks, percentiles), joined with straight lines.
    private var curvePoints: [FieldCurvePoint] {
        guard activeBenchmark != nil else { return [] }
        let percentilesDict = activeBenchmark?.percentiles?[selectedGender] ?? activeBenchmark?.percentiles?["overall"]
        var raw: [FieldCurvePoint] = []
        if let winnerTime, let m = GoalEstimate.parseTimeToMinutes(winnerTime) {
            raw.append(FieldCurvePoint(minutes: m, percentile: finisherCount.map { 100.0 / Double($0) } ?? 0, label: L("Winner")))
        }
        if let n = finisherCount, n > 0 {
            for t in topTimes where t.rank > 1 {
                if let m = GoalEstimate.parseTimeToMinutes(t.time) {
                    raw.append(FieldCurvePoint(minutes: m, percentile: 100.0 * Double(t.rank) / Double(n), label: L("Top %lld", t.rank)))
                }
            }
        }
        let pcts: [(String?, Double)] = [(percentilesDict?.p5, 5), (percentilesDict?.p10, 10), (percentilesDict?.p25, 25),
                                         (percentilesDict?.p50, 50), (percentilesDict?.p75, 75), (percentilesDict?.p90, 90)]
        for (time, q) in pcts {
            if let time, let m = GoalEstimate.parseTimeToMinutes(time) {
                raw.append(FieldCurvePoint(minutes: m, percentile: q, label: L("Top %lld%%", Int(q))))
            }
        }
        var anchors: [FieldCurvePoint] = []
        for pt in raw.sorted(by: { $0.percentile < $1.percentile }) {
            if let prev = anchors.last, !(pt.percentile > prev.percentile && pt.minutes > prev.minutes) { continue }
            anchors.append(pt)
        }
        return anchors
    }

    private var goalMarkers: [GoalMarkerPoint] {
        guard let goals, !curvePoints.isEmpty else { return [] }
        var markers: [GoalMarkerPoint] = []

        let tiers: [(String, Double, Color)] = [
            ("A", goals.ambitious, Color(hex: "#10b981")),
            ("B", goals.realistic, UH.Palette.accentInk),
            ("C", goals.safe, Color(hex: "#f59e0b"))
        ]

        for (lbl, mins, col) in tiers {
            let pct = interpolatePercentile(mins: mins)
            markers.append(GoalMarkerPoint(label: lbl, minutes: mins, percentile: pct, color: col))
        }

        return markers
    }

    private func interpolatePercentile(mins: Double) -> Double {
        guard let first = curvePoints.first else { return 50.0 }
        guard let last = curvePoints.last else { return 50.0 }

        if mins <= first.minutes { return first.percentile }
        if mins >= last.minutes { return min(99.0, last.percentile + 5.0) }

        for i in 0..<(curvePoints.count - 1) {
            let p1 = curvePoints[i]
            let p2 = curvePoints[i + 1]
            if mins >= p1.minutes && mins <= p2.minutes {
                let fraction = (mins - p1.minutes) / (p2.minutes - p1.minutes)
                return p1.percentile + fraction * (p2.percentile - p1.percentile)
            }
        }
        return 50.0
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with filters
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("FIELD DISTRIBUTION (CDF)")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.muted)
                    Text("Finishers Field Curve")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                }

                Spacer()

                // Year selector
                if availableYears.count > 1 {
                    Menu {
                        Button("All Years") { selectedYear = nil }
                        ForEach(availableYears, id: \.self) { y in
                            Button("\(y)") { selectedYear = y }
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Text(selectedYear.map(String.init) ?? L("All Years"))
                                .font(UH.TextStyle.caption.weight(.bold))
                            Image(systemName: "chevron.down")
                                .font(.system(size: 10))
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(UH.Palette.card, in: Capsule())
                        .overlay(Capsule().stroke(UH.Palette.line))
                    }
                }
            }

            // Gender Segmented Picker
            Picker("Gender", selection: $selectedGender) {
                Text("Overall").tag("overall")
                Text("Men").tag("men")
                Text("Women").tag("women")
            }
            .pickerStyle(.segmented)

            // Swift Chart
            if !curvePoints.isEmpty {
                Chart {
                    // Fill area under curve
                    ForEach(curvePoints) { pt in
                        AreaMark(
                            x: .value("Time (mins)", pt.minutes),
                            y: .value("Percentile", pt.percentile)
                        )
                        .foregroundStyle(
                            LinearGradient(
                                colors: [UH.Palette.accentInk.opacity(0.18), UH.Palette.accentInk.opacity(0.02)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                    }

                    // Line curve
                    ForEach(curvePoints) { pt in
                        LineMark(
                            x: .value("Time (mins)", pt.minutes),
                            y: .value("Percentile", pt.percentile)
                        )
                        .foregroundStyle(UH.Palette.accentInk)
                        .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round, lineJoin: .round))

                        PointMark(
                            x: .value("Time (mins)", pt.minutes),
                            y: .value("Percentile", pt.percentile)
                        )
                        .foregroundStyle(UH.Palette.ink)
                        .symbolSize(30)
                    }

                    if let touched = touchedMinutes, let first = curvePoints.first, let last = curvePoints.last,
                       touched >= first.minutes, touched <= last.minutes {
                        let pct = interpolatePercentile(mins: touched)
                        RuleMark(x: .value("Selected", touched))
                            .foregroundStyle(UH.Palette.ink.opacity(0.35))
                            .lineStyle(StrokeStyle(lineWidth: 1))
                            .annotation(position: .top, overflowResolution: .init(x: .fit(to: .chart), y: .disabled)) {
                                VStack(spacing: 1) {
                                    Text(GoalEstimate.formatMinutes(touched))
                                        .font(.system(size: 13, weight: .bold, design: .monospaced))
                                    Text(L("top %@%%", pct < 5 ? String(format: "%.1f", pct) : String(Int(pct.rounded()))))
                                        .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                .padding(.horizontal, 8).padding(.vertical, 4)
                                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: 6))
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(UH.Palette.line))
                            }
                        PointMark(x: .value("Selected", touched), y: .value("Pct", pct))
                            .foregroundStyle(UH.Palette.ink)
                            .symbolSize(60)
                    }

                    // Goal Markers (A, B, C)
                    ForEach(goalMarkers) { m in
                        RuleMark(x: .value("Goal Time", m.minutes))
                            .foregroundStyle(m.color.opacity(0.6))
                            .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [4, 4]))

                        PointMark(
                            x: .value("Goal Time", m.minutes),
                            y: .value("Goal Pct", m.percentile)
                        )
                        .foregroundStyle(m.color)
                        .symbolSize(80)
                        .annotation(position: .top) {
                            Text("\(m.label): top \(Int(m.percentile))%")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 4)
                                .padding(.vertical, 2)
                                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: 4))
                                .overlay(RoundedRectangle(cornerRadius: 4).stroke(m.color, lineWidth: 1))
                        }
                    }
                }
                .chartXSelection(value: $touchedMinutes)
                .chartYScale(domain: 0...100)
                .chartYAxis {
                    AxisMarks(values: [0, 25, 50, 75, 100]) { value in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [2, 2]))
                            .foregroundStyle(UH.Palette.line)
                        AxisValueLabel {
                            if let intVal = value.as(Int.self) {
                                Text("\(intVal)%")
                                    .font(.system(size: 9.5, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                        }
                    }
                }
                .chartXAxis {
                    AxisMarks { value in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [2, 2]))
                            .foregroundStyle(UH.Palette.line)
                        AxisValueLabel {
                            if let mins = value.as(Double.self) {
                                Text(GoalEstimate.formatMinutes(mins))
                                    .font(.system(size: 9.5, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                        }
                    }
                }
                .frame(height: chartHeight)
                .sensoryFeedback(.selection, trigger: touchedMinutes.map { Int($0 / 5) })
                .padding(.vertical, 8)

                Text("Drag across the chart to read any finish time.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)

                podiumStrip

                // Legend
                HStack(spacing: 14) {
                    legendItem(color: Color(hex: "#10b981"), label: L("A: Ambitious"))
                    legendItem(color: UH.Palette.accentInk, label: L("B: Realistic"))
                    legendItem(color: Color(hex: "#f59e0b"), label: L("C: Safe"))
                    Spacer()
                    Text("UTMB verified")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                }
            } else {
                Text("No verified benchmark field data available for this race.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, UH.Space.regular)
            }
        }
        .trainingCard()
    }

    /// Reference times: winner and ranked top-N finishes for the selected group.
    @ViewBuilder private var podiumStrip: some View {
        let rows: [(String, String)] = (winnerTime.map { [(L("Winner"), $0)] } ?? [])
            + topTimes.filter { $0.rank > 1 }.map { (L("Top %lld", $0.rank), $0.time) }
        if !rows.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("PODIUM & TOP TIMES")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Spacer()
                    if let n = finisherCount {
                        Text(L("%lld finishers", n))
                            .font(.system(size: 10, weight: .semibold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                    }
                }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 92), spacing: 8)], spacing: 8) {
                    ForEach(Array(rows.enumerated()), id: \.offset) { index, row in
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 4) {
                                if index == 0 && winnerTime != nil {
                                    Image(systemName: "trophy.fill").font(.system(size: 10)).foregroundStyle(Color(hex: "#d4a017"))
                                }
                                Text(row.0)
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Text(row.1)
                                .font(.system(size: 15, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                }
            }
        }
    }

    private func legendItem(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(label)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
    }
}

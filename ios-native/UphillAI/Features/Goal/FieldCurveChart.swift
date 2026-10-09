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

    private var availableYears: [Int] {
        Array(Set(benchmarks.map { $0.year })).sorted(by: >)
    }

    private var activeBenchmark: RaceBenchmark? {
        if let year = selectedYear {
            return benchmarks.first { $0.year == year }
        }
        return benchmarks.first
    }

    private var curvePoints: [FieldCurvePoint] {
        guard let bench = activeBenchmark,
              let percentilesDict = bench.percentiles?[selectedGender] ?? bench.percentiles?["overall"] else {
            return []
        }

        var points: [FieldCurvePoint] = []

        // Winner time anchor (approx 0.1 percentile)
        let winnerTimeStr = selectedGender == "women" ? (bench.winnerTimeWomen ?? bench.winnerTime) : bench.winnerTime
        if let winnerTimeStr, let winnerMins = GoalEstimate.parseTimeToMinutes(winnerTimeStr) {
            points.append(FieldCurvePoint(minutes: winnerMins, percentile: 0.2, label: L("Winner")))
        }

        if let p5 = percentilesDict.p5, let m = GoalEstimate.parseTimeToMinutes(p5) {
            points.append(FieldCurvePoint(minutes: m, percentile: 5.0, label: L("Top 5%")))
        }
        if let p10 = percentilesDict.p10, let m = GoalEstimate.parseTimeToMinutes(p10) {
            points.append(FieldCurvePoint(minutes: m, percentile: 10.0, label: L("Top 10%")))
        }
        if let p25 = percentilesDict.p25, let m = GoalEstimate.parseTimeToMinutes(p25) {
            points.append(FieldCurvePoint(minutes: m, percentile: 25.0, label: L("Top 25%")))
        }
        if let p50 = percentilesDict.p50, let m = GoalEstimate.parseTimeToMinutes(p50) {
            points.append(FieldCurvePoint(minutes: m, percentile: 50.0, label: L("Median (50%)")))
        }
        if let p75 = percentilesDict.p75, let m = GoalEstimate.parseTimeToMinutes(p75) {
            points.append(FieldCurvePoint(minutes: m, percentile: 75.0, label: L("Top 75%")))
        }
        if let p90 = percentilesDict.p90, let m = GoalEstimate.parseTimeToMinutes(p90) {
            points.append(FieldCurvePoint(minutes: m, percentile: 90.0, label: L("Top 90%")))
        }

        return points.sorted(by: { $0.minutes < $1.minutes })
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
                .frame(height: 220)
                .padding(.vertical, 8)

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

    private func legendItem(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 7, height: 7)
            Text(label)
                .font(.system(size: 10, weight: .medium, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
    }
}

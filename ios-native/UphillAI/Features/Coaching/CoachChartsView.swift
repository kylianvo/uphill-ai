import SwiftUI
import Charts

struct AdherenceTrendChartView: View {
    let trend: [AdherenceTrendEntry]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Adherence Trend", systemImage: "chart.xyaxis.line")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Text("Target: 80%")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            if trend.isEmpty {
                Text("No adherence data recorded yet")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.vertical, UH.Space.medium)
            } else {
                Chart {
                    ForEach(trend) { entry in
                        AreaMark(
                            x: .value("Week", "W\(entry.weekNumber)"),
                            y: .value("Adherence", entry.adherencePct * 100)
                        )
                        .foregroundStyle(
                            LinearGradient(
                                colors: [UH.Palette.accent.opacity(0.35), UH.Palette.accent.opacity(0.05)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )

                        LineMark(
                            x: .value("Week", "W\(entry.weekNumber)"),
                            y: .value("Adherence", entry.adherencePct * 100)
                        )
                        .foregroundStyle(UH.Palette.accent)
                        .lineStyle(StrokeStyle(lineWidth: 2.5))

                        PointMark(
                            x: .value("Week", "W\(entry.weekNumber)"),
                            y: .value("Adherence", entry.adherencePct * 100)
                        )
                        .foregroundStyle(UH.Palette.accent)
                    }

                    RuleMark(y: .value("Target", 80))
                        .foregroundStyle(Color.green.opacity(0.4))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 4]))
                }
                .chartYScale(domain: 0...100)
                .chartYAxis {
                    AxisMarks(values: [0, 50, 80, 100]) { value in
                        AxisGridLine()
                        AxisValueLabel {
                            if let intVal = value.as(Int.self) {
                                Text("\(intVal)%")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(UH.Palette.muted)
                            }
                        }
                    }
                }
                .chartXAxis {
                    AxisMarks { value in
                        AxisValueLabel {
                            if let str = value.as(String.self) {
                                Text(str)
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                        }
                    }
                }
                .frame(height: 120)
            }
        }
        .trainingCard()
    }
}

struct MissedByDayChartView: View {
    let missedByDay: [MissedByDayEntry]

    private let dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    private var filledDays: [MissedByDayEntry] {
        let counts = Dictionary(uniqueKeysWithValues: missedByDay.map { ($0.dayOfWeek, $0.count) })
        return dayOrder.map { day in
            MissedByDayEntry(dayOfWeek: day, count: counts[day] ?? 0)
        }
    }

    private func shortDay(_ day: String) -> String {
        switch day {
        case "Monday": return "Mon"
        case "Tuesday": return "Tue"
        case "Wednesday": return "Wed"
        case "Thursday": return "Thu"
        case "Friday": return "Fri"
        case "Saturday": return "Sat"
        case "Sunday": return "Sun"
        default: return String(day.prefix(3))
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Missed by Day", systemImage: "calendar.badge.exclamationmark")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                let total = missedByDay.reduce(0) { $0 + $1.count }
                Text("\(total) total misses")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            Chart(filledDays) { entry in
                BarMark(
                    x: .value("Day", shortDay(entry.dayOfWeek)),
                    y: .value("Missed", entry.count)
                )
                .foregroundStyle(entry.count > 0 ? Color.red.opacity(0.85) : UH.Palette.line.opacity(0.5))
                .cornerRadius(4)
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisGridLine()
                    AxisValueLabel()
                }
            }
            .chartXAxis {
                AxisMarks { value in
                    AxisValueLabel {
                        if let str = value.as(String.self) {
                            Text(str)
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }
                }
            }
            .frame(height: 120)
        }
        .trainingCard()
    }
}

struct WorkoutTypeMixChartView: View {
    let mix: [WorkoutTypeMixEntry]

    private func colorFor(type: String) -> Color {
        let t = type.lowercased()
        if t.contains("easy") || t.contains("recovery") { return Color.blue }
        if t.contains("long") { return Color.green }
        if t.contains("tempo") || t.contains("threshold") { return Color.orange }
        if t.contains("interval") { return Color.red }
        if t.contains("endurance") || t.contains("strength") || t.contains("me") { return Color.purple }
        if t.contains("cross") { return Color.teal }
        return Color.gray
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Label("Workout Type Mix", systemImage: "chart.bar.xaxis")
                .font(UH.TextStyle.sectionTitle)
                .foregroundStyle(UH.Palette.ink)

            if mix.isEmpty {
                Text("No completed workouts in window")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.vertical, UH.Space.small)
            } else {
                VStack(spacing: 8) {
                    ForEach(mix.prefix(6)) { entry in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(colorFor(type: entry.type))
                                .frame(width: 8, height: 8)
                            Text(entry.type)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .frame(width: 110, alignment: .leading)
                                .lineLimit(1)

                            GeometryReader { geo in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(UH.Palette.line.opacity(0.3))
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(colorFor(type: entry.type))
                                        .frame(width: max(4, geo.size.width * CGFloat(min(1.0, entry.pct))))
                                }
                            }
                            .frame(height: 8)

                            Text("\(Int(entry.pct * 100))%")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.secondary)
                                .frame(width: 36, alignment: .trailing)

                            Text("(\(entry.count))")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundStyle(UH.Palette.muted)
                                .frame(width: 30, alignment: .trailing)
                        }
                    }
                }
            }
        }
        .trainingCard()
    }
}

struct RaceBreakdownCardView: View {
    let races: [RaceBreakdownEntry]
    var onSelectRace: ((String) -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Label("Athletes by Target Race", systemImage: "flag.checkered")
                .font(UH.TextStyle.sectionTitle)
                .foregroundStyle(UH.Palette.ink)

            if races.isEmpty {
                Text("No target races configured yet")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.vertical, UH.Space.small)
            } else {
                VStack(spacing: 8) {
                    ForEach(races) { entry in
                        Button {
                            onSelectRace?(entry.raceName)
                        } label: {
                            HStack(alignment: .center, spacing: 12) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(entry.raceName)
                                        .font(UH.TextStyle.label)
                                        .foregroundStyle(UH.Palette.ink)
                                    if let date = entry.raceDate {
                                        Text(date)
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(UH.Palette.muted)
                                    }
                                }
                                Spacer()
                                HStack(spacing: 4) {
                                    Image(systemName: "person.2.fill")
                                        .font(.system(size: 11))
                                    Text("\(entry.count)")
                                        .font(.system(size: 13, weight: .bold, design: .monospaced))
                                }
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(UH.Palette.accent.opacity(0.12))
                                .foregroundStyle(UH.Palette.accent)
                                .clipShape(Capsule())
                            }
                            .padding(10)
                            .background(UH.Palette.hover.opacity(0.5))
                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .trainingCard()
    }
}

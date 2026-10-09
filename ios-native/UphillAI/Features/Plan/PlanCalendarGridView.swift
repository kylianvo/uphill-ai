import SwiftUI

struct PlanCalendarGridView: View {
    let model: PlanViewModel
    let onSelectDay: (Date, Int) -> Void
    @State private var viewMonth: Date = Date()
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private let dayHeaders = ["M", "T", "W", "T", "F", "S", "S"]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            // Month navigation & monthly totals
            monthHeader

            // Intensity color legend
            intensityLegend

            // 7-day header
            HStack(spacing: 0) {
                ForEach(dayHeaders.indices, id: \.self) { i in
                    Text(dayHeaders[i])
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 4)

            // Weeks grid
            let weeks = buildMonthGrid()
            VStack(spacing: 4) {
                ForEach(weeks.indices, id: \.self) { wi in
                    HStack(spacing: 4) {
                        ForEach(weeks[wi]) { cell in
                            dayCellView(cell)
                        }
                    }
                }
            }
        }
        .padding(UH.Space.small)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
        .onAppear {
            if let date = PlanCalendar.day(from: model.snapshot?.plan.startDate) {
                viewMonth = date
            } else {
                viewMonth = Date()
            }
        }
    }

    // MARK: - Month Header

    private var monthHeader: some View {
        HStack {
            Button {
                withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                    viewMonth = Calendar.current.date(byAdding: .month, value: -1, to: viewMonth) ?? viewMonth
                }
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundStyle(UH.Palette.ink)
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel("Previous month")

            Text(viewMonth, format: .dateTime.month(.wide).year())
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(UH.Palette.ink)

            Button {
                withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                    viewMonth = Calendar.current.date(byAdding: .month, value: 1, to: viewMonth) ?? viewMonth
                }
            } label: {
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .bold))
                    .foregroundStyle(UH.Palette.ink)
                    .frame(width: 44, height: 44)
            }
            .accessibilityLabel("Next month")

            Spacer()

            // Month total volume pill
            let totals = calculateMonthTotals()
            Text("~\(Int(totals.km)) km · \(String(format: "%.1f", totals.hours))h")
                .font(.system(size: 11, weight: .medium, design: .monospaced))
                .foregroundStyle(UH.Palette.accentInk)
                .padding(.horizontal, 7)
                .padding(.vertical, 3.5)
                .background(UH.Palette.activeFill, in: Capsule())
        }
    }

    // MARK: - Intensity Legend

    private var intensityLegend: some View {
        HStack(spacing: 8) {
            legendItem(name: L("Easy"), color: Color(hex: "#3b82f6"))
            legendItem(name: L("Mod"), color: Color(hex: "#10b981"))
            legendItem(name: L("Hard"), color: Color(hex: "#ef4444"))
            legendItem(name: L("Strength"), color: Color(hex: "#8b5cf6"))
            legendItem(name: L("Rest"), color: Color(hex: "#94a3b8"))
        }
        .padding(.horizontal, 4)
        .padding(.bottom, 2)
    }

    private func legendItem(name: String, color: Color) -> some View {
        HStack(spacing: 3) {
            Circle().fill(color).frame(width: 6, height: 6)
            Text(name)
                .font(.system(size: 9.5, weight: .medium))
                .foregroundStyle(UH.Palette.muted)
        }
    }

    // MARK: - Day Cell View

    private func dayCellView(_ cell: CalendarDayCell) -> some View {
        Button {
            if let w = cell.weekNumber {
                onSelectDay(cell.date, w)
            }
        } label: {
            VStack(spacing: 2) {
                // Day number & Race Day flag
                HStack(spacing: 1) {
                    Text("\(Calendar.current.component(.day, from: cell.date))")
                        .font(.system(size: 11, weight: cell.isToday ? .bold : .medium, design: .monospaced))
                        .foregroundStyle(cell.isToday ? UH.Palette.accentInk : (cell.isCurrentMonth ? UH.Palette.ink : UH.Palette.muted.opacity(0.5)))

                    if cell.isRaceDay {
                        Image(systemName: "flag.fill")
                            .font(.system(size: 8))
                            .foregroundStyle(Color(hex: "#ef4444"))
                    }
                }

                // Workout indicator bar / tick
                if let workout = cell.primaryWorkout, !workout.isRest {
                    let color = WorkoutTypePresentation.zoneColor(for: workout)
                    ZStack {
                        RoundedRectangle(cornerRadius: 3)
                            .fill(color.opacity(cell.isCurrentMonth ? 0.85 : 0.4))
                            .frame(height: 14)

                        if workout.isDone {
                            Image(systemName: "checkmark")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundStyle(.white)
                        } else if let km = workout.distanceKm, km > 0 {
                            Text(String(format: "%.0f", km))
                                .font(.system(size: 8, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white)
                        }
                    }
                } else {
                    Circle()
                        .fill(cell.isCurrentMonth ? UH.Palette.line.opacity(0.5) : Color.clear)
                        .frame(width: 4, height: 4)
                        .frame(height: 14)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44)
            .padding(.vertical, 2)
            .background(cell.isToday ? UH.Palette.activeFill.opacity(0.35) : Color.clear, in: RoundedRectangle(cornerRadius: 6))
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(cell.isToday ? UH.Palette.accentInk : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .disabled(cell.weekNumber == nil)
        .accessibilityIdentifier("calendar.day.\(cell.id)")
    }

    // MARK: - Grid Calculation

    private func buildMonthGrid() -> [[CalendarDayCell]] {
        let cal = Calendar.current
        let components = cal.dateComponents([.year, .month], from: viewMonth)
        guard let firstOfMonth = cal.date(from: components),
              let monthRange = cal.range(of: .day, in: .month, for: firstOfMonth) else { return [] }

        let startMonday = PlanCalendar.monday(of: firstOfMonth)
        let lastDayOfMonth = cal.date(byAdding: .day, value: monthRange.count - 1, to: firstOfMonth)!
        let endSunday = cal.date(byAdding: .day, value: 6, to: PlanCalendar.monday(of: lastDayOfMonth))!

        let plan = model.snapshot?.plan
        let workouts = model.snapshot?.workouts ?? []
        let raceDay = PlanCalendar.day(from: plan?.raceDate)
        let today = Date()

        var currentDay = startMonday
        var weeks: [[CalendarDayCell]] = []
        var currentWeekRow: [CalendarDayCell] = []

        while currentDay <= endSunday {
            let isCurrentMonth = cal.isDate(currentDay, equalTo: firstOfMonth, toGranularity: .month)
            let isToday = cal.isDate(currentDay, inSameDayAs: today)
            let isRace = raceDay.map { cal.isDate(currentDay, inSameDayAs: $0) } ?? false

            // Find matching workouts for this day
            var matching: [Workout] = []
            var foundWeek: Int? = nil

            if let plan {
                for w in workouts {
                    if let d = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan, workouts: workouts) {
                        if cal.isDate(currentDay, inSameDayAs: d) {
                            matching.append(w)
                            foundWeek = w.weekNumber
                        }
                    }
                }
            }

            let cell = CalendarDayCell(
                date: currentDay,
                isCurrentMonth: isCurrentMonth,
                isToday: isToday,
                isRaceDay: isRace,
                weekNumber: foundWeek,
                workouts: matching
            )

            currentWeekRow.append(cell)
            if currentWeekRow.count == 7 {
                weeks.append(currentWeekRow)
                currentWeekRow = []
            }

            currentDay = cal.date(byAdding: .day, value: 1, to: currentDay)!
        }

        return weeks
    }

    private func calculateMonthTotals() -> (km: Double, hours: Double) {
        let cal = Calendar.current
        guard let plan = model.snapshot?.plan else { return (0, 0) }
        let workouts = model.snapshot?.workouts ?? []

        var km = 0.0
        var mins = 0.0

        for w in workouts {
            if let d = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan, workouts: workouts) {
                if cal.isDate(d, equalTo: viewMonth, toGranularity: .month) {
                    km += w.distanceKm ?? 0.0
                    mins += w.durationMinutes
                }
            }
        }
        return (km, mins / 60.0)
    }
}

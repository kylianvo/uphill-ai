import SwiftUI

/// Month view of the plan. Each week is a row that reads like a small bar chart: one bar per
/// session (height = distance, colour = effort, fill = done / planned / missed) on a shared
/// baseline, with the week's km at the end of the row.
struct PlanCalendarGridView: View {
    let model: PlanViewModel
    let onSelectDay: (MoveTarget) -> Void
    let onOpenWeek: (Int) -> Void
    @State private var viewMonth: Date
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private static let numberZone: CGFloat = 24
    private static let barZone: CGFloat = 26
    private static let rowHeight: CGFloat = 62
    private static let totalWidth: CGFloat = 44

    init(model: PlanViewModel, onSelectDay: @escaping (MoveTarget) -> Void, onOpenWeek: @escaping (Int) -> Void) {
        self.model = model
        self.onSelectDay = onSelectDay
        self.onOpenWeek = onOpenWeek
        _viewMonth = State(initialValue: model.calendarFocusDate)
    }

    var body: some View {
        let month = model.calendarMonth(viewMonth)
        VStack(alignment: .leading, spacing: UH.Space.small) {
            header(month)
            VStack(spacing: 0) {
                weekdayHeader
                grid(month)
                    .id(String(PlanCalendar.ymd(viewMonth).prefix(7)))
                    .transition(.opacity)
            }
            // shortcut: the grid stops following Dynamic Type at xxxLarge (cells are fixed-size); header, legend and day sheet keep scaling.
            .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
            .contentShape(Rectangle())
            .simultaneousGesture(swipe)
            legend(month)
        }
        .padding(10)
        .background(Ink.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(Ink.line))
        .sensoryFeedback(.selection, trigger: viewMonth)
    }

    // MARK: - Header

    private func header(_ month: CalendarMonth) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            headerControls(month)
            // Own full-width line so it never wraps beside the Today pill (the grid would shift between months).
            Text(summary(month))
                .font(.footnote)
                .foregroundStyle(Ink.muted)
                .monospacedDigit()
                .lineLimit(2)
                .minimumScaleFactor(0.8)
                .padding(.leading, 4)
        }
    }

    private func headerControls(_ month: CalendarMonth) -> some View {
        HStack(alignment: .center, spacing: 0) {
            Text(monthTitle)
                .font(.title3.weight(.bold))
                .foregroundStyle(Ink.ink)
                .padding(.leading, 4)
                .accessibilityAddTraits(.isHeader)
            Spacer(minLength: UH.Space.compact)
            if !month.isCurrentMonth {
                Button { goTo(model.calendarToday) } label: {
                    Text("Today")
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Ink.accentInk)
                        .padding(.horizontal, 12)
                        .frame(minHeight: 32)
                        .background(UH.Palette.activeFill, in: Capsule())
                }
                .buttonStyle(.plain)
                .frame(minHeight: 44)
                .accessibilityIdentifier("calendar.today")
            }
            monthStep("chevron.left", label: L("Previous month"), delta: -1)
            monthStep("chevron.right", label: L("Next month"), delta: 1)
        }
    }

    /// "October 2026" / "Tháng 10 năm 2026": the locale pattern, first letter capitalised.
    private var monthTitle: String {
        let s = viewMonth.formatted(.dateTime.month(.wide).year().locale(AppLanguage.current.locale))
        return s.prefix(1).uppercased() + s.dropFirst()
    }

    private func summary(_ month: CalendarMonth) -> String {
        guard month.sessionsTotal > 0 else { return L("No sessions planned this month") }
        let hours = month.hours.formatted(.number.precision(.fractionLength(1)).locale(AppLanguage.current.locale))
        return L("%lld km · %@ h · %lld of %lld sessions done", Int(month.km.rounded()), hours, month.sessionsDone, month.sessionsTotal)
    }

    private func monthStep(_ icon: String, label: String, delta: Int) -> some View {
        Button { shift(delta) } label: {
            Image(systemName: icon)
                .font(.body.weight(.semibold))
                .foregroundStyle(Ink.ink)
                .frame(width: 44, height: 44)
        }
        .accessibilityLabel(label)
    }

    private func shift(_ delta: Int) {
        guard let next = PlanCalendar.calendar.date(byAdding: .month, value: delta, to: viewMonth) else { return }
        goTo(next)
    }

    private func goTo(_ date: Date) {
        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.2)) { viewMonth = date }
        AccessibilityNotification.Announcement(monthTitle).post()
    }

    /// Horizontal flick pages months; the chevrons stay as the accessible path.
    private var swipe: some Gesture {
        DragGesture(minimumDistance: 30).onEnded { v in
            guard abs(v.translation.width) > 60, abs(v.translation.width) > abs(v.translation.height) * 1.5 else { return }
            shift(v.translation.width < 0 ? 1 : -1)
        }
    }

    // MARK: - Grid

    private var weekdayHeader: some View {
        HStack(spacing: 0) {
            ForEach(Array(weekdaySymbols.enumerated()), id: \.offset) { _, symbol in
                Text(symbol)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(Ink.muted)
                    .frame(maxWidth: .infinity)
            }
            Text(L("km/wk"))
                .font(.caption2.weight(.semibold))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
                .foregroundStyle(Ink.muted)
                .frame(width: Self.totalWidth)
        }
        .padding(.bottom, 2)
        .accessibilityHidden(true)
    }

    /// Monday-first single-letter weekday names in the app language.
    private var weekdaySymbols: [String] {
        var c = Calendar(identifier: .gregorian)
        c.locale = AppLanguage.current.locale
        let sunFirst = c.veryShortStandaloneWeekdaySymbols
        return Array(sunFirst.dropFirst()) + [sunFirst[0]]
    }

    private func grid(_ month: CalendarMonth) -> some View {
        VStack(spacing: 0) {
            ForEach(month.weeks) { row in
                HStack(spacing: 0) {
                    ForEach(Array(row.cells.enumerated()), id: \.element.id) { index, cell in
                        dayCell(cell, weekday: Weekday.allCases[index], month: month)
                    }
                    weekTotal(row, month: month)
                }
                .frame(height: Self.rowHeight)
            }
        }
    }

    @ViewBuilder
    private func dayCell(_ cell: CalendarDayCell, weekday: Weekday, month: CalendarMonth) -> some View {
        let content = VStack(spacing: 4) {
            dayNumber(cell)
            bars(cell, month: month)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 3)
        .frame(height: Self.rowHeight, alignment: .top)
        .background {
            if cell.isToday { RoundedRectangle(cornerRadius: UH.Radius.control).fill(Ink.wash) }
        }
        .contentShape(Rectangle())

        if let week = cell.weekNumber {
            Button { onSelectDay(MoveTarget(week: week, weekday: weekday, date: cell.date)) } label: { content }
                .buttonStyle(.plain)
                .accessibilityLabel(accessibilityLabel(cell))
                .accessibilityHint(L("Show sessions"))
                .accessibilityIdentifier("calendar.day.\(cell.id)")
        } else {
            content
                .accessibilityElement(children: .ignore)
                .accessibilityLabel(accessibilityLabel(cell))
        }
    }

    private func dayNumber(_ cell: CalendarDayCell) -> some View {
        Group {
            Text("\(PlanCalendar.calendar.component(.day, from: cell.date))")
                .font(.footnote.weight(cell.isToday ? .bold : .medium))
                .monospacedDigit()
                .foregroundStyle(cell.isToday ? Ink.onAccent : (cell.isCurrentMonth ? Ink.ink : Ink.muted))
                .frame(minWidth: Self.numberZone, minHeight: Self.numberZone)
                .background {
                    if cell.isToday { Circle().fill(Ink.accentInk) }
                }
        }
        .overlay(alignment: .trailing) {
            if cell.isRaceDay {
                Image(systemName: "flag.checkered")
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(Ink.race)
                    .offset(x: 11)
            }
        }
    }

    private func bars(_ cell: CalendarDayCell, month: CalendarMonth) -> some View {
        let sessions = Array(cell.sessions.prefix(3))
        let ceiling = Self.barZone - 2
        return ZStack(alignment: .bottom) {
            Rectangle().fill(Ink.line).frame(height: 1)
            HStack(alignment: .bottom, spacing: 2) {
                ForEach(sessions) { w in
                    let share = month.maxSessionLoad > 0 ? w.calendarLoad / month.maxSessionLoad : 0
                    SessionBar(color: WorkoutTypePresentation.zoneColor(for: w), state: SessionBar.Fill(w))
                        .frame(width: sessions.count > 1 ? 9 : 11, height: min(ceiling, max(5, ceiling * share)))
                }
            }
            .opacity(cell.isCurrentMonth ? 1 : 0.5)
        }
        .frame(height: Self.barZone, alignment: .bottom)
    }

    @ViewBuilder
    private func weekTotal(_ row: CalendarWeekRow, month: CalendarMonth) -> some View {
        let share = month.maxWeekKm > 0 ? min(1, row.km / month.maxWeekKm) : 0
        let content = VStack(spacing: 4) {
            Text(row.km > 0 ? "\(Int(row.km.rounded()))" : "–")
                .font(.footnote.weight(.semibold))
                .monospacedDigit()
                .foregroundStyle(row.containsToday ? Ink.accentInk : Ink.ink)
                .frame(minHeight: Self.numberZone)
            ZStack(alignment: .bottomLeading) {
                if row.km > 0 {
                    Capsule().fill(Ink.line).frame(height: 4)
                    Capsule().fill(Ink.accentInk).frame(width: 30 * share, height: 4)
                }
            }
            .frame(width: 30, height: Self.barZone, alignment: .bottom)
        }
        .padding(.top, 3)
        .frame(width: Self.totalWidth, height: Self.rowHeight, alignment: .top)
        .contentShape(Rectangle())

        if let week = row.weekNumber {
            Button { onOpenWeek(week) } label: { content }
                .buttonStyle(.plain)
                .accessibilityLabel(L("Week %lld, %lld km", week, Int(row.km.rounded())))
                .accessibilityHint(L("Open in list"))
                .accessibilityIdentifier("calendar.week.\(week)")
        } else {
            content.accessibilityHidden(true)
        }
    }

    private func accessibilityLabel(_ cell: CalendarDayCell) -> String {
        var parts = [cell.date.formatted(.dateTime.weekday(.wide).day().month(.wide).locale(AppLanguage.current.locale))]
        if cell.isToday { parts.insert(L("Today"), at: 0) }
        if cell.isRaceDay { parts.append(L("Race day")) }
        if cell.sessions.isEmpty {
            if cell.weekNumber != nil { parts.append(L("Rest")) }
        } else {
            for w in cell.sessions {
                parts.append("\(w.title), \(WorkoutTypePresentation.formatMetrics(for: w)), \(SessionBar.Fill(w).name)")
            }
        }
        return parts.joined(separator: ", ")
    }

    // MARK: - Legend

    /// Only the effort kinds that appear on screen, then how a bar's fill reads.
    @ViewBuilder
    private func legend(_ month: CalendarMonth) -> some View {
        let kinds = legendKinds(month)
        if !kinds.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                FlowLayout(spacing: 8) {
                    ForEach(kinds, id: \.0) { label, color in
                        HStack(spacing: 4) {
                            Circle().fill(color).frame(width: 8, height: 8)
                            Text(verbatim: label)
                        }
                    }
                }
                FlowLayout(spacing: 8) {
                    ForEach([SessionBar.Fill.done, .planned, .missed], id: \.self) { fill in
                        HStack(spacing: 4) {
                            SessionBar(color: Ink.ink, state: fill).frame(width: 7, height: 11)
                            Text(fill.name)
                        }
                    }
                }
            }
            .font(.caption2)
            .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
            .foregroundStyle(Ink.muted)
            .padding(.horizontal, 4)
            .padding(.top, 2)
            .accessibilityHidden(true)
        }
    }

    private func legendKinds(_ month: CalendarMonth) -> [(String, Color)] {
        var seen = Set<String>()
        return month.weeks.flatMap(\.cells).flatMap(\.sessions).compactMap { w in
            let label = WorkoutTypePresentation.chipLabel(for: w)
            return seen.insert(label).inserted ? (label, WorkoutTypePresentation.zoneColor(for: w)) : nil
        }
    }
}

/// One session: solid when done, tinted outline when planned, dashed grey when missed.
private struct SessionBar: View {
    enum Fill: Hashable {
        case done, planned, missed

        init(_ w: Workout) { self = w.isDone ? .done : (w.isMissedFlag ? .missed : .planned) }

        var name: String {
            switch self {
            case .done: L("Done")
            case .planned: L("Planned")
            case .missed: L("Missed")
            }
        }
    }

    let color: Color
    let state: Fill

    var body: some View {
        let shape = UnevenRoundedRectangle(topLeadingRadius: 3, topTrailingRadius: 3)
        switch state {
        case .done:
            shape.fill(color)
        case .planned:
            shape.fill(color.opacity(0.22)).overlay(shape.stroke(color, lineWidth: 1.5))
        case .missed:
            shape.fill(color.opacity(0.08)).overlay(shape.stroke(color, style: StrokeStyle(lineWidth: 1.5, dash: [2.5, 2])))
        }
    }
}

/// Grid colours with a dark variant each. The app is locked to light today (Info.plist and
/// UphillAIApp); these follow the system appearance so the grid is ready when that lock lifts.
private enum Ink {
    static let ink = Color(light: "#172b26", dark: "#e8f1ec")
    static let muted = Color(light: "#5d7167", dark: "#9fb3a9")
    static let line = Color(light: "#dce5df", dark: "#2f403a")
    static let card = Color(light: "#ffffff", dark: "#17201c")
    static let accentInk = Color(light: "#08764f", dark: "#19ce8b")
    static let onAccent = Color(light: "#ffffff", dark: "#063e2b")
    static let race = Color(light: "#b42318", dark: "#f97066")
    static let wash = Color(hex: "#19ce8b").opacity(0.12)
}

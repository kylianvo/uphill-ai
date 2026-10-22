import SwiftUI

struct DayRow: View {
    let day: PlanDay
    var onToggleDone: ((Workout) -> Void)? = nil
    var onMoveOrSwap: ((PlanDay) -> Void)? = nil
    let onSelect: (Workout) -> Void

    var body: some View {
        if day.isCollapsed {
            restRow
        } else {
            dayCard
        }
    }

    private var dateText: String {
        guard let date = day.date else { return day.weekday.short }
        return date.formatted(Date.FormatStyle(locale: AppLanguage.current.locale).weekday(.abbreviated).day().month(.abbreviated))
    }

    private var dayIdentifier: String {
        day.eyebrow == "TODAY" ? "day.today" : "day.\(day.weekday.rawValue)"
    }

    private var primaryWorkout: Workout? {
        day.workouts.first(where: { !$0.isRest }) ?? day.workouts.first
    }

    private var primaryColor: Color {
        guard let w = primaryWorkout, !day.isRest else {
            return UH.Palette.muted
        }
        return WorkoutTypePresentation.zoneColor(for: w)
    }

    /// The date, or "Today" in the accent colour; the only place a row says it is today.
    private func dayLabel(font: Font, color: Color) -> some View {
        Text(day.isToday ? L("Today") : dateText)
            .font(day.isToday ? UH.TextStyle.eyebrow : font)
            .foregroundStyle(day.isToday ? UH.Palette.accentInk : color)
    }

    // MARK: - Rest Row (Collapsed)

    private var restRow: some View {
        HStack(spacing: UH.Space.compact) {
            dayLabel(font: UH.TextStyle.label, color: UH.Palette.secondary)
            Spacer()
            Label("Rest", systemImage: "moon.zzz")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.muted)
        }
        .padding(.horizontal, UH.Space.regular)
        .padding(.vertical, 10)
        .frame(minHeight: 44)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.workoutDay)
                .stroke(day.isToday ? UH.Palette.accentInk.opacity(0.4) : UH.Palette.line, lineWidth: 1)
        )
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier(dayIdentifier)
        .contextMenu {
            if let onMoveOrSwap {
                Button {
                    onMoveOrSwap(day)
                } label: {
                    Label("Move or swap this day", systemImage: "arrow.left.arrow.right")
                }
            }
        }
    }

    // MARK: - Day Card (Active Workouts with Workout Type Color Highlights)

    private var dayCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            if day.workouts.count > 1 {
                doubleDayHeader
            }

            ForEach(Array(day.workouts.enumerated()), id: \.element.id) { index, workout in
                if index > 0 {
                    Divider().overlay(UH.Palette.line.opacity(0.6))
                }
                workoutRow(workout, isDouble: day.workouts.count > 1)
                }
        }
        .padding(.vertical, UH.Space.regular)
        .padding(.trailing, UH.Space.regular)
        .padding(.leading, UH.Space.regular + 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(day.isToday ? UH.Palette.activeFill : UH.Palette.card,
                    in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.panel)
                .stroke(day.isToday ? UH.Palette.accentInk.opacity(0.4) : UH.Palette.line, lineWidth: 1)
        )
        .overlay(alignment: .leading) {
            // Prominent Left Accent Stripe matching workout type
            RoundedRectangle(cornerRadius: 2.5)
                .fill(primaryColor)
                .frame(width: 4.5)
                .padding(.vertical, 7)
                .padding(.leading, 7)
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier(dayIdentifier)
        .contextMenu {
            if let onMoveOrSwap {
                Button {
                    onMoveOrSwap(day)
                } label: {
                    Label("Move or swap this day", systemImage: "arrow.left.arrow.right")
                }
            }
        }
    }

    // Header when 2+ workouts exist in a single day
    private var doubleDayHeader: some View {
        HStack(spacing: UH.Space.compact) {
            dayLabel(font: UH.TextStyle.label, color: UH.Palette.ink)
            Text(verbatim: "· " + L("%lld sessions", day.workouts.count))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            Spacer()
        }
    }

    // MARK: - 3-Line Workout Row

    private func workoutRow(_ workout: Workout, isDouble: Bool) -> some View {
        let zoneColor = WorkoutTypePresentation.zoneColor(for: workout)
        return HStack(alignment: .center, spacing: UH.Space.small) {
            if isDouble {
                Capsule()
                    .fill(zoneColor)
                    .frame(width: 3.5, height: 32)
            }

            // Tappable main body (Lines 1 to 3)
            Button {
                onSelect(workout)
            } label: {
                VStack(alignment: .leading, spacing: 3) {
                    // Line 1: Date/Session, Markers (Today/Priority), Type Chip in Zone Colour
                    line1(workout, isDouble: isDouble)

                    // Line 2: Title
                    HStack(spacing: 4) {
                        if workout.isPriority {
                            Image(systemName: "star.fill")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.accentInk)
                                .accessibilityHidden(true)
                        }
                        Text(workout.title)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(1)
                    }

                    // Line 3: Zone Dot + SF Mono numbers (Duration · Est. distance · Pace)
                    line3(workout)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("workout.\(workout.id)")
            .accessibilityLabel(accessibility(workout))

            // Right side: Done check / calm missed state
            doneCheckButton(workout)
        }
        .padding(.vertical, 2)
    }

    // Line 1: date (or session slot), type chip, and at most one status pill
    private func line1(_ workout: Workout, isDouble: Bool) -> some View {
        let zoneColor = WorkoutTypePresentation.zoneColor(for: workout)
        let chipLabel = WorkoutTypePresentation.chipLabel(for: workout)

        return HStack(spacing: 6) {
            if !isDouble {
                dayLabel(font: UH.TextStyle.caption, color: UH.Palette.secondary)
            } else {
                Text(L(workout.sessionSlot?.capitalized ?? "Session"))
                    .font(UH.TextStyle.eyebrow)
                    .foregroundStyle(zoneColor)
            }

            Text(chipLabel)
                .font(UH.TextStyle.eyebrow)
                .foregroundStyle(zoneColor)
                .padding(.horizontal, 7)
                .padding(.vertical, 2)
                .background(zoneColor.opacity(0.14), in: RoundedRectangle(cornerRadius: UH.Radius.topic))

            if WorkoutTypePresentation.rowStatus(for: workout) == .matched {
                Label {
                    Text("Matched")
                } icon: {
                    Image(systemName: workout.matchedFromAppleHealth ? "heart.fill" : "applewatch")
                        .foregroundStyle(workout.matchedFromAppleHealth ? UH.Palette.healthPink : UH.Palette.accentInk)
                }
                .labelStyle(.titleAndIcon)
                .font(UH.TextStyle.eyebrow)
                .foregroundStyle(UH.Palette.accentInk)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(UH.Palette.activeFill, in: Capsule())
                .accessibilityLabel(L("Matched with %@", workout.matchedSourceName))
                .accessibilityIdentifier("workout.\(workout.id).matched")
            }
        }
    }

    // Line 3: Duration · Est. distance · Pace (SF Mono numbers, zone dot)
    private func line3(_ workout: Workout) -> some View {
        let zoneColor = WorkoutTypePresentation.zoneColor(for: workout)
        let metrics = WorkoutTypePresentation.formatMetrics(for: workout)

        return HStack(spacing: 6) {
            Circle()
                .fill(zoneColor)
                .frame(width: 7, height: 7)

            Text(metrics)
                .font(UH.TextStyle.caption.monospacedDigit())
                .foregroundStyle(UH.Palette.secondary)
                .lineLimit(1)
        }
    }

    // Right-hand Done Checkmark or calm Missed state
    @ViewBuilder
    private func doneCheckButton(_ workout: Workout) -> some View {
        Button {
            onToggleDone?(workout)
        } label: {
            ZStack {
                if workout.isDone {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(UH.Palette.accentInk)
                } else if workout.isMissedFlag || PlanCalendar.isUnloggedPast(workout, on: day.date) {
                    HStack(spacing: 3) {
                        Image(systemName: "xmark.circle")
                        Text(workout.isMissedFlag ? "Missed" : "Not logged")
                    }
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 4)
                    .background(UH.Palette.hover, in: Capsule())
                } else {
                    Image(systemName: "circle")
                        .font(.title2)
                        .foregroundStyle(UH.Palette.line)
                }
            }
            .frame(minWidth: 44, minHeight: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(onToggleDone == nil)
        .accessibilityIdentifier("workout.\(workout.id).done")
        .accessibilityLabel(workout.isDone ? L("Mark as not done") : L("Mark as done"))
    }

    private func accessibility(_ w: Workout) -> String {
        var parts = [w.title, L("%lld minutes", Int(w.durationMinutes))]
        if let km = w.distanceKm, km > 0 { parts.append(L("%@ kilometres", km.formatted(.number.precision(.fractionLength(0...1))))) }
        if w.isPriority { parts.append(L("Coach's pick")) }
        if w.isMatched { parts.append(L("Matched with %@", w.matchedSourceName)) }
        if w.isDone { parts.append("done") } else if w.isMissedFlag { parts.append("missed") }
        return parts.joined(separator: ", ")
    }
}

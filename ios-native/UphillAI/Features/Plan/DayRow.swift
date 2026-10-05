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
        return date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
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

    private var hasPriority: Bool {
        day.workouts.contains(where: \.isPriority)
    }

    private var dayBorderColor: Color {
        if day.isToday { return UH.Palette.accentInk }
        if hasPriority { return primaryColor.opacity(0.85) }
        return primaryColor.opacity(0.25)
    }

    // MARK: - Rest Row (Collapsed)

    private var restRow: some View {
        HStack(spacing: UH.Space.compact) {
            if day.isToday {
                Text("TODAY")
                    .font(.system(size: 10, weight: .bold))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }
            Text(dateText)
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.secondary)
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
                if workout.isMatched {
                    matchedActivityBadge(workout)
                }
            }
        }
        .padding(.vertical, UH.Space.regular)
        .padding(.trailing, UH.Space.regular)
        .padding(.leading, UH.Space.regular + 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            // Subtle Gradient Background Wash in workout type color
            LinearGradient(
                colors: [
                    primaryColor.opacity(day.isToday ? 0.16 : 0.09),
                    primaryColor.opacity(0.02),
                    day.isToday ? UH.Palette.activeFill.opacity(0.45) : UH.Palette.card
                ],
                startPoint: .leading,
                endPoint: .trailing
            ),
            in: RoundedRectangle(cornerRadius: UH.Radius.landing)
        )
        .overlay(
            // Border tinted with type color
            RoundedRectangle(cornerRadius: UH.Radius.landing)
                .stroke(dayBorderColor, lineWidth: day.isToday || hasPriority ? 1.5 : 1)
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
            Text(dateText)
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.ink)
            if day.isToday {
                Text("TODAY")
                    .font(.system(size: 10, weight: .bold))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }
            Spacer()
            Text("2 SESSIONS")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(primaryColor)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(primaryColor.opacity(0.12), in: Capsule())

            if let onMoveOrSwap {
                Button {
                    onMoveOrSwap(day)
                } label: {
                    HStack(spacing: 3) {
                        Image(systemName: "arrow.left.arrow.right")
                            .font(.system(size: 10, weight: .bold))
                        Text("SWAP")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                    }
                    .foregroundStyle(UH.Palette.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.hover, in: Capsule())
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("day.\(day.weekday.rawValue).moveswap")
            }
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
                    Text(workout.title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                        .lineLimit(1)

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

    // Line 1: Date + Markers + Type Chip in Zone Colour
    private func line1(_ workout: Workout, isDouble: Bool) -> some View {
        let zoneColor = WorkoutTypePresentation.zoneColor(for: workout)
        let chipLabel = WorkoutTypePresentation.chipLabel(for: workout)

        return HStack(spacing: 6) {
            if !isDouble {
                Text(dateText)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)

                if day.isToday {
                    Text("TODAY")
                        .font(.system(size: 9, weight: .bold))
                        .tracking(0.5)
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1.5)
                        .background(UH.Palette.activeFill, in: Capsule())
                }
            } else {
                let slot = workout.sessionSlot?.capitalized ?? "Session"
                Text(slot)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(zoneColor)
            }

            if workout.isPriority {
                Text("PRIORITY")
                    .font(.system(size: 9, weight: .bold))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 5)
                    .padding(.vertical, 1.5)
                    .background(UH.Palette.activeFill, in: Capsule())
            }

            // Type Chip in Zone Colour with inner colored indicator dot
            HStack(spacing: 4) {
                Circle()
                    .fill(zoneColor)
                    .frame(width: 5, height: 5)
                Text(chipLabel)
                    .font(.system(size: 11, weight: .bold))
            }
            .foregroundStyle(zoneColor)
            .padding(.horizontal, 7)
            .padding(.vertical, 2)
            .background(zoneColor.opacity(0.14), in: RoundedRectangle(cornerRadius: 6))
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(zoneColor.opacity(0.35), lineWidth: 0.9))
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
                .font(.system(size: 12.5, weight: .medium, design: .monospaced))
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
                        .font(.system(size: 24))
                        .foregroundStyle(UH.Palette.accentInk)
                } else if workout.isMissedFlag {
                    HStack(spacing: 3) {
                        Image(systemName: "xmark.circle")
                            .font(.system(size: 13))
                        Text("Missed")
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 4)
                    .background(UH.Palette.hover, in: Capsule())
                } else {
                    Image(systemName: "circle")
                        .font(.system(size: 24))
                        .foregroundStyle(UH.Palette.line)
                }
            }
            .frame(minWidth: 44, minHeight: 44)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("workout.\(workout.id).done")
        .accessibilityLabel(workout.isDone ? "Mark as not done" : "Mark as done")
    }

    private func accessibility(_ w: Workout) -> String {
        var parts = [w.title, "\(Int(w.durationMinutes)) minutes"]
        if let km = w.distanceKm, km > 0 { parts.append("\(km.formatted(.number.precision(.fractionLength(0...1)))) kilometres") }
        if w.isPriority { parts.append("priority") }
        if w.isDone { parts.append("done") } else if w.isMissedFlag { parts.append("missed") }
        return parts.joined(separator: ", ")
    }

    // MARK: - Compact Synced Watch Badge

    private func matchedActivityBadge(_ workout: Workout) -> some View {
        let modelName = workout.matchedDeviceModel ?? "COROS"
        return Button {
            onSelect(workout)
        } label: {
            HStack(spacing: 5) {
                Image(systemName: "applewatch")
                    .font(.system(size: 10.5, weight: .semibold))
                    .foregroundStyle(UH.Palette.accentInk)
                Text(modelName)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(UH.Palette.ink)

                if let km = workout.matchedDistanceKm {
                    Text("· \(String(format: "%.1f", km)) km")
                        .font(.system(size: 10.5, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }
                if let secs = workout.matchedDurationSeconds {
                    let mins = Int(secs / 60)
                    Text("· \(mins)m")
                        .font(.system(size: 10.5, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }
                if let hr = workout.matchedAvgHr {
                    Text("· \(hr) bpm")
                        .font(.system(size: 10.5, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }

                Spacer()

                HStack(spacing: 3) {
                    Circle()
                        .fill(UH.Palette.accentInk)
                        .frame(width: 4, height: 4)
                    Text("Matched")
                        .font(.system(size: 9.5, weight: .bold))
                        .foregroundStyle(UH.Palette.accentInk)
                }
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(UH.Palette.activeFill, in: Capsule())
                .fixedSize()

                Image(systemName: "chevron.right")
                    .font(.system(size: 8.5, weight: .bold))
                    .foregroundStyle(UH.Palette.muted)
            }
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(UH.Palette.surface.opacity(0.85), in: RoundedRectangle(cornerRadius: 6))
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(UH.Palette.line.opacity(0.6), lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("workout.\(workout.id).matched")
    }
}

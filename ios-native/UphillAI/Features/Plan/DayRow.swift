import SwiftUI

struct DayRow: View {
    let day: PlanDay
    let onSelect: (Workout) -> Void

    var body: some View {
        if day.isCollapsed {
            restRow
        } else {
            workoutCard
        }
    }

    private var dateText: String {
        guard let date = day.date else { return day.weekday.short }
        return date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
    }

    private var isPriority: Bool { day.workouts.contains(where: \.isPriority) }

    private var restRow: some View {
        HStack(spacing: UH.Space.compact) {
            if let eyebrow = day.eyebrow {
                Text(eyebrow).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.accentInk)
            }
            Text(dateText).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
            Spacer()
            Label("Rest", systemImage: "moon.zzz")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.muted)
        }
        .padding(.horizontal, UH.Space.regular)
        .frame(minHeight: 44)
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier(dayIdentifier)
    }

    private var dayIdentifier: String { day.eyebrow == "TODAY" ? "day.today" : "day.\(day.weekday.rawValue)" }

    private var workoutCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            ViewThatFits(in: .horizontal) {
                HStack(spacing: UH.Space.compact) { markers; dateCaption }
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: UH.Space.compact) { markers }
                    dateCaption
                }
            }
            ForEach(day.workouts) { workout in
                Button { onSelect(workout) } label: { workoutRow(workout) }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("workout.\(workout.id)")
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier(dayIdentifier)
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(day.isToday ? UH.Palette.activeFill : UH.Palette.card,
                    in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.workoutDay)
                .stroke(isPriority ? UH.Palette.accentInk : UH.Palette.line, lineWidth: isPriority ? 1.5 : 1)
        )
    }

    @ViewBuilder
    private var markers: some View {
        if let eyebrow = day.eyebrow {
            Text(eyebrow).font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
        }
        if isPriority {
            Text("PRIORITY").font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.accentInk)
        }
    }

    private var dateCaption: some View {
        Text(dateText).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
    }

    private func workoutRow(_ workout: Workout) -> some View {
        HStack(spacing: UH.Space.small) {
            VStack(alignment: .leading, spacing: 2) {
                Text(workout.title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text(details(workout)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            stateIcon(workout)
        }
        .frame(minHeight: 44)
        .contentShape(Rectangle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibility(workout))
        .accessibilityAddTraits(.isButton)
    }

    private func details(_ w: Workout) -> String {
        var parts = ["\(Int(w.durationMinutes)) min"]
        if let km = w.distanceKm, km > 0 { parts.append(km.formatted(.number.precision(.fractionLength(0...1))) + " km") }
        if !w.targetZone.isEmpty, w.targetZone != "Rest" { parts.append(w.targetZone) }
        return parts.joined(separator: " · ")
    }

    @ViewBuilder
    private func stateIcon(_ w: Workout) -> some View {
        if w.isDone {
            Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk)
        } else if w.isMissedFlag {
            Image(systemName: "xmark.circle").foregroundStyle(UH.Palette.danger)
        } else {
            Image(systemName: "chevron.right").foregroundStyle(UH.Palette.muted).font(UH.TextStyle.disclosure)
        }
    }

    private func accessibility(_ w: Workout) -> String {
        var parts = [w.title, "\(Int(w.durationMinutes)) minutes"]
        if let km = w.distanceKm, km > 0 { parts.append(km.formatted(.number.precision(.fractionLength(0...1))) + " kilometres") }
        if w.isPriority { parts.append("priority") }
        if w.isDone { parts.append("done") } else if w.isMissedFlag { parts.append("missed") }
        return parts.joined(separator: ", ")
    }
}

import SwiftUI

extension BRaceLevel {
    var ink: Color {
        switch self {
        case .good: UH.Palette.accentInk
        case .conditions: UH.Palette.warningInk
        case .risky, .notRecommended: UH.Palette.danger
        }
    }

    var fill: Color {
        switch self {
        case .good: UH.Palette.activeFill
        case .conditions: UH.Palette.warningFill
        case .risky, .notRecommended: UH.Palette.danger.opacity(0.12)
        }
    }
}

/// The plan's B-races and its A-race by date, each with a badge; opens a race, adds one, or asks for a debrief.
struct NextRacesCard: View {
    let model: PlanViewModel
    let onAdd: () -> Void
    let onOpen: (BRace) -> Void
    let onDebrief: (BRace) -> Void
    @Environment(\.locale) private var locale

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            HStack {
                Text(L("Next races").uppercased())
                    .font(UH.TextStyle.eyebrow).tracking(0.5).foregroundStyle(UH.Palette.secondary)
                Spacer()
                if model.canAddRaces {
                    Button(L("+ Add race"), action: onAdd)
                        .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("races.add")
                }
            }
            ForEach(model.nextRaces) { row in
                VStack(alignment: .leading, spacing: 6) {
                    if let race = row.race {
                        Button { onOpen(race) } label: { rowView(row) }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("races.open.\(race.id)")
                        if model.raceNeedsDebrief(race) {
                            Button(L("How did %@ go?", race.raceName)) { onDebrief(race) }
                                .font(UH.TextStyle.label)
                                .padding(.horizontal, UH.Space.small).frame(minHeight: 40)
                                .background(UH.Palette.hover, in: Capsule())
                                .foregroundStyle(UH.Palette.ink)
                                .accessibilityIdentifier("races.debrief.\(race.id)")
                        }
                    } else {
                        rowView(row)
                    }
                }
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line, lineWidth: 1))
        .accessibilityIdentifier("plan.nextRaces")
    }

    private func rowView(_ row: NextRace) -> some View {
        HStack(spacing: UH.Space.small) {
            VStack(spacing: 0) {
                Text(verbatim: monthLabel(row.date)).font(.caption2.weight(.bold)).lineLimit(1).minimumScaleFactor(0.7)
                Text(row.date, format: .dateTime.day()).font(.headline)
            }
            .frame(width: 44, height: 44)
            .background(row.isGoal ? UH.Palette.ink : UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: 10))
            .foregroundStyle(row.isGoal ? UH.Palette.card : UH.Palette.accentInk)
            .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 2) {
                Text(verbatim: row.name).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink).lineLimit(2)
                Text(verbatim: subtitle(row)).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
            Spacer(minLength: 4)
            if let level = row.race?.verdict.level {
                Text(verbatim: level.title)
                    .font(.caption.weight(.bold)).padding(.horizontal, 9).padding(.vertical, 3)
                    .background(level.fill, in: Capsule()).foregroundStyle(level.ink)
            } else {
                Text("Goal")
                    .font(.caption.weight(.bold)).padding(.horizontal, 9).padding(.vertical, 3)
                    .background(UH.Palette.ink, in: Capsule()).foregroundStyle(UH.Palette.card)
            }
        }
        .frame(minHeight: 44)
        .contentShape(Rectangle())
    }

    /// "NOV" in English; "TH11" in Vietnamese, where the month name ("tháng 11") is too long for the badge.
    private func monthLabel(_ date: Date) -> String {
        if locale.language.languageCode == .vietnamese {
            return "TH\(Calendar(identifier: .gregorian).component(.month, from: date))"
        }
        return date.formatted(.dateTime.month(.abbreviated).locale(locale)).uppercased()
    }

    private func subtitle(_ row: NextRace) -> String {
        guard let race = row.race else { return L("A-race") }
        let km = race.distanceKm.formatted(.number.precision(.fractionLength(0...1)))
        return race.effort == .training ? L("B-race · %@ km · training run", km) : L("B-race · %@ km", km)
    }
}

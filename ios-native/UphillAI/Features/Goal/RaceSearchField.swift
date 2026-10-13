import SwiftUI

/// Race name field that suggests known races from the KB as you type, then
/// lets you pick which of the race's distances you're running.
struct RaceSearchField: View {
    @Binding var raceName: String
    let service: RaceMatchService?
    var placeholder: String = L("Search race name or enter manually")
    /// Called with the picked course (distance km, D+ m, label).
    let onPick: (RaceDistance) -> Void
    /// Called when the name is edited away from a matched race, so stale course values can be dropped.
    var onClear: (() -> Void)? = nil

    @State private var candidates: [RaceMatch] = []
    @State private var selected: RaceMatch?
    @State private var pickedDistance: RaceDistance?

    private var distances: [RaceDistance] {
        guard let selected else { return [] }
        var list = selected.distances ?? []
        if list.isEmpty, let km = selected.distanceKm {
            list = [RaceDistance(label: selected.distanceLabel, distanceKm: km, elevationGainM: selected.elevationGainM)]
        }
        return list.sorted { $0.distanceKm < $1.distanceKm }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").foregroundStyle(UH.Palette.muted)
                TextField(placeholder, text: $raceName)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .font(UH.TextStyle.body)
                if selected != nil {
                    Image(systemName: "checkmark.seal.fill").foregroundStyle(UH.Palette.accentInk)
                        .accessibilityLabel(L("Matched race"))
                }
            }
            .padding(10)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(selected != nil ? UH.Palette.accent : UH.Palette.line))

            if !candidates.isEmpty {
                VStack(spacing: 0) {
                    ForEach(Array(candidates.prefix(5).enumerated()), id: \.offset) { index, race in
                        Button { select(race) } label: {
                            HStack(spacing: 10) {
                                Image(systemName: "flag.checkered").foregroundStyle(UH.Palette.accentInk)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(race.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                                    if let summary = summary(race) {
                                        Text(summary).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                    }
                                }
                                Spacer()
                                Image(systemName: "arrow.up.left").font(.caption).foregroundStyle(UH.Palette.muted)
                            }
                            .padding(.horizontal, 10)
                            .frame(minHeight: 48)
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("raceSearch.candidate.\(index)")
                        if index < min(candidates.count, 5) - 1 { Divider() }
                    }
                }
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
            }

            if distances.count > 1 {
                Text("Which distance?").font(UH.TextStyle.disclosure).foregroundStyle(UH.Palette.secondary)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(distances, id: \.self) { d in
                            let on = pickedDistance == d
                            Button { pick(d) } label: {
                                Text(d.label ?? L("%@ km", d.distanceKm.formatted()))
                                    .font(UH.TextStyle.caption.weight(.semibold).monospacedDigit())
                                    .padding(.horizontal, 12)
                                    .frame(minHeight: 36)
                                    .foregroundStyle(on ? UH.Palette.accentInk : UH.Palette.ink)
                                    .background(on ? UH.Palette.activeFill : UH.Palette.card, in: Capsule())
                                    .overlay(Capsule().stroke(on ? UH.Palette.accent : UH.Palette.line))
                            }
                            .buttonStyle(.plain)
                            .accessibilityAddTraits(on ? .isSelected : [])
                        }
                    }
                }
            }
        }
        .task(id: raceName) { await search() }
    }

    private func summary(_ race: RaceMatch) -> String? {
        if let label = race.distanceLabel { return label }
        let labels = (race.distances ?? []).compactMap { $0.label ?? "\(Int($0.distanceKm)) km" }
        return labels.isEmpty ? nil : labels.joined(separator: " · ")
    }

    private func select(_ race: RaceMatch) {
        selected = race
        candidates = []
        raceName = race.raceName
        if let km = race.distanceKm {
            pick(RaceDistance(label: race.distanceLabel, distanceKm: km, elevationGainM: race.elevationGainM))
        } else if distances.count == 1, let only = distances.first {
            pick(only)
        }
    }

    private func pick(_ d: RaceDistance) {
        pickedDistance = d
        onPick(d)
    }

    private func search() async {
        let name = raceName.trimmingCharacters(in: .whitespacesAndNewlines)
        if selected?.raceName == name { return }
        if selected != nil { onClear?() }
        selected = nil
        pickedDistance = nil
        guard name.count >= 3, let service else { candidates = []; return }
        do {
            try await Task.sleep(for: .milliseconds(450))
            let result = try await service.match(name: name)
            try Task.checkCancellation()
            if result.autoApply == true, let match = result.match {
                select(match)
            } else {
                candidates = result.candidates ?? (result.match.map { [$0] } ?? [])
            }
        } catch {}
    }
}

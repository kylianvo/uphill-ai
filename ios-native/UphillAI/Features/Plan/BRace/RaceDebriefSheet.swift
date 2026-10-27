import SwiftUI

/// After a B-race: the time (pre-filled when the watch gave it), three one-tap rehearsal questions, then the
/// coach's debrief and, when the goal estimate moved, a pointer to the Goal sheet (the runner confirms there).
struct RaceDebriefSheet: View {
    let model: PlanViewModel
    let race: BRace
    @Environment(\.dismiss) private var dismiss
    @State private var time: String
    @State private var answers = BRaceDebriefAnswers()
    @State private var result: BRaceDebriefResult?
    @State private var error: String?
    @State private var busy = false

    init(model: PlanViewModel, race: BRace) {
        self.model = model
        self.race = race
        _time = State(initialValue: race.resultSeconds?.raceTime ?? "")
    }

    private static let options: [(key: WritableKeyPath<BRaceDebriefAnswers, String?>, title: LocalizedStringKey, choices: [(String, LocalizedStringKey)])] = [
        (\.fuel, "Fuel", [("plan", "Went to plan"), ("stomach", "Stomach trouble"), ("skipped", "Skipped some")]),
        (\.pacing, "Pacing", [("even", "Even"), ("fast_start", "Too fast early"), ("held_back", "Held back")]),
        (\.gear, "Gear", [("ok", "All good"), ("change", "Something to change")]),
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let result {
                        Text(verbatim: result.debrief.text ?? "").font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
                            .accessibilityIdentifier("debrief.text")
                        if let hours = result.goal.suggestedTargetHours {
                            Text(L("Your goal-race estimate moved to %@. Review it in Goal.", Self.hours(hours)))
                                .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                        }
                        Button { dismiss() } label: { Text("Done").frame(maxWidth: .infinity) }.buttonStyle(PrimaryButtonStyle())
                    } else {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Finish time (h:mm:ss)").font(UH.TextStyle.label)
                            TextField("3:11:00", text: $time).keyboardType(.numbersAndPunctuation)
                                .padding(UH.Space.small)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                                .accessibilityIdentifier("debrief.time")
                            if let p = race.predicted {
                                Text(L("Predicted: %@–%@", p.lowSec.raceTime, p.highSec.raceTime))
                                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            }
                        }
                        Text(L("How did the rehearsal go?").uppercased()).font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        ForEach(Self.options.indices, id: \.self) { i in
                            let group = Self.options[i]
                            VStack(alignment: .leading, spacing: 6) {
                                Text(group.title).font(UH.TextStyle.label)
                                FlowRow(group.choices.map(\.0)) { value in
                                    let label = group.choices.first { $0.0 == value }!.1
                                    let on = answers[keyPath: group.key] == value
                                    Button { answers[keyPath: group.key] = value } label: {
                                        Text(label).font(UH.TextStyle.caption.weight(on ? .semibold : .regular))
                                            .padding(.horizontal, UH.Space.small).frame(minHeight: 40)
                                            .background(on ? UH.Palette.activeFill : UH.Palette.card, in: Capsule())
                                            .overlay(Capsule().stroke(on ? UH.Palette.accentInk : UH.Palette.line, lineWidth: 1))
                                            .foregroundStyle(on ? UH.Palette.accentInk : UH.Palette.ink)
                                    }
                                    .buttonStyle(.plain)
                                    .accessibilityAddTraits(on ? .isSelected : [])
                                }
                            }
                        }
                        if let error { Text(verbatim: error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
                        Button { send() } label: { Text("Get my debrief").frame(maxWidth: .infinity) }
                            .buttonStyle(PrimaryButtonStyle()).disabled(busy)
                            .accessibilityIdentifier("debrief.send")
                    }
                }
                .padding(UH.Space.regular)
            }
            .navigationTitle(L("%@ · Debrief", race.raceName))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Close") { dismiss() } } }
        }
    }

    /// "3:11:00" or "3:11" → seconds; nil when it isn't a time.
    static func seconds(_ text: String) -> Int? {
        let parts = text.trimmingCharacters(in: .whitespaces).split(separator: ":").map { Int($0) }
        guard (2...3).contains(parts.count), parts.allSatisfy({ $0 != nil && $0! >= 0 }) else { return nil }
        let h = parts[0]!, m = parts[1]!, s = parts.count == 3 ? parts[2]! : 0
        guard m < 60, s < 60, h * 3600 + m * 60 + s > 0 else { return nil }
        return h * 3600 + m * 60 + s
    }

    static func hours(_ h: Double) -> String { String(format: "%d:%02d", Int(h), Int(((h - floor(h)) * 60).rounded())) }

    private func send() {
        let trimmed = time.trimmingCharacters(in: .whitespaces)
        let secs = trimmed.isEmpty ? nil : Self.seconds(trimmed)
        if !trimmed.isEmpty && secs == nil { error = L("Enter a time like 3:11:00."); return }
        busy = true
        Task {
            switch await model.submitRaceDebrief(race, seconds: secs, answers: answers) {
            case .success(let r): result = r; error = nil
            case .failure(let e): error = e.userMessage
            }
            busy = false
        }
    }
}

/// Wraps chips onto as many lines as they need.
private struct FlowRow<Content: View>: View {
    let values: [String]
    let content: (String) -> Content
    init(_ values: [String], @ViewBuilder content: @escaping (String) -> Content) { self.values = values; self.content = content }
    var body: some View {
        ViewThatFits(in: .horizontal) {
            HStack(spacing: 6) { ForEach(values, id: \.self, content: content) }
            VStack(alignment: .leading, spacing: 6) { ForEach(values, id: \.self, content: content) }
        }
    }
}

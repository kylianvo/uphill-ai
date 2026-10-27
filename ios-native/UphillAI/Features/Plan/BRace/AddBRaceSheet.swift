import SwiftUI

/// Add a B-race (or open one): the coach's verdict updates as the race changes, and the safer option is the
/// main button whenever the race isn't a good test. The runner can always keep their own choice.
/// Built like plan setup: pick the race from the race list (or type one in), its distance, then the effort.
struct AddBRaceSheet: View {
    let model: PlanViewModel
    var race: BRace? = nil
    var raceMatch: RaceMatchService? = nil
    var goalService: (any GoalEstimateServicing)? = nil
    var raceHistory: (any RaceHistoryServicing)? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var input: BRaceInput
    @State private var date: Date
    /// True once a race from the race list and one of its distances is picked: the course comes from the list.
    @State private var matched = false
    @State private var assessment: BRaceAssessment?
    @State private var error: String?
    @State private var busy = false
    @State private var confirmCancel = false
    @State private var showGoal = false

    init(model: PlanViewModel, race: BRace? = nil, raceMatch: RaceMatchService? = nil,
         goalService: (any GoalEstimateServicing)? = nil, raceHistory: (any RaceHistoryServicing)? = nil) {
        self.model = model
        self.race = race
        self.raceMatch = raceMatch
        self.goalService = goalService
        self.raceHistory = raceHistory
        let day = race.flatMap { PlanCalendar.day(from: $0.raceDate) } ?? Calendar.current.date(byAdding: .day, value: 28, to: Date())!
        _date = State(initialValue: day)
        _input = State(initialValue: BRaceInput(raceName: race?.raceName ?? "", raceDate: PlanCalendar.ymd(day),
                                               distanceKm: race?.distanceKm, elevationGainM: race?.elevationGainM,
                                               effort: race?.effort ?? .race, raceId: race?.id))
    }

    private var named: Bool { input.raceName.trimmingCharacters(in: .whitespaces).count >= 3 }
    /// A matched race waits for its distance chip; a typed-in race is checked as soon as it has a name.
    private var ready: Bool { named && (!matched || input.distanceKm != nil) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let opinion = race?.opinion {
                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                            Label("Coach Uphill", systemImage: "quote.bubble.fill")
                                .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                            Text(verbatim: opinion).font(UH.TextStyle.body).foregroundStyle(UH.Palette.ink)
                        }
                        .trainingCard()
                    }

                    raceCard

                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("How will you run it?").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        SetupOption(title: "Race it", symbol: "flame.fill", selected: input.effort == .race) { input.effort = .race }
                        SetupOption(title: "As a training run", symbol: "figure.run", selected: input.effort == .training) { input.effort = .training }
                    }

                    if let error {
                        Label { Text(verbatim: error) } icon: { Image(systemName: "exclamationmark.circle.fill") }
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.danger)
                            .padding(UH.Space.small)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(UH.Palette.danger.opacity(0.08), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if let assessment {
                        verdictCard(assessment)
                        goalLink
                        actions(assessment.verdict)
                    } else if ready && error == nil {
                        ProgressView(L("Coach Uphill is checking…"))
                            .font(UH.TextStyle.caption)
                            .frame(maxWidth: .infinity, minHeight: 64)
                    }

                    if let race {
                        Button("Cancel this race", role: .destructive) { confirmCancel = true }
                            .font(UH.TextStyle.label)
                            .frame(maxWidth: .infinity, minHeight: 44)
                            .confirmationDialog("Cancel this race? Your plan goes back to normal.", isPresented: $confirmCancel, titleVisibility: .visible) {
                                Button("Cancel race", role: .destructive) {
                                    Task { if await model.cancelRace(race.id) == nil { dismiss() } }
                                }
                            }
                    }
                }
                .padding(UH.Space.regular)
            }
            .scrollDismissesKeyboard(.interactively)
            .background(UH.Palette.surface)
            .navigationTitle(race == nil ? L("Add a race") : L("Your B-race"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Close") { dismiss() } } }
            .onChange(of: date) { _, d in input.raceDate = PlanCalendar.ymd(d) }
            .task(id: input) { await assess() }
            .sheet(isPresented: $showGoal) {
                if let goalService {
                    NavigationStack {
                        GoalDeterminerSheet(service: goalService, isPresentedInSheet: true, raceHistoryService: raceHistory,
                                            prefill: GoalPrefill(raceName: input.raceName, distanceKm: input.distanceKm,
                                                                 elevationGainM: input.elevationGainM, raceDate: date))
                            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Close") { showGoal = false } } }
                    }
                }
            }
        }
    }

    /// The race: search the race list, pick its distance, set the date; course fields only for a race not in the list.
    private var raceCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            RaceSearchField(raceName: $input.raceName, service: raceMatch,
                            onPick: { d in
                                matched = true
                                input.distanceKm = d.distanceKm
                                input.elevationGainM = d.elevationGainM
                            },
                            onClear: {
                                matched = false
                                input.distanceKm = nil
                                input.elevationGainM = nil
                            },
                            selectedKm: race?.distanceKm)
                .accessibilityIdentifier("race.name")

            Divider().overlay(UH.Palette.line.opacity(0.6))

            DatePicker("Date", selection: $date, displayedComponents: .date)
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.ink)
                .tint(UH.Palette.accentInk)

            if matched, let km = input.distanceKm {
                Label(courseLine(km: km, gain: input.elevationGainM), systemImage: "mountain.2.fill")
                    .font(UH.TextStyle.caption.monospacedDigit())
                    .foregroundStyle(UH.Palette.secondary)
            } else if named {
                Divider().overlay(UH.Palette.line.opacity(0.6))
                courseField("Distance (km)", value: $input.distanceKm, unit: "km", keyboard: .decimalPad)
                    .accessibilityIdentifier("race.distance")
                courseField("Climbing (m)", value: $input.elevationGainM, unit: "m", keyboard: .numberPad)
            }
        }
        .trainingCard()
    }

    private func courseField(_ title: LocalizedStringKey, value: Binding<Double?>, unit: String, keyboard: UIKeyboardType) -> some View {
        HStack {
            Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            Spacer()
            TextField(unit, value: value, format: .number)
                .keyboardType(keyboard)
                .multilineTextAlignment(.trailing)
                .font(UH.TextStyle.body.monospacedDigit())
                .frame(maxWidth: 120)
        }
        .frame(minHeight: 44)
    }

    private func courseLine(km: Double, gain: Double?) -> String {
        let distance = L("%@ km", km.formatted(.number.precision(.fractionLength(0...1))))
        guard let gain, gain > 0 else { return distance }
        return "\(distance) · \(Int(gain).formatted()) m D+"
    }

    /// Opens the Goal Determiner on this race, as plan setup does for the goal race.
    @ViewBuilder private var goalLink: some View {
        if goalService != nil, input.distanceKm != nil {
            Button { showGoal = true } label: {
                HStack(spacing: UH.Space.small) {
                    Image(systemName: "target")
                    Text("Estimate your finish time")
                    Spacer()
                    Image(systemName: "chevron.right").font(.footnote.weight(.semibold))
                }
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.accentInk)
                .frame(minHeight: 44)
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("race.goalDeterminer")
        }
    }

    private func assess() async {
        guard ready else { error = nil; assessment = nil; return }
        try? await Task.sleep(for: .milliseconds(400))  // debounce typing
        guard !Task.isCancelled else { return }
        switch await model.assessRace(input) {
        case .success(let result): assessment = result; error = nil
        case .failure(let failure): assessment = nil; error = Self.message(failure)
        }
    }

    static func message(_ error: APIError) -> String {
        if case .http(_, let message, _) = error {
            switch message {
            case "distance_required": return L("Not in our race list: enter the distance below.")
            case "date_out_of_range": return L("Pick a date after today and before your goal race.")
            case "too_many_races": return L("A plan holds up to 3 B-races.")
            case "rebuild_in_progress": return L("Your plan is still updating. Try again in a minute.")
            default: break
            }
        }
        return error.userMessage
    }

    private func verdictCard(_ a: BRaceAssessment) -> some View {
        let v = a.verdict
        return VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(alignment: .firstTextBaseline) {
                Text(verbatim: v.level.title)
                    .font(UH.TextStyle.label.weight(.bold))
                    .padding(.horizontal, 10).padding(.vertical, 4)
                    .background(v.level.ink, in: Capsule())
                    .foregroundStyle(UH.Palette.card)
                Spacer()
                if let p = a.predicted {
                    Text(L("Predicted: %@–%@", p.lowSec.raceTime, p.highSec.raceTime))
                        .font(UH.TextStyle.caption.monospacedDigit())
                        .foregroundStyle(UH.Palette.ink)
                }
            }
            ForEach(v.reasons, id: \.self) { reason in
                Label(BRaceVerdict.reasonTitle(reason), systemImage: v.level == .good ? "checkmark" : "exclamationmark.triangle")
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.ink)
            }
            Text(L("%lld easy days before, %lld easy days after.", v.taperDays, v.recoveryDays))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            if let changes = v.cost?.changed, !changes.isEmpty {
                Divider().overlay(v.level.ink.opacity(0.2))
                Text("What it would change").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                ForEach(changes.prefix(5), id: \.self) { c in
                    HStack(alignment: .firstTextBaseline, spacing: UH.Space.compact) {
                        Text(verbatim: "W\(c.week) \(L(c.day).prefix(3))")
                            .font(UH.TextStyle.caption.monospacedDigit().weight(.semibold))
                            .foregroundStyle(UH.Palette.secondary)
                            .frame(width: 64, alignment: .leading)
                        Text(verbatim: "\(c.titleBefore) → \(c.titleAfter)")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.ink)
                    }
                }
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(v.level.fill, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(v.level.ink.opacity(0.25), lineWidth: 1))
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("race.verdict")
    }

    private func actions(_ verdict: BRaceVerdict) -> some View {
        let choice = BRaceChoice.options(for: verdict, input: input)
        return VStack(spacing: UH.Space.compact) {
            Button { save(choice.primary.input) } label: {
                Text(verbatim: race != nil && verdict.level == .good ? L("Save") : choice.primary.label).frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(busy)
            .accessibilityIdentifier("race.primary")
            if let secondary = choice.secondary {
                Button { save(secondary.input) } label: { Text(verbatim: secondary.label).frame(maxWidth: .infinity, minHeight: 44) }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(secondary.isWarning ? UH.Palette.danger : UH.Palette.ink)
                    .disabled(busy)
                    .accessibilityIdentifier("race.secondary")
            }
        }
    }

    private func save(_ body: BRaceInput) {
        busy = true
        Task {
            let failure = await model.saveRace(body, raceID: race?.id)
            busy = false
            if let failure { error = failure } else { dismiss() }
        }
    }
}

import SwiftUI

/// Add a B-race (or open one): the coach's verdict updates as the race changes, and the safer option is the
/// main button whenever the race isn't a good test. The runner can always keep their own choice.
struct AddBRaceSheet: View {
    let model: PlanViewModel
    var race: BRace? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var input: BRaceInput
    @State private var date: Date
    @State private var assessment: BRaceAssessment?
    @State private var error: String?
    @State private var busy = false
    @State private var confirmCancel = false

    init(model: PlanViewModel, race: BRace? = nil) {
        self.model = model
        self.race = race
        let day = race.flatMap { PlanCalendar.day(from: $0.raceDate) } ?? Calendar.current.date(byAdding: .day, value: 28, to: Date())!
        _date = State(initialValue: day)
        _input = State(initialValue: BRaceInput(raceName: race?.raceName ?? "", raceDate: PlanCalendar.ymd(day),
                                               distanceKm: race?.distanceKm, elevationGainM: race?.elevationGainM,
                                               effort: race?.effort ?? .race))
    }

    private var ready: Bool { input.raceName.trimmingCharacters(in: .whitespaces).count >= 3 }

    var body: some View {
        NavigationStack {
            Form {
                if let opinion = race?.opinion {
                    Section("Coach Uphill") { Text(verbatim: opinion).font(UH.TextStyle.body) }
                }
                Section {
                    TextField("Race", text: $input.raceName).textInputAutocapitalization(.words)
                        .accessibilityIdentifier("race.name")
                    DatePicker("Date", selection: $date, displayedComponents: .date)
                    HStack {
                        Text("Distance (km)")
                        TextField("km", value: $input.distanceKm, format: .number).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                            .accessibilityIdentifier("race.distance")
                    }
                    HStack {
                        Text("Climbing (m)")
                        TextField("m", value: $input.elevationGainM, format: .number).keyboardType(.numberPad).multilineTextAlignment(.trailing)
                    }
                    if let options = assessment?.race.optionsKm, options.count > 1 {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                ForEach(options, id: \.self) { km in
                                    Button("\(km.formatted(.number.precision(.fractionLength(0...1)))) km") { input.distanceKm = km }
                                        .buttonStyle(.bordered)
                                        .tint(km == input.distanceKm ? UH.Palette.accentInk : UH.Palette.secondary)
                                }
                            }
                        }
                    }
                    Picker("How will you run it?", selection: $input.effort) {
                        Text("Race it").tag(BRaceEffort.race)
                        Text("As a training run").tag(BRaceEffort.training)
                    }
                    .pickerStyle(.segmented)
                }
                if let error {
                    Section { Text(verbatim: error).foregroundStyle(UH.Palette.danger).font(UH.TextStyle.caption) }
                }
                if let assessment {
                    verdictSection(assessment)
                    actionSection(assessment.verdict)
                } else if ready && error == nil {
                    Section { ProgressView(L("Coach Uphill is checking…")) }
                }
                if let race {
                    Section {
                        Button("Cancel this race", role: .destructive) { confirmCancel = true }
                    }
                    .confirmationDialog("Cancel this race? Your plan goes back to normal.", isPresented: $confirmCancel, titleVisibility: .visible) {
                        Button("Cancel race", role: .destructive) {
                            Task { if await model.cancelRace(race.id) == nil { dismiss() } }
                        }
                    }
                }
            }
            .navigationTitle(race == nil ? L("Add a race") : L("Your B-race"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Close") { dismiss() } } }
            .onChange(of: date) { _, d in input.raceDate = PlanCalendar.ymd(d) }
            .task(id: input) { await assess() }
        }
    }

    private func assess() async {
        guard ready else { return }
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
            case "distance_required": return L("We couldn't find this race in our list: add its distance.")
            case "date_out_of_range": return L("Pick a date after today and before your goal race.")
            case "too_many_races": return L("A plan holds up to 3 B-races.")
            default: break
            }
        }
        return error.userMessage
    }

    private func verdictSection(_ a: BRaceAssessment) -> some View {
        let v = a.verdict
        return Section {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text(verbatim: v.level.title)
                    .font(.caption.weight(.bold)).padding(.horizontal, 9).padding(.vertical, 3)
                    .background(v.level.ink, in: Capsule()).foregroundStyle(UH.Palette.card)
                ForEach(v.reasons, id: \.self) { Text(verbatim: "• " + BRaceVerdict.reasonTitle($0)).font(UH.TextStyle.body) }
                Text(L("%lld easy days before, %lld easy days after.", v.taperDays, v.recoveryDays))
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                if let p = a.predicted {
                    Text(L("Predicted: %@–%@", p.lowSec.raceTime, p.highSec.raceTime)).font(UH.TextStyle.caption)
                }
                if let changes = v.cost?.changed, !changes.isEmpty {
                    Text("What it would change").font(UH.TextStyle.label).padding(.top, 4)
                    ForEach(changes.prefix(5), id: \.self) { c in
                        Text(verbatim: "W\(c.week) \(L(c.day).prefix(3)): \(c.titleBefore) → \(c.titleAfter)").font(UH.TextStyle.caption)
                    }
                }
            }
            .padding(.vertical, 4)
            .listRowBackground(v.level.fill)
            .accessibilityIdentifier("race.verdict")
        }
    }

    private func actionSection(_ verdict: BRaceVerdict) -> some View {
        let choice = BRaceChoice.options(for: verdict, input: input)
        return Section {
            Button { save(choice.primary.input) } label: {
                Text(verbatim: race != nil && verdict.level == .good ? L("Save") : choice.primary.label).frame(maxWidth: .infinity)
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(busy)
            .accessibilityIdentifier("race.primary")
            if let secondary = choice.secondary {
                Button { save(secondary.input) } label: { Text(verbatim: secondary.label).frame(maxWidth: .infinity) }
                    .foregroundStyle(secondary.isWarning ? UH.Palette.danger : UH.Palette.ink)
                    .disabled(busy)
                    .accessibilityIdentifier("race.secondary")
            }
        }
        .listRowBackground(Color.clear)
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

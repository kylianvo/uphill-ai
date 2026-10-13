import SwiftUI

struct AddRaceSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any RaceHistoryServicing
    let editingResult: RaceResult?
    var onSaved: ((RaceResult) -> Void)? = nil
    @State private var draft: ManualRaceDraft
    @State private var isSaving = false
    @State private var errorMessage: String?

    init(service: any RaceHistoryServicing, editingResult: RaceResult? = nil, onSaved: ((RaceResult) -> Void)? = nil) {
        self.service = service; self.editingResult = editingResult; self.onSaved = onSaved
        _draft = State(initialValue: ManualRaceDraft(result: editingResult))
    }

    var body: some View {
        NavigationStack {
            Form {
                if let errorMessage {
                    Section { Text(errorMessage).foregroundStyle(UH.Palette.danger).accessibilityIdentifier("race.form.error") }
                }
                Section("Race") {
                    TextField("Race name", text: $draft.raceName).accessibilityIdentifier("race.form.name")
                    DatePicker("Race date", selection: $draft.date, displayedComponents: .date)
                    Picker("Discipline", selection: $draft.discipline) {
                        Text("Trail").tag("trail"); Text("Road").tag("road")
                    }.pickerStyle(.segmented)
                    TextField("Location (optional)", text: $draft.location)
                }
                Section("Course") {
                    TextField("Distance in km", text: $draft.distance).keyboardType(.decimalPad).accessibilityIdentifier("race.form.distance")
                    TextField("Elevation gain in m (optional)", text: $draft.elevation).keyboardType(.decimalPad)
                }
                Section("Your result") {
                    Toggle("Did not finish", isOn: $draft.isDnf)
                    if !draft.isDnf {
                        TextField("Finish time — h:mm:ss", text: $draft.duration).keyboardType(.numbersAndPunctuation).accessibilityIdentifier("race.form.time")
                    }
                    TextField("Bib (optional)", text: $draft.bib)
                    TextField("Result link (optional)", text: $draft.resultUrl).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    Text("A result link supports your record; it does not verify your identity.").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
                Section("Rankings (optional)") {
                    rankPair("Overall", rank: $draft.rankOverall, total: $draft.totalOverall)
                    rankPair("Gender", rank: $draft.rankGender, total: $draft.totalGender)
                    rankPair("Age group", rank: $draft.rankAgeGroup, total: $draft.totalAgeGroup)
                }
                Section("Race note") {
                    TextField("What would you like to remember?", text: $draft.userNote, axis: .vertical).lineLimit(3...8)
                }
            }
            .scrollDismissesKeyboard(.immediately)
            .disabled(isSaving)
            .navigationTitle(editingResult == nil ? "Add race result" : "Edit race result")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() }.disabled(isSaving) }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isSaving ? "Saving…" : "Save") { Task { await save() } }
                        .disabled(isSaving).accessibilityIdentifier("race.form.save")
                }
            }
        }
    }

    private func rankPair(_ label: String, rank: Binding<String>, total: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label).font(UH.TextStyle.label)
            HStack {
                TextField("Rank", text: rank).keyboardType(.numberPad).accessibilityLabel("\(label) rank")
                Text("of").foregroundStyle(UH.Palette.secondary)
                TextField("Finishers", text: total).keyboardType(.numberPad).accessibilityLabel("\(label) finishers")
            }
        }
    }

    private func save() async {
        isSaving = true; errorMessage = nil
        defer { isSaving = false }
        do {
            let payload = try draft.payload()
            let result: RaceResult
            if let editingResult { result = try await service.updateResult(id: editingResult.id, changes: payload.patchChanges()) }
            else { result = try await service.addResult(payload: payload) }
            onSaved?(result); dismiss()
        } catch { errorMessage = error.raceHistoryMessage }
    }
}

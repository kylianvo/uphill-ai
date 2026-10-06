import SwiftUI

struct AddRaceSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any RaceHistoryServicing
    var onSaved: ((RaceResult) -> Void)? = nil

    @State private var raceName: String = ""
    @State private var raceDate: Date = Date()
    @State private var discipline: String = "trail"
    @State private var distanceKm: Double = 50.0
    @State private var elevationGainM: Double = 2200.0
    @State private var hours: Int = 6
    @State private var minutes: Int = 30
    @State private var seconds: Int = 0
    @State private var isDnf: Bool = false
    @State private var rankOverall: String = ""
    @State private var totalOverall: String = ""

    @State private var isSaving: Bool = false
    @State private var errorMessage: String? = nil

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    var body: some View {
        NavigationStack {
            Form {
                if let error = errorMessage {
                    Section {
                        Text(error)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.danger)
                    }
                }

                Section("RACE DETAILS") {
                    TextField("Race name (e.g. Vietnam Mountain Marathon)", text: $raceName)
                    DatePicker("Race Date", selection: $raceDate, displayedComponents: .date)
                    Picker("Discipline", selection: $discipline) {
                        Text("Trail").tag("trail")
                        Text("Road").tag("road")
                    }
                    .pickerStyle(.segmented)
                }

                Section("COURSE STATS") {
                    HStack {
                        Text("Distance")
                        Spacer()
                        TextField("50", value: $distanceKm, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                        Text("km")
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    HStack {
                        Text("Elevation Gain (D+)")
                        Spacer()
                        TextField("Optional", value: $elevationGainM, format: .number)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                        Text("m")
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }

                Section("FINISH TIME & RANK") {
                    Toggle("Did not finish (DNF)", isOn: $isDnf)

                    if !isDnf {
                        HStack {
                            Text("Time")
                            Spacer()
                            HStack(spacing: 4) {
                                Picker("Hours", selection: $hours) {
                                    ForEach(0..<60) { h in Text("\(h)h").tag(h) }
                                }
                                .pickerStyle(.wheel)
                                .frame(width: 60, height: 90)
                                .clipped()

                                Picker("Minutes", selection: $minutes) {
                                    ForEach(0..<60) { m in Text("\(m)m").tag(m) }
                                }
                                .pickerStyle(.wheel)
                                .frame(width: 60, height: 90)
                                .clipped()

                                Picker("Seconds", selection: $seconds) {
                                    ForEach(0..<60) { s in Text("\(s)s").tag(s) }
                                }
                                .pickerStyle(.wheel)
                                .frame(width: 60, height: 90)
                                .clipped()
                            }
                        }
                    }

                    HStack {
                        Text("Overall Rank")
                        Spacer()
                        TextField("e.g. 42", text: $rankOverall)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }

                    HStack {
                        Text("Total Finishers")
                        Spacer()
                        TextField("e.g. 1200", text: $totalOverall)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                    }
                }
            }
            .navigationTitle("Add Race Result")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await save() }
                    } label: {
                        if isSaving {
                            ProgressView()
                        } else {
                            Text("Save")
                                .font(UH.TextStyle.label)
                        }
                    }
                    .disabled(isSaving || raceName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    private func save() async {
        isSaving = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        let timeSec: Int? = isDnf ? nil : (hours * 3600 + minutes * 60 + seconds)
        let rank: Int? = Int(rankOverall.trimmingCharacters(in: .whitespaces))
        let total: Int? = Int(totalOverall.trimmingCharacters(in: .whitespaces))

        let payload = ManualResultPayload(
            raceName: raceName.trimmingCharacters(in: .whitespaces),
            raceDate: Self.dateFormatter.string(from: raceDate),
            discipline: discipline,
            distanceKm: distanceKm,
            elevationGainM: elevationGainM > 0 ? elevationGainM : nil,
            finishTimeSec: timeSec,
            isDnf: isDnf,
            rankOverall: rank,
            totalOverall: total
        )

        do {
            let result = try await service.addResult(payload: payload)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            onSaved?(result)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
        isSaving = false
    }
}

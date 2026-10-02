import SwiftUI

struct AdaptWeekSheet: View {
    let model: PlanViewModel
    let week: Int
    @Environment(\.dismiss) private var dismiss
    @State private var fatigue = FatigueLevel.medium
    @State private var rpe: Int?
    @State private var notes = ""
    @State private var isSubmitting = false
    @State private var error: String?
    @State private var schedule: ScheduleDraft

    init(model: PlanViewModel, week: Int) {
        self.model = model
        self.week = week
        _schedule = State(initialValue: ScheduleDraft(plan: model.snapshot?.plan))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Coach Uphill rebuilds the workouts you haven't done yet. Finished and synced workouts stay as they are.")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
                .listRowBackground(Color.clear)
                Section("How do you feel?") {
                    ForEach(FatigueLevel.allCases) { level in
                        Button { fatigue = level } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(level.title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                                    Text(level.subtitle).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                }
                                Spacer()
                                if fatigue == level { Image(systemName: "checkmark").foregroundStyle(UH.Palette.accentInk) }
                            }
                            .frame(minHeight: 44)
                        }
                        .accessibilityAddTraits(fatigue == level ? .isSelected : [])
                    }
                }
                .listRowBackground(UH.Palette.card)
                Section {
                    Stepper(value: Binding(get: { rpe ?? 5 }, set: { rpe = $0 }), in: 1...10) {
                        HStack {
                            Text("Effort (RPE)")
                            Spacer()
                            Text(rpe.map(String.init) ?? "Not set").foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    TextField("What's going on?", text: $notes, axis: .vertical).lineLimit(2...5)
                }
                .listRowBackground(UH.Palette.card)
                Section {
                    DisclosureGroup("Change my schedule") {
                        ScheduleEditor(draft: $schedule, workouts: model.snapshot?.workouts.filter { $0.weekNumber == week } ?? [])
                    }
                }.listRowBackground(UH.Palette.card)
                Section {
                    if let error { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
                    Button { Task { await submit() } } label: {
                        if isSubmitting { ProgressView() } else { Text("Adapt week \(week)") }
                    }
                    .buttonStyle(.uhPrimary).disabled(isSubmitting).accessibilityIdentifier("adapt.submit")
                    .listRowBackground(Color.clear).listRowInsets(EdgeInsets())
                }
            }
            .scrollContentBackground(.hidden)
            .background(UH.Palette.surface)
            .navigationTitle("Adapt week \(week)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { Button("Cancel") { dismiss() } }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private func submit() async {
        isSubmitting = true
        error = nil
        defer { isSubmitting = false }
        if let message = await model.adaptWeek(week, fatigue: fatigue, rpe: rpe, notes: notes, schedule: schedule) { error = message } else { dismiss() }
    }
}

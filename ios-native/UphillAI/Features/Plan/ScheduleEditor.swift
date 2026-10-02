import SwiftUI

/// Shared schedule editor, following Phase 2b design-baseline.md.
struct ScheduleEditor: View {
    @Binding var draft: ScheduleDraft
    let workouts: [Workout]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Stepper("Runs per week: \(draft.daysPerWeek)", value: $draft.daysPerWeek, in: 3...7)
            Text("Run days").font(UH.TextStyle.label)
            days(selected: draft.preferredDays, available: Set(Weekday.allCases)) { day in
                if draft.preferredDays.contains(day) {
                    draft.preferredDays.remove(day)
                    draft.doubleSessionDays.remove(day)
                } else { draft.preferredDays.insert(day) }
                draft.daysPerWeek = max(3, min(7, draft.preferredDays.count))
            }
            Picker("Long-run day", selection: $draft.longRunDay) {
                if draft.longRunDay == nil { Text("Not set").tag(Weekday?.none) }
                ForEach(Weekday.allCases) { Text($0.rawValue).tag(Weekday?($0)) }
            }
            Text("Double-session days").font(UH.TextStyle.label)
            days(selected: draft.doubleSessionDays, available: draft.preferredDays) { day in
                if draft.doubleSessionDays.contains(day) { draft.doubleSessionDays.remove(day) }
                else if draft.doubleSessionDays.count < 2 { draft.doubleSessionDays.insert(day) }
            }
            Toggle("I can use a gym", isOn: $draft.hasGymAccess)
            Toggle("I can use a treadmill", isOn: $draft.useTreadmill)
            Picker("Terrain near me", selection: $draft.environment) {
                Text("Mostly flat").tag(TrainingEnvironment.flat)
                Text("Hilly").tag(TrainingEnvironment.hilly)
                Text("A mix").tag(TrainingEnvironment.mixed)
            }
            if draft.isGettingStarted {
                Stepper("Longest run without walking: \(draft.maxContinuousJogMin) minutes", value: $draft.maxContinuousJogMin, in: 0...120)
            }
            if draft.hasHardDayBeforeLongRun(workouts: workouts) {
                Label("A hard day right before the long run makes both harder.", systemImage: "exclamationmark.triangle")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
        }.padding(.vertical, UH.Space.small)
    }

    private func days(selected: Set<Weekday>, available: Set<Weekday>, toggle: @escaping (Weekday) -> Void) -> some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 70))], spacing: UH.Space.small) {
            ForEach(Weekday.allCases.filter(available.contains)) { day in
                Button { toggle(day) } label: {
                    Text(day.short).font(UH.TextStyle.label).frame(maxWidth: .infinity, minHeight: 44)
                        .background(selected.contains(day) ? UH.Palette.activeFill : UH.Palette.card,
                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }.buttonStyle(.plain)
                    .accessibilityLabel(day.rawValue).accessibilityAddTraits(selected.contains(day) ? .isSelected : [])
            }
        }
    }
}

struct ScheduleChangeSheet: View {
    let model: PlanViewModel
    @State private var draft: ScheduleDraft
    @State private var confirm = false
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(model: PlanViewModel) {
        self.model = model
        _draft = State(initialValue: ScheduleDraft(plan: model.snapshot?.plan))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section { ScheduleEditor(draft: $draft, workouts: model.snapshot?.workouts.filter { $0.weekNumber == model.currentWeek } ?? []) }
                Section {
                    if let error { Text(error).foregroundStyle(UH.Palette.danger) }
                    Button { confirm = true } label: {
                        if saving { ProgressView() } else { Text("Rebuild week") }
                    }.buttonStyle(.uhPrimary).disabled(saving || !draft.hasChanges)
                }
            }.scrollContentBackground(.hidden).background(UH.Palette.surface)
                .navigationTitle("Schedule").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } } }
                .confirmationDialog("Rebuild this week around your new schedule?", isPresented: $confirm, titleVisibility: .visible) {
                    Button("Rebuild week") { Task { await save() } }
                    Button("Not now", role: .cancel) {}
                }
        }.presentationDetents([.large]).presentationBackground(UH.Palette.surface)
    }

    private func save() async {
        guard !saving else { return }
        saving = true
        defer { saving = false }
        error = await model.adaptWeek(model.currentWeek, fatigue: .medium, rpe: nil, notes: "", schedule: draft)
        if error == nil { dismiss() }
    }
}

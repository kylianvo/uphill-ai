import SwiftUI

/// Redesigned training schedule editor with custom cards and day pills.
struct ScheduleEditor: View {
    @Binding var draft: ScheduleDraft
    let workouts: [Workout]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            // Runs per week stepper
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Runs per week").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text("\(draft.daysPerWeek) days / week").font(.system(.subheadline, design: .monospaced).weight(.bold)).foregroundStyle(UH.Palette.secondary)
                }
                Spacer()
                Stepper("Runs per week", value: $draft.daysPerWeek, in: 3...7)
                    .labelsHidden()
            }
            .frame(minHeight: 44)

            Divider()

            // Run days pills
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Preferred run days").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                daysGrid(selected: draft.preferredDays, available: Set(Weekday.allCases)) { day in
                    if draft.preferredDays.contains(day) {
                        draft.preferredDays.remove(day)
                        draft.doubleSessionDays.remove(day)
                    } else {
                        draft.preferredDays.insert(day)
                    }
                    draft.daysPerWeek = max(3, min(7, draft.preferredDays.count))
                }
            }

            Divider()

            // Long run day
            HStack {
                Text("Long-run day").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Spacer()
                Picker("Long-run day", selection: $draft.longRunDay) {
                    if draft.longRunDay == nil { Text("Not set").tag(Weekday?.none) }
                    ForEach(Weekday.allCases) { Text($0.rawValue).tag(Weekday?($0)) }
                }
                .pickerStyle(.menu)
                .tint(UH.Palette.accentInk)
            }
            .frame(minHeight: 44)

            Divider()

            // Double session days
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Double-session days (max 2)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                daysGrid(selected: draft.doubleSessionDays, available: draft.preferredDays) { day in
                    if draft.doubleSessionDays.contains(day) {
                        draft.doubleSessionDays.remove(day)
                    } else if draft.doubleSessionDays.count < 2 {
                        draft.doubleSessionDays.insert(day)
                    }
                }
            }

            Divider()

            // Gym & Treadmill
            VStack(spacing: UH.Space.small) {
                Toggle("I can use a gym", isOn: $draft.hasGymAccess)
                    .font(UH.TextStyle.label)
                    .tint(UH.Palette.accent)
                Toggle("I can use a treadmill", isOn: $draft.useTreadmill)
                    .font(UH.TextStyle.label)
                    .tint(UH.Palette.accent)
            }

            Divider()

            // Terrain near me
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Terrain near me").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Picker("Terrain", selection: $draft.environment) {
                    Text("Mostly flat").tag(TrainingEnvironment.flat)
                    Text("Hilly").tag(TrainingEnvironment.hilly)
                    Text("A mix").tag(TrainingEnvironment.mixed)
                }
                .pickerStyle(.segmented)
            }

            Divider()

            // Where the athlete can train: hill days, stairs, treadmill ceiling
            TrainingVenueSection(
                mountainDays: $draft.mountainDays,
                stairAccess: $draft.stairAccess,
                treadmillMaxIncline: draft.useTreadmill ? $draft.treadmillMaxIncline : nil
            )

            if draft.isGettingStarted {
                Divider()
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Continuous jog").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        Text("\(draft.maxContinuousJogMin) minutes").font(.system(.subheadline, design: .monospaced).weight(.bold)).foregroundStyle(UH.Palette.secondary)
                    }
                    Spacer()
                    Stepper("Continuous jog", value: $draft.maxContinuousJogMin, in: 0...120, step: 5)
                        .labelsHidden()
                }
                .frame(minHeight: 44)
            }

            // Hard day warning
            if draft.hasHardDayBeforeLongRun(workouts: workouts) {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(UH.Palette.warningInk)
                    Text("A hard day right before the long run makes both harder.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.warningInk)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(UH.Space.small)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
        }
        .padding(.vertical, UH.Space.small)
    }

    private func daysGrid(selected: Set<Weekday>, available: Set<Weekday>, toggle: @escaping (Weekday) -> Void) -> some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 44))], spacing: 8) {
            ForEach(Weekday.allCases) { day in
                let isAvailable = available.contains(day)
                let isSelected = selected.contains(day)

                Button {
                    if isAvailable { toggle(day) }
                } label: {
                    Text(day.short)
                        .font(UH.TextStyle.label)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .foregroundStyle(isSelected ? UH.Palette.buttonInk : (isAvailable ? UH.Palette.ink : UH.Palette.muted))
                        .background(isSelected ? UH.Palette.activeFill : (isAvailable ? UH.Palette.surface : UH.Palette.surface.opacity(0.4)),
                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                }
                .buttonStyle(.plain)
                .disabled(!isAvailable)
                .accessibilityLabel(day.rawValue)
                .accessibilityAddTraits(isSelected ? .isSelected : [])
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
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Text("Weekly Schedule").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                        Text("Adjust your preferred running days, long run, and training environment.")
                            .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        ScheduleEditor(draft: $draft, workouts: model.snapshot?.workouts.filter { $0.weekNumber == model.currentWeek } ?? [])
                    }
                    .trainingCard()

                    VStack(spacing: UH.Space.small) {
                        if let error {
                            Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                        }
                        Button {
                            confirm = true
                        } label: {
                            if saving { ProgressView().tint(.white) } else { Text("Rebuild week") }
                        }
                        .buttonStyle(.uhPrimary)
                        .disabled(saving || !draft.hasChanges)
                    }
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Schedule")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .confirmationDialog("Rebuild this week around your new schedule?", isPresented: $confirm, titleVisibility: .visible) {
                Button("Rebuild week") { Task { await save() } }
                Button("Not now", role: .cancel) {}
            }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private func save() async {
        guard !saving else { return }
        saving = true
        defer { saving = false }
        error = await model.adaptWeek(model.currentWeek, fatigue: .medium, rpe: nil, notes: "", schedule: draft)
        if error == nil { dismiss() }
    }
}

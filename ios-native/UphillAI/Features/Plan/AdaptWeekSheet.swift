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
    @State private var scheduleExpanded = false

    init(model: PlanViewModel, week: Int) {
        self.model = model
        self.week = week
        _schedule = State(initialValue: ScheduleDraft(plan: model.snapshot?.plan))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    // Coach Note Banner
                    HStack(alignment: .top, spacing: UH.Space.small) {
                        Image(systemName: "figure.run.circle.fill")
                            .font(.title2)
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("Coach Uphill rebuilds the workouts you haven't done yet. Finished and synced workouts stay as they are.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .trainingCard()

                    // Fatigue Level Selection Card
                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("How do you feel?")
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.ink)
                            Text("Calibrates remaining volume and workout intensity for week \(week).")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }

                        VStack(spacing: UH.Space.small) {
                            ForEach(FatigueLevel.allCases) { level in
                                let isSelected = fatigue == level
                                Button {
                                    fatigue = level
                                } label: {
                                    HStack(spacing: UH.Space.small) {
                                        Image(systemName: levelSymbol(level))
                                            .font(.title3)
                                            .foregroundStyle(isSelected ? UH.Palette.accentInk : UH.Palette.secondary)
                                            .frame(width: 28)
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(level.title)
                                                .font(UH.TextStyle.label)
                                                .foregroundStyle(UH.Palette.ink)
                                            Text(level.subtitle)
                                                .font(UH.TextStyle.caption)
                                                .foregroundStyle(UH.Palette.secondary)
                                        }
                                        Spacer()
                                        if isSelected {
                                            Image(systemName: "checkmark.circle.fill")
                                                .font(.title3)
                                                .foregroundStyle(UH.Palette.accentInk)
                                        }
                                    }
                                    .padding(.horizontal, UH.Space.small)
                                    .frame(minHeight: 52)
                                    .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                                }
                                .buttonStyle(.plain)
                                .accessibilityAddTraits(isSelected ? .isSelected : [])
                                .sensoryFeedback(.selection, trigger: isSelected)
                            }
                        }
                    }
                    .trainingCard()

                    // Effort & Context Card
                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Effort & Context")
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.ink)
                            Text("Rate your recent perceived exertion and note any soreness or schedule conflicts.")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }

                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Effort (RPE)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                                Text(rpe.map { "\($0) / 10" } ?? "Not set")
                                    .font(.system(.subheadline, design: .monospaced).weight(.bold))
                                    .foregroundStyle(rpe != nil ? UH.Palette.accentInk : UH.Palette.secondary)
                            }
                            Spacer()
                            Stepper("Effort (RPE)", value: Binding(get: { rpe ?? 5 }, set: { rpe = $0 }), in: 1...10)
                                .labelsHidden()
                        }
                        .frame(minHeight: 44)

                        Divider()

                        VStack(alignment: .leading, spacing: UH.Space.compact) {
                            Text("What's going on?").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                            TextField("e.g. Travel, illness, race postponed, sore calf...", text: $notes, axis: .vertical)
                                .lineLimit(2...5)
                                .padding(UH.Space.small)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                        }
                    }
                    .trainingCard()

                    // Schedule Disclosure Card
                    DisclosureGroup(isExpanded: $scheduleExpanded) {
                        VStack(spacing: UH.Space.regular) {
                            Divider()
                            ScheduleEditor(draft: $schedule, workouts: model.snapshot?.workouts.filter { $0.weekNumber == week } ?? [])
                        }
                        .padding(.top, UH.Space.compact)
                    } label: {
                        HStack(spacing: UH.Space.compact) {
                            Image(systemName: "calendar.badge.clock")
                                .font(.headline)
                                .foregroundStyle(UH.Palette.accentInk)
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Change my schedule")
                                    .font(UH.TextStyle.sectionTitle)
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Modify available days, long run day, or weekly volume")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                        }
                        .frame(minHeight: 44)
                    }
                    .trainingCard()

                    // Submit Button & Error
                    VStack(spacing: UH.Space.small) {
                        if let error {
                            Text(error)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.danger)
                        }
                        Button {
                            Task { await submit() }
                        } label: {
                            if isSubmitting {
                                ProgressView().tint(.white)
                            } else {
                                Text("Adapt week \(week)")
                            }
                        }
                        .buttonStyle(.uhPrimary)
                        .disabled(isSubmitting)
                        .accessibilityIdentifier("adapt.submit")
                    }
                    .padding(.top, UH.Space.small)
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Adapt week \(week)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
        .presentationDetents([.large])
        .presentationBackground(UH.Palette.surface)
    }

    private func levelSymbol(_ level: FatigueLevel) -> String {
        switch level {
        case .easy: "sparkles"
        case .medium: "figure.run"
        case .hard: "figure.walk"
        case .exhausted: "bed.double.fill"
        }
    }

    private func submit() async {
        isSubmitting = true
        error = nil
        defer { isSubmitting = false }
        if let message = await model.adaptWeek(week, fatigue: fatigue, rpe: rpe, notes: notes, schedule: schedule) {
            error = message
        } else {
            dismiss()
        }
    }
}

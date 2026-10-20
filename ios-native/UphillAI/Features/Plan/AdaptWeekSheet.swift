import SwiftUI

struct AdaptWeekSheet: View {
    let model: PlanViewModel
    let week: Int
    @Environment(\.dismiss) private var dismiss
    @State private var fatigue = FatigueLevel.medium
    @State private var rpe: Int?
    @State private var notes = ""
    @State private var healthIssue: String?
    @State private var isSubmitting = false
    @State private var error: String?
    @State private var schedule: ScheduleDraft
    @State private var scheduleExpanded = false

    init(model: PlanViewModel, week: Int) {
        self.model = model
        self.week = week
        _schedule = State(initialValue: ScheduleDraft(plan: model.snapshot?.plan))
    }

    /// Last week's sessions marked missed, so the athlete can say why before the week is rebuilt.
    private var missedLastWeek: [Workout] {
        (model.snapshot?.workouts ?? []).filter { $0.weekNumber == week - 1 && $0.isMissedFlag && !$0.isRest }
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

                    // Last week's missed sessions: why? Feeds the missed-session rules.
                    if !missedLastWeek.isEmpty {
                        VStack(alignment: .leading, spacing: UH.Space.regular) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Missed last week")
                                    .font(UH.TextStyle.sectionTitle)
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Tell the coach why. It shapes this week.")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            ForEach(missedLastWeek) { missed in
                                VStack(alignment: .leading, spacing: UH.Space.compact) {
                                    Text(verbatim: "\(L(missed.weekday.rawValue)) · \(missed.title)")
                                        .font(UH.TextStyle.label)
                                        .foregroundStyle(UH.Palette.ink)
                                    MissedReasonChips(selected: missed.missedReason) { reason in
                                        Task { await model.setMissed(missed, reason: reason.rawValue) }
                                    }
                                }
                            }
                        }
                        .trainingCard()
                        .accessibilityIdentifier("adapt.missed")
                    }

                    // Illness or pain right now
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Illness or pain right now")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        Picker("Illness or pain right now", selection: $healthIssue) {
                            Text("None").tag(String?.none)
                            Text("Sick").tag(String?.some("sick"))
                            Text("Pain").tag(String?.some("pain"))
                        }
                        .pickerStyle(.segmented)
                        .accessibilityIdentifier("adapt.healthIssue")
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

                        VStack(alignment: .leading, spacing: UH.Space.small) {
                            Text("Effort").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                            EffortSelector(selection: $rpe, identifier: "adapt.rpe")
                            Text("Choose the effort that best matches how it felt.")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }

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
                                Text("Modify run days, long run, or training venues")
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
                                ProgressView().tint(UH.Palette.onSolid)
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
        if let message = await model.adaptWeek(week, fatigue: fatigue, rpe: rpe, notes: notes, healthIssue: healthIssue, schedule: schedule) {
            error = message
        } else {
            dismiss()
        }
    }
}

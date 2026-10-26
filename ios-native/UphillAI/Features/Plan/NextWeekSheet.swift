import SwiftUI

struct NextWeekSheet: View {
    let model: PlanViewModel
    let offer: NextWeekOffer
    @Environment(\.dismiss) private var dismiss

    @State private var rpe: Int?
    @State private var notes = ""
    @State private var schedule: ScheduleDraft
    @State private var scheduleExpanded = false
    @State private var isSubmitting = false
    @State private var confirmMessage: String?
    @State private var confirming = false
    @State private var error: String?
    @State private var coachNotes = ""
    @State private var evaluation: BlockEvaluation?

    /// A coach builds the block for an athlete: the athlete's own effort review isn't theirs to give.
    private var isCoach: Bool { model.athleteId != nil }

    init(model: PlanViewModel, offer: NextWeekOffer) {
        self.model = model
        self.offer = offer
        _schedule = State(initialValue: ScheduleDraft(plan: model.snapshot?.plan))
    }

    private var currentOffer: NextWeekOffer { model.nextWeekOffer ?? offer }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let error {
                        HStack(spacing: UH.Space.compact) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(UH.Palette.danger)
                            Text(error)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.danger)
                        }
                        .padding(UH.Space.small)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    // Block info & unlock status
                    blockStatusCard

                    missedLastWeekCard

                    if isCoach {
                        coachGuidanceCard
                    } else {
                        rpeCard
                        notesCard
                    }

                    // Schedule Preferences Card (Optional)
                    scheduleCard

                    // Submit action
                    submitButton
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle(currentOffer.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .confirmationDialog("Build the next block anyway?", isPresented: $confirming, titleVisibility: .visible) {
                Button("Build anyway") { Task { await submit(override: true) } }
                Button("Not yet", role: .cancel) {}
            } message: {
                Text(confirmMessage ?? L("You haven't completed 70% of the current block yet."))
            }
        }
        .task { evaluation = await model.blockEvaluation(for: currentOffer) }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("nextweek.sheet")
    }

    // MARK: - Missed last week

    /// The sessions marked missed in the week before the new block, so the athlete can say why
    /// before the block is built. The backend applies the missed-session rules to these reasons.
    private var missedBeforeBlock: [Workout] {
        (model.snapshot?.workouts ?? []).filter {
            $0.weekNumber == currentOffer.weekStart - 1 && !$0.isRest && model.needsMissedReason($0)
        }
    }

    @ViewBuilder
    private var missedLastWeekCard: some View {
        if !missedBeforeBlock.isEmpty {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Missed last week")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Tell the coach why. It shapes this week.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                ForEach(missedBeforeBlock) { missed in
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
            .padding(UH.Space.regular)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line, lineWidth: 1))
            .accessibilityIdentifier("nextweek.missed")
        }
    }

    // MARK: - Block Status Card

    private var blockStatusCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text("BLOCK \(max(1, currentOffer.blockNumber - 1)) REVIEW")
                    .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                if currentOffer.unlocked {
                    HStack(spacing: 4) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("Ready to unlock")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                } else {
                    HStack(spacing: 4) {
                        Image(systemName: "lock.fill")
                            .foregroundStyle(UH.Palette.secondary)
                        Text("Gated")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            Text("Coach Uphill uses your feedback and past training consistency to shape the next block of workouts.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)

            if let pct = currentOffer.previousCompletionPct {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Completion")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                        Spacer()
                        Text("\(Int(pct))% / 70% required")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(pct >= 70 ? UH.Palette.accentInk : UH.Palette.secondary)
                    }
                    ProgressView(value: min(100, max(0, pct)), total: 100)
                        .tint(pct >= 70 ? UH.Palette.accentInk : UH.Palette.secondary)
                }
                .padding(.top, 2)
            }

            if let evaluation {
                evaluationDetails(evaluation)
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Block Evaluation

    private func evaluationDetails(_ evaluation: BlockEvaluation) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Divider()
            HStack(spacing: UH.Space.regular) {
                stat(value: "\(evaluation.sessionsCompleted)/\(evaluation.sessionsTotal)", label: L("Sessions done"))
                stat(value: "\(Self.km(evaluation.actualKm))/\(Self.km(evaluation.plannedKm))", label: L("km run"))
                if let grade = evaluation.qualityGrade, let score = evaluation.avgQualityScore {
                    stat(value: grade, label: L("Run quality · %lld%%", Int(score.rounded())))
                }
            }
            .accessibilityElement(children: .combine)

            if let summary = evaluation.coachSummary, !summary.isEmpty {
                Text(summary)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }

            if !evaluation.coachingTakeaways.isEmpty {
                bulletList(title: L("From your watch runs"), items: evaluation.coachingTakeaways, icon: "waveform.path.ecg")
            }
            if !evaluation.coachNotes.isEmpty {
                bulletList(title: L("Coach notes on this block"), items: evaluation.coachNotes, icon: "person.fill")
            }
        }
        .accessibilityIdentifier("nextweek.evaluation")
    }

    private func stat(value: String, label: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(.system(size: 17, weight: .bold))
                .monospacedDigit()
                .foregroundStyle(UH.Palette.ink)
            Text(label)
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
    }

    private func bulletList(title: String, items: [String], icon: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            ForEach(items, id: \.self) { item in
                Label {
                    Text(item).fixedSize(horizontal: false, vertical: true)
                } icon: {
                    Image(systemName: icon).foregroundStyle(UH.Palette.accentInk)
                }
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            }
        }
    }

    private static func km(_ value: Double) -> String {
        value.formatted(.number.precision(.fractionLength(0...1)))
    }

    // MARK: - Coach Guidance Card

    private var coachGuidanceCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("Guidance for this block").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text("Coach Uphill follows this when it writes the new weeks. Optional.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            TextField("Focus, limits, races or travel to plan around…", text: $coachNotes, axis: .vertical)
                .font(UH.TextStyle.body)
                .lineLimit(3...6)
                .padding(UH.Space.small)
                .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                .accessibilityIdentifier("nextweek.coachNotes")
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - RPE Card

    private var rpeCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("Overall effort").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            EffortSelector(selection: $rpe, identifier: "nextweek.rpe")
            Text("Choose the effort that best matches how it felt.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Coach Notes Card

    private var notesCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("NOTES FOR COACH UPHILL (OPTIONAL)")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)

            TextField("Fatigue, minor niggles, upcoming travel, or schedule changes…", text: $notes, axis: .vertical)
                .font(UH.TextStyle.body)
                .lineLimit(3...6)
                .padding(UH.Space.small)
                .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                .accessibilityIdentifier("nextweek.notes")
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Schedule Preferences Card

    private var scheduleCard: some View {
        DisclosureGroup(isExpanded: $scheduleExpanded) {
            VStack(spacing: UH.Space.regular) {
                Divider()
                ScheduleEditor(draft: $schedule, workouts: model.snapshot?.workouts.filter { $0.weekNumber == model.currentWeek } ?? [], includeBeginnerProgress: false, showLongDayFormat: true)
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
                    Text("These changes apply starting with Block \(currentOffer.blockNumber)")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                Spacer()
            }
            .frame(minHeight: 44)
        }
        .trainingCard()
        .accessibilityIdentifier("nextweek.schedule")
    }

    // MARK: - Submit Button

    private var submitButton: some View {
        Button {
            Task { await submit(override: false) }
        } label: {
            if isSubmitting {
                ProgressView()
                    .frame(maxWidth: .infinity)
            } else {
                Text(currentOffer.unlocked ? currentOffer.title : L("Generate Block %lld anyway", currentOffer.blockNumber))
                    .frame(maxWidth: .infinity)
            }
        }
        .buttonStyle(.uhPrimary)
        .disabled(isSubmitting)
        .accessibilityIdentifier("nextweek.submit")
    }

    private func submit(override: Bool) async {
        isSubmitting = true
        error = nil
        defer { isSubmitting = false }
        switch await model.buildNextWeek(rpe: isCoach ? nil : rpe, notes: isCoach ? "" : notes, override: override,
                                       schedule: schedule.hasChanges ? schedule : nil, coachNotes: coachNotes) {
        case .started:
            dismiss()
        case .needsConfirmation(let message):
            confirmMessage = message
            confirming = true
        case .failed(let message):
            error = message
        }
    }
}

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

                    // RPE selector card
                    rpeCard

                    // Coach notes card
                    notesCard

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
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("nextweek.sheet")
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
                ScheduleEditor(draft: $schedule, workouts: model.snapshot?.workouts.filter { $0.weekNumber == model.currentWeek } ?? [], includeBeginnerProgress: false)
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
        switch await model.buildNextWeek(rpe: rpe, notes: notes, override: override, schedule: schedule.hasChanges ? schedule : nil) {
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

import SwiftUI

/// On a runner's Plan tab, for their coach: why the runner needs you, their recovery, the plan check
/// for a plan to review, and the one action that fits. Styled like Coach's Review.
struct CoachFocusCard: View {
    let app: AppModel
    let athleteId: Int
    let athleteName: String
    let plan: Plan?
    let onAdapt: () -> Void
    let onBuildPlan: () -> Void
    let onBuildNextWeek: () -> Void
    let onChanged: () async -> Void

    @State private var review: PlanReview?
    @State private var latestNote: CoachNote?
    @State private var showNote = false
    @State private var showReview = false
    @State private var reviewNote = ""
    @State private var showPublish = false
    @State private var working = false
    @State private var error: String?

    init(app: AppModel, athleteId: Int, athleteName: String, plan: Plan?, onAdapt: @escaping () -> Void,
         onBuildPlan: @escaping () -> Void, onBuildNextWeek: @escaping () -> Void, onChanged: @escaping () async -> Void,
         review: PlanReview? = nil, latestNote: CoachNote? = nil) {
        self.app = app
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.plan = plan
        self.onAdapt = onAdapt
        self.onBuildPlan = onBuildPlan
        self.onBuildNextWeek = onBuildNextWeek
        self.onChanged = onChanged
        _review = State(initialValue: review)
        _latestNote = State(initialValue: latestNote)
    }

    private var athlete: CoachOverviewAthlete? {
        app.coachDashboard?.overview.athletes.first { $0.athleteId == athleteId }
    }

    private var reasons: [CoachSignal] { (athlete?.signals ?? []).filter { $0.severity != .highlight } }
    private var primary: CoachAction? { CoachFocus.primary(athlete, planStatus: plan?.planStatus) }
    private var tint: Color { (athlete?.section ?? .onTrack).tint }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(spacing: 10) {
                Image(systemName: (athlete?.section ?? .onTrack).symbol)
                    .font(.system(size: 14))
                    .foregroundStyle(tint)
                    .padding(6)
                    .background(tint.opacity(0.12), in: Circle())
                Text(athlete.map { $0.section.title } ?? "On track")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .textCase(.uppercase)
                    .foregroundStyle(tint)
                if let planType = athlete?.effectivePlanType { PlanTypeTag(planType: planType) }
                Spacer()
            }

            if reasons.isEmpty {
                Text(plan?.planStatus == "draft" ? L("Draft plan not published") : L("Nothing needs you this week."))
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
            } else {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(reasons.enumerated()), id: \.offset) { i, s in
                        Text(CoachSignalText.sentence(s))
                            .font(i == 0 ? .subheadline.weight(.semibold) : .footnote)
                            .foregroundStyle(i == 0 ? UH.Palette.ink : UH.Palette.secondary)
                    }
                }
            }

            if let r = athlete?.recovery { recoveryRow(r) }

            if let review, review.needsReview || plan?.planStatus == "draft" { planCheck(review) }

            if let latestNote {
                VStack(alignment: .leading, spacing: 2) {
                    Text("YOUR LAST NOTE")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Text(verbatim: latestNote.note)
                        .font(.footnote)
                        .foregroundStyle(UH.Palette.secondary)
                        .lineLimit(3)
                }
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
            }

            if let error { Text(error).font(.footnote).foregroundStyle(UH.Palette.danger) }

            HStack(spacing: 8) {
                if let primary, primary != .note {
                    Button(CoachFocus.label(primary)) { perform(primary) }
                        .buttonStyle(.uhPrimary)
                        .disabled(working)
                        .accessibilityIdentifier("coachCard.primary")
                }
                Button(CoachFocus.label(.note)) { showNote = true }
                    .buttonStyle(.uhSecondary)
            }
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(tint.opacity(0.35), lineWidth: 1))
        .task(id: plan?.id) { await loadDetails() }
        .sheet(isPresented: $showNote) {
            CoachNoteSheet(athleteName: athleteName) { text in
                latestNote = try await app.coachingService.addNote(
                    athleteId: athleteId, payload: CoachNoteCreatePayload(targetType: "general", note: text))
            }
        }
        .alert("Mark reviewed", isPresented: $showReview) {
            TextField("Note to the runner (optional)", text: $reviewNote)
            Button("Mark reviewed") { Task { await markReviewed() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text(L("Weeks up to %lld will count as reviewed.", review?.generatedBlock ?? 1))
        }
        .confirmationDialog("Publish this plan?", isPresented: $showPublish, titleVisibility: .visible) {
            Button("Publish plan") { Task { await publish() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text(L("%@ will see every session in it.", athleteName))
        }
    }

    private func recoveryRow(_ r: CoachRecovery) -> some View {
        HStack(spacing: 8) {
            if let hrv = r.hrvStatus { stat(hrv == "low" ? L("Low") : L("Normal"), "HRV", alert: hrv == "low") }
            if let rhr = r.restingHr { stat("\(rhr)", L("Resting HR"), alert: false) }
            if let sleep = r.sleepAvg7DMin { stat(String(format: "%d:%02d", sleep / 60, sleep % 60), L("Sleep, 7-day avg"), alert: sleep < 390) }
        }
    }

    private func stat(_ value: String, _ caption: String, alert: Bool) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(verbatim: value)
                .font(.headline.monospacedDigit())
                .foregroundStyle(alert ? UH.Palette.danger : UH.Palette.ink)
            Text(verbatim: caption).font(.caption2).foregroundStyle(UH.Palette.secondary).lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(8)
        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
    }

    private func planCheck(_ review: PlanReview) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("PLAN CHECK")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            if review.issues.isEmpty {
                Text("No problems found in the generated weeks.").font(.footnote).foregroundStyle(UH.Palette.secondary)
            }
            ForEach(Array(review.issues.prefix(5).enumerated()), id: \.offset) { _, issue in
                Label(PlanReviewText.sentence(issue), systemImage: "exclamationmark.triangle")
                    .font(.footnote)
                    .foregroundStyle(UH.Palette.ink)
            }
            if let fit = review.feasibility, fit != "supported" {
                Text(fit == "stretch" ? L("The goal is a stretch for this runner's week.") : L("The runner's week can't hold this goal yet."))
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(UH.Palette.warningInk)
            }
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
    }

    private func perform(_ action: CoachAction) {
        switch action {
        case .adaptWeek: onAdapt()
        case .reviewPlan: reviewNote = ""; showReview = true
        case .buildPlan: onBuildPlan()
        case .openDraft, .reviewChanges: showPublish = true
        case .buildNextWeek: onBuildNextWeek()
        case .note: showNote = true
        }
    }

    private func loadDetails() async {
        let service = app.coachingService
        latestNote = (try? await service.fetchNotes(athleteId: athleteId, targetType: nil, targetId: nil))?.first
        guard let plan else { review = nil; return }
        review = try? await service.planReview(athleteId: athleteId, planId: plan.id)
        // The Athletes tab can tap an action straight through to this card.
        if let pending = app.takePendingCoachAction(), pending != .note { perform(pending) }
    }

    private func markReviewed() async {
        guard let plan else { return }
        await run {
            let note = reviewNote.trimmingCharacters(in: .whitespacesAndNewlines)
            review = try await app.coachingService.markReviewed(athleteId: athleteId, planId: plan.id, note: note.isEmpty ? nil : note)
        }
    }

    private func publish() async {
        guard let plan else { return }
        await run { _ = try await app.coachingService.publish(athleteId: athleteId, planId: plan.id) }
    }

    /// Runs a coach action, then refreshes the plan and the Athletes overview so both show the new state.
    private func run(_ body: () async throws -> Void) async {
        working = true
        defer { working = false }
        do {
            try await body()
            error = nil
            await onChanged()
            if let o = try? await app.coachingService.fetchOverview(days: 14, athleteId: nil, level: nil) {
                app.coachDashboard?.overview = o
            }
        } catch {
            self.error = error.localizedDescription
        }
    }
}

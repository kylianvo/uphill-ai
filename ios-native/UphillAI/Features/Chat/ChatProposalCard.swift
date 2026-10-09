import SwiftUI

/// Both coach proposal cards: `schedule_proposal` (move 1-5 workouts, diff in the card) and
/// `schedule_rebuild` (week drafted in the background; the diff is polled until ready).
struct ChatProposalCard: View {
    let payload: ToolResultPayload
    let proposalState: String?
    var rebuildDiff: RebuildDiff? = nil
    var onLoadRebuild: ((Int) async -> Void)? = nil
    let onApply: (Int) async -> Bool
    let onDiscard: (Int) async -> Void

    @State private var isBusy = false
    @State private var applyFailed = false

    private var proposalData: ScheduleProposalCardData? {
        payload.decodeScheduleProposal()
    }

    private var isRebuild: Bool { payload.cardType == "schedule_rebuild" }

    private var status: String {
        proposalState ?? proposalData?.status ?? (isRebuild ? "generating" : "proposed")
    }

    var body: some View {
        if let data = proposalData, let proposalId = data.proposalId {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                HStack(alignment: .center) {
                    Label(title(data), systemImage: "calendar.badge.clock")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    statusBadge
                }

                if let rationale = data.rationale, !rationale.isEmpty {
                    Text(rationale)
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.ink)
                        .fixedSize(horizontal: false, vertical: true)
                }

                if isRebuild {
                    rebuildBody(data)
                } else {
                    movesBody(data.diff ?? [])
                }

                if status == "proposed", let warnings = data.warnings, !warnings.isEmpty {
                    warningsView(warnings)
                }

                statusFooter

                if status == "proposed", !isRebuild || rebuildDiff != nil {
                    actions(proposalId)
                }
            }
            .uhCard()
            .task(id: proposalId) {
                // Load the draft for a rebuild that is still generating or was reloaded from history.
                if isRebuild, rebuildDiff == nil, status == "generating" || status == "proposed" {
                    await onLoadRebuild?(proposalId)
                }
            }
        }
    }

    private func title(_ data: ScheduleProposalCardData) -> String {
        if isRebuild, let week = data.week { return L("Proposed rebuild · Week %lld", week) }
        return L("Proposed schedule change")
    }

    // MARK: Move proposal

    @ViewBuilder
    private func movesBody(_ moves: [ProposalMove]) -> some View {
        ForEach(Array(moves.enumerated()), id: \.offset) { _, move in
            VStack(alignment: .leading, spacing: 2) {
                Text(verbatim: "\(weekDay(move.fromWeek, move.fromDay)) → \(weekDay(move.toWeek, move.toDay))")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.muted)
                if let workout = move.workout {
                    Text(verbatim: brief(workout))
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.ink)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(UH.Space.compact)
            .background(Color.black.opacity(0.03), in: RoundedRectangle(cornerRadius: UH.Radius.control))
        }
    }

    // MARK: Rebuild

    @ViewBuilder
    private func rebuildBody(_ data: ScheduleProposalCardData) -> some View {
        if status == "generating" {
            HStack(spacing: 8) {
                ProgressView().controlSize(.small)
                Text(L("Drafting week %lld…", data.week ?? 0))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
            }
        } else if let diff = rebuildDiff, status != "failed" {
            if let totals = diff.totals {
                Text(verbatim: "\(L("Week total")): \(totalsLine(totals.before)) → \(totalsLine(totals.after))")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.ink)
            }
            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array(diff.days.enumerated()), id: \.offset) { _, day in
                    rebuildDayRow(day)
                }
            }
        }
    }

    @ViewBuilder
    private func rebuildDayRow(_ day: RebuildDay) -> some View {
        let changed = !day.before.isEmpty || !day.after.isEmpty
        if changed || !day.kept.isEmpty {
            let same = changed && joined(day.before) == joined(day.after)
            VStack(alignment: .leading, spacing: 2) {
                Text(verbatim: shortDay(day.day))
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.ink)
                ForEach(Array(day.kept.enumerated()), id: \.offset) { _, kept in
                    Text(verbatim: "\(brief(kept)) (\(L("kept")))")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
                if changed && !same {
                    if !day.before.isEmpty {
                        Text(verbatim: L("was: %@", joined(day.before)))
                            .font(UH.TextStyle.caption)
                            .strikethrough()
                            .foregroundStyle(UH.Palette.muted)
                    }
                    Text(verbatim: joined(day.after))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.ink)
                } else if changed {
                    Text(verbatim: joined(day.after))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .opacity(!changed || same ? 0.55 : 1)
        }
    }

    // MARK: Shared pieces

    private func warningsView(_ warnings: [ScheduleWarning]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(Array(warnings.enumerated()), id: \.offset) { _, warning in
                HStack(alignment: .top, spacing: 6) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(UH.Palette.warningInk)
                        .font(.caption)
                    Text(verbatim: ScheduleMessages.warningText(warning))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.warningInk)
                }
            }
        }
        .padding(UH.Space.compact)
        .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
    }

    @ViewBuilder
    private var statusFooter: some View {
        if status == "stale" {
            footerText(L("Your plan changed since this was proposed — ask the coach again."))
        } else if status == "failed" {
            footerText(L("Couldn't draft this week — ask the coach to try again."))
        } else if applyFailed, status == "proposed" {
            footerText(L("Couldn't apply — try again."))
        }
    }

    private func footerText(_ text: String) -> some View {
        Text(verbatim: text)
            .font(UH.TextStyle.caption)
            .foregroundStyle(UH.Palette.warningInk)
            .fixedSize(horizontal: false, vertical: true)
    }

    private func actions(_ proposalId: Int) -> some View {
        HStack(spacing: UH.Space.compact) {
            Button {
                Task {
                    isBusy = true
                    applyFailed = false
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    applyFailed = !(await onApply(proposalId))
                    isBusy = false
                }
            } label: {
                HStack(spacing: 6) {
                    if isBusy {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "checkmark")
                    }
                    Text("Apply Change")
                }
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.buttonInk)
                .frame(maxWidth: .infinity, minHeight: 40)
                .background(UH.Palette.accent, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
            .disabled(isBusy)

            Button {
                Task {
                    isBusy = true
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    await onDiscard(proposalId)
                    isBusy = false
                }
            } label: {
                Text("Discard")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.muted)
                    .frame(minWidth: 80, minHeight: 40)
                    .background(Color.black.opacity(0.05), in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
            .disabled(isBusy)
        }
        .padding(.top, 4)
    }

    private var statusBadge: some View {
        let (text, ink, fill): (String, Color, Color) = switch status {
        case "applied": (L("Applied"), UH.Palette.accentInk, UH.Palette.activeFill)
        case "discarded": (L("Discarded"), UH.Palette.muted, Color.black.opacity(0.06))
        case "stale": (L("Stale"), UH.Palette.muted, Color.black.opacity(0.06))
        case "failed": (L("Failed"), UH.Palette.warningInk, UH.Palette.warningFill)
        case "generating": (L("Drafting"), UH.Palette.muted, Color.black.opacity(0.06))
        default: (L("Proposed"), UH.Palette.warningInk, UH.Palette.warningFill)
        }
        return Text(verbatim: text)
            .font(UH.TextStyle.disclosure)
            .foregroundStyle(ink)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(fill, in: Capsule())
    }

    // MARK: Formatting (mirrors the web cards)

    private func weekDay(_ week: Int?, _ day: String?) -> String {
        L("Week %lld · %@", week ?? 0, shortDay(day ?? ""))
    }

    private func shortDay(_ day: String) -> String {
        let key = String(day.prefix(3))
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].contains(key) ? L(key) : day
    }

    private func brief(_ w: ProposalWorkout) -> String {
        let minutes = Int((w.durationMinutes ?? 0).rounded())
        return "\(w.title ?? L("Workout")) · \(minutes)′"
    }

    private func joined(_ rows: [ProposalWorkout]) -> String {
        rows.isEmpty ? L("Rest") : rows.map(brief).joined(separator: " + ")
    }

    private func totalsLine(_ t: RebuildTotals) -> String {
        L("%lld min · %@ km · +%lld m", Int((t.min ?? 0).rounded()), String(format: "%g", t.km ?? 0), Int((t.vert ?? 0).rounded()))
    }
}

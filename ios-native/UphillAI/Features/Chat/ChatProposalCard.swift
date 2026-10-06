import SwiftUI

struct ChatProposalCard: View {
    let payload: ToolResultPayload
    let proposalState: String?
    let onApply: (Int) async -> Void
    let onDiscard: (Int) async -> Void

    @State private var isBusy = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var proposalData: ScheduleProposalCardData? {
        payload.decodeScheduleProposal()
    }

    private var status: String {
        proposalState ?? proposalData?.status ?? "proposed"
    }

    private var isProposed: Bool {
        status == "proposed"
    }

    var body: some View {
        if let data = proposalData {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                // Header with badge
                HStack(alignment: .center) {
                    Label("Schedule Proposal", systemImage: "calendar.badge.clock")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)

                    Spacer()

                    statusBadge
                }

                // Rationale
                if let rationale = data.rationale, !rationale.isEmpty {
                    Text(rationale)
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.ink)
                        .fixedSize(horizontal: false, vertical: true)
                }

                // Warnings
                if let warnings = data.warnings, !warnings.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(warnings, id: \.self) { warning in
                            HStack(alignment: .top, spacing: 6) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundStyle(UH.Palette.warningInk)
                                    .font(.caption)
                                Text(warning)
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.warningInk)
                            }
                        }
                    }
                    .padding(UH.Space.compact)
                    .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }

                // Action buttons if still in "proposed" state
                if isProposed, let proposalId = data.proposalId {
                    HStack(spacing: UH.Space.compact) {
                        Button {
                            Task {
                                isBusy = true
                                UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                                await onApply(proposalId)
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
            }
            .uhCard()
        }
    }

    private var statusBadge: some View {
        Group {
            switch status {
            case "applied":
                Text("Applied")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(UH.Palette.activeFill, in: Capsule())
            case "discarded":
                Text("Discarded")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.black.opacity(0.06), in: Capsule())
            case "stale":
                Text("Stale")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.black.opacity(0.06), in: Capsule())
            default:
                Text("Proposed")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.warningInk)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(UH.Palette.warningFill, in: Capsule())
            }
        }
    }
}

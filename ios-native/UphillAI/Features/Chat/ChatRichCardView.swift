import SwiftUI

struct ChatRichCardView: View {
    let payload: ToolResultPayload
    let proposalStates: [Int: String]
    let onApplyProposal: (Int) async -> Void
    let onDiscardProposal: (Int) async -> Void

    var body: some View {
        switch payload.cardType {
        case "schedule_proposal", "schedule_rebuild":
            if let pId = payload.decodeScheduleProposal()?.proposalId {
                ChatProposalCard(
                    payload: payload,
                    proposalState: proposalStates[pId],
                    onApply: onApplyProposal,
                    onDiscard: onDiscardProposal
                )
            }

        case "week_schedule":
            if let data = payload.decodeWeekSchedule() {
                ChatWeekScheduleCard(data: data)
            }

        case "week_review":
            if let data = payload.decodeWeekReview() {
                ChatWeekReviewCard(data: data)
            }

        case "pacing_splits":
            if let data = payload.decodePacingSplits() {
                ChatPacingSplitsCard(data: data)
            }

        default:
            EmptyView()
        }
    }
}

struct ChatWeekScheduleCard: View {
    let data: WeekScheduleCardData

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Week \(data.weekNumber ?? 1) Schedule", systemImage: "calendar")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                if let km = data.totalDistanceKm {
                    Text(String(format: "%.1f km", km))
                        .font(UH.TextStyle.metric)
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }

            if let workouts = data.workouts, !workouts.isEmpty {
                VStack(spacing: 6) {
                    ForEach(workouts) { workout in
                        HStack(spacing: 8) {
                            Text(workout.dayOfWeek.prefix(3))
                                .font(UH.TextStyle.disclosure)
                                .foregroundStyle(UH.Palette.muted)
                                .frame(width: 32, alignment: .leading)

                            Text(workout.title)
                                .font(UH.TextStyle.body)
                                .foregroundStyle(UH.Palette.ink)
                                .lineLimit(1)

                            Spacer()

                            Text(workout.targetZone)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .padding(.vertical, 4)
                        .padding(.horizontal, 8)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                }
            }
        }
        .uhCard()
    }
}

struct ChatWeekReviewCard: View {
    let data: WeekReviewCardData

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Week \(data.weekNumber ?? 1) Review", systemImage: "chart.bar.xaxis")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                if let comp = data.compliancePercent {
                    Text(String(format: "%.0f%% Done", comp))
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(comp >= 80 ? UH.Palette.accentInk : UH.Palette.warningInk)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(comp >= 80 ? UH.Palette.activeFill : UH.Palette.warningFill, in: Capsule())
                }
            }

            HStack(spacing: UH.Space.section) {
                if let planned = data.plannedDistanceKm {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Planned")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                        Text(String(format: "%.1f km", planned))
                            .font(UH.TextStyle.metric)
                            .foregroundStyle(UH.Palette.ink)
                    }
                }

                if let actual = data.actualDistanceKm {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Completed")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                        Text(String(format: "%.1f km", actual))
                            .font(UH.TextStyle.metric)
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }

            if let summary = data.summary, !summary.isEmpty {
                Text(summary)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .uhCard()
    }
}

struct ChatPacingSplitsCard: View {
    let data: PacingSplitsCardData

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label(data.raceName ?? "Pacing Strategy", systemImage: "timer")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                if let km = data.totalDistanceKm {
                    Text(String(format: "%.1f km", km))
                        .font(UH.TextStyle.disclosure)
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            if let splits = data.splits, !splits.isEmpty {
                VStack(spacing: 4) {
                    ForEach(splits) { split in
                        HStack {
                            Text(split.checkpoint)
                                .font(UH.TextStyle.body)
                                .foregroundStyle(UH.Palette.ink)

                            Spacer()

                            if let pace = split.targetPace {
                                Text(pace)
                                    .font(UH.TextStyle.metric)
                                    .foregroundStyle(UH.Palette.secondary)
                            }

                            if let target = split.elapsedTarget {
                                Text(target)
                                    .font(UH.TextStyle.metric)
                                    .foregroundStyle(UH.Palette.accentInk)
                                    .frame(minWidth: 50, alignment: .trailing)
                            }
                        }
                        .padding(.vertical, 4)
                        .padding(.horizontal, 8)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                }
            }
        }
        .uhCard()
    }
}

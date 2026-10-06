import SwiftUI

struct ChatRichCardView: View {
    let payload: ToolResultPayload
    let proposalStates: [Int: String]
    var onSelectWorkout: ((Int) -> Void)? = nil
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
                ChatWeekScheduleCard(data: data, onSelectWorkout: onSelectWorkout)
            }

        case "week_review":
            if let data = payload.decodeWeekReview() {
                ChatWeekReviewCard(data: data)
            }

        case "pacing_splits":
            if let data = payload.decodePacingSplits() {
                ChatPacingSplitsCard(data: data)
            }

        case "nutrition_plan", "fueling_plan":
            if let plan = payload.decodeNutritionPlan() {
                ChatNutritionCard(plan: plan)
            }

        case "gear_recommendation", "shoe_recommendations", "gear_plan":
            if let plan = payload.decodeGearPlan() {
                ChatGearCard(plan: plan)
            }

        case "goal_estimate":
            if let estimate = payload.decodeGoalEstimate() {
                ChatGoalCard(estimate: estimate)
            }

        default:
            EmptyView()
        }
    }
}

struct ChatWeekScheduleCard: View {
    let data: WeekScheduleCardData
    var onSelectWorkout: ((Int) -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(alignment: .firstTextBaseline) {
                Label("Week \(data.weekNumber ?? 1) Schedule", systemImage: "calendar")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                HStack(spacing: 8) {
                    if let km = data.totalDistanceKm, km > 0 {
                        Text(String(format: "%.1f km", km))
                            .font(UH.TextStyle.metric)
                            .foregroundStyle(UH.Palette.ink)
                    }
                    if let gain = data.totalElevationGainM, gain > 0 {
                        Text("+\(Int(gain)) m")
                            .font(UH.TextStyle.disclosure)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            if let workouts = data.workouts, !workouts.isEmpty {
                VStack(spacing: 6) {
                    ForEach(workouts) { workout in
                        ChatWorkoutRow(workout: workout, onSelect: onSelectWorkout.map { action in { action(workout.id) } })
                    }
                }
            }
        }
        .uhCard()
    }
}

struct ChatWorkoutRow: View {
    let workout: Workout
    var onSelect: (() -> Void)? = nil

    private var isRest: Bool {
        workout.type.lowercased() == "rest" || workout.durationMinutes == 0
    }

    var body: some View {
        Button {
            if !isRest, let onSelect {
                UIImpactFeedbackGenerator(style: .light).impactOccurred()
                onSelect()
            }
        } label: {
            HStack(spacing: 8) {
                Text(workout.dayOfWeek.prefix(3).uppercased())
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(isRest ? UH.Palette.muted : UH.Palette.secondary)
                    .frame(width: 32, alignment: .leading)

                if !isRest {
                    Text(WorkoutTypePresentation.chipLabel(for: workout))
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundStyle(WorkoutTypePresentation.zoneColor(for: workout))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(WorkoutTypePresentation.zoneColor(for: workout).opacity(0.12), in: Capsule())
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 4) {
                        Text(workout.title)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(isRest ? UH.Palette.muted : UH.Palette.ink)
                            .lineLimit(2)
                            .multilineTextAlignment(.leading)

                        if workout.isPriority {
                            Image(systemName: "star.fill")
                                .font(.system(size: 9))
                                .foregroundStyle(UH.Palette.warningInk)
                        }
                    }

                    if !isRest {
                        let metrics = WorkoutTypePresentation.formatMetrics(for: workout)
                        if !metrics.isEmpty {
                            Text(metrics)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }
                }

                Spacer()

                if workout.isCompleted == 1 {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 14))
                        .foregroundStyle(UH.Palette.accentInk)
                } else if isRest {
                    Text("Rest")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                } else if onSelect != nil {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundStyle(UH.Palette.muted)
                }
            }
            .padding(.vertical, 6)
            .padding(.horizontal, 8)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        }
        .buttonStyle(.plain)
        .disabled(isRest || onSelect == nil)
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

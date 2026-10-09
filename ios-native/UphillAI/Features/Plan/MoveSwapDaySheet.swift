import SwiftUI

struct MoveSwapDaySheet: View {
    let model: PlanViewModel
    let sourceDay: PlanDay
    @Environment(\.dismiss) private var dismiss

    enum Mode: String, CaseIterable {
        case swap = "Swap Days"
        case move = "Move Workout"
    }

    @State private var mode: Mode = .swap
    @State private var selectedWorkoutID: Int?
    @State private var isSubmitting = false
    @State private var errorMessage: String?

    init(model: PlanViewModel, sourceDay: PlanDay) {
        self.model = model
        self.sourceDay = sourceDay
        _selectedWorkoutID = State(initialValue: sourceDay.workouts.first?.id)
    }

    private var selectedWorkout: Workout? {
        if let id = selectedWorkoutID {
            return sourceDay.workouts.first { $0.id == id }
        }
        return sourceDay.workouts.first
    }

    private var otherDays: [PlanDay] {
        model.days(for: sourceDay.week).filter { $0.weekday != sourceDay.weekday }
    }

    private var canMove: Bool {
        guard let w = selectedWorkout else { return false }
        return !w.isRest && !model.moveTargets(for: w).isEmpty
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let errorMessage {
                        HStack(spacing: UH.Space.compact) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundStyle(UH.Palette.danger)
                            Text(errorMessage)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.danger)
                        }
                        .padding(UH.Space.small)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    // Source day summary card
                    sourceDayCard

                    // Mode picker if moving workouts is possible
                    if !sourceDay.workouts.isEmpty && canMove {
                        Picker("Action", selection: $mode) {
                            ForEach(Mode.allCases, id: \.self) { m in
                                Text(m.rawValue).tag(m)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    if mode == .swap || sourceDay.workouts.isEmpty || !canMove {
                        swapSection
                    } else {
                        moveSection
                    }
                }
                .padding(UH.Space.regular)
            }
            .background(UH.Palette.surface)
            .navigationTitle("Move or Swap")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .disabled(isSubmitting)
            .overlay {
                if isSubmitting {
                    ProgressView()
                        .padding()
                        .background(UH.Palette.card.opacity(0.9), in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationBackground(UH.Palette.surface)
        .accessibilityIdentifier("moveswap.sheet")
    }

    // MARK: - Source Day Card

    private var sourceDayCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text(sourceDateText.uppercased())
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.secondary)
                Spacer()
                Text("WEEK \(sourceDay.week)")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.hover, in: Capsule())
            }

            if sourceDay.workouts.isEmpty || sourceDay.isRest {
                HStack(spacing: UH.Space.compact) {
                    Image(systemName: "moon.zzz")
                        .foregroundStyle(UH.Palette.muted)
                    Text("Rest Day")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                }
                .padding(.vertical, 4)
            } else {
                ForEach(sourceDay.workouts) { w in
                    HStack(spacing: UH.Space.compact) {
                        Text(WorkoutTypePresentation.chipLabel(for: w))
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(WorkoutTypePresentation.zoneColor(for: w))
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(WorkoutTypePresentation.zoneColor(for: w).opacity(0.12), in: RoundedRectangle(cornerRadius: 4))

                        Text(w.title)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(1)

                        Spacer()

                        Text(WorkoutTypePresentation.formatMetrics(for: w))
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    private var sourceDateText: String {
        guard let d = sourceDay.date else { return sourceDay.weekday.rawValue }
        return d.formatted(.dateTime.weekday(.wide).month(.abbreviated).day())
    }

    // MARK: - Swap Section

    private var swapSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("SWAP WITH ANOTHER DAY THIS WEEK")
                .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)
                .padding(.top, 4)

            ForEach(otherDays) { targetDay in
                Button {
                    performSwap(targetDay)
                } label: {
                    HStack(spacing: UH.Space.compact) {
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(targetDay.weekday.rawValue)
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)
                                if let d = targetDay.date {
                                    Text(d.formatted(.dateTime.month(.abbreviated).day()))
                                        .font(UH.TextStyle.caption)
                                        .foregroundStyle(UH.Palette.muted)
                                }
                            }

                            if targetDay.workouts.isEmpty || targetDay.isRest {
                                Text("Rest Day")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            } else {
                                Text(targetDay.workouts.map(\.title).joined(separator: " · "))
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                    .lineLimit(1)
                            }
                        }

                        Spacer()

                        HStack(spacing: 4) {
                            Image(systemName: "arrow.left.arrow.right")
                                .font(.system(size: 11, weight: .bold))
                            Text("Swap")
                                .font(.system(size: 12, weight: .bold))
                        }
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                    .padding(UH.Space.small)
                    .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("moveswap.swap.\(targetDay.weekday.rawValue)")
            }
        }
    }

    private func performSwap(_ targetDay: PlanDay) {
        Task {
            isSubmitting = true
            errorMessage = nil
            let success = await model.swapDays(week: sourceDay.week, day1: sourceDay.weekday, day2: targetDay.weekday)
            isSubmitting = false
            if success {
                dismiss()
            } else if let err = model.actionError {
                errorMessage = err
            }
        }
    }

    // MARK: - Move Section

    private var moveSection: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            if sourceDay.workouts.count > 1 {
                Text("SELECT WORKOUT TO MOVE")
                    .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.muted)

                ForEach(sourceDay.workouts) { w in
                    Button {
                        selectedWorkoutID = w.id
                    } label: {
                        HStack {
                            Text(w.title)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Spacer()
                            if selectedWorkout?.id == w.id {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(UH.Palette.accentInk)
                            }
                        }
                        .padding(UH.Space.small)
                        .background(selectedWorkout?.id == w.id ? UH.Palette.activeFill : UH.Palette.card,
                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                    }
                    .buttonStyle(.plain)
                }
            }

            if let w = selectedWorkout {
                let targets = model.moveTargets(for: w)
                Text("MOVE TO A DAY THIS WEEK OR NEXT WEEK")
                    .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                    .tracking(0.5)
                    .foregroundStyle(UH.Palette.muted)
                    .padding(.top, 4)

                if targets.isEmpty {
                    Text("No available target days.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .padding(UH.Space.small)
                } else {
                    ForEach(targets) { target in
                        Button {
                            performMove(w, to: target)
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(target.weekday.rawValue)
                                        .font(UH.TextStyle.label)
                                        .foregroundStyle(UH.Palette.ink)
                                    Text(target.date.formatted(.dateTime.weekday(.abbreviated).month(.abbreviated).day()))
                                        .font(UH.TextStyle.caption)
                                        .foregroundStyle(UH.Palette.muted)
                                }

                                Spacer()

                                Text(target.week == sourceDay.week ? L("This week") : L("Next week"))
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(UH.Palette.hover, in: Capsule())

                                Image(systemName: "arrow.right")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundStyle(UH.Palette.accentInk)
                            }
                            .padding(UH.Space.small)
                            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("moveswap.move.\(target.week).\(target.weekday.rawValue)")
                    }
                }
            }
        }
    }

    private func performMove(_ workout: Workout, to target: MoveTarget) {
        Task {
            isSubmitting = true
            errorMessage = nil
            let success = await model.move(workout, to: target)
            isSubmitting = false
            if success {
                dismiss()
            } else if let err = model.actionError {
                errorMessage = err
            }
        }
    }
}

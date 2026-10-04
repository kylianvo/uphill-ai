import SwiftUI

struct WorkoutDetailSheet: View {
    let model: PlanViewModel
    let workoutID: Int
    @Environment(\.dismiss) private var dismiss
    @State private var rpe: Int?
    @State private var notes: String = ""
    @State private var isBusy = false
    @State private var showSaved = false
    @State private var didLoadLog = false
    @State private var isTreadmill = false
    @State private var confirmMissed = false

    init(model: PlanViewModel, workoutID: Int, initialTreadmill: Bool = false, initialRpe: Int? = nil, initialNotes: String? = nil) {
        self.model = model
        self.workoutID = workoutID
        _isTreadmill = State(initialValue: initialTreadmill)
        if let initialRpe {
            _rpe = State(initialValue: initialRpe)
            _didLoadLog = State(initialValue: true)
        }
        if let initialNotes {
            _notes = State(initialValue: initialNotes)
            _didLoadLog = State(initialValue: true)
        }
    }

    private var workout: Workout? {
        model.snapshot?.workouts.first { $0.id == workoutID }
    }

    var body: some View {
        NavigationStack {
            Group {
                if let workout {
                    ScrollView {
                        VStack(alignment: .leading, spacing: UH.Space.regular) {
                            // a. Type chip, title, 3 stat tiles, quiet line
                            headerSection(workout)
                            statTiles(workout)
                            quietLine(workout)

                            if workout.isMatched {
                                matchedWatchCard(workout)
                            }

                            // b & f. Step timeline with Treadmill toggle
                            stepTimelineSection(workout)

                            // c. What it builds
                            let parsed = WorkoutStepParser.parseDescription(workout.description)
                            if let benefit = parsed.benefit, !benefit.isEmpty {
                                whatItBuildsSection(benefit)
                            }

                            // d. Common mistake
                            if let mistake = parsed.warning, !mistake.isEmpty {
                                commonMistakeSection(mistake)
                            }

                            // e. Coach Uphill note
                            if let coachQuote = parsed.coachNotes, !coachQuote.isEmpty {
                                coachQuoteSection(coachQuote)
                            }

                            // g. Primary action & How did it feel? (Log)
                            if workout.approvedAt == nil {
                                Label("Waiting for your coach's approval", systemImage: "hourglass")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                    .padding(.vertical, UH.Space.compact)
                            } else {
                                bottomActionBar(workout)
                                if !workout.isRest {
                                    howDidItFeelSection(workout)
                                }
                            }
                        }
                        .padding(UH.Space.regular)
                    }
                    .background(UH.Palette.surface.ignoresSafeArea())
                    .toolbar {
                        ToolbarItem(placement: .topBarLeading) {
                            Button("Done") { dismiss() }
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        ToolbarItem(placement: .topBarTrailing) {
                            menuActions(workout)
                        }
                    }
                    .confirmationDialog("Mark session as missed?", isPresented: $confirmMissed, titleVisibility: .visible) {
                        Button("Mark Missed", role: .destructive) {
                            run { await model.setMissed(workout) }
                        }
                        Button("Cancel", role: .cancel) {}
                    } message: {
                        Text("This logs the session as missed and notifies Coach Uphill to balance upcoming load.")
                    }
                    .onAppear { loadLog(workout) }
                } else {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .sensoryFeedback(.success, trigger: model.lastCompletedID)
        .sensoryFeedback(.error, trigger: model.actionError) { _, new in new != nil }
        .onDisappear { model.clearActionError() }
    }

    // MARK: - Header & Stat Tiles (a)

    private func headerSection(_ w: Workout) -> some View {
        let zoneColor = WorkoutTypePresentation.zoneColor(for: w)
        let chip = WorkoutTypePresentation.chipLabel(for: w)

        return VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Text(chip)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundStyle(zoneColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(zoneColor.opacity(0.12), in: Capsule())
                    .overlay(Capsule().stroke(zoneColor.opacity(0.3), lineWidth: 1))

                if w.isPriority {
                    Text("PRIORITY")
                        .font(.system(size: 10, weight: .bold))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(UH.Palette.activeFill, in: Capsule())
                }
                Spacer()
            }

            Text(w.title)
                .font(.system(size: 24, weight: .bold))
                .foregroundStyle(UH.Palette.ink)

            Text(subtitle(w))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
    }

    private func subtitle(_ w: Workout) -> String {
        guard let plan = model.snapshot?.plan,
              let date = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan,
                                           workouts: model.snapshot?.workouts ?? []) else { return w.phase }
        return date.formatted(.dateTime.weekday(.wide).day().month(.wide)) + " · " + w.phase + " Phase"
    }

    // Three stat tiles: Duration, Est. distance, Pace (/km) in SF Mono
    private func statTiles(_ w: Workout) -> some View {
        HStack(spacing: UH.Space.small) {
            statTile(
                label: "DURATION",
                value: "\(Int(w.durationMinutes)) min"
            )

            statTile(
                label: "EST. DISTANCE",
                value: w.distanceKm.flatMap { $0 > 0 ? String(format: "%.1f km", $0) : nil } ?? "—"
            )

            statTile(
                label: "PACE (/KM)",
                value: w.targetPace ?? "—"
            )
        }
    }

    private func statTile(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            Text(value)
                .font(.system(size: 15, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
                .minimumScaleFactor(0.8)
                .lineLimit(1)
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    // Quiet line with HR range and zone; elevation only when present
    private func quietLine(_ w: Workout) -> some View {
        var items: [String] = []
        if let hr = w.targetHrRange, !hr.isEmpty {
            items.append("HR \(hr)")
        }
        if !w.targetZone.isEmpty && w.targetZone != "Rest" {
            items.append("Zone \(w.targetZone)")
        }
        if let gain = w.elevationGainM, gain > 0 {
            items.append("+\(Int(gain)) m elevation gain")
        }

        return HStack(spacing: 6) {
            Image(systemName: "heart.fill")
                .font(.system(size: 10))
                .foregroundStyle(UH.Palette.muted)

            Text(items.joined(separator: " · "))
                .font(.system(size: 12, weight: .medium, design: .monospaced))
                .foregroundStyle(UH.Palette.secondary)
        }
        .padding(.horizontal, 4)
    }

    // MARK: - Step Timeline (b) & Treadmill Toggle (f)

    private func stepTimelineSection(_ w: Workout) -> some View {
        let parsed = WorkoutStepParser.parseDescription(w.description)
        let steps = WorkoutStepParser.parseSteps(workout: w, description: parsed, isTreadmill: isTreadmill)

        return VStack(alignment: .leading, spacing: UH.Space.compact) {
            HStack {
                Text("HOW TO EXECUTE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)

                Spacer()

                // Treadmill toggle
                Button {
                    withAnimation(UH.Motion.standard) {
                        isTreadmill.toggle()
                    }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "figure.run.treadmill")
                            .font(.system(size: 12))
                        Text("Treadmill")
                            .font(.system(size: 11, weight: .semibold))
                    }
                    .foregroundStyle(isTreadmill ? UH.Palette.buttonInk : UH.Palette.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(isTreadmill ? UH.Palette.accent : UH.Palette.card, in: Capsule())
                    .overlay(Capsule().stroke(isTreadmill ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                }
                .buttonStyle(.plain)
            }

            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(steps.enumerated()), id: \.element.id) { index, step in
                    timelineRow(step: step, isLast: index == steps.count - 1, workout: w)
                }
            }
            .padding(UH.Space.regular)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
        }
    }

    private func timelineRow(step: ExecutionStepItem, isLast: Bool, workout: Workout) -> some View {
        let nodeColor = (step.phase == .main) ? WorkoutTypePresentation.zoneColor(for: workout) : UH.Palette.muted

        return HStack(alignment: .top, spacing: 12) {
            // Timeline line & icon node
            VStack(spacing: 0) {
                ZStack {
                    Circle()
                        .fill(nodeColor.opacity(0.15))
                        .frame(width: 24, height: 24)

                    Image(systemName: step.phase.iconName)
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(nodeColor)
                }

                if !isLast {
                    Rectangle()
                        .fill(UH.Palette.line)
                        .frame(width: 2)
                        .frame(minHeight: 36)
                        .padding(.vertical, 2)
                }
            }

            // Step contents
            VStack(alignment: .leading, spacing: 3) {
                HStack {
                    Text(step.phase.rawValue.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(nodeColor)

                    if let dur = step.duration {
                        Text("· \(dur)")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }

                Text(step.target)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(UH.Palette.ink)

                if let rec = step.recovery {
                    Text(rec)
                        .font(.system(size: 12))
                        .foregroundStyle(UH.Palette.secondary)
                }

                let extraCues = step.steps.filter { line in
                    let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                    return !trimmed.isEmpty && trimmed != step.target && trimmed != step.recovery
                }
                if !extraCues.isEmpty {
                    VStack(alignment: .leading, spacing: 2) {
                        ForEach(extraCues, id: \.self) { line in
                            Text(line)
                                .font(.system(size: 12))
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    .padding(.top, 2)
                }
            }
            .padding(.bottom, isLast ? 0 : 16)
        }
    }

    // MARK: - What It Builds (c)

    private func whatItBuildsSection(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 4) {
                Image(systemName: "bolt.heart.fill")
                    .font(.system(size: 11))
                    .foregroundStyle(UH.Palette.accentInk)
                Text("WHAT IT BUILDS")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
            }

            Text(text)
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.ink)
                .lineSpacing(2)
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Common Mistake (d)

    private func commonMistakeSection(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 14))
                .foregroundStyle(UH.Palette.warningInk)
                .padding(.top, 1)

            VStack(alignment: .leading, spacing: 2) {
                Text("COMMON MISTAKE")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.warningInk)

                Text(text)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(UH.Palette.ink)
            }
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.warningInk.opacity(0.3), lineWidth: 1))
    }

    // MARK: - Coach Uphill Note (e)

    private func coachQuoteSection(_ quote: String) -> some View {
        HStack(spacing: 12) {
            Rectangle()
                .fill(UH.Palette.accentInk)
                .frame(width: 3)

            VStack(alignment: .leading, spacing: 4) {
                Text("“\(quote)”")
                    .font(.system(size: 13, weight: .medium))
                    .italic()
                    .foregroundStyle(UH.Palette.ink)

                Text("— Coach Uphill")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
            }
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    // MARK: - Bottom Action Bar (g)

    private func bottomActionBar(_ w: Workout) -> some View {
        VStack(spacing: UH.Space.compact) {
            if w.isDone {
                Button("Undo done") {
                    run { await model.setDone(w, false) }
                }
                .buttonStyle(.uhSecondary)
                .accessibilityIdentifier("detail.undoDone")
            } else if !w.isRest {
                Button("Mark as done") {
                    run { await model.setDone(w, true) }
                }
                .buttonStyle(.uhPrimary)
                .accessibilityIdentifier("detail.markDone")
            }

            if w.isMissedFlag {
                Text("Marked as missed")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
            }
        }
        .disabled(isBusy)
    }

    // Secondary actions in ⋯ menu
    private func menuActions(_ w: Workout) -> some View {
        Menu {
            if !w.isRest {
                let targets = model.moveTargets(for: w)
                if !targets.isEmpty {
                    Menu("Move to…") {
                        ForEach(targets) { target in
                            Button(moveLabel(target)) {
                                run {
                                    if await model.move(w, to: target) { dismiss() }
                                }
                            }
                        }
                    }
                }

                if !w.isMissedFlag && !w.isDone {
                    Button(role: .destructive) {
                        confirmMissed = true
                    } label: {
                        Label("Mark as missed", systemImage: "xmark.circle")
                    }
                }
            }
        } label: {
            Image(systemName: "ellipsis.circle")
                .font(.system(size: 18))
                .foregroundStyle(UH.Palette.ink)
                .frame(minWidth: 44, minHeight: 44)
        }
    }

    private func moveLabel(_ target: MoveTarget) -> String {
        let day = target.date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated))
        return target.week > model.currentWeek ? "Next week · \(day)" : day
    }

    // MARK: - How Did It Feel? (Log section)

    private func howDidItFeelSection(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text("HOW DID IT FEEL?")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                if let val = rpe {
                    Text("RPE \(val)/10")
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }

            // 1-10 Pill selector
            HStack(spacing: 5) {
                ForEach(1...10, id: \.self) { num in
                    Button {
                        rpe = num
                    } label: {
                        Text("\(num)")
                            .font(.system(size: 12.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(rpe == num ? Color.white : UH.Palette.ink)
                            .frame(maxWidth: .infinity)
                            .frame(height: 34)
                            .background(
                                rpe == num ? UH.Palette.accentInk : UH.Palette.surface,
                                in: RoundedRectangle(cornerRadius: 8)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(rpe == num ? UH.Palette.accentInk : UH.Palette.line, lineWidth: 1)
                            )
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("detail.rpe.\(num)")
                }
            }

            if let val = rpe {
                Text(effortLabel(for: val))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            TextField("Add session notes (legs, terrain, weather)…", text: $notes, axis: .vertical)
                .lineLimit(3...5)
                .padding(UH.Space.small)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

            Button(showSaved ? "Saved" : "Save Log") {
                run {
                    if await model.saveLog(w, rpe: rpe, notes: notes) {
                        showSaved = true
                        try? await Task.sleep(for: .seconds(2))
                        showSaved = false
                    }
                }
            }
            .buttonStyle(.uhSecondary)
            .disabled(rpe == w.rpe && notes == (w.notes ?? ""))
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    private func effortLabel(for val: Int) -> String {
        switch val {
        case 1...2: "Very easy · Active recovery / barely noticeable effort"
        case 3...4: "Easy · Conversation pace, Zone 2 aerobic base"
        case 5...6: "Moderate · Steady aerobic effort, can speak in short sentences"
        case 7...8: "Hard · Threshold effort, heavy breathing, sustained focus"
        case 9...10: "Maximum effort · All out interval / race sprint finish"
        default: ""
        }
    }

    private func loadLog(_ w: Workout) {
        guard !didLoadLog else { return }
        rpe = w.rpe
        notes = w.notes ?? ""
        didLoadLog = true
    }

    private func run(_ action: @escaping @MainActor () async -> Void) {
        Task {
            isBusy = true
            await action()
            isBusy = false
        }
    }

    // MARK: - Matched Watch Workout Card

    @ViewBuilder
    private func matchedWatchCard(_ w: Workout) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                HStack(spacing: 6) {
                    Image(systemName: "applewatch")
                        .foregroundStyle(UH.Palette.accentInk)
                    Text(w.matchedDeviceModel ?? "COROS APEX 2 Pro")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                }

                Spacer()

                HStack(spacing: 4) {
                    Circle()
                        .fill(UH.Palette.accentInk)
                        .frame(width: 5, height: 5)
                    Text("Matched")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(UH.Palette.activeFill, in: Capsule())
            }

            // Target vs Actual 2x2 comparison grid
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                if let km = w.matchedDistanceKm {
                    comparisonTile(
                        label: "DISTANCE",
                        actual: String(format: "%.2f km", km),
                        target: w.distanceKm.map { String(format: "%.1f km", $0) }
                    )
                }

                if let secs = w.matchedDurationSeconds {
                    let mins = Int(secs / 60)
                    let remSecs = Int(secs) % 60
                    comparisonTile(
                        label: "DURATION",
                        actual: "\(mins):\(String(format: "%02d", remSecs))",
                        target: "\(Int(w.durationMinutes))m"
                    )
                }

                if let km = w.matchedDistanceKm, let secs = w.matchedDurationSeconds, km > 0 {
                    let paceSecs = secs / km
                    let pMin = Int(paceSecs / 60)
                    let pSec = Int(paceSecs) % 60
                    comparisonTile(
                        label: "PACE",
                        actual: "\(pMin):\(String(format: "%02d", pSec)) /km",
                        target: w.targetPace
                    )
                }

                if let hr = w.matchedAvgHr {
                    comparisonTile(
                        label: "AVG HR",
                        actual: "\(hr) bpm",
                        target: w.targetHrRange ?? (w.targetZone.isEmpty ? nil : "Z\(w.targetZone)")
                    )
                }
            }

            HStack {
                Text("Synced automatically via watch integration")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                if let id = w.matchedActivityId {
                    Text("#\(id)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                }
            }
        }
        .trainingCard()
        .accessibilityIdentifier("detail.matchedCard")
    }

    private func comparisonTile(label: String, actual: String, target: String?) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            Text(actual)
                .font(.system(size: 14, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
            if let target, !target.isEmpty {
                Text("Target: \(target)")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(UH.Palette.secondary)
            }
        }
        .padding(8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 8))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(UH.Palette.line, lineWidth: 1))
    }

}

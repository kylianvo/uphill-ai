import SwiftUI

struct WorkoutDetailSheet: View {
    let model: PlanViewModel
    let workoutID: Int
    var actingAsAthlete: CoachedAthleteRow? = nil
    var coachingService: (any CoachingServicing)? = nil
    var deviceService: (any DeviceConnectionServicing)? = nil
    var currentUserId: Int? = nil
    var onWorkoutUpdated: (() -> Void)? = nil
    @Environment(\.dismiss) private var dismiss
    @State private var rpe: Int?
    @State private var notes: String = ""
    @State private var isBusy = false
    @State private var showSaved = false
    @State private var didLoadLog = false
    @State private var isTreadmill = false
    @State private var confirmMissed = false
    @State private var showEditWorkout = false
    @State private var confirmDeleteWorkout = false
    /// Parsed description + steps. Filled after the sheet is on screen so tapping a row never waits on it.
    @State private var content: WorkoutDetailContent?

    @State private var corosSendState: CorosSendState = .idle
    @State private var corosSendNotice: String? = nil

    private enum CorosSendState: Equatable {
        case idle, sending, sent, error(String), notConnected
    }

    private struct ContentKey: Equatable {
        let workoutID: Int
        let description: String?
        let isTreadmill: Bool
    }

    init(model: PlanViewModel, workoutID: Int,
         actingAsAthlete: CoachedAthleteRow? = nil,
         coachingService: (any CoachingServicing)? = nil,
         deviceService: (any DeviceConnectionServicing)? = nil,
         currentUserId: Int? = nil,
         onWorkoutUpdated: (() -> Void)? = nil,
         initialTreadmill: Bool = false, initialRpe: Int? = nil, initialNotes: String? = nil) {
        self.model = model
        self.workoutID = workoutID
        self.actingAsAthlete = actingAsAthlete
        self.coachingService = coachingService
        self.deviceService = deviceService
        self.currentUserId = currentUserId
        self.onWorkoutUpdated = onWorkoutUpdated
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

                            // Nutrition / Fueling tip
                            if let tip = workout.fuelingTip, !tip.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                                fuelingTipSection(tip)
                            }

                            if workout.isMatched {
                                matchedWatchCard(workout)
                            }

                            // b & f. Step timeline with Treadmill toggle
                            stepTimelineSection(workout)

                            // c. About this session block (Overall, Why/reason, Benefit)
                            let parsed = content?.description ?? ParsedWorkoutDescription(overview: nil, process: nil, benefit: nil, warning: nil, coachNotes: nil)
                            let extractedSections = content?.sections ?? DescriptionSections(overall: nil, process: nil, reason: nil, benefit: nil, warning: nil)
                            aboutThisSessionSection(sections: extractedSections, parsed: parsed)

                            // d. Distinct caution callout for warning
                            let warningText = extractedSections.warning ?? parsed.warning
                            if let warningText, !warningText.isEmpty {
                                cautionCalloutSection(warningText)
                            }

                            // e. Coach Uphill note
                            if let coachQuote = parsed.coachNotes, !coachQuote.isEmpty {
                                coachQuoteSection(coachQuote)
                            }

                            // g. Primary action & How did it feel? (Log)
                            if workout.approvedAt == nil {
                                if let athlete = actingAsAthlete, let service = coachingService, let plan = model.snapshot?.plan {
                                    VStack(spacing: 8) {
                                        Button {
                                            run {
                                                do {
                                                    _ = try await service.approveWorkout(athleteId: athlete.athleteId, planId: plan.id, workoutId: workout.id)
                                                    onWorkoutUpdated?()
                                                    await model.load()
                                                } catch {
                                                    print("Failed to approve workout: \(error)")
                                                }
                                            }
                                        } label: {
                                            HStack(spacing: 6) {
                                                Image(systemName: "checkmark.seal.fill")
                                                Text("Approve Workout")
                                            }
                                            .font(UH.TextStyle.label)
                                            .foregroundStyle(Color.white)
                                            .frame(maxWidth: .infinity)
                                            .frame(height: 48)
                                            .background(UH.Palette.accentInk, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                        }
                                        .buttonStyle(.plain)
                                        .accessibilityIdentifier("detail.coach.approveWorkout")

                                        Text("This session was created for the athlete and is awaiting your review.")
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(UH.Palette.secondary)
                                    }
                                } else {
                                    Label("Waiting for your coach's approval", systemImage: "hourglass")
                                        .font(UH.TextStyle.caption)
                                        .foregroundStyle(UH.Palette.secondary)
                                        .padding(.vertical, UH.Space.compact)
                                }
                            } else {
                                bottomActionBar(workout)
                                if actingAsAthlete == nil && !workout.isRest && !workout.isDone && isTodayOrFuture(workout) {
                                    sendToCorosSection(workout)
                                }
                                if !workout.isRest {
                                    howDidItFeelSection(workout)
                                }
                            }

                            // Coach / Athlete Note Thread
                            if content != nil,
                               let noteAthleteId = actingAsAthlete?.athleteId ?? currentUserId,
                               let service = coachingService {
                                CoachNoteThreadView(
                                    athleteId: noteAthleteId,
                                    targetType: "workout",
                                    targetId: workout.id,
                                    service: service,
                                    canAdd: true,
                                    audience: actingAsAthlete == nil ? .athlete : .coach
                                )
                                .accessibilityIdentifier("detail.coachNotesThread")
                            }
                        }
                        .padding(UH.Space.regular)
                    }
                    .background(UH.Palette.surface.ignoresSafeArea())
                    .navigationTitle("Workout")
                    .navigationBarTitleDisplayMode(.inline)
                    // A real bar behind Done and the menu so scrolling text never shows through them.
                    .toolbarBackground(.visible, for: .navigationBar)
                    .toolbarBackground(.bar, for: .navigationBar)
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
                    .confirmationDialog("Remove this workout?", isPresented: $confirmDeleteWorkout, titleVisibility: .visible) {
                        Button("Remove Workout", role: .destructive) {
                            run {
                                guard let plan = model.snapshot?.plan,
                                      let service = coachingService,
                                      let athlete = actingAsAthlete else { return }
                                do {
                                    _ = try await service.removeWorkout(athleteId: athlete.athleteId, planId: plan.id, workoutId: workout.id)
                                    onWorkoutUpdated?()
                                    await model.load()
                                    dismiss()
                                } catch {
                                    print("Failed to remove workout: \(error)")
                                }
                            }
                        }
                        Button("Cancel", role: .cancel) {}
                    } message: {
                        Text("This will permanently remove the workout from the runner's training schedule.")
                    }
                    .sheet(isPresented: $showEditWorkout) {
                        if let plan = model.snapshot?.plan,
                           let service = coachingService,
                           let athlete = actingAsAthlete {
                            CoachEditWorkoutSheet(
                                athleteId: athlete.athleteId,
                                planId: plan.id,
                                workout: workout,
                                service: service,
                                onSaved: { _ in
                                    onWorkoutUpdated?()
                                    Task { await model.load() }
                                }
                            )
                        }
                    }
                    .onAppear { loadLog(workout) }
                    .task(id: ContentKey(workoutID: workout.id, description: workout.description, isTreadmill: isTreadmill)) {
                        let snapshot = workout, treadmill = isTreadmill
                        let built = await Task.detached(priority: .userInitiated) {
                            WorkoutDetailContent.make(workout: snapshot, isTreadmill: treadmill)
                        }.value
                        content = built
                    }
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
        let estDistance: String = {
            if w.isStrengthOrME { return "—" }
            return w.distanceKm.flatMap { $0 > 0 ? String(format: "%.1f km", $0) : nil } ?? "—"
        }()

        let paceValue: String = {
            if w.isStrengthOrME { return "—" }
            return WorkoutTypePresentation.paceTileValue(w.targetPace)
        }()

        return HStack(spacing: UH.Space.small) {
            statTile(
                label: "DURATION",
                value: "\(Int(w.durationMinutes)) min"
            )

            statTile(
                label: "EST. DISTANCE",
                value: estDistance
            )

            statTile(
                label: "PACE (/KM)",
                value: paceValue
            )
        }
    }

    private func statTile(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            Text(value)
                .font(.system(size: 14, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
                // Wraps to a second line instead of truncating at large Dynamic Type.
                .lineLimit(2)
                .minimumScaleFactor(0.8)
                .fixedSize(horizontal: false, vertical: true)
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
        if let zone = WorkoutTypePresentation.zoneLabel(w.targetZone) {
            items.append(zone)
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
        let steps = content?.steps ?? []

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
                if content == nil {
                    ProgressView().frame(maxWidth: .infinity, minHeight: 80)
                }
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

    // MARK: - Nutrition & Fueling Tip

    private func fuelingTipSection(_ tip: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "fork.knife.circle.fill")
                .font(.system(size: 16))
                .foregroundStyle(Color(red: 16/255, green: 185/255, blue: 129/255))
                .padding(.top, 1)

            VStack(alignment: .leading, spacing: 2) {
                Text("NUTRITION & FUELING")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(Color(red: 5/255, green: 150/255, blue: 105/255))

                Text(tip)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(UH.Palette.ink)
                    .lineSpacing(2)
            }
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(red: 16/255, green: 185/255, blue: 129/255).opacity(0.08), in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(Color(red: 16/255, green: 185/255, blue: 129/255).opacity(0.3), lineWidth: 1))
        .accessibilityIdentifier("detail.fuelingTip")
    }

    // MARK: - About This Session (Overall, Why, Benefit)

    private func aboutThisSessionSection(sections: DescriptionSections, parsed: ParsedWorkoutDescription) -> some View {
        let overall = sections.overall ?? parsed.overview ?? parsed.intent
        let reason = sections.reason ?? parsed.reason
        let benefit = sections.benefit ?? parsed.benefit

        let hasContent = (overall != nil && !overall!.isEmpty) ||
                         (reason != nil && !reason!.isEmpty) ||
                         (benefit != nil && !benefit!.isEmpty)

        return Group {
            if hasContent {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 5) {
                        Image(systemName: "info.circle.fill")
                            .font(.system(size: 11))
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("ABOUT THIS SESSION")
                            .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                    }

                    if let overall, !overall.isEmpty {
                        Text(overall)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(UH.Palette.ink)
                            .lineSpacing(2)
                    }

                    if let reason, !reason.isEmpty {
                        HStack(alignment: .top, spacing: 6) {
                            Text("Why:")
                                .font(.system(size: 12.5, weight: .bold))
                                .foregroundStyle(UH.Palette.secondary)
                            Text(reason)
                                .font(.system(size: 12.5))
                                .foregroundStyle(UH.Palette.secondary)
                                .lineSpacing(1.5)
                        }
                    }

                    if let benefit, !benefit.isEmpty {
                        HStack(alignment: .top, spacing: 6) {
                            Text("Benefit:")
                                .font(.system(size: 12.5, weight: .bold))
                                .foregroundStyle(Color(red: 16/255, green: 185/255, blue: 129/255))
                            Text(benefit)
                                .font(.system(size: 12.5))
                                .foregroundStyle(UH.Palette.ink)
                                .lineSpacing(1.5)
                        }
                    }
                }
                .padding(UH.Space.regular)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
                .accessibilityIdentifier("detail.aboutSession")
            }
        }
    }

    // MARK: - Caution Callout (Warning)

    private func cautionCalloutSection(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 14))
                .foregroundStyle(UH.Palette.danger)
                .padding(.top, 1)

            VStack(alignment: .leading, spacing: 2) {
                Text("CAUTION")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.danger)

                Text(text)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(UH.Palette.ink)
                    .lineSpacing(1.5)
            }
        }
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.danger.opacity(0.08), in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.danger.opacity(0.3), lineWidth: 1))
        .accessibilityIdentifier("detail.cautionCallout")
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

    // MARK: - Send to Watch (COROS)

    private func isTodayOrFuture(_ w: Workout) -> Bool {
        guard let plan = model.snapshot?.plan,
              let date = PlanCalendar.date(week: w.weekNumber, weekday: w.weekday, plan: plan,
                                           workouts: model.snapshot?.workouts ?? []) else {
            return true
        }
        let cal = Calendar.current
        let startOfToday = cal.startOfDay(for: Date())
        let startOfWorkoutDate = cal.startOfDay(for: date)
        return startOfWorkoutDate >= startOfToday
    }

    private func sendToCorosSection(_ w: Workout) -> some View {
        VStack(spacing: 6) {
            Button {
                Task { await performSendToCoros() }
            } label: {
                HStack(spacing: 6) {
                    if UIImage(named: "coros_mark") != nil {
                        Image("coros_mark")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 14, height: 14)
                    } else {
                        Image(systemName: "applewatch")
                            .font(.system(size: 13, weight: .bold))
                    }

                    switch corosSendState {
                    case .sending:
                        ProgressView().controlSize(.small)
                        Text("Sending…")
                            .font(.system(size: 13, weight: .semibold))
                    case .sent:
                        Image(systemName: "checkmark")
                            .font(.system(size: 11, weight: .bold))
                        Text("Sent to COROS")
                            .font(.system(size: 13, weight: .semibold))
                    case .notConnected:
                        Text("Connect COROS in Profile")
                            .font(.system(size: 13, weight: .semibold))
                    case .idle, .error:
                        Text("Send next 4 weeks to COROS")
                            .font(.system(size: 13, weight: .semibold))
                    }
                }
                .foregroundStyle(corosSendState == .sent ? UH.Palette.accentInk : UH.Palette.ink)
                .frame(maxWidth: .infinity)
                .frame(height: 44)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(
                    RoundedRectangle(cornerRadius: UH.Radius.control)
                        .stroke(corosSendState == .sent ? UH.Palette.accentInk : UH.Palette.line, lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
            .disabled(corosSendState == .sending)
            .accessibilityIdentifier("detail.sendToCoros")

            if let notice = corosSendNotice {
                Text(notice)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(corosSendState == .sent ? UH.Palette.accentInk : UH.Palette.danger)
            }
        }
        .padding(.vertical, 4)
    }

    private func performSendToCoros() async {
        guard let service = deviceService else {
            corosSendState = .notConnected
            corosSendNotice = "COROS isn't connected. Connect it in Profile."
            return
        }

        if let status = try? await service.fetchStatus(), !status.isCorosConnected {
            corosSendState = .notConnected
            corosSendNotice = "COROS isn't connected. Connect it in Profile."
            return
        }

        corosSendState = .sending
        corosSendNotice = nil
        // Local date: ISO8601DateFormatter is UTC, a day behind in Vietnam before 7am.
        let today = Date.ISO8601FormatStyle(timeZone: .current).year().month().day().format(Date())
        do {
            // The backend sends the plan's next weeks, not just this workout.
            let outcome = try await service.pushToCoros(clientToday: today, lang: AppLanguage.code)
            if outcome.isSuccess {
                corosSendState = .sent
                let count = outcome.summary?.workoutsSent ?? 0
                let end = outcome.summary?.windowEnd ?? "the upcoming weeks"
                corosSendNotice = "Sent \(count) workouts to COROS through \(end)."
            } else {
                let err = outcome.errorMessage ?? "Could not send to COROS."
                corosSendState = .error(err)
                corosSendNotice = err
            }
        } catch {
            let err = error.localizedDescription
            corosSendState = .error(err)
            corosSendNotice = err
        }
    }

    // Secondary actions in ⋯ menu
    private func menuActions(_ w: Workout) -> some View {
        Menu {
            if actingAsAthlete != nil {
                Button {
                    showEditWorkout = true
                } label: {
                    Label("Edit Workout", systemImage: "pencil")
                }
                .accessibilityIdentifier("detail.coach.editWorkout")

                Button(role: .destructive) {
                    confirmDeleteWorkout = true
                } label: {
                    Label("Remove Workout", systemImage: "trash")
                }
                .accessibilityIdentifier("detail.coach.removeWorkout")

                Divider()
            }

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

    // MARK: - How Did It Feel? (5-Level Feeling Scale)

    private func howDidItFeelSection(_ w: Workout) -> some View {
        let activeFeeling = WorkoutFeeling.from(rpe: rpe)

        return VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text("HOW DID IT FEEL?")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                if let feel = activeFeeling {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(feel.color)
                            .frame(width: 6, height: 6)
                        Text("\(feel.label) · RPE \(feel.rpe)/10")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(feel.color)
                    }
                }
            }

            // 5-level segmented bar
            HStack(spacing: 5) {
                ForEach(WorkoutFeeling.allCases) { feel in
                    let isSelected = activeFeeling == feel
                    Button {
                        rpe = feel.rpe
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    } label: {
                        VStack(spacing: 4) {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(isSelected ? feel.color : UH.Palette.line)
                                .frame(width: isSelected ? 20 : 12, height: 3.5)

                            Text(feel.label)
                                .font(.system(size: 10, weight: isSelected ? .bold : .medium))
                                .foregroundStyle(isSelected ? feel.color : UH.Palette.ink)
                                .lineLimit(1)
                                .minimumScaleFactor(0.7)

                            Text("RPE \(feel.rpe)")
                                .font(.system(size: 9, weight: .semibold, design: .monospaced))
                                .foregroundStyle(isSelected ? feel.color : UH.Palette.muted)
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 52)
                        .background(
                            isSelected ? feel.color.opacity(0.12) : UH.Palette.surface,
                            in: RoundedRectangle(cornerRadius: 8)
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(isSelected ? feel.color : UH.Palette.line, lineWidth: isSelected ? 1.5 : 1)
                        )
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("detail.feeling.\(feel.rawValue)")
                }
            }

            // Spotlight card for selected feeling
            if let feel = activeFeeling {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: feel.iconName)
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(feel.color)
                        Text(feel.label)
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(feel.color)
                        Spacer()
                        Text("RPE \(feel.rpe) / 10")
                            .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(feel.color)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(feel.color.opacity(0.12), in: Capsule())
                    }

                    Text(feel.subLabel)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)

                    HStack(alignment: .top, spacing: 6) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 11))
                            .foregroundStyle(feel.color)
                            .padding(.top, 1)
                        Text(feel.coachDescription)
                            .font(.system(size: 11.5))
                            .foregroundStyle(UH.Palette.ink)
                            .lineSpacing(1.5)
                    }
                    .padding(8)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 6))
                }
                .padding(10)
                .background(feel.color.opacity(0.06), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(feel.color.opacity(0.25), lineWidth: 1))
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
                    Text("COROS")
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
                        target: w.targetHrRange ?? WorkoutTypePresentation.zoneShort(w.targetZone)
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

import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel
    let generation: GenerationCenter
    let onBuildPlan: () -> Void
    let onViewProgress: () -> Void
    var user: User? = nil
    var onSharpen: (TrainingDestination) -> Void = { _ in }
    var initialVolumeMode: VolumeChartMode = .weekDays
    var app: AppModel? = nil
    @State private var viewMode: PlanViewMode = .list

    init(model: PlanViewModel, generation: GenerationCenter, onBuildPlan: @escaping () -> Void,
         onViewProgress: @escaping () -> Void, user: User? = nil, onSharpen: @escaping (TrainingDestination) -> Void = { _ in },
         initialViewMode: PlanViewMode = .list,
         initialVolumeMode: VolumeChartMode = .weekDays,
         app: AppModel? = nil) {
        self.model = model
        self.generation = generation
        self.onBuildPlan = onBuildPlan
        self.onViewProgress = onViewProgress
        self.user = user
        self.onSharpen = onSharpen
        self.initialVolumeMode = initialVolumeMode
        self.app = app
        _viewMode = State(initialValue: initialViewMode)
    }
    @State private var selectedWorkout: Workout?
    @State private var moveSwapDay: PlanDay?
    @State private var calendarDay: MoveTarget?
    /// Runs once the calendar day sheet has finished dismissing; a second sheet can't open while it is up.
    @State private var afterCalendarDay: (() -> Void)?
    @State private var showManage = false
    @State private var toolAfterManage: TrainingDestination? = nil
    @State private var startNewAfterManage = false
    @State private var scheduleAfterManage = false
    @State private var showSchedule = false
    @State private var showNextWeek = false
    @State private var showAdapt = false
    @State private var adaptAfterManage = false
    @State private var showReview = false
    @State private var showGoal = false
    @State private var showAddWorkout = false
    @State private var readyBanner: String?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private func openWeekInList(_ week: Int) {
        withAnimation(reduceMotion ? nil : UH.Motion.standard) {
            model.selectedWeek = week
            viewMode = .list
        }
    }

    var body: some View {
        NavigationStack {
            content
                .background(UH.Palette.surface.ignoresSafeArea())
                .onChange(of: model.notificationRoute, initial: true) { _, route in
                    guard let route else { return }
                    if let week = route.weekNumber { openWeekInList(week) }
                    if let id = route.workoutId { selectedWorkout = model.snapshot?.workouts.first { $0.id == id } }
                    if route.kind == "review" { showReview = true }
                    if route.intent == "adapt", route.weekNumber != nil, model.canAdaptWeek(model.selectedWeek) { showAdapt = true }
                    if route.kind == "plan", route.intent == "planning", model.nextWeekOffer != nil { showNextWeek = true }
                    app?.notifications.visibleRoute = route
                    model.notificationRoute = nil
                }
                .navigationTitle("Plan")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItemGroup(placement: .topBarTrailing) {
                        if app?.actingAsAthlete != nil {
                            Button {
                                showAddWorkout = true
                            } label: {
                                Image(systemName: "plus")
                            }
                            .accessibilityIdentifier("plan.coach.addWorkout")
                        }
                        Button("Manage") { showManage = true }
                            .disabled(model.snapshot == nil)
                            .accessibilityIdentifier("plan.manageButton")
                    }
                }
                .sheet(item: $selectedWorkout, onDismiss: { app?.notifications.visibleRoute = nil }) { workout in
                    WorkoutDetailSheet(
                        model: model,
                        workoutID: workout.id,
                        actingAsAthlete: app?.actingAsAthlete,
                        coachingService: app?.coachingService,
                        deviceService: app?.deviceConnectionService,
                        currentUserId: user?.id,
                        onWorkoutUpdated: {
                            Task { await model.load() }
                        }
                    )
                }
                .sheet(isPresented: $showAddWorkout) {
                    if let app, let athlete = app.actingAsAthlete, let plan = model.snapshot?.plan {
                        CoachAddWorkoutSheet(
                            athleteId: athlete.athleteId,
                            planId: plan.id,
                            initialWeek: model.selectedWeek,
                            service: app.coachingService,
                            onAdded: { _ in
                                Task { await model.load() }
                            }
                        )
                    }
                }
                .sheet(item: $calendarDay, onDismiss: {
                    afterCalendarDay?()
                    afterCalendarDay = nil
                }) { target in
                    CalendarDaySheet(
                        model: model,
                        target: target,
                        onOpenWeek: { week in afterCalendarDay = { openWeekInList(week) }; calendarDay = nil },
                        onSelect: { workout in afterCalendarDay = { selectedWorkout = workout }; calendarDay = nil },
                        onMoveOrSwap: model.athleteId == nil ? { day in afterCalendarDay = { moveSwapDay = day }; calendarDay = nil } : nil
                    )
                }
                .sheet(item: $moveSwapDay) { day in
                    MoveSwapDaySheet(model: model, sourceDay: day)
                }
                .sheet(isPresented: $showSchedule) { ScheduleChangeSheet(model: model) }
                .sheet(isPresented: $showAdapt) { AdaptWeekSheet(model: model, week: model.selectedWeek) }
                .sheet(isPresented: $showGoal) { GoalSheet(model: model) }
                .sheet(isPresented: $showReview) { WeekReviewSheet(model: model, week: model.selectedWeek) }
                .sheet(isPresented: $showNextWeek) {
                    if let offer = model.nextWeekOffer { NextWeekSheet(model: model, offer: offer) }
                }
                .sheet(isPresented: $showManage, onDismiss: {
                    if startNewAfterManage { startNewAfterManage = false; onBuildPlan() }
                    if scheduleAfterManage { scheduleAfterManage = false; showSchedule = true }
                    if adaptAfterManage { adaptAfterManage = false; showAdapt = true }
                    if let tool = toolAfterManage {
                        toolAfterManage = nil
                        onSharpen(tool)
                    }
                }) {
                    ManagePlanSheet(model: model,
                                    deviceService: app?.deviceConnectionService,
                                    onStartNew: { startNewAfterManage = true },
                                    onSchedule: { scheduleAfterManage = true },
                                    onAdapt: model.canAdaptWeek(model.selectedWeek) ? { adaptAfterManage = true } : nil,
                                    onTool: { dest in toolAfterManage = dest })
                }
        }
        .task {
            if model.state == .loading { await model.load() }
            if let app { await app.refreshPendingInvites() }
        }
        .onChange(of: model.beginnerMilestones) { _, _ in model.refreshCelebration() }
        .task(id: model.snapshot?.plan.id) { model.refreshCelebration() }
        .sheet(item: Binding(get: { model.celebration }, set: { if $0 == nil { model.dismissCelebration() } })) { item in
            MilestoneCelebrationSheet(
                item: item,
                next: model.beginnerMilestones?.next,
                targetTitle: model.beginnerMilestones?.targetTitle ?? "",
                canUpgrade: model.beginnerMilestones?.canUpgrade == true,
                onUpgrade: { Task { await model.upgradeMilestoneTarget(clearEvent: model.beginnerMilestones?.hasEvent == true) } }
            )
        }
    }

    @ViewBuilder
    private var content: some View {
        switch model.state {
        case .loading:
            ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
        case .empty:
            VStack(spacing: UH.Space.section) {
                if generation.running?.kind == .newPlan { buildingBanner }
                VStack(spacing: UH.Space.compact) {
                    Image(systemName: "mountain.2").font(Font.largeTitle).foregroundStyle(UH.Palette.accentInk)
                        .accessibilityHidden(true)
                    Text("No plan yet").font(UH.TextStyle.screenTitle).foregroundStyle(UH.Palette.ink)
                    Text("Your weekly workouts show up here once Coach Uphill builds your plan.")
                        .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Button("Build my plan", action: onBuildPlan)
                    .buttonStyle(.uhPrimary).frame(maxWidth: 280).accessibilityIdentifier("plan.build")
            }
            .padding(UH.Space.section)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .failed(let error):
            VStack(spacing: UH.Space.regular) {
                message(title: L("Couldn't load your plan"), body: error)
                Button("Try again") { Task { await model.load() } }
                    .buttonStyle(.uhPrimary)
                    .frame(maxWidth: 220)
            }
        case .loaded:
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        if generation.running != nil { buildingBanner }
                        if let notice = model.calendarNotice {
                            ScheduleNoticeBanner(notice: notice, onDismiss: model.dismissCalendarNotice)
                                .padding(.horizontal, UH.Space.regular)
                        }
                        if let cachedAt = model.cachedAt { offlineBanner(cachedAt) }

                        if let app, app.actingAsAthlete == nil,
                           let changes = app.session.user?.coachProfileChanges, !changes.isEmpty {
                            CoachProfileChangesCard(changes: changes) {
                                Task { await app.acknowledgeCoachProfileChanges() }
                            }
                            .padding(.horizontal, UH.Space.regular)
                        }

                        if let app, !app.pendingInvites.isEmpty {
                            PendingInviteBanner(
                                invites: app.pendingInvites,
                                onAccept: { inviteId in
                                    Task { await app.acceptInvite(inviteId: inviteId) }
                                },
                                onDecline: { inviteId in
                                    Task { await app.declineInvite(inviteId: inviteId) }
                                }
                            )
                            .padding(.horizontal, UH.Space.regular)
                        }

                        // 1. Race and goal header
                        raceGoalHeader

                        if let app, let athlete = app.actingAsAthlete {
                            CoachFocusCard(app: app, athleteId: athlete.athleteId, athleteName: athlete.displayName,
                                           plan: model.snapshot?.plan,
                                           onAdapt: { showAdapt = true },
                                           onBuildPlan: onBuildPlan,
                                           onBuildNextWeek: { showNextWeek = model.nextWeekOffer != nil },
                                           onChanged: { await model.load() })
                                .padding(.horizontal, UH.Space.regular)
                        }

                        // 3. Summary carousel
                        SummaryCarousel(model: model,
                                        onGoal: { showGoal = true },
                                        initialVolumeMode: initialVolumeMode)

                        // 4. Coach review card
                        CoachReviewCard(model: model, onOpenReview: { showReview = true })
                            .padding(.horizontal, UH.Space.regular)
                            .task(id: briefTaskID) { await model.loadWeekBrief() }

                        if let app, let user, app.actingAsAthlete == nil {
                            SharpenChecklistCard(
                                user: user,
                                corosConnected: app.corosConnected || app.appleHealthConnected,
                                raceHistoryLinked: !(app.raceHistory?.claims.isEmpty ?? true),
                                onOpen: onSharpen, notifications: app.notifications
                            )
                            .padding(.horizontal, UH.Space.regular)
                            .task {
                                async let coros: Void = app.loadCorosStatus()
                                async let races: Void = app.loadRaceHistory()
                                _ = await (coros, races)
                            }
                        }

                        // 4. Week switcher with List / Calendar toggle
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek, viewMode: $viewMode)
                            .padding(.horizontal, UH.Space.regular)

                        // 5. Day list, Month Calendar grid, or Ungenerated Week CTA
                        if model.isWeekUngenerated(model.selectedWeek) {
                            ungeneratedWeekCTA(model.selectedWeek)
                                .padding(.horizontal, UH.Space.regular)
                        } else if viewMode == .calendar {
                            PlanCalendarGridView(model: model, onSelectDay: { calendarDay = $0 }, onOpenWeek: openWeekInList)
                            .padding(.horizontal, UH.Space.regular)
                        } else {
                            LazyVStack(spacing: UH.Space.compact) {
                                ForEach(model.days) { day in
                                    DayRow(day: day, onToggleDone: model.athleteId == nil ? { workout in
                                        Task { await model.setDone(workout, !workout.isDone) }
                                    } : nil, onMoveOrSwap: model.athleteId == nil ? { day in
                                        moveSwapDay = day
                                    } : nil, onSelect: { selectedWorkout = $0 })
                                        .id(day.id)
                                }
                            }
                            .padding(.horizontal, UH.Space.regular)
                        }

                        // 7. Next week card
                        nextWeekCard
                    }
                    .padding(.vertical, UH.Space.regular)
                }
                .refreshable { await model.load() }
                .onChange(of: model.selectedWeek) { Task { await model.refreshNextWeekOffer() } }
                .onChange(of: generation.lastOutcome) { _, outcome in
                    guard let outcome, outcome.kind == .nextWeek || outcome.kind == .adaptWeek else { return }
                    generation.clearOutcome()
                    if case .done = outcome.outcome {
                        readyBanner = outcome.kind == .adaptWeek ? L("Week updated") : L("New week is ready")
                        Task { try? await Task.sleep(for: .seconds(3)); readyBanner = nil }
                    }
                }
                .onChange(of: model.lastCompletedID) { _, id in
                    guard let id, let line = model.doneLine(for: id) else { return }
                    readyBanner = line
                    Task { try? await Task.sleep(for: .seconds(3)); if readyBanner == line { readyBanner = nil } }
                }
                .onChange(of: model.autoSyncSummary) { _, summary in
                    guard let summary else { return }
                    model.clearAutoSyncSummary()
                    readyBanner = summary
                    Task { try? await Task.sleep(for: .seconds(3)); readyBanner = nil }
                }
                .sensoryFeedback(.success, trigger: readyBanner)
                .overlay(alignment: .top) {
                    if let readyBanner {
                        Label(readyBanner, systemImage: "checkmark.circle.fill")
                            .font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                            .padding(UH.Space.small)
                            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                            .padding(.top, UH.Space.small)
                            .transition(reduceMotion ? .opacity : .move(edge: .top).combined(with: .opacity))
                    }
                }
                .animation(reduceMotion ? nil : UH.Motion.standard, value: readyBanner)
                .task(id: "\(model.selectedWeek)-\(model.days.count)") {
                    // A coach lands on the coach card at the top, not on today's session.
                    guard model.selectedWeek == model.currentWeek, app?.actingAsAthlete == nil else { return }
                    // Let the lazy list lay out its rows before scrolling.
                    await Task.yield()
                    try? await Task.sleep(for: .milliseconds(150))
                    scrollToToday(proxy)
                }
            }
        }
    }

    private func scrollToToday(_ proxy: ScrollViewProxy) {
        guard let today = model.days.first(where: { $0.isToday }) else { return }
        if reduceMotion {
            proxy.scrollTo(today.id, anchor: .top)
        } else {
            withAnimation(UH.Motion.standard) { proxy.scrollTo(today.id, anchor: .top) }
        }
    }

    @ViewBuilder
    private var nextWeekCard: some View {
        if generation.running?.kind == .nextWeek {
            HStack(spacing: UH.Space.small) {
                ProgressView()
                Text("Building the next block…").font(UH.TextStyle.label)
            }
            .frame(maxWidth: .infinity, alignment: .leading).uhCard().padding(.horizontal, UH.Space.regular)
        } else if let offer = model.nextWeekOffer {
            if offer.unlocked {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack(spacing: UH.Space.compact) {
                        Text(offer.title).font(UH.TextStyle.sectionTitle)
                    }
                    Text("Coach Uphill uses how this block went to shape the next one.").foregroundStyle(UH.Palette.secondary)
                    if let pct = offer.previousCompletionPct {
                        Text("Block completion: \(Int(pct))% done").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                    Button(offer.title) { showNextWeek = true }
                        .buttonStyle(.uhPrimary)
                        .accessibilityIdentifier("plan.nextweek")
                }
                .frame(maxWidth: .infinity, alignment: .leading).uhCard().padding(.horizontal, UH.Space.regular)
            } else {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack(spacing: UH.Space.compact) {
                        Text(verbatim: offer.sessionsToUnlock.map { L("%lld more sessions to shape Block %lld", $0, offer.blockNumber) }
                             ?? L("Keep going to shape Block %lld", offer.blockNumber))
                            .font(UH.TextStyle.sectionTitle)
                    }
                    Text("Coach Uphill builds the next block from how this one goes.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                    if let pct = offer.previousCompletionPct {
                        ProgressView(value: min(70, max(0, pct)), total: 70)
                            .tint(UH.Palette.accentInk)
                            .accessibilityLabel(L("Block progress"))
                    }
                    Button("Generate anyway") { showNextWeek = true }
                        .buttonStyle(.uhSecondary)
                        .accessibilityIdentifier("plan.nextweek")
                }
                .frame(maxWidth: .infinity, alignment: .leading).uhCard().padding(.horizontal, UH.Space.regular)
            }
        }
    }

    private var buildingBanner: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let elapsed = max(0, Int(context.date.timeIntervalSince(generation.running?.startedAt ?? context.date)))
            let kind = generation.running?.kind
            let title: String = switch kind {
            case .adaptWeek: L("Adapting your week…")
            case .nextWeek: L("Building the next block…")
            default: L("Building your plan…")
            }
            HStack(spacing: UH.Space.small) {
                ProgressView()
                Text("\(title) \(elapsed / 60):\(String(format: "%02d", elapsed % 60))")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.ink)
                Spacer(minLength: 0)
                if kind == .newPlan {
                    Button("View", action: onViewProgress).font(UH.TextStyle.disclosure).frame(minWidth: 44, minHeight: 44)
                }
            }
            .frame(minHeight: 44)
            .padding(.horizontal, UH.Space.small)
            .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .padding(.horizontal, UH.Space.regular)
        }
    }

    private func offlineBanner(_ date: Date) -> some View {
        Label {
            Text("Offline · showing your plan from \(date, format: .relative(presentation: .named))")
        } icon: {
            Image(systemName: "wifi.slash")
        }
        .font(UH.TextStyle.caption)
        .foregroundStyle(UH.Palette.secondary)
        .padding(UH.Space.small)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .padding(.horizontal, UH.Space.regular)
    }

    private func message(title: String, body: String) -> some View {
        VStack(spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text(body).font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Ungenerated Week Call To Action

    private func ungeneratedWeekCTA(_ week: Int) -> some View {
        VStack(spacing: UH.Space.regular) {
            ZStack {
                Circle()
                    .fill(UH.Palette.activeFill)
                    .frame(width: 56, height: 56)
                Image(systemName: "sparkles")
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.accentInk)
            }
            .padding(.top, 8)

            VStack(spacing: 4) {
                Text("Week \(week) is ready to generate")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)

                Text("Coach Uphill will generate your personalized workouts based on your recent training consistency and progress.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .multilineTextAlignment(.center)
                    .lineSpacing(2)
                    .padding(.horizontal, 16)
            }

            Button {
                showNextWeek = true
            } label: {
                HStack(spacing: 6) {
                    if generation.running?.kind == .nextWeek {
                        ProgressView().tint(UH.Palette.onSolid)
                        Text("Building the next block…")
                    } else {
                        Text("Generate Week \(week)")
                    }
                }
                .font(UH.TextStyle.label)
                .frame(maxWidth: .infinity)
                .frame(height: 44)
                .foregroundStyle(UH.Palette.onSolid)
                .background(UH.Palette.accentInk, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
            .buttonStyle(.plain)
            .disabled(generation.running?.kind == .nextWeek)
            .accessibilityIdentifier("plan.generateWeekCTA")
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .padding(UH.Space.regular)
        .frame(maxWidth: .infinity)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line))
    }

    // MARK: - Race and Goal Header

    /// Refetch the brief when the week changes or its workouts are rebuilt (adapt, next week).
    private var briefTaskID: String {
        let ids = (model.snapshot?.workouts ?? []).filter { $0.weekNumber == model.selectedWeek }.map { String($0.id) }
        return "\(model.selectedWeek):" + ids.joined(separator: ",")
    }

    private func raceFacts(_ plan: Plan) -> Text {
        let date = PlanCalendar.day(from: plan.raceDate)?.formatted(.dateTime.month(.abbreviated).day().year())
        let facts = [date, PlanSummary.courseLine(km: plan.courseDistanceKm, gainM: plan.courseElevationGainM)].compactMap { $0 }
        var text = Text(verbatim: facts.joined(separator: " · ")).foregroundStyle(UH.Palette.secondary)
        if let days = model.daysToRace {
            let countdown = days == 0 ? "· " + L("Race day")
                : days < 7 ? "· " + L("Race week")
                : L("· %lld weeks to go", Int((Double(days) / 7).rounded(.up)))
            text = text + Text(verbatim: (facts.isEmpty ? "" : " ") + countdown).foregroundStyle(UH.Palette.accentInk)
        }
        return text
    }

    private var raceGoalHeader: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let plan = model.snapshot?.plan {
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(plan.raceName)
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(1)

                        if let beginnerHeader = model.beginnerHeaderText {
                            Text(verbatim: beginnerHeader)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.accentInk)
                                .accessibilityIdentifier("plan.milestones.header")
                        } else {
                            // Race date and course, so the week's km below isn't read as the race distance; one Text so it wraps.
                            raceFacts(plan)
                                .font(UH.TextStyle.caption)
                                .fixedSize(horizontal: false, vertical: true)
                                .accessibilityIdentifier("plan.raceFacts")
                        }
                    }

                }

                Text(verbatim: PlanSummary.weekLine(PlanSummary.volume(week: model.selectedWeek, workouts: model.snapshot?.workouts ?? [])))
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("plan.weekLine")
            }
        }
        .padding(.horizontal, UH.Space.regular)
    }

}

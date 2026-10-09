import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel
    let generation: GenerationCenter
    let onBuildPlan: () -> Void
    let onViewProgress: () -> Void
    var user: User? = nil
    var onSharpen: (TrainingDestination) -> Void = { _ in }
    var initialCoachExpanded: Bool = false
    var initialVolumeMode: VolumeChartMode = .weekDays
    var app: AppModel? = nil
    @State private var viewMode: PlanViewMode = .list

    init(model: PlanViewModel, generation: GenerationCenter, onBuildPlan: @escaping () -> Void,
         onViewProgress: @escaping () -> Void, user: User? = nil, onSharpen: @escaping (TrainingDestination) -> Void = { _ in },
         initialViewMode: PlanViewMode = .list, initialCoachExpanded: Bool = false,
         initialVolumeMode: VolumeChartMode = .weekDays,
         app: AppModel? = nil) {
        self.model = model
        self.generation = generation
        self.onBuildPlan = onBuildPlan
        self.onViewProgress = onViewProgress
        self.user = user
        self.onSharpen = onSharpen
        self.initialCoachExpanded = initialCoachExpanded
        self.initialVolumeMode = initialVolumeMode
        self.app = app
        _viewMode = State(initialValue: initialViewMode)
    }
    @State private var selectedWorkout: Workout?
    @State private var moveSwapDay: PlanDay?
    @State private var showManage = false
    @State private var toolAfterManage: TrainingDestination? = nil
    @State private var startNewAfterManage = false
    @State private var scheduleAfterManage = false
    @State private var showSchedule = false
    @State private var showNextWeek = false
    @State private var showAdapt = false
    @State private var showReview = false
    @State private var showGoal = false
    @State private var showAddWorkout = false
    @State private var readyBanner: String?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        NavigationStack {
            content
                .background(UH.Palette.surface.ignoresSafeArea())
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
                .sheet(item: $selectedWorkout) { workout in
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
                    if let tool = toolAfterManage {
                        toolAfterManage = nil
                        onSharpen(tool)
                    }
                }) {
                    ManagePlanSheet(model: model,
                                    deviceService: app?.deviceConnectionService,
                                    onStartNew: { startNewAfterManage = true },
                                    onSchedule: { scheduleAfterManage = true },
                                    onTool: { dest in toolAfterManage = dest })
                }
        }
        .task {
            if model.state == .loading { await model.load() }
            if let app { await app.refreshPendingInvites() }
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
                    Image(systemName: "mountain.2").font(.system(size: 48)).foregroundStyle(UH.Palette.accentInk)
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
                        if generation.running?.kind == .newPlan { buildingBanner }
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

                        // 2. Summary carousel
                        SummaryCarousel(model: model,
                                        adapting: generation.running?.kind == .adaptWeek ? model.selectedWeek : nil,
                                        onReview: { showReview = true }, onAdapt: { showAdapt = true },
                                        onGoal: { showGoal = true },
                                        initialVolumeMode: initialVolumeMode)

                        // 3. Coach review card
                        CoachReviewCard(model: model, onOpenReview: { showReview = true }, initialExpanded: initialCoachExpanded)
                            .padding(.horizontal, UH.Space.regular)

                        // Adapt week button
                        if model.canAdaptWeek(model.selectedWeek) {
                            HStack {
                                Spacer()
                                Button {
                                    showAdapt = true
                                } label: {
                                    HStack(spacing: 5) {
                                        Image(systemName: "sparkles")
                                            .font(.system(size: 11, weight: .bold))
                                        Text("Adapt Week \(model.selectedWeek)")
                                            .font(.system(size: 12, weight: .semibold))
                                    }
                                    .foregroundStyle(UH.Palette.accentInk)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(UH.Palette.activeFill, in: Capsule())
                                    .overlay(Capsule().stroke(UH.Palette.accentInk.opacity(0.3), lineWidth: 1))
                                }
                                .buttonStyle(.plain)
                                .accessibilityIdentifier("plan.adaptWeek")
                            }
                            .padding(.horizontal, UH.Space.regular)
                        }

                        // 4. Week switcher with List / Calendar toggle
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek, viewMode: $viewMode)
                            .padding(.horizontal, UH.Space.regular)

                        // 5. Day list, Month Calendar grid, or Ungenerated Week CTA
                        if model.isWeekUngenerated(model.selectedWeek) {
                            ungeneratedWeekCTA(model.selectedWeek)
                                .padding(.horizontal, UH.Space.regular)
                        } else if viewMode == .calendar {
                            PlanCalendarGridView(model: model) { date, week in
                                withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                                    model.selectedWeek = week
                                    viewMode = .list
                                }
                            }
                            .padding(.horizontal, UH.Space.regular)
                        } else {
                            LazyVStack(spacing: UH.Space.compact) {
                                ForEach(model.days) { day in
                                    DayRow(day: day, onToggleDone: { workout in
                                        Task { await model.setDone(workout, !workout.isDone) }
                                    }, onMoveOrSwap: { day in
                                        moveSwapDay = day
                                    }, onSelect: { selectedWorkout = $0 })
                                        .id(day.id)
                                }
                            }
                            .padding(.horizontal, UH.Space.regular)
                        }

                        // 6. Coach's pick this week (contextual knowledge card)
                        if let card = model.contextKnowledgeCard {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("COACH'S PICK THIS WEEK")
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .tracking(0.5)
                                    .foregroundStyle(UH.Palette.muted)
                                    .padding(.horizontal, 2)

                                KnowledgeCardView(card: card)
                            }
                            .padding(.horizontal, UH.Space.regular)
                            .padding(.top, 4)
                        }

                        // 7. Next week card
                        nextWeekCard
                    }
                    .padding(.vertical, UH.Space.regular)
                }
                .refreshable { await model.load() }
                .onChange(of: model.selectedWeek) { Task { await model.refreshNextWeekOffer(); await model.loadKnowledgeCard() } }
                .onChange(of: generation.lastOutcome) { _, outcome in
                    guard let outcome, outcome.kind == .nextWeek || outcome.kind == .adaptWeek else { return }
                    generation.clearOutcome()
                    if case .done = outcome.outcome {
                        readyBanner = outcome.kind == .adaptWeek ? L("Week updated") : L("New week is ready")
                        Task { try? await Task.sleep(for: .seconds(3)); readyBanner = nil }
                    }
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
                    guard model.selectedWeek == model.currentWeek else { return }
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
                        Image(systemName: "sparkles")
                            .foregroundStyle(UH.Palette.accentInk)
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
                        Image(systemName: "lock.fill")
                            .foregroundStyle(UH.Palette.secondary)
                        Text("Complete the current block to unlock")
                            .font(UH.TextStyle.sectionTitle)
                    }
                    if let pct = offer.previousCompletionPct {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Block progress")
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
            HStack(spacing: UH.Space.small) {
                ProgressView()
                Text("Building your plan… \(elapsed / 60):\(String(format: "%02d", elapsed % 60))")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.ink)
                Spacer(minLength: 0)
                Button("View", action: onViewProgress).font(UH.TextStyle.disclosure).frame(minWidth: 44, minHeight: 44)
            }
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
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundStyle(UH.Palette.accentInk)
            }
            .padding(.top, 8)

            VStack(spacing: 4) {
                Text("Week \(week) is ready to generate")
                    .font(.system(size: 18, weight: .bold))
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
                    Image(systemName: "sparkles")
                    Text("Generate Week \(week)")
                }
                .font(.system(size: 14, weight: .bold))
                .frame(maxWidth: .infinity)
                .frame(height: 44)
                .foregroundStyle(Color.white)
                .background(UH.Palette.accentInk, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
            .buttonStyle(.plain)
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

    private var raceGoalHeader: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let plan = model.snapshot?.plan {
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(plan.raceName)
                            .font(.system(size: 19, weight: .bold))
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(1)

                        HStack(spacing: 6) {
                            if let date = PlanCalendar.day(from: plan.raceDate) {
                                Text(date, format: .dateTime.month(.abbreviated).day().year())
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            if let days = model.daysToRace {
                                Text("· \(days / 7) weeks to go")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.accentInk)
                            }
                        }
                    }

                    Spacer()

                    if let pill = model.goalPillText {
                        Button { showGoal = true } label: {
                            Text(pill)
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(model.goal?.status.kind == .behind ? UH.Palette.danger : UH.Palette.accentInk)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(UH.Palette.hover, in: Capsule())
                                .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 1))
                        }
                        .accessibilityIdentifier("plan.goalpill")
                    }
                }
            }
        }
        .padding(.horizontal, UH.Space.regular)
    }

    private func comingSoonBadge(_ text: String) -> some View {
        HStack(spacing: 4) {
            Text(text)
                .font(.system(size: 10.5, weight: .medium))
                .foregroundStyle(UH.Palette.muted)
            Text("Soon")
                .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
                .padding(.horizontal, 4)
                .padding(.vertical, 1)
                .background(UH.Palette.line.opacity(0.6), in: Capsule())
        }
        .padding(.horizontal, 7)
        .padding(.vertical, 3.5)
        .background(UH.Palette.surface, in: Capsule())
        .overlay(Capsule().stroke(UH.Palette.line, lineWidth: 0.8))
        .opacity(0.85)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(text) Coming soon")
    }

}

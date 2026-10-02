import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel
    let generation: GenerationCenter
    let onBuildPlan: () -> Void
    let onViewProgress: () -> Void
    var user: User? = nil
    var onSharpen: (TrainingDestination) -> Void = { _ in }
    @State private var viewMode: PlanViewMode = .list
    @State private var selectedWorkout: Workout?
    @State private var showManage = false
    @State private var startNewAfterManage = false
    @State private var scheduleAfterManage = false
    @State private var showSchedule = false
    @State private var showNextWeek = false
    @State private var showAdapt = false
    @State private var showReview = false
    @State private var showGoal = false
    @State private var readyBanner: String?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        NavigationStack {
            content
                .background(UH.Palette.surface.ignoresSafeArea())
                .navigationTitle(model.snapshot?.plan.raceName ?? "Plan")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Manage") { showManage = true }
                            .disabled(model.snapshot == nil)
                    }
                }
                .sheet(item: $selectedWorkout) { workout in
                    WorkoutDetailSheet(model: model, workoutID: workout.id)
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
                }) {
                    ManagePlanSheet(model: model, onStartNew: { startNewAfterManage = true },
                                    onSchedule: { scheduleAfterManage = true })
                }
        }
        .task { if model.state == .loading { await model.load() } }
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
                message(title: "Couldn't load your plan", body: error)
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

                        // 1. Race and goal header
                        raceGoalHeader

                        // 2. Summary carousel
                        SummaryCarousel(model: model,
                                        adapting: generation.running?.kind == .adaptWeek ? model.selectedWeek : nil,
                                        onReview: { showReview = true }, onAdapt: { showAdapt = true },
                                        onGoal: { showGoal = true })

                        // 3. Coach review card
                        CoachReviewCard(model: model, onOpenReview: { showReview = true })
                            .padding(.horizontal, UH.Space.regular)

                        // 4. Week switcher with List / Calendar toggle
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek, viewMode: $viewMode)
                            .padding(.horizontal, UH.Space.regular)

                        // 5. Day list or Month Calendar grid
                        if viewMode == .calendar {
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
                                    }, onSelect: { selectedWorkout = $0 })
                                        .id(day.id)
                                }
                            }
                            .padding(.horizontal, UH.Space.regular)
                        }

                        // 6. Next week card
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
                        readyBanner = outcome.kind == .adaptWeek ? "Week updated" : "New week is ready"
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
                Text("Building the next week…").font(UH.TextStyle.label)
            }
            .frame(maxWidth: .infinity, alignment: .leading).uhCard().padding(.horizontal, UH.Space.regular)
        } else if let offer = model.nextWeekOffer {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text(offer.title).font(UH.TextStyle.sectionTitle)
                Text("Coach Uphill uses how this week went to shape the next one.").foregroundStyle(UH.Palette.secondary)
                if let pct = offer.previousCompletionPct {
                    Text("This week: \(Int(pct)) % done").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
                Button(offer.title) { showNextWeek = true }.buttonStyle(.uhPrimary).accessibilityIdentifier("plan.nextweek")
            }
            .frame(maxWidth: .infinity, alignment: .leading).uhCard().padding(.horizontal, UH.Space.regular)
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

                // Disabled Coming Soon rows until Phase 5
                HStack(spacing: 8) {
                    comingSoonBadge("Plan your pace →")
                    comingSoonBadge("Refine in Goal Determiner →")
                }
                .padding(.top, 2)
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

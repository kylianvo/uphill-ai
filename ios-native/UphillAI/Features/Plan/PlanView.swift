import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel
    let generation: GenerationCenter
    let onBuildPlan: () -> Void
    let onViewProgress: () -> Void
    @State private var selectedWorkout: Workout?
    @State private var showManage = false
    @State private var startNewAfterManage = false
    @State private var showNextWeek = false
    @State private var showAdapt = false
    @State private var showReview = false
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
                .sheet(isPresented: $showAdapt) { AdaptWeekSheet(model: model, week: model.selectedWeek) }
                .sheet(isPresented: $showReview) { WeekReviewSheet(model: model, week: model.selectedWeek) }
                .sheet(isPresented: $showNextWeek) {
                    if let offer = model.nextWeekOffer { NextWeekSheet(model: model, offer: offer) }
                }
                .sheet(isPresented: $showManage, onDismiss: {
                    if startNewAfterManage { startNewAfterManage = false; onBuildPlan() }
                }) { ManagePlanSheet(model: model) { startNewAfterManage = true } }
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
                    Text("No plan yet").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                    Text("Your weekly workouts show up here once Coach Uphill builds your plan.")
                        .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
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
                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        if generation.running?.kind == .newPlan { buildingBanner }
                        if let cachedAt = model.cachedAt { offlineBanner(cachedAt) }
                        SummaryCarousel(model: model,
                                        adapting: generation.running?.kind == .adaptWeek ? model.selectedWeek : nil,
                                        onReview: { showReview = true }, onAdapt: { showAdapt = true })
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek)
                            .padding(.horizontal, UH.Space.regular)
                        LazyVStack(spacing: UH.Space.compact) {
                            ForEach(model.days) { day in
                                DayRow(day: day) { selectedWorkout = $0 }
                                    .id(day.id)
                            }
                        }
                        .padding(.horizontal, UH.Space.regular)
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
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

import SwiftUI

struct PlanView: View {
    @Bindable var model: PlanViewModel
    @State private var selectedWorkout: Workout?   // Task 9's detail sheet reads this
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        NavigationStack {
            content
                .background(UH.Palette.surface.ignoresSafeArea())
                .navigationTitle(model.snapshot?.plan.raceName ?? "Plan")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Manage") {}
                            .disabled(true)   // Task 9
                    }
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
            message(title: "No active plan yet",
                    body: "Create your first plan on uphill-ai.io.vn for now. Plan creation is coming to the app soon.")
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
                        if let cachedAt = model.cachedAt { offlineBanner(cachedAt) }
                        SummaryCarousel(model: model)
                        WeekSwitcher(weeks: model.weeks, selected: $model.selectedWeek, currentWeek: model.currentWeek)
                            .padding(.horizontal, UH.Space.regular)
                        LazyVStack(spacing: UH.Space.compact) {
                            ForEach(model.days) { day in
                                DayRow(day: day) { selectedWorkout = $0 }
                                    .id(day.id)
                            }
                        }
                        .padding(.horizontal, UH.Space.regular)
                    }
                    .padding(.vertical, UH.Space.regular)
                }
                .refreshable { await model.load() }
                .onAppear { scrollToToday(proxy) }
                .onChange(of: model.selectedWeek) { _, week in
                    if week == model.currentWeek { scrollToToday(proxy) }
                }
            }
        }
    }

    private func scrollToToday(_ proxy: ScrollViewProxy) {
        guard let today = model.days.first(where: { $0.eyebrow == "TODAY" }) else { return }
        if reduceMotion {
            proxy.scrollTo(today.id, anchor: .top)
        } else {
            withAnimation(UH.Motion.standard) { proxy.scrollTo(today.id, anchor: .top) }
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

import SwiftUI

/// The Progress tab: Training and Health cards. Renders exactly the cards the backend returns, so a
/// card without enough data never appears -- there is no placeholder chart anywhere in this file.
struct ProgressTabView: View {
    @Bindable var model: ProgressViewModel
    let goalPath: GoalPath?
    let deviceService: any DeviceConnectionServicing
    let onBuildPlan: () -> Void

    @State private var showConnect = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    Picker(L("Section"), selection: Binding(get: { model.section }, set: { s in Task { await model.select(s) } })) {
                        Text(L("Training")).tag(ProgressSection.training)
                        Text(L("Health")).tag(ProgressSection.health)
                    }
                    .pickerStyle(.segmented)
                    content
                }
                .padding(UH.Space.regular)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle(L("Progress"))
            .refreshable { await model.load() }
            .task { if model.response == nil { await model.load() } }
            .sheet(isPresented: $showConnect) {
                NavigationStack { ConnectedAccountsView(service: deviceService) }
            }
        }
    }

    @ViewBuilder private var content: some View {
        switch model.state {
        case .loading:
            SwiftUI.ProgressView().frame(maxWidth: .infinity).padding(.top, UH.Space.reading)
        case .failed:
            message(L("Couldn't load your progress. Pull to try again."), action: nil)
        case .empty, .loaded:
            if let response = model.response { sections(response) }
        }
    }

    @ViewBuilder private func sections(_ response: ProgressResponse) -> some View {
        let isTraining = model.section == .training
        if isTraining && !response.hasPlan {
            message(L("Build a plan to track consistency, volume and your goal."), action: (L("Build a plan"), onBuildPlan))
        }
        if !isTraining && !response.connected && response.cards.isEmpty {
            message(L("Connect COROS or Apple Health to see sleep, HRV and resting heart rate."),
                    action: (L("Connect a device"), { showConnect = true }))
        } else if response.cards.isEmpty && (isTraining ? response.hasPlan : true) {
            message(L("Your trends appear here as data comes in."), action: nil)
        }
        ForEach(response.cards) { card in
            if card.key == "goal" {
                if let goalPath {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Label(ProgressText.title("goal"), systemImage: ProgressText.symbol("goal"))
                            .font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                        GoalPathRow(path: goalPath)
                    }
                    .uhCard()
                }
            } else if card.key == "coach_read" {
                ProgressCardView(card: card)
            } else {
                NavigationLink { ProgressDetailView(card: card, model: model) } label: { ProgressCardView(card: card) }
                    .buttonStyle(.plain)
            }
        }
        if let next = response.pending.first(where: { !ProgressText.pending($0).isEmpty }) {
            Text(ProgressText.pending(next))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.muted)
                .frame(maxWidth: .infinity, alignment: .center)
        }
    }

    private func message(_ text: String, action: (String, () -> Void)?) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text(text).foregroundStyle(UH.Palette.ink)
            if let action {
                Button(action.0, action: action.1).buttonStyle(.borderedProminent).tint(UH.Palette.accentInk)
            }
        }
        .uhCard()
    }
}

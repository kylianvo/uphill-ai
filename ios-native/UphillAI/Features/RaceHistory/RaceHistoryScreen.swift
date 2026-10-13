import SwiftUI

struct RaceHistoryScreen: View {
    let service: any RaceHistoryServicing
    var onSelectBadge: ((DistanceBadge) -> Void)? = nil
    var onHistoryChanged: ((RaceHistoryResponse) -> Void)? = nil
    @State private var model: RaceHistoryViewModel
    @State private var showAddRace = false
    @State private var showLinkProfile = false
    @State private var detailResult: RaceResult?
    @State private var editingResult: RaceResult?
    @State private var deletingResult: RaceResult?
    @State private var unlinkingClaim: RaceClaim?

    init(service: any RaceHistoryServicing, onSelectBadge: ((DistanceBadge) -> Void)? = nil,
         initialHistory: RaceHistoryResponse? = nil, onHistoryChanged: ((RaceHistoryResponse) -> Void)? = nil) {
        self.service = service; self.onSelectBadge = onSelectBadge; self.onHistoryChanged = onHistoryChanged
        _model = State(initialValue: RaceHistoryViewModel(service: service, history: initialHistory))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                if let error = model.errorMessage {
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text(error).font(UH.TextStyle.body).foregroundStyle(UH.Palette.danger)
                        Button("Retry") { Task { await model.load() } }
                    }.accessibilityIdentifier("race.history.error")
                }
                if let history = model.history {
                    HStack(alignment: .top, spacing: UH.Space.small) {
                        stat("Trail finishes", value: String(history.summary.trailFinishes))
                        stat("Ultras", value: String(history.summary.ultras))
                        stat("Longest trail", value: history.summary.longestFinish?.formattedDistance ?? "—")
                    }
                    .padding(UH.Space.regular)
                    .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                    RoadPersonalBestsView(summary: history.summary) { id in detailResult = history.results.first { $0.id == id } }
                    DistanceBadgeGrid(badges: DistanceBadge.deriveBadges(from: history.results), onSelectBadge: { badge in detailResult = history.results.first { $0.id == badge.resultId } })
                    if !history.claims.isEmpty {
                        VStack(alignment: .leading, spacing: UH.Space.small) {
                            Text("Linked athlete profiles").font(UH.TextStyle.sectionTitle)
                            ForEach(history.claims) { claimCard($0) }
                        }
                    }
                    let pending = history.results.filter { $0.source == "vbm" && !$0.selected }
                    if !pending.isEmpty {
                        VStack(alignment: .leading, spacing: UH.Space.small) {
                            Text("Confirm your VBM results").font(UH.TextStyle.sectionTitle)
                            Text("Choose the races you ran. Confirmed results count toward your personal bests.")
                                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            ForEach(pending) { result in
                                VStack(alignment: .leading, spacing: UH.Space.small) {
                                    NavigationLink { detailScreen(result) } label: { resultSummary(result) }.buttonStyle(.plain)
                                    Button("This is my result") { Task { await model.confirm(id: result.id, selected: true) } }
                                        .buttonStyle(PrimaryButtonStyle())
                                        .disabled(model.isMutating).accessibilityIdentifier("race.confirm.\(result.id)")
                                }.trainingCard()
                            }
                        }
                    }
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        let selected = history.results.filter { $0.selected }
                        Text("Your races (\(selected.count))").font(UH.TextStyle.sectionTitle)
                        if selected.isEmpty {
                            Text("Add a result or confirm an imported race to start your history.")
                                .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary).padding(.vertical, UH.Space.regular)
                        }
                        ForEach(selected) { result in
                            NavigationLink { detailScreen(result) } label: { resultSummary(result).trainingCard() }.buttonStyle(.plain).contextMenu {
                                if result.source == "manual" {
                                    Button("Edit result", systemImage: "pencil") { editingResult = result }
                                    Button("Delete result", systemImage: "trash", role: .destructive) { deletingResult = result }
                                } else if result.source == "vbm" {
                                    Button("Not my result", systemImage: "person.crop.circle.badge.xmark") {
                                        Task { await model.confirm(id: result.id, selected: false) }
                                    }.disabled(model.isMutating)
                                }
                            }
                        }
                    }
                } else if model.isLoading { ProgressView("Loading race history…").frame(maxWidth: .infinity).padding(.top, UH.Space.section) }
            }.padding(UH.Space.regular)
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Race History").navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                HStack {
                    Button("Link profile", systemImage: "link") { showLinkProfile = true }
                    Button("Add result", systemImage: "plus") { showAddRace = true }
                }
            }
        }
        .navigationDestination(isPresented: Binding(get: { detailResult != nil }, set: { if !$0 { detailResult = nil } })) {
            if let detailResult { detailScreen(detailResult) }
        }
        .sheet(isPresented: $showAddRace) { AddRaceSheet(service: service) { _ in Task { await model.reloadAfterSave() } } }
        .sheet(item: $editingResult) { result in AddRaceSheet(service: service, editingResult: result) { _ in Task { await model.reloadAfterSave() } } }
        .sheet(isPresented: $showLinkProfile) { LinkProfileSheet(service: service) { Task { await model.load() } } }
        .confirmationDialog("Delete this manual result?", isPresented: Binding(get: { deletingResult != nil }, set: { if !$0 { deletingResult = nil } }), titleVisibility: .visible, presenting: deletingResult) { result in
            Button("Delete result", role: .destructive) {
                Task { await model.deleteManual(id: result.id); deletingResult = nil }
            }
        }
        .confirmationDialog("Unlink this athlete profile?", isPresented: Binding(get: { unlinkingClaim != nil }, set: { if !$0 { unlinkingClaim = nil } }), titleVisibility: .visible, presenting: unlinkingClaim) { claim in
            Button("Unlink profile", role: .destructive) {
                Task { await model.perform { try await service.deleteClaim(id: claim.id) }; unlinkingClaim = nil }
            }
        }
        .task { await model.load() }
        .task(id: model.history?.claims.filter { $0.syncStatus == "pending" }.map(\.id)) {
            while !Task.isCancelled, model.history?.claims.contains(where: { $0.syncStatus == "pending" }) == true {
                do { try await Task.sleep(for: .seconds(5)) } catch { return }
                await model.load()
            }
        }
        .onChange(of: model.history) { _, history in if let history { onHistoryChanged?(history) } }
    }

    private func detailScreen(_ result: RaceResult) -> some View {
        RaceDetailScreen(result: result, service: service) { Task { await model.load() } }
    }

    private func stat(_ title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            Text(value).font(UH.TextStyle.metric).foregroundStyle(UH.Palette.ink)
        }.frame(maxWidth: .infinity, alignment: .leading)
    }

    private func resultSummary(_ result: RaceResult) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            HStack(alignment: .top) {
                Text(result.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink).fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 8)
                Text(result.formattedDuration).font(UH.TextStyle.label.monospacedDigit()).foregroundStyle(UH.Palette.ink)
            }
            Text("\(result.raceDate) · \(result.formattedDistance) · \(result.discipline.capitalized) · \(result.source.uppercased())")
                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            if let rank = result.rankOverall { Text("Overall rank #\(rank)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.accentInk) }
        }.accessibilityIdentifier("race.result.\(result.id)")
    }

    private func claimCard(_ claim: RaceClaim) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(claim.displayName).font(UH.TextStyle.label)
                    Text("\(claim.source.uppercased()) · \(claim.syncStatus == "ok" ? "Synced" : claim.syncStatus.capitalized)")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
                Spacer()
                Button("Refresh profile", systemImage: "arrow.clockwise") {
                    Task { await model.perform { try await service.refreshClaim(id: claim.id) } }
                }.labelStyle(.iconOnly).disabled(model.isMutating || claim.syncStatus == "pending")
            }
            if let error = claim.syncError { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
            if claim.verified { Label("Evidence matched", systemImage: "checkmark.seal").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.accentInk) }
            Button("Unlink", role: .destructive) { unlinkingClaim = claim }.disabled(model.isMutating)
        }.trainingCard()
    }
}

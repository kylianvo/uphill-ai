import SwiftUI

struct RaceHistoryScreen: View {
    let service: any RaceHistoryServicing
    var onSelectBadge: ((DistanceBadge) -> Void)? = nil
    var onLoaded: ((RaceHistoryResponse) -> Void)? = nil

    @State private var history: RaceHistoryResponse?
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    @State private var filter: String = "all" // all, trail, road
    @State private var showAddRace: Bool = false
    @State private var showLinkProfile: Bool = false
    @State private var activeBibClaimId: Int? = nil
    @State private var bibInput: String = ""

    private static let displayDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .none
        return f
    }()

    private static let isoDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    init(
        service: any RaceHistoryServicing,
        onSelectBadge: ((DistanceBadge) -> Void)? = nil,
        initialHistory: RaceHistoryResponse? = nil,
        onLoaded: ((RaceHistoryResponse) -> Void)? = nil
    ) {
        self.service = service
        self.onSelectBadge = onSelectBadge
        self.onLoaded = onLoaded
        _history = State(initialValue: initialHistory)
    }

    var body: some View {
        Group {
            if let history {
                contentView(history)
            } else if isLoading {
                VStack(spacing: 12) {
                    ProgressView()
                    Text("Loading race history…")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 12) {
                    if let err = errorMessage {
                        Text(err)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.danger)
                    }
                    Button("Retry") {
                        Task { await load() }
                    }
                    .font(UH.TextStyle.label)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Race History")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                HStack(spacing: 14) {
                    Button {
                        showLinkProfile = true
                    } label: {
                        Image(systemName: "link")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(UH.Palette.ink)
                    }

                    Button {
                        showAddRace = true
                    } label: {
                        Image(systemName: "plus")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundStyle(UH.Palette.ink)
                    }
                }
            }
        }
        .sheet(isPresented: $showAddRace) {
            AddRaceSheet(service: service) { _ in
                Task { await load() }
            }
        }
        .sheet(isPresented: $showLinkProfile) {
            LinkProfileSheet(service: service) {
                Task { await load() }
            }
        }
        .task {
            await load()
        }
    }

    private func contentView(_ history: RaceHistoryResponse) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                // Section 1: Top stats summary
                VStack(spacing: 8) {
                    HStack(spacing: 8) {
                        statTile(title: L("TRAIL FINISHES"), value: "\(history.summary.trailFinishes)")
                        statTile(title: L("ULTRAS COMPLETED"), value: "\(history.summary.ultras)")
                        let longest = history.summary.longestFinish.map { "\($0.formattedDistance)" } ?? "—"
                        statTile(title: L("LONGEST TRAIL"), value: longest)
                    }

                    // PR / UTMB sub-row
                    if history.summary.roadHmPr != nil || history.summary.roadFmPr != nil {
                        HStack(spacing: 8) {
                            if let hm = history.summary.roadHmPr {
                                prChip(title: "HM PR", timeSec: hm.timeSec, stale: hm.stale)
                            }
                            if let fm = history.summary.roadFmPr {
                                prChip(title: "FM PR", timeSec: fm.timeSec, stale: fm.stale)
                            }
                        }
                    }
                }

                // Section 2: Distance Badges
                let badges = DistanceBadge.deriveBadges(from: history.results)
                DistanceBadgeGrid(badges: badges) { badge in
                    onSelectBadge?(badge)
                }

                // Section 3: Linked Profiles (UTMB / VBM)
                if !history.claims.isEmpty {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Text("LINKED ATHLETE PROFILES")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)

                        ForEach(history.claims) { claim in
                            claimCard(claim)
                        }
                    }
                }

                // Section 4: Results List
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack {
                        Text("YOUR RACES (\(filteredResults(history.results).count))")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                        Spacer()
                    }

                    // Filter picker
                    Picker("Filter", selection: $filter) {
                        Text("All").tag("all")
                        Text("Trail").tag("trail")
                        Text("Road").tag("road")
                    }
                    .pickerStyle(.segmented)
                    .padding(.bottom, 4)

                    let results = filteredResults(history.results)
                    if results.isEmpty {
                        VStack(spacing: 8) {
                            Image(systemName: "flag.slash")
                                .font(.system(size: 28))
                                .foregroundStyle(UH.Palette.muted)
                            Text("No races logged yet")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Text("Tap + to add a race or link your UTMB/VBM profile.")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, UH.Space.section)
                    } else {
                        ForEach(results) { result in
                            raceResultCard(result)
                        }
                    }
                }
            }
            .padding(UH.Space.regular)
        }
    }

    private func statTile(title: String, value: String) -> some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(UH.TextStyle.metric)
                .foregroundStyle(UH.Palette.ink)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .trainingCard(padding: 4, radius: UH.Radius.control)
    }

    private func prChip(title: String, timeSec: Int, stale: Bool) -> some View {
        HStack(spacing: 4) {
            Image(systemName: "trophy.fill")
                .font(.system(size: 10))
                .foregroundStyle(Color(hex: "#f59e0b"))
            Text("\(title): \(DistanceBadge.formatTime(timeSec))")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
            if stale {
                Text("(>2y)")
                    .font(.system(size: 9.5))
                    .foregroundStyle(UH.Palette.muted)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(UH.Palette.card, in: Capsule())
        .overlay(Capsule().stroke(UH.Palette.line))
    }

    private func claimCard(_ claim: RaceClaim) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(claim.source.uppercased())
                    .font(.system(size: 10, weight: .heavy, design: .monospaced))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: 4))
                    .foregroundStyle(Color.white)

                Text(claim.displayName)
                    .font(UH.TextStyle.body.weight(.semibold))
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                if claim.verified {
                    HStack(spacing: 2) {
                        Image(systemName: "checkmark.seal.fill")
                        Text("Verified")
                    }
                    .font(.system(size: 10.5, weight: .bold))
                    .foregroundStyle(UH.Palette.accentInk)
                }

                Button {
                    Task {
                        try? await service.refreshClaim(id: claim.id)
                        await load()
                    }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 13))
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            HStack {
                Text(claim.syncStatus == "ok" ? L("Synced") : L(claim.syncStatus.capitalized))
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(claim.syncStatus == "ok" ? UH.Palette.accentInk : UH.Palette.muted)

                Spacer()

                Button("Unlink", role: .destructive) {
                    Task {
                        try? await service.deleteClaim(id: claim.id)
                        await load()
                    }
                }
                .font(UH.TextStyle.caption)
            }
        }
        .trainingCard()
    }

    private func raceResultCard(_ result: RaceResult) -> some View {
        HStack(alignment: .top, spacing: 12) {
            // Discipline / Date icon box
            VStack(spacing: 2) {
                Image(systemName: result.discipline == "trail" ? "mountain.2.fill" : "figure.run")
                    .font(.system(size: 16))
                    .foregroundStyle(UH.Palette.ink)
                Text(formattedDate(result.raceDate))
                    .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.secondary)
                    .multilineTextAlignment(.center)
            }
            .frame(width: 52)
            .padding(.vertical, 6)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))

            VStack(alignment: .leading, spacing: 3) {
                HStack {
                    Text(result.raceName)
                        .font(UH.TextStyle.body.weight(.semibold))
                        .foregroundStyle(UH.Palette.ink)
                        .lineLimit(1)
                    Spacer()
                    Text(result.formattedDuration)
                        .font(.system(size: 14, weight: .bold, design: .monospaced))
                        .foregroundStyle(result.isDnf ? UH.Palette.danger : UH.Palette.ink)
                }

                HStack(spacing: 8) {
                    Text(result.formattedDistance)
                        .font(.system(size: 11, weight: .medium, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)

                    if let gain = result.elevationGainM, gain > 0 {
                        Text("+\(Int(gain))m D+")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    if let rank = result.rankOverall {
                        Text("Rank #\(rank)")
                            .font(.system(size: 10.5, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                    }

                    Spacer()

                    if result.verified {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 12))
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }
        }
        .trainingCard()
        .contextMenu {
            Button(role: .destructive) {
                Task {
                    try? await service.deleteResult(id: result.id)
                    await load()
                }
            } label: {
                Label("Delete Result", systemImage: "trash")
            }
        }
    }

    private func filteredResults(_ results: [RaceResult]) -> [RaceResult] {
        results.filter { result in
            if filter == "all" { return true }
            return result.discipline.lowercased() == filter
        }
    }

    private func formattedDate(_ str: String) -> String {
        guard let d = Self.isoDateFormatter.date(from: str) else { return str }
        return Self.displayDateFormatter.string(from: d)
    }

    private func load() async {
        isLoading = history == nil
        errorMessage = nil
        do {
            let fresh = try await service.history()
            history = fresh
            onLoaded?(fresh)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

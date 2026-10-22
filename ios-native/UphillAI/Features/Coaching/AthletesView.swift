import SwiftUI

/// The coach's Athletes tab: filters and this week's numbers on top, highlights, then an inbox
/// sorted by urgency (act now, review & build, check in) and every on-track runner below.
/// Spec: docs/superpowers/specs/2026-10-23-athletes-tab-coach-workbench-design.md
struct AthletesView: View {
    let app: AppModel
    var onSelectTab: ((Int) -> Void)? = nil

    @State private var overview: CoachOverview?
    @State private var roster: [CoachedAthleteRow] = []
    @State private var filter = RosterFilter()
    @State private var weekOffset = 0
    @State private var groupKey: GroupKey = .race
    @State private var search = ""
    @State private var onTrackSort: OnTrackSort = .name
    @State private var isLoading = false
    @State private var loadError: String?
    @State private var showInvite = false
    @State private var noteFor: CoachOverviewAthlete?
    @State private var removeCandidate: CoachedAthleteRow?

    enum OnTrackSort: Hashable { case name, raceDate, done }

    init(app: AppModel, onSelectTab: ((Int) -> Void)? = nil, initialOverview: CoachOverview? = nil,
         initialRoster: [CoachedAthleteRow]? = nil, initialFilter: RosterFilter = RosterFilter()) {
        self.app = app
        self.onSelectTab = onSelectTab
        _overview = State(initialValue: initialOverview)
        _roster = State(initialValue: initialRoster ?? [])
        _filter = State(initialValue: initialFilter)
    }

    private var triage: RosterTriage {
        let all = overview?.athletes ?? []
        let q = search.trimmingCharacters(in: .whitespaces)
        return RosterTriage(athletes: q.isEmpty ? all : all.filter { $0.name.localizedCaseInsensitiveContains(q) },
                            filter: filter, weekOffset: weekOffset)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: UH.Space.regular) {
                    if let loadError { errorCard(loadError) }
                    if let overview {
                        content(overview)
                    } else if isLoading {
                        ProgressView().frame(maxWidth: .infinity).padding(.vertical, UH.Space.reading)
                    }
                }
                .padding(.horizontal, UH.Space.regular)
                .padding(.bottom, UH.Space.reading)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Athletes")
            .searchable(text: $search, prompt: Text("Search runners"))
            .refreshable { await load(force: true) }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showInvite = true } label: { Image(systemName: "plus") }
                        .accessibilityLabel("Invite runner")
                        .accessibilityIdentifier("athletes.invite")
                }
            }
            .sheet(isPresented: $showInvite) {
                InviteAthleteSheet(service: app.coachingService) { row in roster.insert(row, at: 0) }
            }
            .sheet(item: $noteFor) { athlete in
                CoachNoteSheet(athleteName: athlete.name) { text in
                    _ = try await app.coachingService.addNote(
                        athleteId: athlete.athleteId, payload: CoachNoteCreatePayload(targetType: "general", note: text))
                }
            }
            .confirmationDialog("Remove from your roster?", isPresented: Binding(
                get: { removeCandidate != nil }, set: { if !$0 { removeCandidate = nil } }
            ), presenting: removeCandidate) { row in
                Button(L("Remove %@", row.displayName), role: .destructive) { Task { await remove(row) } }
                Button("Cancel", role: .cancel) {}
            } message: { row in
                Text(L("%@ will stop sharing their plan and data with you.", row.displayName))
            }
            .task { await load(force: false) }
        }
    }

    // MARK: - Content

    @ViewBuilder
    private func content(_ overview: CoachOverview) -> some View {
        let t = triage
        filterBar(t)
        if overview.athletes.isEmpty {
            emptyRoster
        } else if t.visible.isEmpty {
            Text("No runners match these filters.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, UH.Space.section)
        } else {
            RosterOverviewCard(triage: t, weekOffset: $weekOffset, groupKey: $groupKey)
            if !t.highlights.isEmpty { highlights(t) }
            let openSections = [TriageSection.actNow, .reviewBuild, .checkIn].filter { !t.athletes(in: $0).isEmpty }
            if openSections.isEmpty {
                Label("Nothing needs you today", systemImage: "checkmark.circle")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.accentInk)
            }
            ForEach(openSections, id: \.self) { section in
                sectionHeader(section, count: t.athletes(in: section).count)
                ForEach(t.athletes(in: section)) { athlete in
                    AthleteTriageRow(athlete: athlete, onOpen: { open(athlete, action: nil) },
                                     onAction: { act($0, on: athlete) }, menu: AnyView(moreMenu(athlete)))
                }
            }
            onTrack(t)
        }
        invited
    }

    private func filterBar(_ t: RosterTriage) -> some View {
        let races = Set((overview?.athletes ?? []).compactMap { $0.activePlan?.raceName }).sorted()
        let phases = Set((overview?.athletes ?? []).compactMap(\.phase)).sorted()
        let counts = t.counts
        return ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                chip(L("All %lld", counts.all), on: filter.planType == nil) { filter.planType = nil }
                chip(L("Review %lld", counts.review), on: filter.planType == "review") { filter.planType = "review" }
                chip(L("Coached %lld", counts.coached), on: filter.planType == "coached") { filter.planType = "coached" }
                menuChip(L("Race"), value: filter.race, options: races) { filter.race = $0 }
                menuChip(L("Level"), value: filter.level, options: ["beginner", "intermediate", "advanced", "elite"]) {
                    filter.level = $0
                }
                menuChip(L("Phase"), value: filter.phase, options: phases) { filter.phase = $0 }
            }
        }
        .contentMargins(.horizontal, UH.Space.regular, for: .scrollContent)
        .padding(.horizontal, -UH.Space.regular)
    }

    private func chip(_ title: String, on: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.footnote.weight(on ? .semibold : .regular))
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(on ? UH.Palette.ink : UH.Palette.tint, in: Capsule())
                .foregroundStyle(on ? UH.Palette.card : UH.Palette.ink)
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(on ? .isSelected : [])
    }

    private func menuChip(_ title: String, value: String?, options: [String], set: @escaping (String?) -> Void) -> some View {
        Menu {
            Button(L("Any")) { set(nil) }
            ForEach(options, id: \.self) { o in Button(o.count > 12 ? o : o.capitalized) { set(o) } }
        } label: {
            HStack(spacing: 4) {
                Text(value.map { $0.count > 12 ? $0 : $0.capitalized } ?? title).lineLimit(1)
                Image(systemName: "chevron.down").font(.caption2.weight(.semibold))
            }
            .font(.footnote.weight(value == nil ? .regular : .semibold))
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(value == nil ? UH.Palette.tint : UH.Palette.ink, in: Capsule())
            .foregroundStyle(value == nil ? UH.Palette.ink : UH.Palette.card)
        }
    }

    private func highlights(_ t: RosterTriage) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("HIGHLIGHTS").font(UH.TextStyle.eyebrow).tracking(0.6).foregroundStyle(UH.Palette.secondary)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(Array(t.highlights.enumerated()), id: \.offset) { _, item in
                        Button { open(item.athlete, action: nil) } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Image(systemName: highlightSymbol(item.signal.code))
                                    .foregroundStyle(UH.Palette.accentInk)
                                Text(item.athlete.name).font(.footnote.weight(.semibold)).foregroundStyle(UH.Palette.ink)
                                Text(CoachSignalText.sentence(item.signal))
                                    .font(.caption).foregroundStyle(UH.Palette.secondary)
                                    .lineLimit(2).multilineTextAlignment(.leading)
                            }
                            .frame(width: 156, alignment: .leading)
                            .padding(10)
                            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .contentMargins(.horizontal, UH.Space.regular, for: .scrollContent)
            .padding(.horizontal, -UH.Space.regular)
        }
    }

    private func highlightSymbol(_ code: String) -> String {
        switch code {
        case "race_soon": "flag.checkered"
        case "phase_start": "mountain.2"
        case "longest_long_run": "figure.run"
        case "new_result": "medal"
        default: "checkmark.seal"
        }
    }

    private func sectionHeader(_ section: TriageSection, count: Int) -> some View {
        HStack(spacing: 6) {
            Image(systemName: section.symbol).foregroundStyle(section.tint)
            Text(section.title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            Text("\(count)").font(.footnote.monospacedDigit()).foregroundStyle(UH.Palette.muted)
        }
        .padding(.top, 4)
        .accessibilityAddTraits(.isHeader)
    }

    @ViewBuilder
    private func onTrack(_ t: RosterTriage) -> some View {
        let rows = sorted(t.athletes(in: .onTrack))
        if !rows.isEmpty {
            HStack {
                sectionHeader(.onTrack, count: rows.count)
                Spacer()
                Menu {
                    Picker("Sort", selection: $onTrackSort) {
                        Text("Name").tag(OnTrackSort.name)
                        Text("Race date").tag(OnTrackSort.raceDate)
                        Text("Done %").tag(OnTrackSort.done)
                    }
                } label: {
                    Image(systemName: "arrow.up.arrow.down").font(.footnote)
                }
                .accessibilityLabel("Sort on-track runners")
            }
            VStack(spacing: 0) {
                ForEach(rows) { athlete in
                    OnTrackRow(athlete: athlete) { open(athlete, action: nil) }
                        .contextMenu { moreMenuItems(athlete) }
                    if athlete.id != rows.last?.id { Divider() }
                }
            }
            .padding(.horizontal, UH.Space.small)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
        }
    }

    private func sorted(_ rows: [CoachOverviewAthlete]) -> [CoachOverviewAthlete] {
        switch onTrackSort {
        case .name: rows.sorted { $0.name.localizedCompare($1.name) == .orderedAscending }
        case .raceDate: rows.sorted { ($0.raceDate ?? "9999") < ($1.raceDate ?? "9999") }
        case .done: rows.sorted { ($0.adherence14D ?? -1) > ($1.adherence14D ?? -1) }
        }
    }

    @ViewBuilder
    private var invited: some View {
        let pending = roster.filter { !$0.isActive }
        if !pending.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                Text(L("Invited (%lld)", pending.count)).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                ForEach(pending) { row in
                    HStack {
                        Text(row.displayName).font(.footnote).foregroundStyle(UH.Palette.secondary)
                        Spacer()
                        Button(role: .destructive) { removeCandidate = row } label: { Image(systemName: "xmark") }
                            .font(.footnote)
                            .buttonStyle(.borderless)
                            .accessibilityLabel(L("Cancel invite to %@", row.displayName))
                    }
                }
            }
            .padding(.top, UH.Space.small)
        }
    }

    private var emptyRoster: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("No runners yet").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            Text("Invite a runner who already has an Uphill AI account.")
                .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary)
            Button("Invite runner") { showInvite = true }.buttonStyle(.uhPrimary)
        }
        .trainingCard()
    }

    private func errorCard(_ message: String) -> some View {
        HStack {
            Text(message).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
            Spacer()
            Button("Retry") { Task { await load(force: true) } }.font(UH.TextStyle.label)
        }
        .trainingCard()
    }

    // MARK: - Menu

    private func moreMenu(_ athlete: CoachOverviewAthlete) -> some View {
        Menu { moreMenuItems(athlete) } label: {
            Image(systemName: "ellipsis")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(UH.Palette.muted)
                .frame(width: 28, height: 22)
                .contentShape(Rectangle())
        }
        .accessibilityLabel(L("More for %@", athlete.name))
    }

    @ViewBuilder
    private func moreMenuItems(_ athlete: CoachOverviewAthlete) -> some View {
        Button { open(athlete, action: nil) } label: { Label("Open plan", systemImage: "calendar") }
        Button { noteFor = athlete } label: { Label("Note", systemImage: "square.and.pencil") }
        if let row = rosterRow(athlete) {
            let coached = athlete.effectivePlanType == "coached"
            Button { Task { await setPlanType(row, coached ? "review" : "coached") } } label: {
                Label(coached ? "Switch to Review" : "Switch to Coached", systemImage: "arrow.triangle.swap")
            }
            Button(role: .destructive) { removeCandidate = row } label: { Label("Remove", systemImage: "person.badge.minus") }
        }
    }

    // MARK: - Actions

    private func rosterRow(_ a: CoachOverviewAthlete) -> CoachedAthleteRow? {
        roster.first { $0.athleteId == a.athleteId }
    }

    private func open(_ athlete: CoachOverviewAthlete, action: CoachAction?) {
        app.pendingCoachAction = action
        app.enterAthleteView(athlete: rosterRow(athlete) ?? CoachedAthleteRow(fromOverview: athlete))
        onSelectTab?(1)
    }

    private func act(_ action: CoachAction, on athlete: CoachOverviewAthlete) {
        if action == .note { noteFor = athlete } else { open(athlete, action: action) }
    }

    private func load(force: Bool) async {
        if overview == nil, let cached = app.coachDashboard {
            overview = cached.overview
            roster = cached.roster
        }
        if !force && overview != nil && !roster.isEmpty { return }
        isLoading = true
        defer { isLoading = false }
        do {
            async let ov = app.coachingService.fetchOverview(days: 14, athleteId: nil, level: nil)
            async let rst = app.coachingService.fetchRoster()
            let (o, r) = try await (ov, rst)
            overview = o
            roster = r
            app.coachDashboard = CoachDashboardData(overview: o, roster: r, invites: app.coachDashboard?.invites ?? [])
            loadError = nil
        } catch {
            loadError = error.localizedDescription
        }
    }

    private func setPlanType(_ row: CoachedAthleteRow, _ planType: String) async {
        do {
            _ = try await app.coachingService.setPlanType(linkId: row.id, planType: planType)
            await load(force: true)
        } catch {
            loadError = error.localizedDescription
        }
    }

    private func remove(_ row: CoachedAthleteRow) async {
        do {
            try await app.coachingService.removeFromRoster(linkId: row.id)
            roster.removeAll { $0.id == row.id }
            await load(force: true)
        } catch {
            loadError = error.localizedDescription
        }
    }
}

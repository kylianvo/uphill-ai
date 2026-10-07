import SwiftUI

struct CoachDashboardView: View {
    let app: AppModel
    var onSelectTab: ((Int) -> Void)? = nil

    @State private var activeSection: Section = .overview
    @State private var overview: CoachOverview? = nil
    @State private var roster: [CoachedAthleteRow] = []
    @State private var pendingInvites: [CoachingInvite] = []

    @State private var daysFilter: Int = 14
    @State private var levelFilter: String = "all"
    @State private var rosterSearch: String = ""
    @State private var inviteEmail: String = ""

    @State private var isLoading = false
    @State private var isInviting = false
    @State private var inviteError: String? = nil
    @State private var inviteSuccess: String? = nil
    @State private var removeCandidate: CoachedAthleteRow? = nil
    @State private var selectedAthleteForProfile: CoachedAthleteRow? = nil

    enum Section: String, CaseIterable, Identifiable {
        case overview = "Overview"
        case roster = "Roster"
        var id: String { rawValue }
    }

    private let levels = ["all", "beginner", "intermediate", "advanced", "elite"]
    private let dayOptions = [7, 14, 30]

    init(
        app: AppModel,
        onSelectTab: ((Int) -> Void)? = nil,
        initialSection: Section = .overview,
        initialOverview: CoachOverview? = nil,
        initialRoster: [CoachedAthleteRow]? = nil
    ) {
        self.app = app
        self.onSelectTab = onSelectTab
        _activeSection = State(initialValue: initialSection)
        if let initialOverview {
            _overview = State(initialValue: initialOverview)
        }
        if let initialRoster {
            _roster = State(initialValue: initialRoster)
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: UH.Space.medium) {
                    // Top Section Switcher
                    Picker("Section", selection: $activeSection) {
                        ForEach(Section.allCases) { sec in
                            Text(sec.rawValue).tag(sec)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal, UH.Space.regular)

                    switch activeSection {
                    case .overview:
                        overviewSection
                    case .roster:
                        rosterSection
                    }
                }
                .padding(.vertical, UH.Space.small)
            }
            .navigationTitle("Coach Hub")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await loadData() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 13, weight: .semibold))
                    }
                }
            }
            .sheet(item: $selectedAthleteForProfile) { athlete in
                NavigationStack {
                    CoachedAthleteProfileView(
                        athlete: athlete,
                        profile: app.coachedAthleteProfile,
                        service: app.coachingService
                    )
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Done") { selectedAthleteForProfile = nil }
                        }
                    }
                }
            }
            .confirmationDialog(
                "Remove Athlete from Roster?",
                isPresented: Binding(
                    get: { removeCandidate != nil },
                    set: { if !$0 { removeCandidate = nil } }
                ),
                presenting: removeCandidate
            ) { candidate in
                Button("Remove \(candidate.displayName)", role: .destructive) {
                    Task { await removeAthlete(candidate) }
                }
                Button("Cancel", role: .cancel) { removeCandidate = nil }
            } message: { candidate in
                Text("Are you sure you want to remove \(candidate.displayName)? They will no longer share their plan and data with you.")
            }
            .task {
                await loadData()
            }
        }
    }

    // MARK: - Overview Section

    private var overviewSection: some View {
        VStack(spacing: UH.Space.medium) {
            // Filters Bar
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Text("Window:")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                    ForEach(dayOptions, id: \.self) { d in
                        Button("\(d)d") {
                            daysFilter = d
                            Task { await fetchOverviewOnly() }
                        }
                        .font(.system(size: 12, weight: daysFilter == d ? .bold : .medium))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(daysFilter == d ? UH.Palette.accent.opacity(0.18) : UH.Palette.hover)
                        .foregroundStyle(daysFilter == d ? UH.Palette.accent : UH.Palette.secondary)
                        .clipShape(Capsule())
                    }
                    Spacer()
                }

                Text("Level:")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                // Scrolls edge to edge of the card; the content margin keeps the first and last chip
                // inset like the rest of the card instead of being cut at the border.
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(levels, id: \.self) { lvl in
                            Button(lvl.capitalized) {
                                levelFilter = lvl
                                Task { await fetchOverviewOnly() }
                            }
                            .font(.system(size: 11, weight: levelFilter == lvl ? .bold : .medium))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(levelFilter == lvl ? UH.Palette.ink.opacity(0.12) : UH.Palette.hover)
                            .foregroundStyle(levelFilter == lvl ? UH.Palette.ink : UH.Palette.muted)
                            .clipShape(Capsule())
                        }
                    }
                }
                .contentMargins(.horizontal, UH.Space.regular, for: .scrollContent)
                .padding(.horizontal, -UH.Space.regular)
            }
            .trainingCard()
            .padding(.horizontal, UH.Space.regular)

            if isLoading && overview == nil {
                ProgressView().padding(.vertical, UH.Space.section)
            } else if let ov = overview {
                // Phase Alerts
                if !ov.phaseAlerts.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Phase Alerts", systemImage: "exclamationmark.triangle.fill")
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(Color.orange)

                        ForEach(ov.phaseAlerts) { alert in
                            Button {
                                if let found = roster.first(where: { $0.athleteId == alert.athleteId }) {
                                    app.enterAthleteView(athlete: found)
                                    onSelectTab?(1)
                                }
                            } label: {
                                HStack(spacing: 8) {
                                    Circle()
                                        .fill(Color.orange)
                                        .frame(width: 8, height: 8)
                                    Text("\(alert.athleteName) enters \(alert.phase) \(alert.starts == "this_week" ? "this week" : "next week")")
                                        .font(UH.TextStyle.label)
                                        .foregroundStyle(UH.Palette.ink)
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .font(.system(size: 11))
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                .padding(10)
                                .background(Color.orange.opacity(0.08))
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .trainingCard()
                    .padding(.horizontal, UH.Space.regular)
                }

                // Action Items
                VStack(alignment: .leading, spacing: 10) {
                    Label("Action Items", systemImage: "checklist")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("\(ov.actionItems.draftPlans.count)")
                                .font(.system(size: 24, weight: .black, design: .rounded))
                                .foregroundStyle(UH.Palette.ink)
                            Text("Draft plans to finish")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                        .background(UH.Palette.hover)
                        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))

                        VStack(alignment: .leading, spacing: 2) {
                            Text("\(ov.actionItems.pendingWorkoutApprovals.count)")
                                .font(.system(size: 24, weight: .black, design: .rounded))
                                .foregroundStyle(Color.orange)
                            Text("Workouts pending approval")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                        .background(UH.Palette.hover)
                        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if !ov.actionItems.draftPlans.isEmpty || !ov.actionItems.pendingWorkoutApprovals.isEmpty {
                        VStack(spacing: 6) {
                            ForEach(ov.actionItems.draftPlans) { item in
                                Button {
                                    if let found = roster.first(where: { $0.athleteId == item.athleteId }) {
                                        app.enterAthleteView(athlete: found)
                                        onSelectTab?(1)
                                    }
                                } label: {
                                    HStack {
                                        Text("\(item.athleteName): Draft plan \"\(item.raceName)\"")
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(UH.Palette.secondary)
                                        Spacer()
                                        Image(systemName: "chevron.right").font(.system(size: 10))
                                    }
                                    .padding(.vertical, 4)
                                }
                                .buttonStyle(.plain)
                            }
                            ForEach(ov.actionItems.pendingWorkoutApprovals) { item in
                                Button {
                                    if let found = roster.first(where: { $0.athleteId == item.athleteId }) {
                                        app.enterAthleteView(athlete: found)
                                        onSelectTab?(1)
                                    }
                                } label: {
                                    HStack {
                                        Text("\(item.athleteName): Session \"\(item.title)\" needs approval")
                                            .font(UH.TextStyle.caption)
                                            .foregroundStyle(Color.orange)
                                        Spacer()
                                        Image(systemName: "chevron.right").font(.system(size: 10))
                                    }
                                    .padding(.vertical, 4)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }
                .trainingCard()
                .padding(.horizontal, UH.Space.regular)

                // Roster Progress List
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Label("Roster Progress", systemImage: "person.3.sequence.fill")
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        Text("\(ov.athletes.count) runners")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    if ov.athletes.isEmpty {
                        Text("No athletes on your roster yet. Switch to Roster tab to invite runners.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.muted)
                            .padding(.vertical, 8)
                    } else {
                        VStack(spacing: 8) {
                            ForEach(ov.athletes) { athlete in
                                HStack(alignment: .center, spacing: 12) {
                                    VStack(alignment: .leading, spacing: 3) {
                                        HStack(spacing: 6) {
                                            Text(athlete.name)
                                                .font(UH.TextStyle.label)
                                                .foregroundStyle(UH.Palette.ink)
                                            if athlete.needsAttention {
                                                Circle()
                                                    .fill(Color.orange)
                                                    .frame(width: 6, height: 6)
                                            }
                                        }

                                        if let plan = athlete.activePlan {
                                            Text("W\(plan.currentWeek)/\(plan.totalWeeks) · \(plan.raceName)")
                                                .font(UH.TextStyle.caption)
                                                .foregroundStyle(UH.Palette.secondary)
                                                .lineLimit(1)
                                        } else {
                                            Text("No active plan")
                                                .font(UH.TextStyle.caption)
                                                .foregroundStyle(UH.Palette.muted)
                                        }
                                    }

                                    Spacer()

                                    if let adh = athlete.adherencePct {
                                        let pct = Int((adh * 100).rounded())
                                        Text(CoachFormat.wholePercent(adh))
                                            .font(.system(size: 12, weight: .bold, design: .monospaced))
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(pct >= 80 ? Color.green.opacity(0.15) : (pct >= 60 ? Color.orange.opacity(0.15) : Color.red.opacity(0.15)))
                                            .foregroundStyle(pct >= 80 ? Color.green : (pct >= 60 ? Color.orange : Color.red))
                                            .clipShape(Capsule())
                                    }

                                    Button {
                                        if let found = roster.first(where: { $0.athleteId == athlete.athleteId }) {
                                            app.enterAthleteView(athlete: found)
                                            onSelectTab?(1)
                                        }
                                    } label: {
                                        HStack(spacing: 4) {
                                            Text("View")
                                                .font(.system(size: 12, weight: .bold))
                                            Image(systemName: "chevron.right")
                                                .font(.system(size: 10))
                                        }
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(UH.Palette.accent)
                                        .foregroundStyle(Color.black)
                                        .clipShape(Capsule())
                                    }
                                    .buttonStyle(.plain)
                                }
                                .padding(10)
                                .background(UH.Palette.hover.opacity(0.5))
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }
                        }
                    }
                }
                .trainingCard()
                .padding(.horizontal, UH.Space.regular)

                // Charts
                VStack(spacing: UH.Space.medium) {
                    AdherenceTrendChartView(trend: ov.adherenceTrend)
                    MissedByDayChartView(missedByDay: ov.missedByDay)
                    WorkoutTypeMixChartView(mix: ov.workoutTypeMix)
                    RaceBreakdownCardView(races: ov.races) { selectedRace in
                        rosterSearch = selectedRace
                        activeSection = .roster
                    }
                }
                .padding(.horizontal, UH.Space.regular)
            }
        }
    }

    // MARK: - Roster Section

    private var rosterSection: some View {
        VStack(spacing: UH.Space.medium) {
            // Add Athlete Card
            VStack(alignment: .leading, spacing: 10) {
                Label("Add an Athlete", systemImage: "person.badge.plus")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)

                HStack(spacing: 8) {
                    TextField("Athlete's Uphill email...", text: $inviteEmail)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                        .font(UH.TextStyle.body)
                        .padding(10)
                        .background(UH.Palette.hover)
                        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(
                            RoundedRectangle(cornerRadius: UH.Radius.control)
                                .stroke(UH.Palette.line, lineWidth: 1)
                        )

                    Button {
                        Task { await sendInvite() }
                    } label: {
                        if isInviting {
                            ProgressView().frame(width: 50)
                        } else {
                            Text("Invite")
                                .font(UH.TextStyle.label)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 10)
                        }
                    }
                    .buttonStyle(.uhPrimary)
                    .disabled(inviteEmail.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isInviting)
                }

                if let inviteError {
                    Text(inviteError).font(UH.TextStyle.caption).foregroundStyle(Color.red)
                }
                if let inviteSuccess {
                    Text(inviteSuccess).font(UH.TextStyle.caption).foregroundStyle(Color.green)
                }

                Text("The athlete must already have an Uphill AI account.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
            }
            .trainingCard()
            .padding(.horizontal, UH.Space.regular)

            // Search Filter
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 13))
                    .foregroundStyle(UH.Palette.secondary)
                TextField("Search athletes by name or email...", text: $rosterSearch)
                    .font(UH.TextStyle.body)
                if !rosterSearch.isEmpty {
                    Button {
                        rosterSearch = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(UH.Palette.muted)
                    }
                }
            }
            .padding(10)
            .background(UH.Palette.hover)
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
            .padding(.horizontal, UH.Space.regular)

            // Athletes List
            let filtered = roster.filter { a in
                if rosterSearch.isEmpty { return true }
                return a.displayName.localizedCaseInsensitiveContains(rosterSearch) ||
                       a.athleteEmail.localizedCaseInsensitiveContains(rosterSearch)
            }

            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Label("Your Athletes", systemImage: "person.2.fill")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                    Text("\(filtered.count) total")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                if filtered.isEmpty {
                    Text(roster.isEmpty ? "No athletes yet — send an invite above to begin coaching." : "No athletes match \"\(rosterSearch)\".")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                        .padding(.vertical, 8)
                } else {
                    VStack(spacing: 8) {
                        ForEach(filtered) { athlete in
                            VStack(spacing: 8) {
                                HStack(spacing: 12) {
                                    ZStack {
                                        Circle()
                                            .fill(athlete.isActive ? Color.green.opacity(0.15) : Color.orange.opacity(0.15))
                                            .frame(width: 36, height: 36)
                                        Text(String(athlete.displayName.prefix(2)).uppercased())
                                            .font(.system(size: 13, weight: .bold, design: .rounded))
                                            .foregroundStyle(athlete.isActive ? Color.green : Color.orange)
                                    }

                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(athlete.displayName)
                                            .font(UH.TextStyle.label)
                                            .foregroundStyle(UH.Palette.ink)
                                        HStack(spacing: 6) {
                                            Text(athlete.isActive ? "Active" : "Invite pending")
                                                .font(.system(size: 10.5, weight: .semibold))
                                                .foregroundStyle(athlete.isActive ? Color.green : Color.orange)
                                            Text("·")
                                                .font(.system(size: 10))
                                                .foregroundStyle(UH.Palette.muted)
                                            Text(athlete.athleteEmail)
                                                .font(.system(size: 11))
                                                .foregroundStyle(UH.Palette.muted)
                                                .lineLimit(1)
                                        }
                                    }

                                    Spacer()

                                    Button {
                                        removeCandidate = athlete
                                    } label: {
                                        Image(systemName: "xmark")
                                            .font(.system(size: 11, weight: .bold))
                                            .foregroundStyle(UH.Palette.muted)
                                            .padding(6)
                                    }
                                    .buttonStyle(.plain)
                                }

                                if athlete.isActive {
                                    HStack(spacing: 8) {
                                        Button {
                                            selectedAthleteForProfile = athlete
                                        } label: {
                                            HStack(spacing: 4) {
                                                Image(systemName: "person.text.rectangle")
                                                Text("Profile")
                                            }
                                            .font(.system(size: 12, weight: .medium))
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 6)
                                            .background(UH.Palette.hover)
                                            .foregroundStyle(UH.Palette.ink)
                                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                                        }
                                        .buttonStyle(.plain)

                                        Spacer()

                                        Button {
                                            app.enterAthleteView(athlete: athlete)
                                            onSelectTab?(1)
                                        } label: {
                                            HStack(spacing: 4) {
                                                Text("View Plan")
                                                    .font(.system(size: 12, weight: .bold))
                                                Image(systemName: "arrow.right")
                                                    .font(.system(size: 10, weight: .bold))
                                            }
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(UH.Palette.accent)
                                            .foregroundStyle(Color.black)
                                            .clipShape(Capsule())
                                        }
                                        .buttonStyle(.plain)
                                    }
                                    .padding(.top, 2)
                                }
                            }
                            .padding(12)
                            .background(UH.Palette.hover.opacity(0.5))
                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                    }
                }
            }
            .trainingCard()
            .padding(.horizontal, UH.Space.regular)
        }
    }

    // MARK: - Actions

    private func loadData() async {
        if overview == nil, let cached = app.coachDashboard {
            overview = cached.overview
            roster = cached.roster
            pendingInvites = cached.invites
        }
        if overview != nil && !roster.isEmpty { return }
        isLoading = true
        do {
            async let ov = app.coachingService.fetchOverview(days: daysFilter, athleteId: nil, level: levelFilter)
            async let rst = app.coachingService.fetchRoster()
            async let invs = app.coachingService.fetchMyInvites()
            let (fetchedOv, fetchedRst, fetchedInvs) = try await (ov, rst, invs)
            self.overview = fetchedOv
            self.roster = fetchedRst
            self.pendingInvites = fetchedInvs
            app.coachDashboard = CoachDashboardData(overview: fetchedOv, roster: fetchedRst, invites: fetchedInvs)
        } catch {
            print("Failed to load coach overview/roster: \(error)")
        }
        isLoading = false
    }

    private func fetchOverviewOnly() async {
        do {
            self.overview = try await app.coachingService.fetchOverview(days: daysFilter, athleteId: nil, level: levelFilter)
        } catch {
            print("Failed to fetch overview: \(error)")
        }
    }

    private func sendInvite() async {
        let email = inviteEmail.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !email.isEmpty else { return }
        isInviting = true
        inviteError = nil
        inviteSuccess = nil
        do {
            let row = try await app.coachingService.sendInvite(athleteEmail: email)
            roster.insert(row, at: 0)
            inviteSuccess = "Invitation sent to \(email)!"
            inviteEmail = ""
        } catch {
            inviteError = error.localizedDescription
        }
        isInviting = false
    }

    private func removeAthlete(_ athlete: CoachedAthleteRow) async {
        do {
            try await app.coachingService.removeFromRoster(linkId: athlete.id)
            roster.removeAll { $0.id == athlete.id }
            removeCandidate = nil
            await fetchOverviewOnly()
        } catch {
            print("Failed to remove athlete: \(error)")
        }
    }
}

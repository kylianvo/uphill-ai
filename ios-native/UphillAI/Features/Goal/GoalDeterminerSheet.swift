import SwiftUI

struct GoalDeterminerSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any GoalEstimateServicing
    var activePlan: Plan?
    var user: User?
    var isPresentedInSheet: Bool = false
    var pacingService: (any PacingServicing)? = nil
    var onApplyGoal: ((Double) -> Void)? = nil
    var onPlanPacing: ((Double) -> Void)? = nil

    // Form inputs
    @State private var raceName: String = ""
    @State private var distanceKm: Double = 50.0
    @State private var elevationGainM: Double = 2200.0
    @State private var raceDate: Date = Date().addingTimeInterval(86400 * 60)

    // "What we use" toggles
    @State private var includeRaceHistory: Bool = true
    @State private var includeUtmbIndex: Bool = true
    @State private var includeWatchData: Bool = true
    @State private var includePhysiology: Bool = true

    // Manual extra result accordion
    @State private var showManualRef: Bool = false
    @State private var manualRaceName: String = ""
    @State private var manualDistanceKm: String = ""
    @State private var manualElevationGainM: String = ""
    @State private var manualFinishTime: String = ""

    // Quick links & presentation
    @State private var showLinkProfileSheet: Bool = false
    @State private var showPacingSheet: Bool = false
    @State private var pacingTargetMins: Double? = nil

    enum GoalResultTab: String, CaseIterable, Identifiable {
        case goals = "Goals & Strategy"
        case whatWeUsed = "What we used"

        var id: String { rawValue }
    }

    // Output & state
    @State private var estimate: GoalEstimate?
    @State private var selectedResultTab: GoalResultTab = .goals
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    @State private var appliedTier: String? = nil

    /// Whole weeks from today to the race, as the server derives them from `raceDate`.
    private var weeksToRace: Int {
        max(0, Calendar.current.dateComponents([.day], from: Calendar.current.startOfDay(for: Date()), to: raceDate).day ?? 0) / 7
    }

    /// The profile's Zone 2 range, which the server averages into the easy-pace prior.
    private var easyPaceLabel: String? {
        guard let lo = user?.zone2PaceMin, let hi = user?.zone2PaceMax, !lo.isEmpty, !hi.isEmpty else { return nil }
        return "\(lo)–\(hi) /km"
    }

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    init(
        service: any GoalEstimateServicing,
        pacingService: (any PacingServicing)? = nil,
        activePlan: Plan? = nil,
        user: User? = nil,
        isPresentedInSheet: Bool = false,
        onApplyGoal: ((Double) -> Void)? = nil,
        onPlanPacing: ((Double) -> Void)? = nil,
        initialEstimate: GoalEstimate? = nil,
        initialTab: GoalResultTab = .goals
    ) {
        self.service = service
        self.pacingService = pacingService
        self.activePlan = activePlan
        self.user = user
        self.isPresentedInSheet = isPresentedInSheet
        self.onApplyGoal = onApplyGoal
        self.onPlanPacing = onPlanPacing
        _estimate = State(initialValue: initialEstimate)
        _selectedResultTab = State(initialValue: initialTab)
    }

    var body: some View {
        Group {
            if let estimate {
                resultsView(estimate)
            } else {
                formView
            }
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Goal Determiner")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if isPresentedInSheet {
                ToolbarItem(placement: .topBarLeading) {
                    if estimate != nil {
                        Button {
                            withAnimation(UH.Motion.standard) {
                                self.estimate = nil
                            }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "chevron.left")
                                Text("Edit")
                            }
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        }
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(UH.Palette.muted)
                            .font(.system(size: 22))
                    }
                    .accessibilityIdentifier("goalDeterminer.dismiss")
                }
            } else {
                if estimate != nil {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Edit") {
                            withAnimation(UH.Motion.standard) {
                                self.estimate = nil
                            }
                        }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }
        }
        .sheet(isPresented: $showPacingSheet) {
            if let pacingService {
                NavigationStack {
                    PaceStrategySheet(
                        service: pacingService,
                        activePlan: activePlan,
                        user: user,
                        initialTargetMins: pacingTargetMins,
                        isPresentedInSheet: true
                    )
                }
            }
        }
            .sheet(isPresented: $showLinkProfileSheet) {
                // Link profile stub/sheet
                NavigationStack {
                    VStack(spacing: 16) {
                        Image(systemName: "link.badge.plus")
                            .font(.system(size: 44))
                            .foregroundStyle(UH.Palette.accentInk)
                            .padding(.top, 40)
                        Text("Link UTMB or VBM Profile")
                            .font(UH.TextStyle.sectionTitle)
                        Text("Connect your verified race history to sharpen your goal calculation.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                        Spacer()
                    }
                    .padding()
                    .toolbar {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button("Done") { showLinkProfileSheet = false }
                        }
                    }
                }
            }
            .task {
                if let p = activePlan {
                    raceName = p.raceName
                    if let d = p.courseDistanceKm, d > 0 { distanceKm = d }
                    if let g = p.courseElevationGainM, g > 0 { elevationGainM = g }
                }
            }
    }

    // MARK: - Form View

    private var formView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                // Header
                VStack(alignment: .leading, spacing: 4) {
                    Text("GOAL ESTIMATION")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.8)
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("Target time & field percentile")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Estimates your finish time from the course, its past field, and your race history, watch training and profile.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                if let error = errorMessage {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(UH.Palette.danger)
                        Text(error)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.danger)
                    }
                    .padding(UH.Space.small)
                    .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }

                // Race info card
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("TARGET RACE")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    TextField("Race name (e.g. Dalat Ultra Trail 50K)", text: $raceName)
                        .font(UH.TextStyle.body)
                        .padding(10)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Distance (km)")
                                .font(UH.TextStyle.disclosure)
                                .foregroundStyle(UH.Palette.secondary)
                            TextField("50", value: $distanceKm, format: .number)
                                .keyboardType(.decimalPad)
                                .font(UH.TextStyle.metric)
                                .padding(10)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Elevation Gain (m)")
                                .font(UH.TextStyle.disclosure)
                                .foregroundStyle(UH.Palette.secondary)
                            TextField("2200", value: $elevationGainM, format: .number)
                                .keyboardType(.numberPad)
                                .font(UH.TextStyle.metric)
                                .padding(10)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                        }
                    }

                    DatePicker("Race Date", selection: $raceDate, displayedComponents: .date)
                        .font(UH.TextStyle.body)
                        .padding(.vertical, 4)
                }
                .trainingCard()

                // Baseline fitness card: read-only, the server derives both
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("CURRENT FITNESS BASELINE")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    baselineRow(
                        title: "Easy pace",
                        detail: easyPaceLabel == nil ? "Not set — add your Zone 2 pace in Profile" : "From your profile Zone 2",
                        value: easyPaceLabel ?? "—"
                    )
                    Divider().padding(.vertical, 4)
                    baselineRow(
                        title: "Weeks to race",
                        detail: "From the race date",
                        value: "\(weeksToRace) wks"
                    )

                    Text("Linked race results and watch volume below count for more than easy pace when you have them.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .padding(.top, 4)
                }
                .trainingCard()

                // WHAT WE USE Section (Prod Web Parity)
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack {
                        Text("WHAT WE USE")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                        Spacer()
                        Button {
                            showLinkProfileSheet = true
                        } label: {
                            Text("Link UTMB / VBM")
                                .font(UH.TextStyle.disclosure.weight(.bold))
                                .foregroundStyle(UH.Palette.accentInk)
                        }
                    }

                    Text("Toggle data sources used by the estimation engine:")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)

                    VStack(spacing: 8) {
                        sourceToggleRow(
                            title: "Linked race results (UTMB / VBM)",
                            subtitle: "Past finish times, pace degradation and course difficulty",
                            isOn: $includeRaceHistory
                        )
                        sourceToggleRow(
                            title: "UTMB Index & Field Ranking",
                            subtitle: "Relative field placement and competitive caliber",
                            isOn: $includeUtmbIndex
                        )
                        sourceToggleRow(
                            title: "Watch 8-week training volume",
                            subtitle: "Recent weekly mileage, vertical gain, and durability",
                            isOn: $includeWatchData
                        )
                        sourceToggleRow(
                            title: "Physiology & Pace Zones",
                            subtitle: "VO2max, COROS race prediction and easy pace",
                            isOn: $includePhysiology
                        )
                    }

                    Divider().padding(.vertical, 4)

                    // Extra manual reference result accordion
                    Button {
                        withAnimation(UH.Motion.standard) {
                            showManualRef.toggle()
                        }
                    } label: {
                        HStack {
                            Text(showManualRef ? "− Hide extra unlinked result" : "+ Add a result that isn't linked")
                                .font(UH.TextStyle.caption.weight(.bold))
                                .foregroundStyle(UH.Palette.accentInk)
                            Spacer()
                            Image(systemName: showManualRef ? "chevron.up" : "chevron.down")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundStyle(UH.Palette.accentInk)
                        }
                    }

                    if showManualRef {
                        VStack(spacing: 10) {
                            TextField("Reference race name (e.g. Sapa 42K)", text: $manualRaceName)
                                .font(UH.TextStyle.caption)
                                .padding(8)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                            HStack(spacing: 8) {
                                TextField("Dist (km)", text: $manualDistanceKm)
                                    .keyboardType(.decimalPad)
                                    .font(UH.TextStyle.caption)
                                    .padding(8)
                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                                TextField("Gain (m)", text: $manualElevationGainM)
                                    .keyboardType(.numberPad)
                                    .font(UH.TextStyle.caption)
                                    .padding(8)
                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                                TextField("Time (4:45:00)", text: $manualFinishTime)
                                    .font(UH.TextStyle.caption)
                                    .padding(8)
                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                            }
                        }
                        .padding(.top, 4)
                    }
                }
                .trainingCard()

                // CTA
                Button {
                    Task { await estimateGoal() }
                } label: {
                    HStack {
                        if isLoading {
                            ProgressView().tint(Color.white)
                        } else {
                            Image(systemName: "speedometer")
                            Text("Estimate Race Goal")
                        }
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(Color.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                }
                .disabled(isLoading || distanceKm <= 0)
                .padding(.bottom, UH.Space.reading)
            }
            .padding(UH.Space.regular)
        }
    }

    private func baselineRow(title: String, detail: String, value: String) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(UH.TextStyle.body.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
                Text(detail)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            Text(value)
                .font(UH.TextStyle.metric)
                .foregroundStyle(UH.Palette.ink)
        }
    }

    private func sourceToggleRow(title: String, subtitle: String, isOn: Binding<Bool>) -> some View {
        Toggle(isOn: isOn) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(UH.TextStyle.body.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
                Text(subtitle)
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)
            }
        }
        .tint(UH.Palette.accentInk)
    }

    // MARK: - Results View

    private func resultsView(_ estimate: GoalEstimate) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                // Tab Picker: Goals & Strategy vs. What we used
                resultTabPicker

                switch selectedResultTab {
                case .goals:
                    goalsTabContent(estimate)
                case .whatWeUsed:
                    whatWeUsedTabContent(estimate)
                }
            }
            .padding(UH.Space.regular)
        }
    }

    private var resultTabPicker: some View {
        HStack(spacing: 8) {
            ForEach(GoalResultTab.allCases) { tab in
                Button {
                    withAnimation(UH.Motion.standard) {
                        selectedResultTab = tab
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: tab == .goals ? "flag.checkered" : "sparkles")
                            .font(.system(size: 11, weight: .bold))

                        Text(tab.rawValue)
                            .font(UH.TextStyle.label)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(
                        selectedResultTab == tab ? UH.Palette.card : Color.clear,
                        in: RoundedRectangle(cornerRadius: UH.Radius.control)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: UH.Radius.control)
                            .stroke(selectedResultTab == tab ? UH.Palette.line : Color.clear)
                    )
                    .foregroundStyle(selectedResultTab == tab ? UH.Palette.ink : UH.Palette.muted)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control + 2))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control + 2).stroke(UH.Palette.line))
    }

    // MARK: - Goals & Strategy Tab Content

    private func goalsTabContent(_ estimate: GoalEstimate) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            // Confidence Indicator & LLM engine notice
            HStack(spacing: 8) {
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.seal.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                        .font(.system(size: 11))
                    Text(estimate.referenceConfidence?.uppercased() ?? "HIGH CONFIDENCE")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(UH.Palette.activeFill, in: Capsule())

                Text("Coach Uphill LLM Assessment")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }

            // 3 Goal Tiers (A Ambitious, B Realistic, C Safe)
            if let goals = estimate.goals {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("TARGET GOAL TIERS")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    tierCard(tier: "A", name: "Ambitious", minutes: goals.ambitious, color: Color(hex: "#10b981"), desc: "Peak race day execution, ideal weather & conditions")
                    tierCard(tier: "B", name: "Realistic", minutes: goals.realistic, color: UH.Palette.accentInk, desc: "Primary target goal with solid execution")
                    tierCard(tier: "C", name: "Safe", minutes: goals.safe, color: Color(hex: "#f59e0b"), desc: "Conservative buffer against heat, fatigue or cramps")
                }
            }

            // Coach Reasoning
            if let reasoning = estimate.reasoning, !reasoning.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        Image(systemName: "quote.bubble.fill")
                            .foregroundStyle(UH.Palette.accentInk)
                            .font(.system(size: 12))
                        Text("COACH UPHILL REASONING")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(reasoning, id: \.self) { line in
                            HStack(alignment: .top, spacing: 6) {
                                Text("•")
                                    .font(UH.TextStyle.body.weight(.bold))
                                    .foregroundStyle(UH.Palette.accentInk)
                                Text(line)
                                    .font(UH.TextStyle.body)
                                    .foregroundStyle(UH.Palette.ink)
                                    .lineSpacing(2)
                            }
                        }
                    }
                }
                .trainingCard()
            }

            // Race Day Pace Strategy Targets Card
            pacingTargetsCard(estimate)

            // Field Curve Chart
            if let benchmarks = estimate.benchmarks, !benchmarks.isEmpty {
                FieldCurveChart(benchmarks: benchmarks, goals: estimate.goals)
            }

            // Disclaimer Note
            Text("Goal times are estimates synthesized from your training data, not a finish line guarantee.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.muted)
                .padding(.horizontal, 4)
        }
    }

    // MARK: - Tier Card with "Use for plan" & "Plan pacing"

    private func tierCard(tier: String, name: String, minutes: Double, color: Color, desc: String) -> some View {
        let isApplied = appliedTier == tier

        return VStack(alignment: .leading, spacing: 10) {
            HStack {
                HStack(spacing: 6) {
                    Text(tier)
                        .font(.system(size: 12, weight: .black, design: .monospaced))
                        .foregroundStyle(color)
                        .frame(width: 22, height: 22)
                        .background(color.opacity(0.14), in: RoundedRectangle(cornerRadius: 4))

                    Text(name.uppercased())
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.ink)
                }

                Spacer()

                Text(GoalEstimate.formatMinutes(minutes))
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.ink)
            }

            Text(desc)
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)

            // Two Action Buttons (Prod Parity)
            HStack(spacing: 8) {
                // Apply button
                Button {
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    appliedTier = tier
                    onApplyGoal?(minutes)
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: isApplied ? "checkmark" : "target")
                        Text(isApplied ? "Target Applied" : "Use for Plan")
                    }
                    .font(UH.TextStyle.caption.weight(.bold))
                    .foregroundStyle(isApplied ? UH.Palette.accentInk : UH.Palette.ink)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(isApplied ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isApplied ? UH.Palette.accentInk : UH.Palette.line))
                }
                .buttonStyle(.plain)
                .disabled(isApplied)

                // Plan Pacing Button
                Button {
                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    if let onPlanPacing {
                        onPlanPacing(minutes)
                    } else {
                        pacingTargetMins = minutes
                        showPacingSheet = true
                    }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "speedometer")
                        Text("Plan Pacing")
                    }
                    .font(UH.TextStyle.caption.weight(.bold))
                    .foregroundStyle(UH.Palette.ink)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
            }
        }
        .trainingCard()
    }

    // MARK: - Pacing Targets Card

    private func pacingTargetsCard(_ estimate: GoalEstimate) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("RACE DAY PACING TARGETS")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                Text("Avg \(estimate.targetAveragePace)")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
            }

            HStack(spacing: 8) {
                pacePill(icon: "mountain.2.fill", title: "CLIMBING", pace: estimate.climbingPaceTarget, desc: "Power hike / high grade")
                pacePill(icon: "figure.run", title: "FLAT", pace: estimate.flatPaceTarget, desc: "Smooth Zone 2 aerobic")
                pacePill(icon: "arrow.down.right", title: "DESCENT", pace: estimate.descentPaceTarget, desc: "Controlled cadence")
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("EXECUTION STRATEGY")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                Text("• First 30%: Discipline in low Zone 2. Bank zero lactate on early climbs.\n• Middle 40%: Settle into steady rhythm, fuel every 30 mins.\n• Final 30%: Empty the tank on runnable sections if quads allow.")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)
                    .lineSpacing(3)
            }
            .padding(.top, 4)
        }
        .trainingCard()
    }

    private func pacePill(icon: String, title: String, pace: String, desc: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 11))
                Text(title)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
            }
            .foregroundStyle(UH.Palette.accentInk)

            Text(pace)
                .font(UH.TextStyle.body.weight(.bold))
                .foregroundStyle(UH.Palette.ink)

            Text(desc)
                .font(.system(size: 10))
                .foregroundStyle(UH.Palette.secondary)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(8)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    // MARK: - "What We Used" Tab Content (LLM Context Transparency)

    private func whatWeUsedTabContent(_ estimate: GoalEstimate) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            VStack(alignment: .leading, spacing: 8) {
                Text("DATA SOURCES")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)

                let sources = estimate.sources ?? []
                if sources.isEmpty {
                    Text("No personal data found, so the goals come from the course and its past field only. Link UTMB / VBM or sync your watch to sharpen them.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                } else {
                    VStack(spacing: 6) {
                        ForEach(sources) { source in
                            sourceStatusRow(title: source.label, source: source.included ? "Used" : "Turned off", isIncluded: source.included)
                        }
                    }
                }
            }
            .trainingCard()

            contextSectionCard(
                icon: "flag.fill",
                title: estimate.raceName ?? activePlan?.raceName ?? "Target Race",
                rows: [
                    ("Distance", "\(String(format: "%.1f", estimate.distanceKm)) km"),
                    ("Elevation Gain", "\(Int(estimate.elevationGainM))m D+"),
                    ("Course Profile", estimate.targetProfileSource == "gpx" ? "Verified GPX" : "Estimated profile"),
                    ("Weeks to Race", "\(weeksToRace) weeks")
                ]
            )

            if let firstBench = estimate.benchmarks?.first {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Label("Historical Field Times (\(firstBench.year))", systemImage: "chart.bar.xaxis")
                            .font(UH.TextStyle.body.weight(.bold))
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                        if let total = firstBench.finishers {
                            Text("\(total) finishers")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }

                    let p = firstBench.percentiles?["overall"]
                    HStack(spacing: 6) {
                        statBox(label: "Winner", value: firstBench.winnerTime ?? "—")
                        statBox(label: "Top 10%", value: p?.p10 ?? "—")
                        statBox(label: "Median 50%", value: p?.p50 ?? "—")
                        statBox(label: "90% Finish", value: p?.p90 ?? "—")
                    }
                }
                .trainingCard()
            }

            let profileRows: [(String, String)] = [
                ("Weekly Volume", user?.currentWeeklyKm.map { "\(Int($0.rounded())) km/week" }),
                ("Easy Pace (Zone 2)", easyPaceLabel),
                ("Threshold Pace", user?.thresholdPace.map { "\($0)/km" }),
                ("Aerobic Threshold (AeT)", user?.aetHr.map { "\($0) bpm" }),
                ("Max Heart Rate", user?.maxHr.map { "\($0) bpm" })
            ].compactMap { label, value in value.map { (label, $0) } }
            if !profileRows.isEmpty {
                contextSectionCard(icon: "person.fill", title: "Your Profile", rows: profileRows)
            }
        }
    }

    private func sourceStatusRow(title: String, source: String, isIncluded: Bool) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(UH.TextStyle.body.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
                Text(source)
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            HStack(spacing: 4) {
                Image(systemName: isIncluded ? "checkmark.circle.fill" : "minus.circle.fill")
                    .foregroundStyle(isIncluded ? UH.Palette.accentInk : UH.Palette.muted)
                Text(isIncluded ? "Included" : "Excluded")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(isIncluded ? UH.Palette.accentInk : UH.Palette.muted)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(
                isIncluded ? UH.Palette.activeFill : UH.Palette.surface,
                in: Capsule()
            )
        }
    }

    private func contextSectionCard(icon: String, title: String, rows: [(String, String)]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: icon)
                .font(UH.TextStyle.body.weight(.bold))
                .foregroundStyle(UH.Palette.ink)

            VStack(spacing: 6) {
                ForEach(rows, id: \.0) { row in
                    HStack {
                        Text(row.0)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                        Spacer()
                        Text(row.1)
                            .font(UH.TextStyle.caption.weight(.medium))
                            .foregroundStyle(UH.Palette.ink)
                    }
                }
            }
        }
        .trainingCard()
    }

    private func statBox(label: String, value: String) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9.5, weight: .medium))
                .foregroundStyle(UH.Palette.secondary)
            Text(value)
                .font(.system(size: 13, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 6)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    private func estimateGoal() async {
        isLoading = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        var exclusions: [String] = []
        if !includeRaceHistory { exclusions.append("race_history") }
        if !includeUtmbIndex { exclusions.append("utmb_index") }
        if !includeWatchData { exclusions.append("watch") }
        if !includePhysiology { exclusions.append("physiology") }

        var reference: GoalEstimateRequest.Reference?
        if showManualRef, let dist = Double(manualDistanceKm), dist > 0, !manualFinishTime.isEmpty {
            reference = .init(
                raceName: manualRaceName.isEmpty ? nil : manualRaceName,
                distanceKm: dist,
                elevationGainM: Double(manualElevationGainM),
                time: manualFinishTime
            )
        }

        let req = GoalEstimateRequest(
            raceName: raceName.isEmpty ? nil : raceName,
            distanceKm: distanceKm,
            elevationGainM: elevationGainM,
            raceDate: Self.dateFormatter.string(from: raceDate),
            exclude: exclusions,
            reference: reference
        )

        do {
            let res = try await service.estimateGoal(request: req)
            withAnimation(UH.Motion.standard) {
                self.estimate = res
            }
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            errorMessage = error.localizedDescription
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
        isLoading = false
    }
}

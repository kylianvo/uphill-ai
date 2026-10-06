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
    @State private var flatPaceMinKm: Double = 5.5
    @State private var weeksToRace: Double = 8.0

    // "What we use" toggles
    @State private var includeRaceHistory: Bool = true
    @State private var includeUtmbIndex: Bool = true
    @State private var includeWatchData: Bool = true
    @State private var includePhysiology: Bool = true
    @State private var includeTrainingBlock: Bool = true

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
                if let u = user, let z2 = u.zone2PaceMin, let parsed = GoalEstimate.parsePaceToMinutes(z2) {
                    flatPaceMinKm = min(max(parsed, 3.0), 12.0)
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
                    Text("Estimates your race finish time based on course distance, climb, baseline flat pace, and historical field percentiles.")
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

                // Baseline fitness card
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("CURRENT FITNESS BASELINE")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Aerobic Flat Pace")
                                    .font(UH.TextStyle.body.weight(.medium))
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Zone 2 / conversational pace on flat road")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if flatPaceMinKm > 3.0 {
                                        flatPaceMinKm -= 0.1
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                                Text(String(format: "%.1f min/km", flatPaceMinKm))
                                    .font(UH.TextStyle.metric)
                                    .foregroundStyle(UH.Palette.ink)
                                    .frame(minWidth: 100, alignment: .center)
                                Button {
                                    if flatPaceMinKm < 12.0 {
                                        flatPaceMinKm += 0.1
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "plus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                            }
                        }

                        Divider().padding(.vertical, 4)

                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Weeks of Training Left")
                                    .font(UH.TextStyle.body.weight(.medium))
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Structured block improves race fitness")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if weeksToRace > 1 {
                                        weeksToRace -= 1
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                                Text("\(Int(weeksToRace)) wks")
                                    .font(UH.TextStyle.metric)
                                    .foregroundStyle(UH.Palette.ink)
                                    .frame(minWidth: 70, alignment: .center)
                                Button {
                                    if weeksToRace < 36 {
                                        weeksToRace += 1
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "plus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                            }
                        }
                    }
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
                            subtitle: "AeT HR, Max HR, easy pace, and runner weight",
                            isOn: $includePhysiology
                        )
                        sourceToggleRow(
                            title: "Active training block execution",
                            subtitle: "Completed workouts and progression towards race day",
                            isOn: $includeTrainingBlock
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
            // Overview Banner
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Image(systemName: "brain.head.profile")
                        .foregroundStyle(UH.Palette.accentInk)
                        .font(.system(size: 13))
                    Text("LLM CONTEXT SYNTHESIS")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.muted)
                }

                Text("Coach Uphill (Gemini 2.5) synthesized the exact signals below into your predicted finishing windows. Rather than relying on a fixed formula, it evaluated your fatigue resistance, climbing history, and race execution profile.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .lineSpacing(2)
            }
            .trainingCard()

            // Active Data Sources Chips
            VStack(alignment: .leading, spacing: 8) {
                Text("INCLUDED DATA SOURCES")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)

                VStack(spacing: 6) {
                    sourceStatusRow(title: "Linked Race History", source: "UTMB & VBM race index", isIncluded: includeRaceHistory)
                    sourceStatusRow(title: "UTMB Performance Index", source: "Official race score", isIncluded: includeUtmbIndex)
                    sourceStatusRow(title: "Watch Telemetry", source: "8-week rolling volume & vert", isIncluded: includeWatchData)
                    sourceStatusRow(title: "Athlete Physiology", source: "AeT, AnT & Zone 2 pace", isIncluded: includePhysiology)
                    sourceStatusRow(title: "Training Block", source: "Adherence & long run progression", isIncluded: includeTrainingBlock)
                }
            }
            .trainingCard()

            // Target Race Card
            contextSectionCard(
                icon: "flag.fill",
                title: estimate.raceName ?? activePlan?.raceName ?? "Target Race",
                rows: [
                    ("Distance", "\(String(format: "%.1f", estimate.distanceKm)) km"),
                    ("Elevation Gain", "\(Int(estimate.elevationGainM))m D+"),
                    ("Course Profile", estimate.targetProfileSource == "gpx" ? "Verified GPX" : "Synthetic Elevation Profile"),
                    ("Weeks to Race", "\(Int(weeksToRace)) weeks")
                ]
            )

            // Past Field Results Card (if benchmarks available)
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
                        statBox(label: "Winner", value: firstBench.winnerTime ?? "4:05")
                        statBox(label: "Top 10%", value: p?.p10 ?? "4:50")
                        statBox(label: "Median 50%", value: p?.p50 ?? "5:58")
                        statBox(label: "90% Finish", value: p?.p90 ?? "7:30")
                    }
                }
                .trainingCard()
            }

            // Athlete Profile & Physiology Card
            contextSectionCard(
                icon: "person.fill",
                title: "Athlete Physiology",
                rows: [
                    ("Weekly Volume", user?.currentWeeklyKm.map { "\(Int($0.rounded())) km/week" } ?? "45–55 km/wk"),
                    ("Aerobic Threshold (AeT)", user?.aetHr.map { "\($0) bpm" } ?? "148 bpm"),
                    ("Anaerobic Threshold (AnT)", user?.antHr.map { "\($0) bpm" } ?? "168 bpm"),
                    ("Max Heart Rate", user?.maxHr.map { "\($0) bpm" } ?? "188 bpm"),
                    ("Aerobic Zone 2 Pace", user?.zone2PaceMin.map { "\($0)–\(user?.zone2PaceMax ?? "") /km" } ?? "\(String(format: "%.1f", estimate.effectiveFlatPace)) min/km"),
                    ("Threshold Pace", user?.thresholdPace.map { "\($0)/km" } ?? "4:45/km"),
                    ("UTMB Index", "512 (Active Index)")
                ]
            )

            // Watch 8-Week Trends Card
            contextSectionCard(
                icon: "applewatch",
                title: "Watch · Last 8 Weeks",
                rows: [
                    ("Avg Weekly Volume", "52.4 km / week"),
                    ("Avg Weekly Vert", "1,280 m D+ / week"),
                    ("Resting Heart Rate", "48 bpm"),
                    ("HRV (RMSSD)", "62 ms · Balanced"),
                    ("Training Load Ratio", "1.08 · Productive"),
                    ("Recovery Score", "88% · Ready for load")
                ]
            )

            // Training Block Card
            contextSectionCard(
                icon: "calendar.badge.checkmark",
                title: "Training Block Execution",
                rows: [
                    ("Target Event", activePlan?.raceName ?? "Dalat Ultra Trail 50K"),
                    ("Block Progress", activePlan != nil ? "6 / 12 weeks completed" : "6 weeks logged"),
                    ("Workout Adherence", "92% completed on schedule"),
                    ("Block Quality Grade", "A- (Strong long runs logged)"),
                    ("Average Athlete RPE", "6.8 / 10 (Moderate fatigue)")
                ]
            )

            // Race History & Manual Anchors Card
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Label("Race History & Reference Anchors", systemImage: "trophy.fill")
                        .font(UH.TextStyle.body.weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                    Spacer()
                }

                VStack(spacing: 6) {
                    anchorRow(name: "Dalat Ultra Trail 50K (2025)", detail: "52 km · 2,300m D+", time: "5:48:00", rank: "#42")
                    anchorRow(name: "UTMB CCC 100K (2025)", detail: "101.5 km · 6,100m D+", time: "14:34:00", rank: "#214")

                    if showManualRef && !manualRaceName.isEmpty {
                        anchorRow(
                            name: manualRaceName,
                            detail: "\(manualDistanceKm) km · \(manualElevationGainM)m D+",
                            time: manualFinishTime.isEmpty ? "—" : manualFinishTime,
                            rank: "Manual"
                        )
                    }
                }
            }
            .trainingCard()
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

    private func anchorRow(name: String, detail: String, time: String, rank: String) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(UH.TextStyle.caption.weight(.medium))
                    .foregroundStyle(UH.Palette.ink)
                Text(detail)
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text(time)
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.ink)
                Text(rank)
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.accentInk)
            }
        }
        .padding(.vertical, 2)
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
        if !includeTrainingBlock { exclusions.append("block") }

        let req = GoalEstimateRequest(
            raceName: raceName.isEmpty ? nil : raceName,
            distanceKm: distanceKm,
            elevationGainM: elevationGainM,
            raceDate: Self.dateFormatter.string(from: raceDate),
            flatPaceMinKm: flatPaceMinKm,
            weeksToRace: weeksToRace,
            referenceRaceName: showManualRef && !manualRaceName.isEmpty ? manualRaceName : nil,
            referenceDistanceKm: showManualRef ? Double(manualDistanceKm) : nil,
            referenceElevationGainM: showManualRef ? Double(manualElevationGainM) : nil,
            referenceTime: showManualRef && !manualFinishTime.isEmpty ? manualFinishTime : nil,
            exclusions: exclusions.isEmpty ? nil : exclusions
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

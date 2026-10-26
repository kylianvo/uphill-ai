import SwiftUI

struct GearVaultSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any GearServicing
    var activePlan: Plan?
    var user: User?
    var isPresentedInSheet: Bool = false
    var onAssignToRotation: ((ShoeItem) -> Void)? = nil
    var raceMatchService: RaceMatchService? = nil

    // Form inputs
    @State private var raceName: String = ""
    @State private var raceDistance: String = ""
    @State private var surface: String = "trail"
    @State private var cushioning: String = "balanced"
    @State private var width: String = "normal"
    @State private var carbonPlate: String = "unknown"
    @State private var terrain: Set<String> = ["runnable"]
    @State private var roadUseCase: String = "daily training"
    @State private var preferredBrands: String = ""
    @State private var budget: String = ""
    @State private var additionalContext: String = ""

    // Output & state
    @State private var gearPlan: GearPlan?
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var expandedShoeId: String? = nil
    @State private var feedbackSent: Int? = nil
    @State private var shoeToAssign: ShoeRecommendation? = nil

    private let quickBrands = ["Salomon", "Hoka", "Nike", "Saucony", "Altra", "Brooks", "Nnormal"]
    private let trailTerrains = ["runnable", "technical", "muddy", "rocky"]
    private let roadUseCases = ["daily training", "race", "speed work"]

    init(
        service: any GearServicing,
        activePlan: Plan? = nil,
        user: User? = nil,
        raceMatchService: RaceMatchService? = nil,
        isPresentedInSheet: Bool = false,
        onAssignToRotation: ((ShoeItem) -> Void)? = nil,
        initialPlan: GearPlan? = nil
    ) {
        self.service = service
        self.raceMatchService = raceMatchService
        _raceName = State(initialValue: activePlan?.raceName ?? "")
        _raceDistance = State(initialValue: activePlan?.courseDistanceKm.map { "\(Int($0.rounded())) km" } ?? "")
        self.activePlan = activePlan
        self.user = user
        self.isPresentedInSheet = isPresentedInSheet
        self.onAssignToRotation = onAssignToRotation
        _gearPlan = State(initialValue: initialPlan)
    }

    var body: some View {
        Group {
            if let gearPlan {
                resultsView(gearPlan)
            } else {
                formView
            }
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Gear Vault")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if isPresentedInSheet {
                ToolbarItem(placement: .topBarLeading) {
                    if gearPlan != nil {
                        Button {
                            withAnimation(UH.Motion.standard) {
                                self.gearPlan = nil
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
                    .accessibilityIdentifier("gearVault.dismiss")
                }
            } else {
                if gearPlan != nil {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Edit") {
                            withAnimation(UH.Motion.standard) {
                                self.gearPlan = nil
                            }
                        }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }
        }
        .sheet(item: $shoeToAssign) { shoe in
            AssignShoeSheet(shoe: shoe) { item in
                onAssignToRotation?(item)
                shoeToAssign = nil
            }
        }
    }

    // MARK: - Form View

    private var formView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                // Header
                VStack(alignment: .leading, spacing: 4) {
                    Text("SHOE SPECIALIST")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.8)
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("Match the right shoe for your terrain")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Find shoes matched to course technicality, foot shape, cushioning preference, and plate requirements.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack {
                        Text("RACE")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                        Spacer()
                        if let plan = activePlan, raceName != plan.raceName {
                            Button("Use my plan's race") {
                                raceName = plan.raceName
                                raceDistance = plan.courseDistanceKm.map { "\(Int($0.rounded())) km" } ?? ""
                            }
                            .font(UH.TextStyle.disclosure.weight(.bold))
                            .foregroundStyle(UH.Palette.accentInk)
                        }
                    }
                    RaceSearchField(raceName: $raceName, service: raceMatchService, placeholder: L("Race name (optional)"),
                                    onPick: { course in raceDistance = course.label ?? "\(Int(course.distanceKm.rounded())) km" },
                                    onClear: { raceDistance = "" })
                    if !raceDistance.isEmpty {
                        Text(L("Distance: %@", raceDistance))
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
                .trainingCard()

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

                // Surface & Terrain
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("SURFACE & TERRAIN")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        Picker("Surface", selection: $surface) {
                            Text("Trail").tag("trail")
                            Text("Road").tag("road")
                        }
                        .pickerStyle(.segmented)

                        if surface == "trail" {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Trail Terrain Types")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)

                                HStack(spacing: 6) {
                                    ForEach(trailTerrains, id: \.self) { t in
                                        let isSelected = terrain.contains(t)
                                        Button {
                                            UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                            if isSelected {
                                                if terrain.count > 1 { terrain.remove(t) }
                                            } else {
                                                terrain.insert(t)
                                            }
                                        } label: {
                                            Text(t.capitalized)
                                                .font(UH.TextStyle.caption.weight(.medium))
                                                .padding(.horizontal, 10)
                                                .padding(.vertical, 6)
                                                .background(isSelected ? UH.Palette.accentInk : UH.Palette.surface, in: Capsule())
                                                .foregroundStyle(isSelected ? UH.Palette.onSolid : UH.Palette.ink)
                                                .overlay(Capsule().stroke(isSelected ? Color.clear : UH.Palette.line))
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }
                            }
                        } else {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Road Use Case")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)

                                Picker("Use Case", selection: $roadUseCase) {
                                    ForEach(roadUseCases, id: \.self) { uc in
                                        Text(uc.capitalized).tag(uc)
                                    }
                                }
                                .pickerStyle(.segmented)
                            }
                        }
                    }
                    .trainingCard()
                }

                // Fit & Cushioning
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("FIT & CUSHIONING")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: UH.Space.regular) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Cushioning")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Picker("Cushioning", selection: $cushioning) {
                                Text("Plush").tag("plush")
                                Text("Balanced").tag("balanced")
                                Text("Firm").tag("firm")
                            }
                            .pickerStyle(.segmented)
                        }

                        Divider()

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Width / Foot Shape")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Picker("Width", selection: $width) {
                                Text("Narrow").tag("narrow")
                                Text("Normal").tag("normal")
                                Text("Wide").tag("wide")
                            }
                            .pickerStyle(.segmented)
                        }

                        Divider()

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Carbon / Propulsion Plate")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                            Picker("Carbon Plate", selection: $carbonPlate) {
                                Text("Yes").tag("yes")
                                Text("No").tag("no")
                                Text("Any").tag("unknown")
                            }
                            .pickerStyle(.segmented)
                        }
                    }
                    .trainingCard()
                }

                // Brands & Budget
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("BRAND PREFERENCES & BUDGET")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: 10) {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(quickBrands, id: \.self) { b in
                                    let isSelected = preferredBrands.localizedCaseInsensitiveContains(b)
                                    Button {
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                        if isSelected {
                                            preferredBrands = preferredBrands.replacingOccurrences(of: b, with: "")
                                                .trimmingCharacters(in: .whitespacesAndNewlines)
                                        } else {
                                            preferredBrands = preferredBrands.isEmpty ? b : "\(preferredBrands), \(b)"
                                        }
                                    } label: {
                                        Text(b)
                                            .font(UH.TextStyle.caption.weight(.medium))
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 6)
                                            .background(isSelected ? UH.Palette.accentInk : UH.Palette.surface, in: Capsule())
                                            .foregroundStyle(isSelected ? UH.Palette.onSolid : UH.Palette.ink)
                                            .overlay(Capsule().stroke(isSelected ? Color.clear : UH.Palette.line))
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }

                        TextField("Preferred brands or specific request", text: $preferredBrands)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                        TextField("Additional notes (e.g. blister prone, rock protection needed)", text: $additionalContext)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                    }
                    .trainingCard()
                }

                // CTA
                Button {
                    Task { await recommend() }
                } label: {
                    HStack {
                        if isLoading {
                            ProgressView().tint(UH.Palette.onSolid)
                        } else {
                            Image(systemName: "magnifyingglass")
                            Text("Recommend Shoes")
                        }
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.onSolid)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(UH.Palette.ink, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                }
                .disabled(isLoading)
                .padding(.bottom, UH.Space.reading)
            }
            .padding(UH.Space.regular)
        }
    }

    // MARK: - Results View

    private func resultsView(_ plan: GearPlan) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                if let race = plan.matchedRace {
                    matchedRaceChip(race)
                }

                // Header badge
                HStack {
                    Text("RECOMMENDED MATCHES (\(plan.recommendations.count))")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.muted)
                    Spacer()
                }

                // Shoe cards
                ForEach(plan.recommendations) { shoe in
                    ShoeCard(
                        shoe: shoe,
                        isExpanded: expandedShoeId == shoe.id,
                        onToggle: { expandedShoeId = expandedShoeId == shoe.id ? nil : shoe.id },
                        onAssign: { shoeToAssign = shoe }
                    )
                }

                // Tips
                if !plan.tips.isEmpty {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Text("GEAR SPECIALIST TIPS")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .padding(.top, 8)

                        ForEach(Array(plan.tips.enumerated()), id: \.offset) { idx, tip in
                            HStack(alignment: .top, spacing: 12) {
                                Text(String(format: "%02d", idx + 1))
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(UH.Palette.accentInk)
                                    .frame(width: 24, height: 24)
                                    .background(UH.Palette.activeFill, in: Circle())

                                Text(tip)
                                    .font(UH.TextStyle.body)
                                    .foregroundStyle(UH.Palette.ink)
                            }
                            .trainingCard()
                        }
                    }
                }

                // Feedback
                if let token = plan.feedbackToken {
                    feedbackRow(token: token)
                }
            }
            .padding(UH.Space.regular)
        }
    }

    private func feedbackRow(token: String) -> some View {
        HStack {
            Text("Helpful recommendations?")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            Spacer()
            if let sent = feedbackSent {
                Text(sent == 1 ? L("Thanks! 👍") : L("Noted. 👎"))
                    .font(UH.TextStyle.caption.weight(.semibold))
                    .foregroundStyle(UH.Palette.accentInk)
            } else {
                Button {
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    feedbackSent = 1
                    Task { try? await service.sendFeedback(token: token, value: 1) }
                } label: {
                    Image(systemName: "hand.thumbsup").font(.system(size: 16)).foregroundStyle(UH.Palette.ink)
                }
                .buttonStyle(.plain)

                Button {
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    feedbackSent = -1
                    Task { try? await service.sendFeedback(token: token, value: -1) }
                } label: {
                    Image(systemName: "hand.thumbsdown").font(.system(size: 16)).foregroundStyle(UH.Palette.ink)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, UH.Space.small)
        .padding(.top, 12)
    }

    private func matchedRaceChip(_ race: RaceMatch) -> some View {
        let detail = race.distanceLabel.map { label in
            race.elevationGainM.map { L("%@, %lld m D+", label, Int($0)) } ?? label
        }
        return HStack(alignment: .firstTextBaseline, spacing: 8) {
            Image(systemName: "mappin.circle.fill").foregroundStyle(UH.Palette.accentInk)
            (Text("Using ") + Text(race.raceName).bold() + Text(" as context") + Text(detail.map { " — \($0)" } ?? ""))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("gear.matchedRace")
    }

    private func recommend() async {
        isLoading = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        let params = GearParams(
            surface: surface,
            cushioning: cushioning,
            width: width,
            carbonPlate: carbonPlate,
            budget: budget.isEmpty ? nil : budget,
            terrain: surface == "trail" ? Array(terrain) : nil,
            useCase: surface == "road" ? roadUseCase : nil,
            preferredBrands: preferredBrands.isEmpty ? nil : preferredBrands,
            additionalContext: additionalContext.isEmpty ? nil : additionalContext,
            raceDistance: raceDistance.isEmpty ? nil : raceDistance,
            raceName: raceName.trimmingCharacters(in: .whitespaces).isEmpty ? nil : raceName,
            userProfile: GearParams.profileContext(user),
            activePlanContext: GearParams.planContext(activePlan)
        )

        do {
            let res = try await service.recommendShoes(params: params)
            withAnimation(UH.Motion.standard) {
                self.gearPlan = res
            }
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            errorMessage = error.localizedDescription
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
        isLoading = false
    }
}

// MARK: - Assign Shoe Sheet Helper

struct AssignShoeSheet: View {
    @Environment(\.dismiss) private var dismiss
    let shoe: ShoeRecommendation
    let onSave: (ShoeItem) -> Void

    @State private var selectedSlot: ShoeRotationSlot = .daily
    @State private var distanceKm: Double = 0.0

    var body: some View {
        NavigationStack {
            Form {
                Section("SHOE") {
                    Text("\(shoe.brand) \(shoe.model)")
                        .font(UH.TextStyle.body.weight(.bold))
                }

                Section("ASSIGN TO ROTATION SLOT") {
                    Picker("Slot", selection: $selectedSlot) {
                        ForEach(ShoeRotationSlot.allCases) { slot in
                            Text("\(slot.title) (\(slot.subtitle))").tag(slot)
                        }
                    }
                }

                Section("CURRENT DISTANCE LOGGED") {
                    HStack {
                        Text("Logged (km)")
                        Spacer()
                        TextField("0", value: $distanceKm, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                    }
                }
            }
            .navigationTitle("Assign Shoe")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Save") {
                        let item = ShoeItem(
                            slot: selectedSlot,
                            brand: shoe.brand,
                            model: shoe.model,
                            distanceKm: distanceKm
                        )
                        onSave(item)
                        dismiss()
                    }
                    .font(UH.TextStyle.label)
                }
            }
        }
    }
}

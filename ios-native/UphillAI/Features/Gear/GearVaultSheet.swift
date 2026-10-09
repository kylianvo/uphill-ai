import SwiftUI

struct GearVaultSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any GearServicing
    var activePlan: Plan?
    var user: User?
    var isPresentedInSheet: Bool = false
    var onAssignToRotation: ((ShoeItem) -> Void)? = nil

    // Form inputs
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
        isPresentedInSheet: Bool = false,
        onAssignToRotation: ((ShoeItem) -> Void)? = nil,
        initialPlan: GearPlan? = nil
    ) {
        self.service = service
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

                if let plan = activePlan {
                    HStack(spacing: 8) {
                        Image(systemName: "flag.fill")
                            .font(.system(size: 12))
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("Active Race: \(plan.raceName)")
                            .font(UH.TextStyle.caption.weight(.semibold))
                            .foregroundStyle(UH.Palette.ink)
                        Spacer()
                    }
                    .padding(UH.Space.small)
                    .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
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
                                                .foregroundStyle(isSelected ? Color.white : UH.Palette.ink)
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
                                            .foregroundStyle(isSelected ? Color.white : UH.Palette.ink)
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
                            ProgressView().tint(Color.white)
                        } else {
                            Image(systemName: "magnifyingglass")
                            Text("Recommend Shoes")
                        }
                    }
                    .font(UH.TextStyle.label)
                    .foregroundStyle(Color.white)
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
                    shoeCard(shoe)
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

    private func shoeCard(_ shoe: ShoeRecommendation) -> some View {
        let isExpanded = expandedShoeId == shoe.id

        return VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top, spacing: 12) {
                // Studio light-base container
                ZStack {
                    RoundedRectangle(cornerRadius: UH.Radius.control)
                        .fill(UH.Palette.surface)
                        .frame(width: 72, height: 72)
                        .overlay(
                            RoundedRectangle(cornerRadius: UH.Radius.control)
                                .stroke(UH.Palette.line, lineWidth: 1)
                        )

                    let asset = GearImageResolver.assetName(brand: shoe.brand, model: shoe.model)
                    if let uiImage = UIImage(named: asset) {
                        Image(uiImage: uiImage)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 58, height: 58)
                    } else {
                        Image(systemName: "shoe.fill")
                            .font(.system(size: 32))
                            .foregroundStyle(UH.Palette.muted)
                    }
                }

                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Text(shoe.brand.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .tracking(0.6)
                            .foregroundStyle(UH.Palette.accentInk)
                        Spacer()
                        if !shoe.price.isEmpty {
                            Text(shoe.price)
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(UH.Palette.hover, in: Capsule())
                                .foregroundStyle(UH.Palette.ink)
                        }
                    }

                    Text(shoe.model)
                        .font(UH.TextStyle.body.weight(.bold))
                        .foregroundStyle(UH.Palette.ink)

                    if !shoe.weight.isEmpty {
                        Text("Weight: \(shoe.weight)")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            // Specs grid
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    if !shoe.drop.isEmpty {
                        specChip(label: "DROP", value: shoe.drop)
                    }
                    if !shoe.stack.isEmpty {
                        specChip(label: "STACK", value: shoe.stack)
                    }
                    if !shoe.lugDepth.isEmpty && shoe.lugDepth != "0mm" {
                        specChip(label: "LUG", value: shoe.lugDepth)
                    }
                    if !shoe.outsoleCompound.isEmpty {
                        specChip(label: "GRIP", value: shoe.outsoleCompound)
                    }
                    if !shoe.foamMaterial.isEmpty {
                        specChip(label: "FOAM", value: shoe.foamMaterial)
                    }
                }
            }

            // Expanded Pros & Cons
            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    if !shoe.pros.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("PROS")
                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.accentInk)
                            Text(shoe.pros)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if !shoe.cons.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("CONS / TRADE-OFFS")
                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color(hex: "#b45309"))
                            Text(shoe.cons)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(hex: "#f59e0b").opacity(0.12), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    // Assign button
                    Button {
                        shoeToAssign = shoe
                    } label: {
                        HStack {
                            Image(systemName: "plus.circle.fill")
                            Text("Assign to Shoe Rotation")
                        }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                    .buttonStyle(.plain)
                }
            }

            // Expand / Collapse trigger
            Button {
                withAnimation(UH.Motion.standard) {
                    expandedShoeId = isExpanded ? nil : shoe.id
                }
            } label: {
                HStack {
                    Text(isExpanded ? L("Show Less") : L("Details & Pros/Cons"))
                        .font(UH.TextStyle.caption.weight(.semibold))
                        .foregroundStyle(UH.Palette.secondary)
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(UH.Palette.muted)
                }
                .padding(.top, 4)
            }
            .buttonStyle(.plain)
        }
        .trainingCard()
    }

    private func specChip(label: String, value: String) -> some View {
        VStack(spacing: 1) {
            Text(label)
                .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 6))
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(UH.Palette.line, lineWidth: 1))
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
            raceName: activePlan?.raceName
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

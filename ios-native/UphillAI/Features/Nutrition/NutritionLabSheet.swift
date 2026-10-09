import SwiftUI

struct NutritionLabSheet: View {
    @Environment(\.dismiss) private var dismiss
    let service: any NutritionServicing
    var activePlan: Plan?
    var user: User?
    var isPresentedInSheet: Bool = false

    // Form inputs
    @State private var durationHours: Double = 4.0
    @State private var temperature: String = "moderate"
    @State private var selectedFormats: Set<ProductFormat> = [.gel]
    @State private var athleteLevel: String = "Recreational"
    @State private var preferredBrands: String = ""
    @State private var targetCarbsH: Double = 60.0
    @State private var targetSodiumH: Double = 500.0
    @State private var additionalContext: String = ""

    // Output & state
    @State private var plan: NutritionPlan?
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var selectedTab: Tab = .timeline
    @State private var feedbackSent: Int? = nil

    enum Tab: String, CaseIterable, Identifiable {
        case timeline = "Timeline"
        case products = "Products"
        case tips = "Coach's Notes"
        var id: String { rawValue }
    }

    private let quickBrands = ["Maurten", "GU", "Tailwind", "SiS", "Skratch", "Precision"]

    init(
        service: any NutritionServicing,
        activePlan: Plan? = nil,
        user: User? = nil,
        isPresentedInSheet: Bool = false,
        initialPlan: NutritionPlan? = nil,
        initialTab: Tab = .timeline
    ) {
        self.service = service
        self.activePlan = activePlan
        self.user = user
        self.isPresentedInSheet = isPresentedInSheet
        _plan = State(initialValue: initialPlan)
        _selectedTab = State(initialValue: initialTab)
    }

    var body: some View {
        Group {
            if let plan {
                resultsView(plan)
            } else {
                formView
            }
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        .navigationTitle("Nutrition Lab")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if isPresentedInSheet {
                ToolbarItem(placement: .topBarLeading) {
                    if plan != nil {
                        Button {
                            withAnimation(UH.Motion.standard) {
                                self.plan = nil
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
                    .accessibilityIdentifier("nutritionLab.dismiss")
                }
            } else {
                if plan != nil {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("Edit") {
                            withAnimation(UH.Motion.standard) {
                                self.plan = nil
                            }
                        }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.accentInk)
                    }
                }
            }
        }
        .task {
            if let activePlan {
                if let hours = activePlan.targetTimeHours, hours > 0 {
                    durationHours = hours
                } else if let dist = activePlan.courseDistanceKm, dist > 0 {
                    // Rough heuristic if target time not specified: 10km/h trail
                    durationHours = max(1.0, (dist / 8.0).rounded())
                }
            }
        }
    }

    // MARK: - Input Form

    private var formView: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                // Header banner
                VStack(alignment: .leading, spacing: 4) {
                    Text("PRECISION FUELING")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .tracking(0.8)
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("Calculate your race nutrition strategy")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Dial in hourly Carbs and Sodium intake based on duration, temperature, and digestive tolerance.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }

                if let plan = activePlan {
                    HStack(spacing: 8) {
                        Image(systemName: "flag.fill")
                            .font(.system(size: 12))
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("Active Race: \(plan.raceName) (\(plan.courseDistanceKm.map { "\(Int($0))km" } ?? "Target"))")
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

                // Section 1: Duration & Weather
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("ENVIRONMENT & DURATION")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(spacing: UH.Space.regular) {
                        // Duration stepper
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Duration")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Estimated hours on course")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if durationHours > 1.0 {
                                        durationHours = max(1.0, (durationHours * 2 - 1) / 2)
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle.fill")
                                        .font(.system(size: 22))
                                        .foregroundStyle(durationHours > 1.0 ? UH.Palette.ink : UH.Palette.muted.opacity(0.4))
                                }
                                .disabled(durationHours <= 1.0)

                                HStack(spacing: 2) {
                                    TextField("4.0", value: $durationHours, format: .number.precision(.fractionLength(1)))
                                        .keyboardType(.decimalPad)
                                        .multilineTextAlignment(.center)
                                        .font(UH.TextStyle.metric)
                                        .foregroundStyle(UH.Palette.ink)
                                        .frame(width: 44)
                                    Text("h")
                                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                .padding(.horizontal, 6)
                                .padding(.vertical, 4)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                                Button {
                                    if durationHours < 36.0 {
                                        durationHours = min(36.0, (durationHours * 2 + 1) / 2)
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 22))
                                        .foregroundStyle(durationHours < 36.0 ? UH.Palette.accentInk : UH.Palette.muted.opacity(0.4))
                                }
                                .disabled(durationHours >= 36.0)
                            }
                        }

                        Divider()

                        // Temperature
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Weather Temperature")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)

                            Picker("Temperature", selection: $temperature) {
                                Text("Cold (<15°C)").tag("cold")
                                Text("Moderate (15–24°C)").tag("moderate")
                                Text("Hot (>25°C)").tag("hot")
                            }
                            .pickerStyle(.segmented)
                        }

                        Divider()

                        // Athlete level
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Athlete Level")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)

                            Picker("Level", selection: $athleteLevel) {
                                Text("Recreational").tag("Recreational")
                                Text("Competitive").tag("Competitive")
                                Text("Elite").tag("Elite")
                            }
                            .pickerStyle(.segmented)
                        }
                    }
                    .trainingCard()
                }

                // Section 2: Preferred Formats
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("PREFERRED FUEL FORMATS")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        Text("Select all formats you can digest during high intensity:")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)

                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            ForEach(ProductFormat.allCases) { format in
                                let isSelected = selectedFormats.contains(format)
                                Button {
                                    UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    if isSelected {
                                        if selectedFormats.count > 1 {
                                            selectedFormats.remove(format)
                                        }
                                    } else {
                                        selectedFormats.insert(format)
                                    }
                                } label: {
                                    HStack(spacing: 8) {
                                        Image(systemName: format.symbolFallback)
                                            .font(.system(size: 14))
                                        Text(format.displayName)
                                            .font(UH.TextStyle.label)
                                        Spacer()
                                        if isSelected {
                                            Image(systemName: "checkmark")
                                                .font(.system(size: 12, weight: .bold))
                                        }
                                    }
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 10)
                                    .foregroundStyle(isSelected ? UH.Palette.accentInk : UH.Palette.ink)
                                    .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                    .overlay(
                                        RoundedRectangle(cornerRadius: UH.Radius.control)
                                            .stroke(isSelected ? UH.Palette.accentInk : UH.Palette.line, lineWidth: isSelected ? 1.5 : 1)
                                    )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                    .trainingCard()
                }

                // Section 3: Target Macros
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("HOURLY TARGETS (HOURLY INTAKE)")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(spacing: UH.Space.regular) {
                        // Carbs stepper
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Carbs per hour")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Gut training baseline: 60g")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if targetCarbsH > 30 {
                                        targetCarbsH -= 10
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }

                                HStack(spacing: 2) {
                                    TextField("60", value: $targetCarbsH, format: .number)
                                        .keyboardType(.numberPad)
                                        .multilineTextAlignment(.center)
                                        .font(UH.TextStyle.metric)
                                        .foregroundStyle(UH.Palette.ink)
                                        .frame(width: 44)
                                    Text("g/h")
                                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                .padding(.horizontal, 6)
                                .padding(.vertical, 4)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                                Button {
                                    if targetCarbsH < 120 {
                                        targetCarbsH += 10
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "plus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                            }
                        }

                        Divider()

                        // Sodium stepper
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Sodium per hour")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.ink)
                                Text("Hydration balance: 500mg")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if targetSodiumH > 200 {
                                        targetSodiumH -= 50
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle")
                                        .font(.system(size: 20))
                                        .foregroundStyle(UH.Palette.ink)
                                }

                                HStack(spacing: 2) {
                                    TextField("500", value: $targetSodiumH, format: .number)
                                        .keyboardType(.numberPad)
                                        .multilineTextAlignment(.center)
                                        .font(UH.TextStyle.metric)
                                        .foregroundStyle(UH.Palette.ink)
                                        .frame(width: 48)
                                    Text("mg/h")
                                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                .padding(.horizontal, 6)
                                .padding(.vertical, 4)
                                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                                Button {
                                    if targetSodiumH < 1200 {
                                        targetSodiumH += 50
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
                    .trainingCard()
                }

                // Section 4: Brand preferences & Notes
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("BRAND PREFERENCES")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)

                    VStack(alignment: .leading, spacing: 10) {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(quickBrands, id: \.self) { brand in
                                    let isSelected = preferredBrands.localizedCaseInsensitiveContains(brand)
                                    Button {
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                        if isSelected {
                                            preferredBrands = preferredBrands.replacingOccurrences(of: brand, with: "")
                                                .trimmingCharacters(in: .whitespacesAndNewlines)
                                        } else {
                                            preferredBrands = preferredBrands.isEmpty ? brand : "\(preferredBrands), \(brand)"
                                        }
                                    } label: {
                                        Text(brand)
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

                        TextField("Other brands or custom request", text: $preferredBrands)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))

                        TextField("Digestive notes (e.g. caffeine sensitive, easily bloated)", text: $additionalContext)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                    }
                    .trainingCard()
                }

                // CTA Button
                Button {
                    Task { await calculate() }
                } label: {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .tint(Color.white)
                        } else {
                            Image(systemName: "bolt.batteryblock.fill")
                            Text("Calculate Fueling Plan")
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

    private func resultsView(_ plan: NutritionPlan) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                // Top Metrics Cards
                VStack(spacing: 8) {
                    HStack(spacing: 8) {
                        metricBox(title: L("TOTAL CARBS"), value: "\(Int(plan.totalCarbs))g", sub: "\(Int(plan.avgCarbsPerHour)) g/h")
                        metricBox(title: L("TOTAL SODIUM"), value: "\(Int(plan.totalSodium))mg", sub: "\(Int(plan.avgSodiumPerHour)) mg/h")
                        metricBox(title: L("DURATION"), value: String(format: "%.1fh", durationHours), sub: L("%lld hours", plan.hourlyPlan.count))
                    }
                }

                // Tab Switcher
                Picker("View", selection: $selectedTab) {
                    ForEach(Tab.allCases) { tab in
                        Text(tab.rawValue).tag(tab)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.vertical, 4)

                // Tab Content
                switch selectedTab {
                case .timeline:
                    timelineTab(plan)
                case .products:
                    productsTab(plan)
                case .tips:
                    tipsTab(plan)
                }

                // Feedback section
                feedbackSection(plan)
            }
            .padding(UH.Space.regular)
        }
    }

    private func metricBox(title: String, value: String, sub: String) -> some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                .tracking(0.5)
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(UH.TextStyle.metric)
                .foregroundStyle(UH.Palette.ink)
            Text(sub)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(UH.Palette.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .trainingCard(padding: 6, radius: UH.Radius.control)
    }

    // MARK: - Timeline Tab (Maurten Style)

    private func timelineTab(_ plan: NutritionPlan) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("HOURLY RACE TIMELINE")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
                .padding(.bottom, 12)

            ForEach(plan.hourlyPlan) { entry in
                HStack(alignment: .top, spacing: 14) {
                    // Left rail: node + line
                    VStack(spacing: 0) {
                        ZStack {
                            Circle()
                                .fill(UH.Palette.ink)
                                .frame(width: 32, height: 32)
                            Text("H\(entry.hour)")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color.white)
                        }

                        if entry.hour != plan.hourlyPlan.last?.hour {
                            Rectangle()
                                .fill(UH.Palette.line)
                                .frame(width: 2)
                                .frame(minHeight: 48)
                        }
                    }

                    // Content card
                    VStack(alignment: .leading, spacing: 6) {
                        Text(entry.action)
                            .font(UH.TextStyle.body.weight(.semibold))
                            .foregroundStyle(UH.Palette.ink)

                        HStack(spacing: 12) {
                            HStack(spacing: 4) {
                                Circle().fill(Color(hex: "#f59e0b")).frame(width: 6, height: 6)
                                Text("\(Int(entry.carbs))g carbs")
                                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }

                            HStack(spacing: 4) {
                                Circle().fill(Color(hex: "#0ea5e9")).frame(width: 6, height: 6)
                                Text("\(Int(entry.sodium))mg sodium")
                                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                        }
                    }
                    .padding(UH.Space.small)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
                    .padding(.bottom, 10)
                }
            }
        }
    }

    // MARK: - Products Tab (Gotcha Style)

    private func productsTab(_ plan: NutritionPlan) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("PACKING LIST & PRODUCTS")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            ForEach(plan.products) { product in
                productCard(product)
            }
        }
    }

    private func productCard(_ product: NutritionProduct) -> some View {
        HStack(alignment: .top, spacing: 14) {
            // Product image preview (Clean light-base studio presentation)
            ZStack {
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .fill(UH.Palette.surface)
                    .frame(width: 68, height: 68)
                    .overlay(
                        RoundedRectangle(cornerRadius: UH.Radius.control)
                            .stroke(UH.Palette.line, lineWidth: 1)
                    )

                let asset = NutritionImageResolver.assetName(brand: product.brand, name: product.name, format: product.format)
                if let uiImage = UIImage(named: asset) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 54, height: 54)
                } else {
                    Image(systemName: product.format.symbolFallback)
                        .font(.system(size: 24))
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(product.brand.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .tracking(0.6)
                        .foregroundStyle(UH.Palette.accentInk)
                    Spacer()
                    Text("Qty: \(product.totalQuantity)")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(UH.Palette.activeFill, in: Capsule())
                        .foregroundStyle(UH.Palette.ink)
                }

                Text(product.name)
                    .font(UH.TextStyle.body.weight(.semibold))
                    .foregroundStyle(UH.Palette.ink)

                if !product.techNotes.isEmpty {
                    Text(product.techNotes)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .lineLimit(2)
                }

                // Macro pill indicators
                HStack(spacing: 8) {
                    macroBadge(label: "C", value: "\(Int(product.carbsPerUnit))g", color: Color(hex: "#f59e0b"))
                    macroBadge(label: "Na", value: "\(Int(product.sodiumPerUnit))mg", color: Color(hex: "#0ea5e9"))
                    if product.proteinPerUnit > 0 {
                        macroBadge(label: "P", value: "\(Int(product.proteinPerUnit))g", color: Color(hex: "#10b981"))
                    }
                }
                .padding(.top, 2)
            }
        }
        .trainingCard()
    }

    private func macroBadge(label: String, value: String, color: Color) -> some View {
        HStack(spacing: 3) {
            Text(label)
                .font(.system(size: 9, weight: .heavy, design: .monospaced))
                .foregroundStyle(color)
            Text(value)
                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(color.opacity(0.12), in: RoundedRectangle(cornerRadius: 4))
    }

    // MARK: - Tips Tab

    private func tipsTab(_ plan: NutritionPlan) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text("COACH'S FUELING PROTOCOLS")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            ForEach(Array(plan.tips.enumerated()), id: \.offset) { index, tip in
                HStack(alignment: .top, spacing: 12) {
                    Text(String(format: "%02d", index + 1))
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

    // MARK: - Feedback Section

    private func feedbackSection(_ plan: NutritionPlan) -> some View {
        VStack(spacing: 12) {
            if let token = plan.feedbackToken {
                Divider()
                HStack {
                    Text("Was this fueling plan helpful?")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                    Spacer()
                    if let sent = feedbackSent {
                        Text(sent == 1 ? L("Thanks for feedback! 👍") : L("Noted. We'll improve! 👎"))
                            .font(UH.TextStyle.caption.weight(.semibold))
                            .foregroundStyle(UH.Palette.accentInk)
                    } else {
                        Button {
                            sendFeedback(token: token, value: 1)
                        } label: {
                            Image(systemName: "hand.thumbsup")
                                .font(.system(size: 16))
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .buttonStyle(.plain)

                        Button {
                            sendFeedback(token: token, value: -1)
                        } label: {
                            Image(systemName: "hand.thumbsdown")
                                .font(.system(size: 16))
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, UH.Space.small)
            }
        }
        .padding(.vertical, UH.Space.regular)
    }

    private func sendFeedback(token: String, value: Int) {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        feedbackSent = value
        Task {
            try? await service.sendFeedback(token: token, value: value)
        }
    }

    // MARK: - API Action

    private func calculate() async {
        isLoading = true
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        let formats = selectedFormats.map { $0.rawValue }
        var activePlanStr: String? = nil
        if let p = activePlan {
            activePlanStr = "\(p.raceName) on \(p.raceDate), Goal: \(p.goalType), Distance: \(p.courseDistanceKm ?? 0)km"
        }
        var userStr: String? = nil
        if let u = user {
            userStr = "Age: \(u.age ?? 0), Max HR: \(u.maxHr ?? 0), Resting HR: \(u.restingHr ?? 0)"
        }

        let params = NutritionParams(
            distanceKm: activePlan?.courseDistanceKm,
            elevationGainM: activePlan?.courseElevationGainM,
            targetTimeHours: durationHours,
            weatherTemp: temperature,
            preferredBrands: preferredBrands.isEmpty ? nil : preferredBrands,
            targetCarbH: targetCarbsH,
            targetSodiumH: targetSodiumH,
            preferredFormat: formats,
            athleteLevel: athleteLevel,
            additionalContext: additionalContext.isEmpty ? nil : additionalContext,
            userProfile: userStr,
            activePlanContext: activePlanStr
        )

        do {
            let res = try await service.calculateFueling(params: params)
            withAnimation(UH.Motion.standard) {
                self.plan = res
                self.selectedTab = .timeline
            }
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        } catch {
            errorMessage = error.localizedDescription
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
        isLoading = false
    }
}

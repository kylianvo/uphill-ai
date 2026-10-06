import SwiftUI

/// Redesigned visual layer for athlete profile & zone settings.
/// Uses custom training cards (radius 16, soft border, off-white surface).
struct ProfileSettingsScreen: View {
    @State private var model: ProfileSettingsModel
    @State private var showGuide = false

    init(app: AppModel, section: TrainingDestination, preloadedModel: ProfileSettingsModel? = nil) {
        if let preloadedModel {
            _model = State(initialValue: preloadedModel)
        } else {
            _model = State(initialValue: ProfileSettingsModel(user: app.session.user!, section: section,
                service: ProfileService(client: app.client), session: app.session,
                isOffline: { app.isOffline || app.plan.cachedAt != nil }))
        }
    }

    private var title: String {
        switch model.section {
        case .aboutYou: "About you"
        case .trainingZones, .heartRate, .paces: "Training zones"
        case .schedule: "Schedule"
        case .raceHistory: "Race History"
        case .nutritionLab: "Nutrition Lab"
        case .gearVault: "Gear Vault"
        case .goalDeterminer: "Goal Determiner"
        case .paceStrategy: "Pace Strategy"
        case .knowledgeHub: "Knowledge Hub"
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                switch model.section {
                case .aboutYou:
                    aboutYouContent
                case .trainingZones, .heartRate, .paces:
                    trainingZonesSegmentedContent
                case .schedule, .raceHistory, .nutritionLab, .gearVault, .goalDeterminer, .paceStrategy, .knowledgeHub:
                    EmptyView()
                }

                saveSection
            }
            .padding(UH.Space.regular)
            .padding(.bottom, 72)
        }
        .background(UH.Palette.surface)
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
        .tint(UH.Palette.accentInk)
        .sheet(isPresented: $showGuide) { WatchZonesGuideSheet() }
        .task(id: model.draft.paceZoneModel) {
            if model.section == .paces || model.section == .trainingZones { await model.loadZones() }
        }
        .task(id: model.selectedZoneTab) {
            if (model.section == .paces || model.section == .trainingZones) && model.selectedZoneTab == .paces && model.zones == nil {
                await model.loadZones()
            }
        }
    }

    // MARK: - Training Zones (Segmented)

    private var trainingZonesSegmentedContent: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            Picker("Zone Category", selection: $model.selectedZoneTab) {
                ForEach(ProfileSettingsModel.ZoneTab.allCases) { tab in
                    Text(tab.rawValue).tag(tab)
                }
            }
            .pickerStyle(.segmented)

            switch model.selectedZoneTab {
            case .heartRate:
                heartRateContent
            case .paces:
                pacesContent
            }
        }
    }

    // MARK: - About You

    private var aboutYouContent: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Athlete Profile").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                Text("Calibrates calorie expenditure, pacing models, and recovery rates.")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)

                stepperRow("Age", value: $model.draft.age, inRange: 15...99, unit: "years")
                Divider()

                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text("Sex").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                        sexOption("Female", symbol: "figure.run", tag: "female")
                        sexOption("Male", symbol: "figure.run", tag: "male")
                        sexOption("Other", symbol: "person.fill", tag: "other")
                        sexOption("Private", symbol: "person.crop.circle", tag: nil)
                    }
                }
                Divider()

                optionalStepperRow("Height", value: $model.draft.heightCm, inRange: 120...230, unit: "cm")
                Divider()

                optionalStepperRow("Weight", value: $model.draft.weightKg, inRange: 35...180, unit: "kg")
            }
            .trainingCard()

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Injuries and notes for Coach Uphill").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                Text("Mention past injuries, current niggles, or training constraints.")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                TextField("e.g. runner's knee, IT band tightness, recent ankle sprain...", text: text($model.draft.athleteNotes), axis: .vertical)
                    .lineLimit(3...8)
                    .padding(UH.Space.small)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
            }
            .trainingCard()
        }
    }

    private func sexOption(_ label: String, symbol: String, tag: String?) -> some View {
        let isSelected = model.draft.gender == tag
        return Button {
            model.draft.gender = tag
        } label: {
            HStack(spacing: 8) {
                Image(systemName: symbol)
                    .font(.subheadline)
                    .foregroundStyle(isSelected ? UH.Palette.buttonInk : UH.Palette.accentInk)
                Text(label)
                    .font(UH.TextStyle.label)
                    .foregroundStyle(isSelected ? UH.Palette.buttonInk : UH.Palette.ink)
                Spacer(minLength: 0)
                if isSelected {
                    Image(systemName: "checkmark").font(.caption.weight(.bold)).foregroundStyle(UH.Palette.buttonInk)
                }
            }
            .padding(.horizontal, 12)
            .frame(maxWidth: .infinity, minHeight: 44)
            .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    // MARK: - Heart Rate

    private var heartRateContent: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            // Spectrum card with horizontal band
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Heart Rate Spectrum").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                Text("Visualizing your aerobic (AeT) and anaerobic (AnT) thresholds from resting to max.")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)

                heartRateBand

                // Chips summary
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                    statChip(title: "RESTING", value: "\(model.draft.restingHr) bpm", color: Color(hex: "#0ea5e9"))
                    statChip(title: "AEROBIC (AeT)", value: "\(model.draft.aetHr) bpm", color: Color(hex: "#10b981"))
                    statChip(title: "ANAEROBIC (AnT)", value: "\(model.draft.antHr) bpm", color: Color(hex: "#f97316"))
                    statChip(title: "MAX HR", value: "\(model.draft.maxHr) bpm", color: Color(hex: "#ef4444"))
                }
            }
            .trainingCard()

            // Number inputs
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Heart rate anchors").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)

                stepperRow("Max heart rate", value: $model.draft.maxHr, inRange: 120...240, unit: "bpm")
                Divider()
                stepperRow("Resting heart rate", value: $model.draft.restingHr, inRange: 30...110, unit: "bpm")
                Divider()
                stepperRow("Aerobic threshold (AeT)", value: $model.draft.aetHr, inRange: 90...190, unit: "bpm")
                Divider()
                stepperRow("Anaerobic threshold (AnT)", value: $model.draft.antHr, inRange: 120...220, unit: "bpm")
            }
            .trainingCard()

            // Watch guide button
            Button {
                showGuide = true
            } label: {
                HStack(spacing: UH.Space.small) {
                    Image(systemName: "questionmark.circle.fill")
                        .font(.title3)
                        .foregroundStyle(UH.Palette.accentInk)
                    VStack(alignment: .leading, spacing: 2) {
                        Text("How to find your zones").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        Text("Step-by-step instructions for Garmin, COROS & Apple Watch").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                    Spacer()
                    Image(systemName: "chevron.right").font(.footnote.weight(.semibold)).foregroundStyle(UH.Palette.muted)
                }
                .frame(minHeight: 44)
            }
            .buttonStyle(.plain)
            .trainingCard()
        }
    }

    private var heartRateBand: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let r = CGFloat(model.draft.restingHr)
            let m = CGFloat(max(model.draft.maxHr, model.draft.restingHr + 20))
            let span = max(1.0, m - r)
            let aetFrac = min(max(0.12, (CGFloat(model.draft.aetHr) - r) / span), 0.88)
            let antFrac = min(max(0.20, (CGFloat(model.draft.antHr) - r) / span), 0.95)

            VStack(spacing: 6) {
                // Marker labels above band
                ZStack(alignment: .leading) {
                    Text("AeT \(model.draft.aetHr)")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(Color(hex: "#10b981"))
                        .offset(x: max(0, min(w - 60, aetFrac * w - 24)))

                    Text("AnT \(model.draft.antHr)")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(Color(hex: "#f97316"))
                        .offset(x: max(0, min(w - 60, antFrac * w - 24)))
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(height: 16)

                // The colored spectrum band
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(LinearGradient(
                            colors: [Color(hex: "#0ea5e9"), Color(hex: "#10b981"), Color(hex: "#f59e0b"), Color(hex: "#f97316"), Color(hex: "#ef4444")],
                            startPoint: .leading,
                            endPoint: .trailing
                        ))
                        .frame(height: 16)

                    // AeT tick
                    Rectangle()
                        .fill(Color.white)
                        .frame(width: 3, height: 16)
                        .shadow(color: .black.opacity(0.3), radius: 1)
                        .offset(x: aetFrac * w)

                    // AnT tick
                    Rectangle()
                        .fill(Color.white)
                        .frame(width: 3, height: 16)
                        .shadow(color: .black.opacity(0.3), radius: 1)
                        .offset(x: antFrac * w)
                }

                // Range baseline
                HStack {
                    Text("Resting \(model.draft.restingHr) bpm")
                        .font(UH.TextStyle.caption.monospacedDigit())
                        .foregroundStyle(UH.Palette.secondary)
                    Spacer()
                    Text("Max \(model.draft.maxHr) bpm")
                        .font(UH.TextStyle.caption.monospacedDigit())
                        .foregroundStyle(UH.Palette.secondary)
                }
            }
        }
        .frame(height: 62)
    }

    private func statChip(title: String, value: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 4) {
                Circle().fill(color).frame(width: 6, height: 6)
                Text(title).font(.system(size: 10, weight: .bold)).foregroundStyle(UH.Palette.secondary)
            }
            Text(value).font(.system(size: 15, weight: .bold, design: .monospaced)).foregroundStyle(UH.Palette.ink)
        }
        .padding(8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
    }

    // MARK: - Paces

    private var pacesContent: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            // Hero card: Your easy pace
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("YOUR EASY PACE").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.accentInk)
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(easyPaceString)
                        .font(.system(.title, design: .monospaced).weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                    Text("/km")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.secondary)
                }
                Text("Most of your running happens here. Conversational aerobic effort that builds stamina without accumulating excess fatigue.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .trainingCard()

            // Zone ladder card
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                ViewThatFits(in: .horizontal) {
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Training Zones").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                            Text("Calibrated from your threshold & fitness profile").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        Spacer()
                        Picker("Zone model", selection: $model.draft.paceZoneModel) {
                            Text("5 zones").tag("5_zone")
                            Text("4 zones").tag("4_zone")
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 160)
                    }
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Training Zones").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                        Picker("Zone model", selection: $model.draft.paceZoneModel) {
                            Text("5 zones").tag("5_zone")
                            Text("4 zones").tag("4_zone")
                        }
                        .pickerStyle(.segmented)
                    }
                }

                if let zones = model.zones {
                    VStack(spacing: UH.Space.regular) {
                        ForEach(zones.rows) { row in
                            zoneRow(row, total: zones.rows.count)
                            if row.id < zones.rows.count {
                                Divider()
                            }
                        }
                    }
                } else {
                    ProgressView().frame(maxWidth: .infinity, minHeight: 120)
                }
            }
            .trainingCard()

            // Adjust card
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Adjust").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                    Text("Fine-tune your training anchors. Your next week adapts automatically.")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }

                paceField("Threshold pace", value: $model.draft.thresholdPace, hint: "m:ss")
                Divider()
                paceField("Easy pace, slower end", value: $model.draft.zone2PaceMin, hint: "m:ss")
                Divider()
                paceField("Easy pace, faster end", value: $model.draft.zone2PaceMax, hint: "m:ss")
            }
            .trainingCard()
        }
    }

    private var easyPaceString: String {
        if let z2 = model.zones?.zone2Pace { return z2 }
        if let min = model.draft.zone2PaceMin, let max = model.draft.zone2PaceMax {
            return "\(min) - \(max)"
        }
        return "6:30 - 5:45"
    }

    private func zoneRow(_ row: PaceZoneRow, total: Int) -> some View {
        let meta = zoneMeta(id: row.id, total: total)
        let barRatio = CGFloat(row.id) / CGFloat(max(1, total))

        return VStack(alignment: .leading, spacing: 6) {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .firstTextBaseline) {
                    HStack(spacing: 6) {
                        Circle().fill(meta.color).frame(width: 8, height: 8)
                        Text(meta.name).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    }
                    Spacer()
                    Text("\(row.pace) /km")
                        .font(.system(.subheadline, design: .monospaced).weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                }
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 6) {
                        Circle().fill(meta.color).frame(width: 8, height: 8)
                        Text(meta.name).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    }
                    Text("\(row.pace) /km")
                        .font(.system(.subheadline, design: .monospaced).weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                }
            }

            // Coloured visual bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(UH.Palette.surface).frame(height: 6)
                    Capsule().fill(meta.color).frame(width: max(28, geo.size.width * barRatio), height: 6)
                }
            }
            .frame(height: 6)

            HStack {
                Text(meta.purpose).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                Spacer()
                if let hr = row.hr {
                    Text(hr).font(UH.TextStyle.caption.monospacedDigit()).foregroundStyle(UH.Palette.muted)
                }
            }
        }
        .padding(.vertical, 2)
    }

    private struct ZoneMeta {
        let name: String
        let purpose: String
        let color: Color
    }

    private func zoneMeta(id: Int, total: Int) -> ZoneMeta {
        if total == 4 {
            switch id {
            case 1: return ZoneMeta(name: "Zone 1 · Recovery", purpose: "Easy recovery runs (< AeT)", color: Color(hex: "#0ea5e9"))
            case 2: return ZoneMeta(name: "Zone 2 · Aerobic Base", purpose: "Aerobic capacity (AeT-AnT)", color: Color(hex: "#10b981"))
            case 3: return ZoneMeta(name: "Zone 3 · Threshold", purpose: "Lactate threshold (AnT)", color: Color(hex: "#f97316"))
            default: return ZoneMeta(name: "Zone 4 · Anaerobic / Max", purpose: "Maximum anaerobic power (> AnT)", color: Color(hex: "#ef4444"))
            }
        } else {
            switch id {
            case 1: return ZoneMeta(name: "Zone 1 · Recovery", purpose: "Active recovery & warm-ups", color: Color(hex: "#0ea5e9"))
            case 2: return ZoneMeta(name: "Zone 2 · Easy / Aerobic", purpose: "Aerobic base; conversational effort", color: Color(hex: "#10b981"))
            case 3: return ZoneMeta(name: "Zone 3 · Tempo", purpose: "Steady rhythm for trail climbing", color: Color(hex: "#f59e0b"))
            case 4: return ZoneMeta(name: "Zone 4 · Threshold", purpose: "Lactate threshold; ~1 hour race pace", color: Color(hex: "#f97316"))
            default: return ZoneMeta(name: "Zone 5 · VO2max / Speed", purpose: "Short intervals & steep climbs", color: Color(hex: "#ef4444"))
            }
        }
    }

    // MARK: - Save Section

    private var saveSection: some View {
        VStack(spacing: UH.Space.small) {
            if let error = model.error {
                Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger).accessibilityAddTraits(.updatesFrequently)
            }
            if model.saved {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill").foregroundStyle(UH.Palette.accentInk)
                    Text("Saved. Your next week will use these.").font(UH.TextStyle.label).foregroundStyle(UH.Palette.accentInk)
                }
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 4)
            }
            Button {
                Task { await model.save() }
            } label: {
                if model.isSaving {
                    ProgressView().tint(.white)
                } else {
                    Text("Save")
                }
            }
            .buttonStyle(.uhPrimary)
            .disabled(model.isSaving)
        }
        .padding(.top, UH.Space.small)
    }

    // MARK: - Form Helpers

    private func text(_ value: Binding<String?>) -> Binding<String> {
        Binding(get: { value.wrappedValue ?? "" }, set: { value.wrappedValue = $0 })
    }

    private func paceField(_ title: String, value: Binding<String?>, hint: String) -> some View {
        HStack {
            Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            Spacer()
            HStack(spacing: 4) {
                TextField(hint, text: text(value))
                    .multilineTextAlignment(.trailing)
                    .font(.system(.body, design: .monospaced))
                    .keyboardType(.numbersAndPunctuation)
                    .frame(width: 80)
                Text("/km").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
        }
        .frame(minHeight: 44)
    }

    private func stepperRow(_ title: String, value: Binding<Int>, inRange: ClosedRange<Int>, unit: String) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text("\(inRange.lowerBound)–\(inRange.upperBound) \(unit)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
            }
            Spacer()
            HStack(spacing: 8) {
                Button {
                    if value.wrappedValue > inRange.lowerBound {
                        value.wrappedValue -= 1
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    }
                } label: {
                    Image(systemName: "minus.circle")
                        .font(.system(size: 20))
                        .foregroundStyle(UH.Palette.ink)
                }

                HStack(spacing: 2) {
                    TextField("\(value.wrappedValue)", value: value, format: .number)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(.system(.subheadline, design: .monospaced).weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                        .frame(width: 48)
                    Text(unit)
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.horizontal, 6)
                .padding(.vertical, 5)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))

                Button {
                    if value.wrappedValue < inRange.upperBound {
                        value.wrappedValue += 1
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    }
                } label: {
                    Image(systemName: "plus.circle")
                        .font(.system(size: 20))
                        .foregroundStyle(UH.Palette.ink)
                }
            }
        }
        .frame(minHeight: 48)
    }

    private func optionalStepperRow(_ title: String, value: Binding<Double?>, inRange: ClosedRange<Double>, unit: String) -> some View {
        let binding = Binding<Double>(
            get: { value.wrappedValue ?? inRange.lowerBound },
            set: { value.wrappedValue = $0 }
        )
        return HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text("\(Int(inRange.lowerBound))–\(Int(inRange.upperBound)) \(unit)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
            }
            Spacer()
            HStack(spacing: 8) {
                Button {
                    if binding.wrappedValue > inRange.lowerBound {
                        binding.wrappedValue -= 1
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    }
                } label: {
                    Image(systemName: "minus.circle")
                        .font(.system(size: 20))
                        .foregroundStyle(UH.Palette.ink)
                }

                HStack(spacing: 2) {
                    TextField("0", value: binding, format: .number)
                        .keyboardType(.numberPad)
                        .multilineTextAlignment(.center)
                        .font(.system(.subheadline, design: .monospaced).weight(.bold))
                        .foregroundStyle(UH.Palette.ink)
                        .frame(width: 48)
                    Text(unit)
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.horizontal, 6)
                .padding(.vertical, 5)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))

                Button {
                    if binding.wrappedValue < inRange.upperBound {
                        binding.wrappedValue += 1
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    }
                } label: {
                    Image(systemName: "plus.circle")
                        .font(.system(size: 20))
                        .foregroundStyle(UH.Palette.ink)
                }
            }
        }
        .frame(minHeight: 48)
    }
}

struct ChangePasswordScreen: View {
    let app: AppModel
    @State private var password = ""
    @State private var confirmation = ""
    @State private var message: String?
    @State private var saving = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    Text("Set New Password").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                    Text("Choose a password with at least 8 characters.").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)

                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("New Password").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        SecureField("Min 8 characters", text: $password)
                            .textContentType(.newPassword)
                            .padding(UH.Space.small)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                    }

                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Confirm New Password").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        SecureField("Confirm password", text: $confirmation)
                            .textContentType(.newPassword)
                            .padding(UH.Space.small)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                    }
                }
                .trainingCard()

                VStack(spacing: UH.Space.small) {
                    if let message {
                        Text(message)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(message.contains("successfully") ? UH.Palette.accentInk : UH.Palette.danger)
                    }

                    Button {
                        Task { await save() }
                    } label: {
                        if saving { ProgressView().tint(.white) } else { Text("Change password") }
                    }
                    .buttonStyle(.uhPrimary)
                    .disabled(saving)
                }
            }
            .padding(UH.Space.regular)
            .padding(.bottom, 72)
        }
        .background(UH.Palette.surface)
        .navigationTitle("Change password")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func save() async {
        if app.isOffline || app.plan.cachedAt != nil { message = PlanViewModel.offlineMessage; return }
        guard password == confirmation else { message = "Passwords do not match."; return }
        guard password.count >= 8 else { message = "Password must be at least 8 characters."; return }
        saving = true
        defer { saving = false }
        do {
            try await ProfileService(client: app.client).changePassword(password)
            password = ""; confirmation = ""
            message = "Password updated successfully."
        } catch let e as APIError { message = e.userMessage }
        catch { message = error.localizedDescription }
    }
}

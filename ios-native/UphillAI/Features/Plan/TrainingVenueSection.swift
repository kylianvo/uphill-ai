import SwiftUI

/// Trail access uses the existing place/day fields; no separate persisted flag is needed.
struct TrainingVenueSection: View {
    @Binding var mountainDays: Set<Weekday>
    @Binding var trainingMountain: String?
    @Binding var mountainMinMinutes: Int?
    @Binding var stairAccess: Bool
    @Binding var useTreadmill: Bool
    var treadmillMaxIncline: Binding<Int>?
    @State private var mountains: [TrainingMountain] = []
    @State private var loadError = false
    @State private var loadAttempt = 0
    @State private var access: Bool?
    @State private var choseOther = false
    @State private var showDuration = false

    static let inclines = [15, 20, 25]

    private var hasAccess: Bool? {
        access ?? ((trainingMountain != nil || !mountainDays.isEmpty) ? true : nil)
    }
    private var hasLocation: Bool { trainingMountain != nil || !mountainDays.isEmpty || choseOther }
    private var mountain: TrainingMountain? { mountains.first { $0.key == trainingMountain } }
    private var minimum: Int? {
        if let mountainMinMinutes, mountainMinMinutes != 0 { return mountainMinMinutes }
        return mountain?.defaultMinMinutes
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            Text("Trail training").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
            VStack(alignment: .leading, spacing: UH.Space.small) {
                stepTitle(1, "Can you get out to train on Trail?")
                HStack(spacing: UH.Space.compact) {
                    accessButton(true, "Yes")
                    accessButton(false, "Not right now")
                }
            }

            if hasAccess == true {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    stepTitle(2, "Where do you usually train?")
                    Picker("Where do you usually train?", selection: Binding(
                        get: { trainingMountain ?? (hasLocation ? "other" : "") },
                        set: { key in
                            guard !key.isEmpty else { return }
                            let selected = mountains.first { $0.key == key }
                            choseOther = key == "other"
                            trainingMountain = selected?.key
                            mountainMinMinutes = selected?.defaultMinMinutes
                        }
                    )) {
                        if !hasLocation { Text("Choose a place").tag("") }
                        if let trainingMountain, mountain == nil { Text("Saved Trail location").tag(trainingMountain) }
                        ForEach(mountains) { mountain in
                            Text(AppLanguage.current == .vi ? mountain.nameVi : mountain.nameEn).tag(mountain.key)
                        }
                        Text("Somewhere else").tag("other")
                    }
                    .labelsHidden()
                    .frame(minHeight: 44, alignment: .leading)
                    .tint(UH.Palette.accentInk)
                    .accessibilityIdentifier("trail.location")
                    if loadError {
                        Text("Mountains unavailable").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        Button("Retry locations") { loadAttempt += 1 }
                            .frame(minHeight: 44).tint(UH.Palette.accentInk)
                    }
                }

                if hasLocation {
                    VStack(alignment: .leading, spacing: UH.Space.small) {
                        stepTitle(3, "Which days can you get there?")
                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 44))], spacing: UH.Space.compact) {
                            ForEach(Weekday.allCases) { day in
                                let isSelected = mountainDays.contains(day)
                                Button {
                                    if isSelected { mountainDays.remove(day) } else { mountainDays.insert(day) }
                                } label: {
                                    Text(L(day.short))
                                        .font(UH.TextStyle.label)
                                        .frame(maxWidth: .infinity, minHeight: 44)
                                        .foregroundStyle(UH.Palette.ink)
                                        .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface,
                                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control)
                                            .stroke(isSelected ? UH.Palette.accentInk : UH.Palette.line, lineWidth: 1))
                                }
                                .buttonStyle(.plain)
                                .accessibilityLabel(L("%@ trail training day", L(day.rawValue)))
                                .accessibilityIdentifier("trail.day.\(day.rawValue)")
                                .accessibilityAddTraits(isSelected ? .isSelected : [])
                            }
                        }
                        Text("Coach will schedule Trail sessions on these days.")
                            .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }

                    Divider()
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Coach plans the session duration").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        if let minimum {
                            Text(L("Minimum Long Run duration: %lld min", minimum))
                                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        DisclosureGroup(isExpanded: $showDuration) {
                            VStack(alignment: .leading, spacing: UH.Space.small) {
                                HStack {
                                    Text("Minimum duration (min)").font(UH.TextStyle.label)
                                    Spacer()
                                    TextField("Minimum duration (min)", value: $mountainMinMinutes, format: .number)
                                        .keyboardType(.numberPad)
                                        .multilineTextAlignment(.trailing)
                                        .frame(width: 90, height: 44)
                                        .accessibilityIdentifier("mountain.minimum")
                                }
                                Text("For Long Runs on Trail days only. This is a minimum, not the maximum time you have available.")
                                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                    .fixedSize(horizontal: false, vertical: true)
                                Button("Use location default") {
                                    mountainMinMinutes = mountain?.defaultMinMinutes
                                    showDuration = false
                                }
                                .frame(minHeight: 44)
                            }
                            .padding(.top, UH.Space.small)
                        } label: {
                            Text("Duration settings").font(UH.TextStyle.label)
                        }
                        .tint(UH.Palette.accentInk)
                    }
                }
            }

            Divider()
            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text("Alternative training").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                Toggle("I can use stairs (fire stairs or a Stairmaster)", isOn: $stairAccess)
                Toggle("I can use a treadmill", isOn: $useTreadmill)
                if let treadmillMaxIncline, useTreadmill {
                    Text("Treadmill max incline").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Picker("Treadmill max incline", selection: Binding(
                        get: { Self.inclines.last(where: { $0 <= treadmillMaxIncline.wrappedValue }) ?? 15 },
                        set: { treadmillMaxIncline.wrappedValue = $0 }
                    )) {
                        ForEach(Self.inclines, id: \.self) { incline in
                            Text(incline == 25 ? "25%+" : "\(incline)%").tag(incline)
                        }
                    }
                    .pickerStyle(.segmented)
                    Text("Most gym treadmills stop at 15%. Pick 25%+ only for an incline trainer.")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .font(UH.TextStyle.label)
            .tint(UH.Palette.accent)
        }
        .task(id: loadAttempt) {
            do {
                let client = APIClient(baseURL: { AppEnvironment.current().baseURL }, tokenStore: InMemoryTokenStore())
                mountains = try await client.send(.get("/api/training-mountains", requiresAuth: false))
                loadError = false
            } catch { loadError = true }
        }
    }

    private func stepTitle(_ number: Int, _ title: String) -> some View {
        Text("\(number). \(L(title))").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            .fixedSize(horizontal: false, vertical: true)
    }

    private func accessButton(_ enabled: Bool, _ title: String) -> some View {
        Button {
            access = enabled
            if !enabled {
                choseOther = false
                showDuration = false
                trainingMountain = nil
                mountainDays = []
                mountainMinMinutes = nil
            }
        } label: {
            Text(L(title)).font(UH.TextStyle.label)
                .frame(maxWidth: .infinity, minHeight: 44)
                .foregroundStyle(UH.Palette.ink)
                .background(hasAccess == enabled ? UH.Palette.activeFill : UH.Palette.surface,
                            in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control)
                    .stroke(hasAccess == enabled ? UH.Palette.accentInk : UH.Palette.line, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier(enabled ? "trail.access.yes" : "trail.access.no")
        .accessibilityAddTraits(hasAccess == enabled ? .isSelected : [])
    }
}

struct TrainingMountain: Decodable, Sendable, Identifiable {
    let key: String
    let area: String
    let nameEn: String
    let nameVi: String
    let climbRate: Double
    let repeatsOnly: Bool
    let defaultMinMinutes: Int?
    var id: String { key }
}

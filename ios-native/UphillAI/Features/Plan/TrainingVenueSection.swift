import SwiftUI

/// Where the athlete can actually train: weekdays with hill/trail access (e.g. weekend trips
/// from a flat city), stairs, and the treadmill's top incline. The backend turns these into a
/// venue for every session type (backend/services/training_venues.py).
struct TrainingVenueSection: View {
    @Binding var mountainDays: Set<Weekday>
    @Binding var trainingMountain: String?
    @Binding var mountainMinMinutes: Int?
    @State private var mountains: [TrainingMountain] = []
    @State private var loadError = false
    @Binding var stairAccess: Bool
    /// Nil hides the incline picker (the athlete has no treadmill, or the flow doesn't ask).
    var treadmillMaxIncline: Binding<Int>?

    static let inclines = [15, 20, 25]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            Picker("Training mountain", selection: Binding(
                get: { trainingMountain ?? "" },
                set: { key in
                    let mountain = mountains.first { $0.key == key }
                    trainingMountain = mountain?.key
                    mountainMinMinutes = mountain?.defaultMinMinutes
                }
            )) {
                Text("Other / none").tag("")
                ForEach(mountains) { mountain in
                    Text("\(AppLanguage.current == .vi ? mountain.nameVi : mountain.nameEn) · \(mountain.climbRate.formatted(.number.precision(.fractionLength(0...1)))) m D+/km").tag(mountain.key)
                }
            }
            .tint(UH.Palette.accentInk)
            if loadError { Text("Mountains unavailable").foregroundStyle(UH.Palette.secondary) }
            HStack {
                Text("Trail minimum (min)").font(UH.TextStyle.label)
                Spacer()
                TextField("Trail minimum (min)", value: $mountainMinMinutes, format: .number)
                    .keyboardType(.numberPad)
                    .multilineTextAlignment(.trailing)
                    .frame(width: 90)
                    .accessibilityIdentifier("mountain.minimum")
            }
            Text("Minimum time for Long Runs on trail training days, in minutes. For example, 180 means 3 hours.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Trail training days").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 44))], spacing: 8) {
                    ForEach(Weekday.allCases) { day in
                        let isSelected = mountainDays.contains(day)
                        Button {
                            if isSelected { mountainDays.remove(day) } else { mountainDays.insert(day) }
                        } label: {
                            Text(L(day.short))
                                .font(UH.TextStyle.label)
                                .frame(maxWidth: .infinity, minHeight: 44)
                                .foregroundStyle(isSelected ? UH.Palette.buttonInk : UH.Palette.ink)
                                .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface,
                                            in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control)
                                    .stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel(L("%@ trail training day", L(day.rawValue)))
                        .accessibilityAddTraits(isSelected ? .isSelected : [])
                    }
                }
                Text("Choose days when you can train on hills or trails. Climbing Long Runs and hill sessions will be scheduled on these days.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            Toggle("I can use stairs (fire stairs or a Stairmaster)", isOn: $stairAccess)
                .font(UH.TextStyle.label)
                .tint(UH.Palette.accent)

            if let treadmillMaxIncline {
                VStack(alignment: .leading, spacing: UH.Space.compact) {
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
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .task {
            do {
                let client = APIClient(baseURL: { AppEnvironment.current().baseURL }, tokenStore: InMemoryTokenStore())
                mountains = try await client.send(.get("/api/training-mountains", requiresAuth: false))
            } catch { loadError = true }
        }
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

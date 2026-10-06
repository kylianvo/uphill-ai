import SwiftUI

/// Where the athlete can actually train: weekdays with hill/trail access (e.g. weekend trips
/// from a flat city), stairs, and the treadmill's top incline. The backend turns these into a
/// venue for every session type (backend/services/training_venues.py).
struct TrainingVenueSection: View {
    @Binding var mountainDays: Set<Weekday>
    @Binding var stairAccess: Bool
    /// Nil hides the incline picker (the athlete has no treadmill, or the flow doesn't ask).
    var treadmillMaxIncline: Binding<Int>?

    static let inclines = [15, 20, 25]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Hill or trail days").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 44))], spacing: 8) {
                    ForEach(Weekday.allCases) { day in
                        let isSelected = mountainDays.contains(day)
                        Button {
                            if isSelected { mountainDays.remove(day) } else { mountainDays.insert(day) }
                        } label: {
                            Text(day.short)
                                .font(UH.TextStyle.label)
                                .frame(maxWidth: .infinity, minHeight: 44)
                                .foregroundStyle(isSelected ? UH.Palette.buttonInk : UH.Palette.ink)
                                .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface,
                                            in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control)
                                    .stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(day.rawValue) hill or trail day")
                        .accessibilityAddTraits(isSelected ? .isSelected : [])
                    }
                }
                Text("Days you can reach real hills or trails, like weekend trips. Climbing long runs and hill sessions go on these days.")
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
    }
}

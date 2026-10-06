import SwiftUI

struct CoachedAthleteProfileView: View {
    let athlete: CoachedAthleteRow
    let profile: User?
    let service: any CoachingServicing
    var onDismiss: (() -> Void)? = nil

    var body: some View {
        ScrollView {
            VStack(spacing: UH.Space.medium) {
                // Header Card
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(UH.Palette.accent.opacity(0.18))
                                .frame(width: 48, height: 48)
                            Text(String(athlete.displayName.prefix(2)).uppercased())
                                .font(.system(size: 18, weight: .black, design: .rounded))
                                .foregroundStyle(UH.Palette.accent)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text(athlete.displayName)
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.ink)
                            Text(athlete.athleteEmail)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.muted)
                        }
                        Spacer()
                    }

                    HStack(spacing: 8) {
                        Text(athlete.status.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(athlete.isActive ? Color.green.opacity(0.15) : Color.orange.opacity(0.15))
                            .foregroundStyle(athlete.isActive ? Color.green : Color.orange)
                            .clipShape(Capsule())

                        if let gender = profile?.gender {
                            Text(gender.capitalized)
                                .font(UH.TextStyle.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(UH.Palette.hover)
                                .clipShape(Capsule())
                        }

                        if let age = profile?.age {
                            Text("\(age) yrs")
                                .font(UH.TextStyle.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 3)
                                .background(UH.Palette.hover)
                                .clipShape(Capsule())
                        }
                    }
                }
                .trainingCard()

                // Physiology & Thresholds Card
                VStack(alignment: .leading, spacing: 12) {
                    Label("Physiology & Threshold Zones", systemImage: "heart.text.square.fill")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        MetricTile(label: "Resting HR", value: profile?.restingHr.map { "\($0) bpm" } ?? "—")
                        MetricTile(label: "Max HR", value: profile?.maxHr.map { "\($0) bpm" } ?? "—")
                        MetricTile(label: "AeT Threshold (Z2)", value: profile?.aetHr.map { "\($0) bpm" } ?? "—", accentColor: Color.blue)
                        MetricTile(label: "AnT Threshold (Z4)", value: profile?.antHr.map { "\($0) bpm" } ?? "—", accentColor: Color.orange)
                    }

                    if let z2Min = profile?.zone2PaceMin, let z2Max = profile?.zone2PaceMax {
                        HStack {
                            Text("Zone 2 Pace Range:")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Text("\(z2Min) – \(z2Max) /km")
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color.blue)
                        }
                        .padding(.top, 4)
                    }

                    if let thresholdPace = profile?.thresholdPace {
                        HStack {
                            Text("Threshold Pace:")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Text("\(thresholdPace) /km")
                                .font(.system(size: 12, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color.orange)
                        }
                    }
                }
                .trainingCard()

                // Training Schedule Preferences Card
                VStack(alignment: .leading, spacing: 10) {
                    Label("Training Preferences & Constraints", systemImage: "calendar.badge.clock")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    HStack {
                        Text("Weekly Sessions:")
                            .font(UH.TextStyle.body)
                            .foregroundStyle(UH.Palette.secondary)
                        Spacer()
                        Text(profile?.daysPerWeek.map { "\($0) days/week" } ?? "—")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                    }

                    if let longRunDay = profile?.longRunDay {
                        HStack {
                            Text("Designated Long Run:")
                                .font(UH.TextStyle.body)
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Text(longRunDay)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(Color.green)
                        }
                    }

                    if let preferred = profile?.preferredRunDays {
                        HStack(alignment: .top) {
                            Text("Running Days:")
                                .font(UH.TextStyle.body)
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Text(preferred.replacingOccurrences(of: "[", with: "").replacingOccurrences(of: "]", with: "").replacingOccurrences(of: "\"", with: ""))
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                                .multilineTextAlignment(.trailing)
                        }
                    }

                    if let injury = profile?.injuryHistory, !injury.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Injury Notes / Limitations:")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(Color.red)
                            Text(injury)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .padding(8)
                        .background(Color.red.opacity(0.06))
                        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if let notes = profile?.athleteNotes, !notes.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Athlete Notes:")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                            Text(notes)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .padding(8)
                        .background(UH.Palette.hover)
                        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                }
                .trainingCard()

                // Coach Notes Thread
                CoachNoteThreadView(
                    athleteId: athlete.athleteId,
                    targetType: "general",
                    targetId: nil,
                    service: service,
                    canAdd: true
                )
            }
            .padding(UH.Space.regular)
        }
        .navigationTitle("Athlete Profile")
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct MetricTile: View {
    let label: String
    let value: String
    var accentColor: Color = UH.Palette.ink

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(.system(size: 15, weight: .bold, design: .monospaced))
                .foregroundStyle(accentColor)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.hover.opacity(0.6))
        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
    }
}

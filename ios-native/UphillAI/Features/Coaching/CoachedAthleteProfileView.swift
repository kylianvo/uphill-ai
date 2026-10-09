import SwiftUI

struct CoachedAthleteProfileView: View {
    let athlete: CoachedAthleteRow
    let service: any CoachingServicing
    var onDismiss: (() -> Void)? = nil
    @State private var profile: User?
    @State private var editing = false

    init(athlete: CoachedAthleteRow, profile: User?, service: any CoachingServicing, onDismiss: (() -> Void)? = nil) {
        self.athlete = athlete
        self.service = service
        self.onDismiss = onDismiss
        // Only reuse a cached profile that belongs to this athlete.
        _profile = State(initialValue: profile?.id == athlete.athleteId ? profile : nil)
    }

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
                    HStack(alignment: .firstTextBaseline) {
                        Label("Physiology & Threshold Zones", systemImage: "heart.text.square.fill")
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)
                        Spacer(minLength: 8)
                        Button(L("Edit")) { editing = true }
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.accentInk)
                            .disabled(profile == nil)
                    }

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        MetricTile(label: "Resting HR", value: profile?.restingHr.map { "\($0) bpm" } ?? "—",
                                   source: source("resting_hr"))
                        MetricTile(label: "Max HR", value: profile?.maxHr.map { "\($0) bpm" } ?? "—",
                                   source: source("max_hr"))
                        MetricTile(label: L("AeT Threshold (Z2)"), value: profile?.aetHr.map { "\($0) bpm" } ?? "—",
                                   accentColor: Color.blue, source: source("aet_hr"))
                        MetricTile(label: L("AnT Threshold (Z4)"), value: profile?.antHr.map { "\($0) bpm" } ?? "—",
                                   accentColor: Color.orange, source: source("ant_hr"))
                    }

                    if let z2Min = profile?.zone2PaceMin, let z2Max = profile?.zone2PaceMax {
                        VStack(alignment: .trailing, spacing: 2) {
                            HStack {
                                Text("Zone 2 Pace Range:")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                Spacer()
                                Text("\(z2Min) – \(z2Max) /km")
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundStyle(Color.blue)
                            }
                            // The pair shares one line; the newer coach edit wins.
                            ProvenanceLine(source: source("zone2_pace_max")?.source == "coach"
                                ? source("zone2_pace_max") : source("zone2_pace_min"))
                        }
                        .padding(.top, 4)
                    }

                    if let thresholdPace = profile?.thresholdPace {
                        VStack(alignment: .trailing, spacing: 2) {
                            HStack {
                                Text("Threshold Pace:")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                Spacer()
                                Text("\(thresholdPace) /km")
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundStyle(Color.orange)
                            }
                            ProvenanceLine(source: source("threshold_pace"))
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
                        Text(profile?.daysPerWeek.map { L("%lld days/week", $0) } ?? "—")
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
        .sheet(isPresented: $editing) {
            if let profile {
                CoachEditPhysiologySheet(
                    athleteId: athlete.athleteId,
                    athleteName: athlete.displayName,
                    profile: profile,
                    service: service,
                    onSaved: { self.profile = $0 }
                )
            }
        }
        .task(id: athlete.athleteId) {
            do {
                profile = try await service.fetchAthleteProfile(athleteId: athlete.athleteId)
            } catch {
                print("Failed to load athlete profile: \(error)")
            }
        }
    }

    private func source(_ field: String) -> ProfileFieldSource? {
        profile?.fieldSources?[field]
    }
}

private struct MetricTile: View {
    let label: String
    let value: String
    var accentColor: Color = UH.Palette.ink
    var source: ProfileFieldSource? = nil

    /// An app fallback isn't the athlete's number; show it, but quietly.
    private var isDefault: Bool { source?.source == "default" }

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(.system(size: 15, weight: .bold, design: .monospaced))
                .foregroundStyle(isDefault ? UH.Palette.muted : accentColor)
            ProvenanceLine(source: source)
                .padding(.top, 2)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(UH.Palette.hover.opacity(0.6))
        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
    }
}

import SwiftUI

/// "This week" for whoever the filters show: three done figures, a week stepper, and a done bar per group.
struct RosterOverviewCard: View {
    let triage: RosterTriage
    @Binding var weekOffset: Int
    @Binding var groupKey: GroupKey

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text(weekOffset == 0 ? "THIS WEEK" : "\(weekOffset) WEEKS AGO")
                    .font(UH.TextStyle.eyebrow)
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.secondary)
                Spacer()
                Button { weekOffset += 1 } label: { Image(systemName: "chevron.left") }
                    .disabled(weekOffset >= 3)
                    .accessibilityLabel("Previous week")
                Button { weekOffset -= 1 } label: { Image(systemName: "chevron.right") }
                    .disabled(weekOffset == 0)
                    .accessibilityLabel("Next week")
            }
            .font(.footnote.weight(.semibold))
            .buttonStyle(.borderless)

            HStack(spacing: 8) {
                metric(triage.sessionsDonePct, "sessions done")
                metric(triage.keyDonePct, "key sessions")
                metric(triage.volumePct, "volume vs plan")
            }
            .fixedSize(horizontal: false, vertical: true)

            Picker("Group by", selection: $groupKey) {
                Text("Race").tag(GroupKey.race)
                Text("Level").tag(GroupKey.level)
                Text("Plan type").tag(GroupKey.planType)
            }
            .pickerStyle(.segmented)

            VStack(spacing: 8) {
                ForEach(triage.groups(by: groupKey), id: \.label) { group in
                    HStack(spacing: 8) {
                        Text("\(label(group.label)) (\(group.count))")
                            .font(.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .lineLimit(1)
                            .frame(width: 128, alignment: .leading)
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule().fill(UH.Palette.tint)
                                Capsule()
                                    .fill((group.donePct ?? 0) >= 0.8 ? UH.Palette.accent : Color.orange.opacity(0.8))
                                    .frame(width: geo.size.width * min(group.donePct ?? 0, 1))
                            }
                        }
                        .frame(height: 6)
                        Text(group.donePct.map(CoachFormat.wholePercent) ?? "—")
                            .font(.caption.weight(.semibold).monospacedDigit())
                            .foregroundStyle(UH.Palette.secondary)
                            .frame(width: 38, alignment: .trailing)
                    }
                    .accessibilityElement(children: .combine)
                }
            }

            if let mix = triage.mix {
                Text(L("Easy %@ · Long Run %@ · Quality %@",
                       CoachFormat.wholePercent(mix.easy), CoachFormat.wholePercent(mix.long), CoachFormat.wholePercent(mix.quality)))
                    .font(.caption)
                    .foregroundStyle(UH.Palette.muted)
            }
        }
        .trainingCard()
    }

    private func metric(_ value: Double?, _ caption: LocalizedStringKey) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value.map(CoachFormat.wholePercent) ?? "—")
                .font(UH.TextStyle.metric)
                .foregroundStyle(UH.Palette.ink)
            Text(caption)
                .font(.caption)
                .foregroundStyle(UH.Palette.secondary)
                .lineLimit(2)
                .minimumScaleFactor(0.85)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .padding(10)
        .background(UH.Palette.hover, in: RoundedRectangle(cornerRadius: UH.Radius.workoutDay))
    }

    private func label(_ key: String) -> String {
        switch (groupKey, key) {
        case (.race, "none"): L("No race")
        case (.planType, "coached"): L("Coached")
        case (.planType, _): L("Review")
        case (.level, _): L(key.capitalized)
        default: key
        }
    }
}

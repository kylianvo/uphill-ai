import SwiftUI

/// Shown to the athlete once after their coach changes their heart-rate or
/// pace numbers: what changed, old → new, until they tap "Got it".
struct CoachProfileChangesCard: View {
    let changes: [CoachProfileChange]
    let onAcknowledge: () -> Void

    private var coachName: String {
        changes.compactMap(\.byName).first ?? L("Your coach")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "person.badge.shield.checkmark")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundStyle(UH.Palette.accentInk)
                    .frame(width: 22)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(L("%@ updated your zones", coachName))
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    Text(L("New workouts use these numbers."))
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            VStack(spacing: 0) {
                ForEach(changes) { change in
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text(ProfileField.label(change.field))
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                        Spacer(minLength: 8)
                        if let previous = change.previous {
                            Text(previous.display)
                                .strikethrough(color: UH.Palette.muted)
                                .foregroundStyle(UH.Palette.muted)
                            Image(systemName: "arrow.right")
                                .font(.caption2.weight(.bold))
                                .foregroundStyle(UH.Palette.muted)
                                .accessibilityHidden(true)
                        }
                        Text("\(change.value?.display ?? "—") \(ProfileField.unit(change.field))")
                            .fontWeight(.bold)
                            .foregroundStyle(UH.Palette.ink)
                    }
                    .font(.subheadline.monospacedDigit())
                    .padding(.vertical, 8)
                    .accessibilityElement(children: .combine)
                    if change.id != changes.last?.id {
                        Divider().overlay(UH.Palette.line)
                    }
                }
            }

            Button(action: onAcknowledge) {
                Text(L("Got it"))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.uhPrimary)
        }
        .padding(14)
        .background(UH.Palette.card)
        .clipShape(RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(
            RoundedRectangle(cornerRadius: UH.Radius.panel)
                .stroke(UH.Palette.accent.opacity(0.55), lineWidth: 1)
        )
    }
}

import SwiftUI

/// Shown once when a milestone is reached. First 5 km and First 10 km get a certificate-style card.
struct MilestoneCelebrationSheet: View {
    let item: PlanMilestones.Item
    let next: PlanMilestones.Item?
    let targetTitle: String
    let canUpgrade: Bool
    let onUpgrade: () -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var pulse = false

    private var isFinish: Bool { item.key == "first_5k" || item.key == "first_10k" }

    var body: some View {
        VStack(spacing: UH.Space.section) {
            Spacer()
            Image(systemName: isFinish ? "rosette" : "checkmark.seal.fill")
                .font(.system(size: 64))
                .foregroundStyle(UH.Palette.accentInk)
                .scaleEffect(pulse ? 1.0 : 0.6)
                .animation(.spring(response: 0.5, dampingFraction: 0.55), value: pulse)
            Text("Milestone reached").font(UH.TextStyle.eyebrow).tracking(0.5).foregroundStyle(UH.Palette.secondary)
            Text(verbatim: item.title).font(UH.TextStyle.screenTitle).multilineTextAlignment(.center).foregroundStyle(UH.Palette.ink)
            if isFinish {
                Text(verbatim: targetTitle).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.accentInk)
                    .padding(UH.Space.regular)
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.accentInk, lineWidth: 2))
            }
            if let next {
                Text(verbatim: L("Next: %@", next.title)).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
            }
            Spacer()
            if canUpgrade {
                Button("Next: First 10K") { onUpgrade(); dismiss() }
                    .buttonStyle(PrimaryButtonStyle())
            }
            if canUpgrade {
                Button("Nice") { dismiss() }.buttonStyle(SecondaryButtonStyle())
            } else {
                Button("Nice") { dismiss() }.buttonStyle(PrimaryButtonStyle())
            }
        }
        .padding(UH.Space.regular)
        .presentationDetents([.medium])
        .sensoryFeedback(.success, trigger: pulse)
        .onAppear { pulse = true }
        .accessibilityIdentifier("milestone.celebration")
    }
}

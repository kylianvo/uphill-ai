import SwiftUI

/// Shown before the system Health permission sheet: what Uphill reads, why, and what leaves the phone.
struct AppleHealthExplainerSheet: View {
    let onContinue: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    Image(systemName: "heart.fill")
                        .font(.largeTitle)
                        .foregroundStyle(UH.Palette.healthPink)
                        .accessibilityHidden(true)
                    Text("Connect Apple Health")
                        .font(UH.TextStyle.screenTitle)
                        .foregroundStyle(UH.Palette.ink)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityAddTraits(.isHeader)
                    point("figure.run", "What I read",
                          "Runs, hikes, stair sessions and strength workouts from the last 12 weeks, then each new one as it's saved.")
                    point("bed.double", "Recovery",
                          "Resting heart rate, HRV and sleep, as daily totals, so your plan eases off when you're not recovering.")
                    point("checkmark.circle", "Why",
                          "To mark your planned sessions done and start your plan from your real weekly mileage.")
                    point("lock", "What I send to Uphill",
                          "Time, distance, climb, heart rate, calories and the app that recorded each workout, plus one daily value each for resting HR, HRV and sleep. Your GPS routes, sleep stages and heart-rate streams stay on your phone.")
                    point("square.and.pencil", "Nothing written", "I never write to Apple Health.")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(UH.Space.section)
            }
            .background(UH.Palette.surface)
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: UH.Space.small) {
                    // Apple's sheet opens with every switch off; Allow alone grants nothing.
                    point("hand.tap", "On the next screen",
                          "Apple starts with every switch off. Turn them all on and choose All Recorded Data, or I can't see your workouts.")
                        .padding(UH.Space.regular)
                        .background(UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .accessibilityIdentifier("health.explainer.turnOnAll")
                    Button("Continue") { dismiss(); onContinue() }
                        .buttonStyle(.uhPrimary)
                        .accessibilityIdentifier("health.explainer.continue")
                    Button("Not now") { dismiss() }
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.secondary)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("health.explainer.notNow")
                }
                .padding(UH.Space.section)
                .background(UH.Palette.surface)
            }
        }
        .presentationDetents([.large])
    }

    private func point(_ symbol: String, _ title: LocalizedStringKey, _ body: LocalizedStringKey) -> some View {
        HStack(alignment: .top, spacing: UH.Space.regular) {
            Image(systemName: symbol)
                .foregroundStyle(UH.Palette.accentInk)
                .frame(width: 24)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Text(body).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .accessibilityElement(children: .combine)
    }
}

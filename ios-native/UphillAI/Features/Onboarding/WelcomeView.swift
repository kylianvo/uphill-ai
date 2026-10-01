import SwiftUI

struct WelcomeView: View {
    let onStart: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                Image(systemName: "mountain.2.fill")
                    .font(.system(size: 56)).foregroundStyle(UH.Palette.accent)
                    .accessibilityHidden(true)
                Text("Let's build your training plan").font(UH.TextStyle.screenTitle)
                Text("Answer a few questions and Coach Uphill builds a plan around your goal, your week and how you feel today.")
                    .foregroundStyle(UH.Palette.secondary)
                Label("About 2 minutes", systemImage: "clock").font(UH.TextStyle.caption)
                Button("Get started", action: onStart).buttonStyle(.uhPrimary).accessibilityIdentifier("welcome.start")
                Button("Not now", action: onNotNow).frame(maxWidth: .infinity, minHeight: 44).tint(UH.Palette.accentInk)
            }
            .padding(UH.Space.section)
            .padding(.top, UH.Space.reading)
        }
        .foregroundStyle(UH.Palette.ink)
        .background(UH.Palette.surface.ignoresSafeArea())
    }
}

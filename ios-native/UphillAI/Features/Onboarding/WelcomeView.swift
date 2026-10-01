import SwiftUI

struct WelcomeView: View {
    let onStart: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                ZStack(alignment: .bottomLeading) {
                    UH.Palette.accent
                    Image(systemName: "mountain.2.fill")
                        .font(.system(size: 168, weight: .black))
                        .foregroundStyle(UH.Palette.buttonInk)
                        .offset(x: UH.Space.section, y: 28)
                        .accessibilityHidden(true)
                }
                .frame(height: 280)
                .clipped()
                .ignoresSafeArea(edges: .top)

                VStack(alignment: .leading, spacing: UH.Space.section) {
                    Text("Let's build your training plan")
                        .font(.system(size: 40, weight: .heavy))
                        .tracking(-0.8)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("Answer a few questions and Coach Uphill builds a plan around your goal, your week and how you feel today.")
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.secondary)
                    Label("About 2 minutes", systemImage: "clock").font(UH.TextStyle.label)
                    Button("Get started", action: onStart).buttonStyle(.uhPrimary).accessibilityIdentifier("welcome.start")
                    Button("Not now", action: onNotNow).frame(maxWidth: .infinity, minHeight: 44).tint(UH.Palette.accentInk)
                }
                .padding(UH.Space.section)
                .padding(.top, UH.Space.small)
            }
        }
        .foregroundStyle(UH.Palette.ink)
        .background(UH.Palette.surface.ignoresSafeArea())
        .ignoresSafeArea(edges: .top)
    }
}

import SwiftUI

/// Shown while the stored session is restored: a Dalat trail photo (day and a long-exposure night
/// version from the asset catalog) behind the logo. Its sky matches the system launch screen's colour,
/// so the hand-off from launch to here to sign-in never flashes.
struct LaunchView: View {
    let error: String?
    let onRetry: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.colorScheme) private var scheme
    @State private var zoomed = false

    var body: some View {
        ZStack(alignment: .top) {
            UH.Palette.surface.ignoresSafeArea()

            Color.clear
                .overlay(
                    Image("LaunchPhoto")
                        .resizable()
                        .scaledToFill()
                        .scaleEffect(zoomed ? 1.06 : 1, anchor: .bottom)
                )
                .clipped()
                .ignoresSafeArea()
                .accessibilityHidden(true)

            // Keeps the text readable over the sky and the ridge line.
            LinearGradient(stops: [.init(color: UH.Palette.surface.opacity(scheme == .dark ? 0.4 : 0.85), location: 0),
                                   .init(color: UH.Palette.surface.opacity(scheme == .dark ? 0.35 : 0.6), location: 0.42),
                                   .init(color: UH.Palette.surface.opacity(0), location: 0.72)],
                           startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 0) {
                LogoMark()
                    .frame(width: 64, height: 64)
                    .shadow(color: .black.opacity(0.18), radius: 12, y: 6)
                    .padding(.bottom, UH.Space.section)
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("Uphill AI")
                        .font(.custom("Plus Jakarta Sans", fixedSize: 46).weight(.heavy))
                        .tracking(-1.6)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Your adaptive training plan for the mountains.")
                        .font(.title3.weight(.medium))
                        .foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .accessibilityElement(children: .combine)

                status
                    .padding(.top, UH.Space.section)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, UH.Space.reading)
            .padding(.top, 96)
        }
        .onAppear {
            // A slow push-in keeps the still alive; Reduce Motion gets the plain photo.
            if !reduceMotion { withAnimation(.easeInOut(duration: 14)) { zoomed = true } }
        }
    }

    @ViewBuilder private var status: some View {
        if let error {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text(error)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.danger)
                Button("Try again", action: onRetry)
                    .buttonStyle(.uhPrimary)
                    .frame(maxWidth: 220)
            }
        } else {
            HStack(spacing: UH.Space.compact) {
                ProgressView().tint(UH.Palette.accentInk)
                Text("Loading your training")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
            .accessibilityElement(children: .combine)
        }
    }
}

/// The app icon's rising-arrow mark, drawn from the web favicon's geometry (icon.svg).
private struct LogoMark: View {
    var body: some View {
        GeometryReader { geo in
            let k = geo.size.width / 256
            ZStack {
                RoundedRectangle(cornerRadius: 56 * k, style: .continuous)
                    .fill(Color(hex: "#0d0c0d"))
                Path { p in
                    let pt = { (x: CGFloat, y: CGFloat) in CGPoint(x: (50 + x) * k, y: (60 + y) * k) }
                    p.addLines([pt(156, 8), pt(76, 108), pt(46, 68), pt(8, 116)])
                    p.addLines([pt(108, 8), pt(156, 8), pt(156, 56)])
                }
                .stroke(UH.Palette.accent, style: StrokeStyle(lineWidth: 20 * k, lineCap: .round, lineJoin: .round))
            }
        }
        .aspectRatio(1, contentMode: .fit)
    }
}

/// A muted, gapless, aspect-filling video loop from the app bundle. Shows the first
/// frame without playing when `playing` is false (Reduce Motion).

#Preview("Loading") { LaunchView(error: nil, onRetry: {}) }
#Preview("Error") { LaunchView(error: "Couldn't reach Uphill AI. Check your connection and try again.", onRetry: {}) }

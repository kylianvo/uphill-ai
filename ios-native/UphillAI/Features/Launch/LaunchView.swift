import SwiftUI

/// Shown while the stored session is restored. Shares the system launch screen's
/// background colour, so the hand-off from launch to here to sign-in never flashes.
struct LaunchView: View {
    let error: String?
    let onRetry: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var risen = false

    var body: some View {
        ZStack(alignment: .bottom) {
            UH.Palette.surface.ignoresSafeArea()

            ridges
                .ignoresSafeArea(edges: .bottom)

            VStack(spacing: 0) {
                Spacer(minLength: 0)
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("Uphill AI")
                        .font(.system(size: 44, weight: .heavy, design: .rounded))
                        .tracking(-1.2)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Your adaptive training plan for the mountains.")
                        .font(.title3.weight(.medium))
                        .foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)

                status
                    .padding(.top, UH.Space.reading)
                    .frame(maxWidth: .infinity, alignment: .leading)
                Spacer(minLength: 0)
                Spacer(minLength: 0)
            }
            .padding(.horizontal, UH.Space.reading)
            .opacity(risen ? 1 : 0)
        }
        .onAppear {
            withAnimation(reduceMotion ? nil : .easeOut(duration: 0.7)) { risen = true }
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
                    .foregroundStyle(UH.Palette.muted)
            }
            .accessibilityElement(children: .combine)
        }
    }

    /// Three layered ridgelines, far to near, that settle up into place once.
    private var ridges: some View {
        GeometryReader { geo in
            let h = geo.size.height
            ZStack(alignment: .bottom) {
                Ridge(peaks: [0.55, 0.30, 0.62, 0.22, 0.48, 0.35])
                    .fill(UH.Palette.accent.opacity(0.14))
                    .frame(height: h * 0.34)
                    .offset(y: risen ? 0 : 60)
                Ridge(peaks: [0.40, 0.65, 0.18, 0.52, 0.28, 0.58])
                    .fill(UH.Palette.accent.opacity(0.28))
                    .frame(height: h * 0.26)
                    .offset(y: risen ? 0 : 90)
                Ridge(peaks: [0.70, 0.38, 0.55, 0.12, 0.60, 0.45])
                    .fill(LinearGradient(colors: [UH.Palette.accentInk, UH.Palette.buttonInk],
                                         startPoint: .top, endPoint: .bottom))
                    .frame(height: h * 0.18)
                    .offset(y: risen ? 0 : 120)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
        }
        .accessibilityHidden(true)
    }
}

/// A jagged skyline. `peaks` are heights from the top (0 = highest) at evenly spaced points.
private struct Ridge: Shape {
    let peaks: [CGFloat]

    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: rect.minX, y: rect.maxY))
        let step = rect.width / CGFloat(peaks.count - 1)
        for (i, peak) in peaks.enumerated() {
            p.addLine(to: CGPoint(x: rect.minX + CGFloat(i) * step, y: rect.minY + peak * rect.height))
        }
        p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
        p.closeSubpath()
        return p
    }
}

#Preview("Loading") { LaunchView(error: nil, onRetry: {}) }
#Preview("Error") { LaunchView(error: "Couldn't reach Uphill AI. Check your connection.", onRetry: {}) }

import AVFoundation
import SwiftUI

/// Shown while the stored session is restored. Plays the web app's valley video;
/// its foggy sky matches the system launch screen's colour, so the hand-off from
/// launch to here to sign-in never flashes.
struct LaunchView: View {
    let error: String?
    let onRetry: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var shown = false

    var body: some View {
        ZStack(alignment: .top) {
            UH.Palette.surface.ignoresSafeArea()

            LoopingVideo(name: "launch_bg", playing: !reduceMotion)
                .ignoresSafeArea()
                .opacity(shown ? 1 : 0)
                .accessibilityHidden(true)

            // Keeps the text readable when the fog thins mid-loop.
            LinearGradient(colors: [UH.Palette.surface.opacity(0.85), UH.Palette.surface.opacity(0)],
                           startPoint: .top, endPoint: .center)
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
            withAnimation(reduceMotion ? nil : .easeOut(duration: 0.8)) { shown = true }
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
private struct LoopingVideo: UIViewRepresentable {
    let name: String
    let playing: Bool

    func makeUIView(context: Context) -> PlayerView {
        let view = PlayerView()
        guard let url = Bundle.main.url(forResource: name, withExtension: "mp4") else { return view }
        let player = AVQueuePlayer()
        player.isMuted = true
        player.preventsDisplaySleepDuringVideoPlayback = false
        // Don't interrupt the user's music or podcast.
        try? AVAudioSession.sharedInstance().setCategory(.ambient, options: .mixWithOthers)
        context.coordinator.looper = AVPlayerLooper(player: player, templateItem: AVPlayerItem(url: url))
        view.playerLayer.player = player
        view.playerLayer.videoGravity = .resizeAspectFill
        if playing { player.play() }
        return view
    }

    func updateUIView(_ view: PlayerView, context: Context) {
        guard let player = view.playerLayer.player else { return }
        if playing { player.play() } else { player.pause() }
    }

    static func dismantleUIView(_ view: PlayerView, coordinator: Coordinator) {
        view.playerLayer.player?.pause()
        coordinator.looper = nil
    }

    func makeCoordinator() -> Coordinator { Coordinator() }
    final class Coordinator { var looper: AVPlayerLooper? }

    final class PlayerView: UIView {
        override static var layerClass: AnyClass { AVPlayerLayer.self }
        var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }
    }
}

#Preview("Loading") { LaunchView(error: nil, onRetry: {}) }
#Preview("Error") { LaunchView(error: "Couldn't reach Uphill AI. Check your connection and try again.", onRetry: {}) }

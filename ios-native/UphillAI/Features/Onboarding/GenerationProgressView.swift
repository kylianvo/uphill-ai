import SwiftUI

struct GenerationProgressView: View {
    let generation: GenerationCenter
    /// True when the plan tab already holds a plan (decides what "lost" means).
    let hasPlan: Bool
    let onShowPlan: () -> Void
    let onLeave: () -> Void
    let onRetry: () -> Void
    let onEditAnswers: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var checkShown = false

    private enum Phase: Equatable {
        case running(GenerationCenter.Running)
        case done
        case failed(String)
    }

    private var phase: Phase {
        if let running = generation.running { return .running(running) }
        switch generation.lastOutcome?.outcome {
        case .failed(let message): return .failed(message)
        case .lost where !hasPlan:
            return .failed("We lost track of your plan while the server restarted. Check the Plan tab; if nothing is there, try again.")
        default: return .done
        }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: UH.Space.section) {
                switch phase {
                case .running(let job): running(job)
                case .done: done
                case .failed(let message): failed(message)
                }
            }
            .padding(UH.Space.section)
            .frame(maxWidth: .infinity)
        }
        .foregroundStyle(UH.Palette.ink)
        .background(UH.Palette.surface.ignoresSafeArea())
        .sensoryFeedback(.success, trigger: phase == .done)
        .sensoryFeedback(.error, trigger: { if case .failed = phase { true } else { false } }())
    }

    private func running(_ job: GenerationCenter.Running) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text("Building your plan").font(UH.TextStyle.screenTitle)
                Text("This usually takes under a minute. You can leave this screen; we'll keep working.")
                    .foregroundStyle(UH.Palette.secondary)
            }
            TimelineView(.periodic(from: .now, by: 1)) { context in
                let elapsed = max(0, Int(context.date.timeIntervalSince(job.startedAt)))
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    HStack(spacing: UH.Space.small) {
                        ProgressView()
                        Text(String(format: "%d:%02d", elapsed / 60, elapsed % 60))
                            .font(UH.TextStyle.metric)
                            .accessibilityLabel("Elapsed \(elapsed / 60) minutes \(elapsed % 60) seconds")
                    }
                    if elapsed >= 90 {
                        Text("Still working. Plans with a race far away take longer.")
                            .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    }
                }
            }
            if !job.summary.isEmpty {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text("Your plan is built around").font(UH.TextStyle.sectionTitle)
                    ForEach(job.summary, id: \.self) { line in
                        Label(line, systemImage: "checkmark").font(UH.TextStyle.body)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .uhCard()
            }
            Button("Keep using the app", action: onLeave).buttonStyle(.uhSecondary)
        }
    }

    private var done: some View {
        VStack(spacing: UH.Space.section) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64)).foregroundStyle(UH.Palette.accent)
                .scaleEffect(checkShown || reduceMotion ? 1 : 0.6)
                .opacity(checkShown ? 1 : 0)
                .accessibilityHidden(true)
            Text("Your plan is ready").font(UH.TextStyle.screenTitle).multilineTextAlignment(.center)
            Button("See my plan", action: onShowPlan).buttonStyle(.uhPrimary).accessibilityIdentifier("generation.seePlan")
        }
        .padding(.top, UH.Space.reading)
        .onAppear { withAnimation(reduceMotion ? .easeOut(duration: 0.15) : UH.Motion.standard) { checkShown = true } }
    }

    private func failed(_ message: String) -> some View {
        VStack(spacing: UH.Space.section) {
            Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 48)).foregroundStyle(UH.Palette.danger)
                .accessibilityHidden(true)
            Text("We couldn't build your plan").font(UH.TextStyle.screenTitle).multilineTextAlignment(.center)
            Text(message).foregroundStyle(UH.Palette.secondary).multilineTextAlignment(.center)
            Button("Try again", action: onRetry).buttonStyle(.uhPrimary).accessibilityIdentifier("generation.retry")
            Button("Edit answers", action: onEditAnswers).buttonStyle(.uhSecondary)
        }
        .padding(.top, UH.Space.reading)
    }
}

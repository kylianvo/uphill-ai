import SwiftUI

struct ChatGoalCard: View {
    let estimate: GoalEstimate

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label(estimate.raceName ?? "Race Goal Estimate", systemImage: "speedometer")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Text(String(format: "%.0f km", estimate.distanceKm))
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.secondary)
            }

            if let goals = estimate.goals {
                HStack(spacing: 8) {
                    tierPill(title: "A: Ambitious", mins: goals.ambitious, color: Color(hex: "#10b981"))
                    tierPill(title: "B: Realistic", mins: goals.realistic, color: UH.Palette.accentInk)
                    tierPill(title: "C: Safe", mins: goals.safe, color: Color(hex: "#f59e0b"))
                }
            } else if let adj = estimate.adjustedTimeMins {
                Text("Target Finish: \(GoalEstimate.formatMinutes(adj))")
                    .font(UH.TextStyle.metric)
                    .foregroundStyle(UH.Palette.ink)
            }

            if let benchmarks = estimate.benchmarks, let first = benchmarks.first {
                HStack(spacing: 4) {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                        .font(.system(size: 10))
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("Calibrated against \(first.year) field (\(first.finishers ?? 0) finishers)")
                        .font(.system(size: 10.5))
                        .foregroundStyle(UH.Palette.secondary)
                }
            }
        }
        .uhCard()
    }

    private func tierPill(title: String, mins: Double, color: Color) -> some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
            Text(GoalEstimate.formatMinutes(mins))
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 6)
        .background(color.opacity(0.1), in: RoundedRectangle(cornerRadius: 6))
    }
}

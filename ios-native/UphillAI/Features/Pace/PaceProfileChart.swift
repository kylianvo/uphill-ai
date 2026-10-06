import SwiftUI

struct PaceProfileChart: View {
    let paced: [PacedCheckpoint]

    init(paced: [PacedCheckpoint]) {
        self.paced = paced
    }

    private var validRows: [PacedCheckpoint] {
        paced.filter { $0.distanceKm > 0 || paced.firstIndex(of: $0) == 0 }
    }

    private var maxDist: Double {
        validRows.last?.distanceKm ?? 1.0
    }

    private var minElev: Double {
        validRows.map(\.elevationM).min() ?? 0.0
    }

    private var maxElev: Double {
        let m = validRows.map(\.elevationM).max() ?? 100.0
        return max(m, minElev + 10.0)
    }

    private func parsePaceToMinutes(_ pace: String) -> Double {
        let parts = pace.split(separator: ":").compactMap { Double($0) }
        if parts.count == 2 {
            return parts[0] + parts[1] / 60.0
        }
        return 6.0
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header / Legend
            HStack {
                Text("COURSE PROFILE & TARGET PACE")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)

                Spacer()

                HStack(spacing: 12) {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(UH.Palette.accentInk)
                            .frame(width: 6, height: 6)
                        Text("Run")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    HStack(spacing: 4) {
                        Circle()
                            .fill(UH.Palette.ink)
                            .frame(width: 6, height: 6)
                        Text("Hike")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            if validRows.count >= 2 {
                GeometryReader { geo in
                    let w = geo.size.width
                    let elevH = geo.size.height * 0.58
                    let paceTop = elevH + 16
                    let paceH = geo.size.height - paceTop - 18

                    ZStack(alignment: .topLeading) {
                        // Background guideline grids
                        Path { path in
                            path.move(to: CGPoint(x: 35, y: elevH))
                            path.addLine(to: CGPoint(x: w, y: elevH))

                            path.move(to: CGPoint(x: 35, y: paceTop + paceH))
                            path.addLine(to: CGPoint(x: w, y: paceTop + paceH))
                        }
                        .stroke(UH.Palette.line, lineWidth: 1)

                        // Elevation Area
                        Path { path in
                            guard let first = validRows.first else { return }
                            let x0 = xPos(first.distanceKm, width: w)
                            let y0 = yElevPos(first.elevationM, height: elevH)
                            path.move(to: CGPoint(x: x0, y: y0))

                            for row in validRows.dropFirst() {
                                let x = xPos(row.distanceKm, width: w)
                                let y = yElevPos(row.elevationM, height: elevH)
                                path.addLine(to: CGPoint(x: x, y: y))
                            }

                            path.addLine(to: CGPoint(x: w, y: elevH))
                            path.addLine(to: CGPoint(x: 35, y: elevH))
                            path.closeSubpath()
                        }
                        .fill(
                            LinearGradient(
                                colors: [UH.Palette.accentInk.opacity(0.22), UH.Palette.accentInk.opacity(0.04)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )

                        // Elevation Stroke Line
                        Path { path in
                            guard let first = validRows.first else { return }
                            let x0 = xPos(first.distanceKm, width: w)
                            let y0 = yElevPos(first.elevationM, height: elevH)
                            path.move(to: CGPoint(x: x0, y: y0))

                            for row in validRows.dropFirst() {
                                let x = xPos(row.distanceKm, width: w)
                                let y = yElevPos(row.elevationM, height: elevH)
                                path.addLine(to: CGPoint(x: x, y: y))
                            }
                        }
                        .stroke(UH.Palette.accentInk, lineWidth: 2)

                        // Target Pace Steps
                        ForEach(1..<validRows.count, id: \.self) { i in
                            let prev = validRows[i - 1]
                            let curr = validRows[i]
                            let x0 = xPos(prev.distanceKm, width: w)
                            let x1 = xPos(curr.distanceKm, width: w)
                            let paceVal = parsePaceToMinutes(curr.targetPace)
                            let y = yPacePos(paceVal, top: paceTop, height: paceH)
                            let isHike = curr.effort == "hike"

                            Path { path in
                                path.move(to: CGPoint(x: x0, y: y))
                                path.addLine(to: CGPoint(x: x1, y: y))
                            }
                            .stroke(isHike ? UH.Palette.ink : UH.Palette.accentInk, lineWidth: isHike ? 3.5 : 2.5)
                        }

                        // Elevation Labels (Y Axis)
                        Text("\(Int(maxElev))m")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .position(x: 18, y: 10)

                        Text("\(Int(minElev))m")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .position(x: 18, y: elevH - 8)

                        // Pace Axis Title
                        Text("PACE")
                            .font(.system(size: 8, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                            .position(x: 18, y: paceTop + 8)

                        // X-axis Distance Markers
                        let fractions: [Double] = [0.0, 0.25, 0.5, 0.75, 1.0]
                        ForEach(fractions, id: \.self) { frac in
                            let kmVal = maxDist * frac
                            Text(String(format: "%.0fk", kmVal))
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.muted)
                                .position(x: xPos(kmVal, width: w), y: geo.size.height - 4)
                        }
                    }
                }
                .frame(height: 180)
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "chart.xyaxis.line")
                        .font(.system(size: 28))
                        .foregroundStyle(UH.Palette.muted)
                    Text("Pacing profile will appear once course is configured")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .frame(maxWidth: .infinity, minHeight: 140)
            }
        }
        .trainingCard()
    }

    private func xPos(_ km: Double, width: Double) -> Double {
        let left = 38.0
        let right = width - 10.0
        guard maxDist > 0 else { return left }
        return left + (km / maxDist) * (right - left)
    }

    private func yElevPos(_ elevation: Double, height: Double) -> Double {
        let top = 12.0
        let bottom = height - 6.0
        let span = max(1.0, maxElev - minElev)
        let frac = (elevation - minElev) / span
        return bottom - frac * (bottom - top)
    }

    private func yPacePos(_ pace: Double, top: Double, height: Double) -> Double {
        // Range 3.5 (fast) to 14.0 (slow steep hike)
        let minPace = 3.5
        let maxPace = 14.0
        let clamped = max(minPace, min(maxPace, pace))
        let frac = (clamped - minPace) / (maxPace - minPace)
        return top + frac * height
    }
}

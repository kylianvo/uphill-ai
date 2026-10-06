import SwiftUI

struct PacingSplitsTableView: View {
    let checkpoints: [PacedCheckpoint]
    @Binding var restMins: [Int: Int]
    let startClock: String

    init(
        checkpoints: [PacedCheckpoint],
        restMins: Binding<[Int: Int]>,
        startClock: String = "05:00"
    ) {
        self.checkpoints = checkpoints
        self._restMins = restMins
        self.startClock = startClock
    }

    private var etas: [String] {
        PacingCalculator.addClockEtas(paced: checkpoints, restMins: restMins, startClock: startClock)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("PACING SPLITS & AID STATION PLAN")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 0) {
                // Table Header
                HStack(spacing: 4) {
                    Text("WAYPOINT")
                        .frame(minWidth: 70, alignment: .leading)
                    Text("DIST")
                        .frame(width: 44, alignment: .trailing)
                    Text("GRADE")
                        .frame(width: 48, alignment: .trailing)
                    Text("PACE")
                        .frame(width: 52, alignment: .trailing)
                    Text("REST")
                        .frame(width: 50, alignment: .center)
                    Text("ETA")
                        .frame(width: 48, alignment: .trailing)
                }
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
                .padding(.vertical, 8)
                .padding(.horizontal, 10)
                .background(UH.Palette.surface.opacity(0.8))

                Divider()

                // Checkpoint Rows
                ForEach(Array(checkpoints.enumerated()), id: \.offset) { idx, cp in
                    HStack(spacing: 4) {
                        // Waypoint
                        HStack(spacing: 4) {
                            if cp.effort == "hike" {
                                Image(systemName: "figure.hiking")
                                    .font(.system(size: 10))
                                    .foregroundStyle(UH.Palette.ink)
                            }
                            Text(cp.name)
                                .font(UH.TextStyle.caption.weight(.medium))
                                .foregroundStyle(UH.Palette.ink)
                                .lineLimit(1)
                        }
                        .frame(minWidth: 70, alignment: .leading)

                        // Distance
                        Text(String(format: "%.1fk", cp.distanceKm))
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                            .frame(width: 44, alignment: .trailing)

                        // Grade
                        Text(cp.gradePct > 0 ? "+\(Int(cp.gradePct))%" : "\(Int(cp.gradePct))%")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundStyle(cp.gradePct > 10 ? Color(hex: "#ef4444") : (cp.gradePct > 0 ? UH.Palette.accentInk : UH.Palette.secondary))
                            .frame(width: 48, alignment: .trailing)

                        // Pace
                        Text(idx == 0 ? "—" : cp.targetPace)
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.ink)
                            .frame(width: 52, alignment: .trailing)

                        // Aid Station Rest (Editable)
                        Group {
                            if idx == 0 || idx == checkpoints.count - 1 {
                                Text("—")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundStyle(UH.Palette.muted)
                            } else {
                                Menu {
                                    ForEach([0, 2, 5, 10, 15, 20], id: \.self) { mins in
                                        Button("\(mins) min") {
                                            restMins[idx] = mins
                                            UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                        }
                                    }
                                } label: {
                                    HStack(spacing: 2) {
                                        Text("\(restMins[idx] ?? 0)m")
                                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                                        Image(systemName: "pencil")
                                            .font(.system(size: 8))
                                    }
                                    .foregroundStyle((restMins[idx] ?? 0) > 0 ? UH.Palette.accentInk : UH.Palette.secondary)
                                    .padding(.horizontal, 4)
                                    .padding(.vertical, 2)
                                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 4))
                                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(UH.Palette.line, lineWidth: 0.5))
                                }
                            }
                        }
                        .frame(width: 50, alignment: .center)

                        // ETA
                        Text(etas.indices.contains(idx) ? etas[idx] : "—")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                            .frame(width: 48, alignment: .trailing)
                    }
                    .padding(.vertical, 8)
                    .padding(.horizontal, 10)
                    .background(idx % 2 == 0 ? Color.clear : UH.Palette.surface.opacity(0.4))

                    if idx < checkpoints.count - 1 {
                        Divider().opacity(0.5)
                    }
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
        }
        .trainingCard()
    }
}

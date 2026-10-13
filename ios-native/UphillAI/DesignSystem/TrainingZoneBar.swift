import SwiftUI

/// Five heart-rate zones on the entered resting-to-max range, or a schematic when anchors are incomplete.
struct TrainingZoneBar: View {
    var aetHr: Int? = nil
    var antHr: Int? = nil
    var restingHr: Int? = nil
    var maxHr: Int? = nil
    @State private var barWidth: CGFloat = 0

    var hasHeartRateScale: Bool {
        guard let restingHr, let aetHr, let antHr, let maxHr else { return false }
        return restingHr < aetHr && aetHr < antHr && antHr < maxHr
    }

    var boundaries: [CGFloat] {
        guard hasHeartRateScale, let restingHr, let aetHr, let antHr, let maxHr else { return [0, 0.2, 0.4, 0.6, 0.8, 1] }
        let span = CGFloat(maxHr - restingHr)
        let values = [restingHr, max(restingHr, Int(Double(aetHr) * 0.9)), aetHr, antHr, (antHr + maxHr) / 2, maxHr]
        return values.map { CGFloat($0 - restingHr) / span }
    }

    var body: some View {
        let antLabelPosition = max(0.55, min(boundaries[3], 0.75))
        let aetLabelPosition = min(max(boundaries[2], 0.25), antLabelPosition - 0.06)
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(alignment: .bottom, spacing: 0) {
                Text(aetHr.map { "AeT \($0)" } ?? "AeT —")
                    .frame(width: barWidth * aetLabelPosition, alignment: .trailing)
                Spacer(minLength: 0).frame(width: barWidth * (antLabelPosition - aetLabelPosition))
                Text(antHr.map { "AnT \($0)" } ?? "AnT —")
                    .frame(width: barWidth * (1 - antLabelPosition), alignment: .leading)
            }
            .font(UH.TextStyle.caption.monospacedDigit().weight(.bold))
            .foregroundStyle(UH.Palette.ink)
            .fixedSize(horizontal: false, vertical: true)

            GeometryReader { geometry in
                HStack(spacing: 0) {
                    ForEach(Array(["#0ea5e9", "#10b981", "#f59e0b", "#f97316", "#ef4444"].enumerated()), id: \.offset) { index, color in
                        Text(geometry.size.width * (boundaries[index + 1] - boundaries[index]) >= 18 ? "Z\(index + 1)" : "")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(Color.black)
                            .frame(width: geometry.size.width * (boundaries[index + 1] - boundaries[index]), height: 32)
                            .background(Color(hex: color))
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(alignment: .leading) {
                    ForEach([2, 3], id: \.self) { boundary in
                        Rectangle().fill(Color.white)
                            .frame(width: 3)
                            .overlay(Rectangle().stroke(UH.Palette.ink, lineWidth: 0.5))
                            .offset(x: geometry.size.width * boundaries[boundary] - 1.5)
                    }
                }
            }
            .frame(height: 32)
            .onGeometryChange(for: CGFloat.self) { $0.size.width } action: { barWidth = $0 }
            .accessibilityHidden(true)

            if hasHeartRateScale, let restingHr, let maxHr {
                ViewThatFits(in: .horizontal) {
                    HStack {
                        Text(L("Resting %lld bpm", restingHr))
                        Spacer()
                        Text(L("Max %lld bpm", maxHr))
                    }
                    VStack(alignment: .leading) {
                        Text(L("Resting %lld bpm", restingHr))
                        Text(L("Max %lld bpm", maxHr))
                    }
                }
                .font(UH.TextStyle.caption.monospacedDigit())
                .foregroundStyle(UH.Palette.secondary)
            }
            Text(hasHeartRateScale ? L("AeT: top of Zone 2. AnT: top of Zone 3.") : L("AeT: top of Zone 2. AnT: top of Zone 3. Zone widths are schematic."))
                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .accessibilityElement(children: .combine)
    }

}

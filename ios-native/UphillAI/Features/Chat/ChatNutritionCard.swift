import SwiftUI

struct ChatNutritionCard: View {
    let plan: NutritionPlan

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Fueling Strategy", systemImage: "drop.fill")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Text("\(Int(plan.avgCarbsPerHour))g carbs/h")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }

            HStack(spacing: UH.Space.regular) {
                VStack(alignment: .leading, spacing: 1) {
                    Text("TOTAL CARBS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Text("\(Int(plan.totalCarbs))g")
                        .font(UH.TextStyle.metric)
                        .foregroundStyle(UH.Palette.ink)
                }

                VStack(alignment: .leading, spacing: 1) {
                    Text("TOTAL SODIUM")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Text("\(Int(plan.totalSodium))mg")
                        .font(UH.TextStyle.metric)
                        .foregroundStyle(UH.Palette.ink)
                }

                VStack(alignment: .leading, spacing: 1) {
                    Text("TIMELINE")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.muted)
                    Text("\(plan.hourlyPlan.count) hours")
                        .font(UH.TextStyle.metric)
                        .foregroundStyle(UH.Palette.secondary)
                }
            }

            if !plan.products.isEmpty {
                Divider()
                VStack(spacing: 4) {
                    ForEach(plan.products.prefix(3)) { p in
                        HStack {
                            Text(p.name)
                                .font(UH.TextStyle.caption.weight(.semibold))
                                .foregroundStyle(UH.Palette.ink)
                                .lineLimit(1)
                            Spacer()
                            Text("\(p.totalQuantity)x")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.secondary)
                            Text("\(Int(p.carbsPerUnit))g C")
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .foregroundStyle(Color(hex: "#f59e0b"))
                        }
                        .padding(.vertical, 3)
                        .padding(.horizontal, 6)
                        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 6))
                    }
                }
            }

            if let firstTip = plan.tips.first {
                Text("💡 \(firstTip)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .padding(.top, 2)
            }
        }
        .uhCard()
    }
}

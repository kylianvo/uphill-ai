import SwiftUI

struct ChatGearCard: View {
    let plan: GearPlan

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Shoe Recommendations", systemImage: "shoe.fill")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Text("\(plan.recommendations.count) shoes")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }

            VStack(spacing: 6) {
                ForEach(plan.recommendations.prefix(3)) { shoe in
                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text(shoe.brand.uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            if !shoe.price.isEmpty {
                                Text(shoe.price)
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundStyle(UH.Palette.ink)
                            }
                        }

                        Text(shoe.model)
                            .font(UH.TextStyle.body.weight(.bold))
                            .foregroundStyle(UH.Palette.ink)

                        HStack(spacing: 6) {
                            if !shoe.drop.isEmpty {
                                Text("Drop: \(shoe.drop)")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            if !shoe.weight.isEmpty {
                                Text("· \(shoe.weight)")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                        }

                        if !shoe.pros.isEmpty {
                            Text("✓ \(shoe.pros)")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.accentInk)
                                .lineLimit(1)
                        }
                    }
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }
            }

            if let firstTip = plan.tips.first {
                Text("💡 \(firstTip)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
        }
        .uhCard()
    }
}

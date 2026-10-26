import SwiftUI

struct ChatGearCard: View {
    let plan: GearPlan
    @State private var expandedId: String?

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Label("Shoe Recommendations", systemImage: "shoe.fill")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.ink)
                Spacer()
                Text("\(min(plan.recommendations.count, 3)) shoes")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(UH.Palette.activeFill, in: Capsule())
            }

            VStack(spacing: 8) {
                ForEach(plan.recommendations.prefix(3)) { shoe in
                    ShoeCard(
                        shoe: shoe,
                        isExpanded: expandedId == shoe.id,
                        onToggle: { expandedId = expandedId == shoe.id ? nil : shoe.id }
                    )
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

import SwiftUI

struct ShoeRotationView: View {
    @Binding var rotation: ShoeRotation
    var onSelectSlot: ((ShoeRotationSlot) -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack {
                Text("SHOE ROTATION")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.muted)
                Spacer()
                Text("4 SLOTS ACTIVE")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(UH.Palette.accentInk)
            }

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: UH.Space.small) {
                ForEach(ShoeRotationSlot.allCases) { slot in
                    let item = rotation.shoe(for: slot)
                    slotCard(slot: slot, item: item)
                }
            }
        }
    }

    private func slotCard(slot: ShoeRotationSlot, item: ShoeItem?) -> some View {
        Button {
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
            onSelectSlot?(slot)
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                // Header: Slot tag & icon
                HStack {
                    Text(slot.title.uppercased())
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(UH.Palette.accentInk)
                    Spacer()
                    Image(systemName: slot.symbolFallback)
                        .font(.system(size: 12))
                        .foregroundStyle(UH.Palette.muted)
                }

                // Shoe graphic container (Studio light-base packshot aesthetic)
                ZStack {
                    RoundedRectangle(cornerRadius: UH.Radius.control)
                        .fill(UH.Palette.surface)
                        .frame(height: 72)
                        .overlay(
                            RoundedRectangle(cornerRadius: UH.Radius.control)
                                .stroke(UH.Palette.line, lineWidth: 1)
                        )

                    let asset = GearImageResolver.assetName(brand: item?.brand ?? "", model: item?.model ?? "", slot: slot)
                    if let uiImage = UIImage(named: asset) {
                        Image(uiImage: uiImage)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(height: 52)
                    } else {
                        Image(systemName: "shoe.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(UH.Palette.muted)
                    }
                }

                // Shoe info
                if let item {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(item.brand.uppercased())
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                        Text(item.model)
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(UH.Palette.ink)
                            .lineLimit(1)
                    }

                    // Wear bar
                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text("\(Int(item.distanceKm)) km")
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.ink)
                            Spacer()
                            Text("\(Int(item.wearRatio * 100))%")
                                .font(.system(size: 9.5, weight: .medium, design: .monospaced))
                                .foregroundStyle(wearColor(item.wearRatio))
                        }

                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule().fill(UH.Palette.line)
                                Capsule()
                                    .fill(wearColor(item.wearRatio))
                                    .frame(width: geo.size.width * CGFloat(item.wearRatio))
                            }
                        }
                        .frame(height: 4)
                    }
                } else {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("EMPTY SLOT")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.muted)
                        Text("Tap to assign shoe")
                            .font(.system(size: 11))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    .frame(height: 42)
                }
            }
            .padding(UH.Space.small)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("me.shoeRotation.\(slot.rawValue)")
    }

    private func wearColor(_ ratio: Double) -> Color {
        if ratio < 0.6 {
            return UH.Palette.accentInk
        } else if ratio < 0.85 {
            return Color(hex: "#f59e0b")
        } else {
            return UH.Palette.danger
        }
    }
}

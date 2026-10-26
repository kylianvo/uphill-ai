import SwiftUI

/// A catalog shoe as the Gear Vault shows it: packshot, brand, price, spec chips, and pros/cons on expand.
/// Used by the Gear Vault and by Coach chat; `onAssign` adds the rotation button (Gear Vault only).
struct ShoeCard: View {
    let shoe: ShoeRecommendation
    let isExpanded: Bool
    let onToggle: () -> Void
    var onAssign: (() -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top, spacing: 12) {
                // Studio light-base container
                ZStack {
                    RoundedRectangle(cornerRadius: UH.Radius.control)
                        .fill(UH.Palette.packshot)
                        .frame(width: 72, height: 72)
                        .overlay(
                            RoundedRectangle(cornerRadius: UH.Radius.control)
                                .stroke(UH.Palette.line, lineWidth: 1)
                        )

                    let asset = GearImageResolver.assetName(brand: shoe.brand, model: shoe.model)
                    if let uiImage = UIImage(named: asset) {
                        Image(uiImage: uiImage)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 58, height: 58)
                    } else {
                        Image(systemName: "shoe.fill")
                            .font(.system(size: 32))
                            .foregroundStyle(UH.Palette.muted)
                    }
                }

                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Text(shoe.brand.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .tracking(0.6)
                            .foregroundStyle(UH.Palette.accentInk)
                        Spacer()
                        if !shoe.price.isEmpty {
                            Text(shoe.price)
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(UH.Palette.hover, in: Capsule())
                                .foregroundStyle(UH.Palette.ink)
                        }
                    }

                    Text(shoe.model)
                        .font(UH.TextStyle.body.weight(.bold))
                        .foregroundStyle(UH.Palette.ink)

                    if !shoe.weight.isEmpty {
                        Text("Weight: \(shoe.weight)")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
            }

            // Specs grid
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    if !shoe.drop.isEmpty {
                        specChip(label: "DROP", value: shoe.drop)
                    }
                    if !shoe.stack.isEmpty {
                        specChip(label: "STACK", value: shoe.stack)
                    }
                    if !shoe.lugDepth.isEmpty && shoe.lugDepth != "0mm" {
                        specChip(label: "LUG", value: shoe.lugDepth)
                    }
                    if !shoe.outsoleCompound.isEmpty {
                        specChip(label: "GRIP", value: shoe.outsoleCompound)
                    }
                    if !shoe.foamMaterial.isEmpty {
                        specChip(label: "FOAM", value: shoe.foamMaterial)
                    }
                }
            }

            // Expanded Pros & Cons
            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    if !shoe.pros.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("PROS")
                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                .foregroundStyle(UH.Palette.accentInk)
                            Text(shoe.pros)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if !shoe.cons.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("CONS / TRADE-OFFS")
                                .font(.system(size: 9.5, weight: .bold, design: .monospaced))
                                .foregroundStyle(Color(hex: "#b45309"))
                            Text(shoe.cons)
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.ink)
                        }
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(hex: "#f59e0b").opacity(0.12), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    // Assign button
                    if let onAssign {
                        Button(action: onAssign) {
                            HStack {
                                Image(systemName: "plus.circle.fill")
                                Text("Assign to Shoe Rotation")
                            }
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.accentInk)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                            .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            // Expand / Collapse trigger
            Button {
                withAnimation(UH.Motion.standard) { onToggle() }
            } label: {
                HStack {
                    Text(isExpanded ? L("Show Less") : L("Details & Pros/Cons"))
                        .font(UH.TextStyle.caption.weight(.semibold))
                        .foregroundStyle(UH.Palette.secondary)
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(UH.Palette.muted)
                }
                .padding(.top, 4)
            }
            .buttonStyle(.plain)
        }
        .trainingCard()
    }

    private func specChip(label: String, value: String) -> some View {
        VStack(spacing: 1) {
            Text(label)
                .font(.system(size: 8.5, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)
            Text(value)
                .font(.system(size: 10.5, weight: .semibold, design: .monospaced))
                .foregroundStyle(UH.Palette.ink)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: 6))
        .overlay(RoundedRectangle(cornerRadius: 6).stroke(UH.Palette.line, lineWidth: 1))
    }
}

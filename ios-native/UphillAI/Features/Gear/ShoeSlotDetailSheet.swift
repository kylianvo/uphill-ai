import SwiftUI

struct ShoeSlotDetailSheet: View {
    @Environment(\.dismiss) private var dismiss
    let slot: ShoeRotationSlot
    @Binding var rotation: ShoeRotation
    var onOpenGearVault: (() -> Void)? = nil

    @State private var customBrand = ""
    @State private var customModel = ""
    @State private var maxDistanceKm: Double = 700
    @State private var showCustomForm = false

    private var currentShoe: ShoeItem? {
        rotation.shoe(for: slot)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    // Header Card: Current Shoe / Empty
                    currentShoeSection

                    // Quick Log Mileage Section
                    if let shoe = currentShoe {
                        mileageSection(shoe: shoe)
                    }

                    // Change / Assign Shoe Section
                    changeShoeSection

                    // AI Gear Specialist Button
                    if let onOpenGearVault {
                        Button {
                            dismiss()
                            onOpenGearVault()
                        } label: {
                            HStack(spacing: 8) {
                                Image(systemName: "sparkles")
                                    .foregroundStyle(UH.Palette.accentInk)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Find Matching Shoes with AI")
                                        .font(UH.TextStyle.body.weight(.semibold))
                                        .foregroundStyle(UH.Palette.ink)
                                    Text("Explore personalized recommendations in Gear Vault")
                                        .font(UH.TextStyle.caption)
                                        .foregroundStyle(UH.Palette.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.system(size: 13, weight: .semibold))
                                    .foregroundStyle(UH.Palette.muted)
                            }
                            .padding(UH.Space.regular)
                            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                    }

                    // Remove / Retire Slot Button
                    if currentShoe != nil {
                        Button(role: .destructive) {
                            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                            rotation.removeShoe(for: slot)
                            dismiss()
                        } label: {
                            HStack {
                                Spacer()
                                Image(systemName: "trash")
                                Text("Remove from \(slot.title) Slot")
                                Spacer()
                            }
                            .font(UH.TextStyle.body.weight(.semibold))
                            .foregroundStyle(UH.Palette.danger)
                            .padding(.vertical, 12)
                            .background(UH.Palette.danger.opacity(0.08), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(UH.Space.regular)
            }
            .navigationTitle("\(slot.title) Trainer")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                        .font(UH.TextStyle.label)
                }
            }
        }
    }

    // MARK: - Current Shoe View

    private var currentShoeSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(slot.title.uppercased())
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.accentInk)
                Text("· \(slot.subtitle)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                Spacer()
            }

            if let shoe = currentShoe {
                HStack(spacing: 16) {
                    // Packshot container
                    ZStack {
                        RoundedRectangle(cornerRadius: UH.Radius.control)
                            .fill(UH.Palette.surface)
                            .frame(width: 88, height: 88)
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))

                        let asset = GearImageResolver.assetName(brand: shoe.brand, model: shoe.model, slot: slot)
                        if let uiImage = UIImage(named: asset) {
                            Image(uiImage: uiImage)
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 72, height: 72)
                        } else {
                            Image(systemName: "shoe.fill")
                                .font(.system(size: 36))
                                .foregroundStyle(UH.Palette.muted)
                        }
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text(shoe.brand.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.secondary)
                        Text(shoe.model)
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)

                        HStack(spacing: 4) {
                            Text(L("%@ km logged", String(format: "%.0f", shoe.distanceKm)))
                                .font(UH.TextStyle.caption.weight(.semibold))
                                .foregroundStyle(UH.Palette.ink)
                            Text("· \(Int(shoe.wearRatio * 100))% wear")
                                .font(UH.TextStyle.caption)
                                .foregroundStyle(UH.Palette.secondary)
                        }
                        .padding(.top, 2)
                    }
                }

                // Wear progress bar
                VStack(spacing: 4) {
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule().fill(UH.Palette.line)
                            Capsule()
                                .fill(wearColor(shoe.wearRatio))
                                .frame(width: max(4, geo.size.width * CGFloat(shoe.wearRatio)))
                        }
                    }
                    .frame(height: 6)

                    HStack {
                        Text("0 km")
                        Spacer()
                        Text("\(Int(shoe.maxDistanceKm)) km expected life")
                    }
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(UH.Palette.muted)
                }
                .padding(.top, 4)
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "shoe.circle")
                        .font(.system(size: 40))
                        .foregroundStyle(UH.Palette.muted)
                    Text("No shoe assigned to this slot")
                        .font(UH.TextStyle.body.weight(.medium))
                        .foregroundStyle(UH.Palette.secondary)
                    Text("Select a recommended model below or configure your current pair.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, UH.Space.regular)
            }
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
    }

    // MARK: - Quick Mileage Logger

    private func mileageSection(shoe: ShoeItem) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("LOG RUN DISTANCE")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            Text("Quickly add kilometers from your latest run:")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)

            HStack(spacing: 8) {
                ForEach([5.0, 10.0, 15.0, 21.1], id: \.self) { km in
                    Button {
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                        rotation.addDistance(km, for: slot)
                    } label: {
                        Text("+\(km == 21.1 ? "21" : String(Int(km))) km")
                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                            .foregroundStyle(UH.Palette.ink)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 8)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
    }

    // MARK: - Change Shoe Section

    private var changeShoeSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("POPULAR \(slot.title.uppercased()) SHOES")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(UH.Palette.muted)

            VStack(spacing: 8) {
                ForEach(slot.popularPresets, id: \.model) { preset in
                    let isCurrent = currentShoe?.brand.lowercased() == preset.brand.lowercased() &&
                                    currentShoe?.model.lowercased() == preset.model.lowercased()

                    Button {
                        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                        let newShoe = ShoeItem(
                            slot: slot,
                            brand: preset.brand,
                            model: preset.model,
                            distanceKm: 0,
                            maxDistanceKm: 700
                        )
                        rotation.setShoe(newShoe)
                    } label: {
                        HStack(spacing: 12) {
                            // Mini thumbnail
                            ZStack {
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(UH.Palette.surface)
                                    .frame(width: 44, height: 44)
                                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(UH.Palette.line, lineWidth: 1))

                                let asset = GearImageResolver.assetName(brand: preset.brand, model: preset.model, slot: slot)
                                if let uiImage = UIImage(named: asset) {
                                    Image(uiImage: uiImage)
                                        .resizable()
                                        .aspectRatio(contentMode: .fit)
                                        .frame(width: 36, height: 36)
                                } else {
                                    Image(systemName: "shoe.fill")
                                        .font(.system(size: 18))
                                        .foregroundStyle(UH.Palette.muted)
                                }
                            }

                            VStack(alignment: .leading, spacing: 2) {
                                Text(preset.brand.uppercased())
                                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                                    .foregroundStyle(UH.Palette.secondary)
                                Text(preset.model)
                                    .font(UH.TextStyle.body.weight(.medium))
                                    .foregroundStyle(UH.Palette.ink)
                            }

                            Spacer()

                            if isCurrent {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(UH.Palette.accentInk)
                                    .font(.system(size: 18))
                            } else {
                                Text("Assign")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundStyle(UH.Palette.accentInk)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(UH.Palette.activeFill, in: Capsule())
                            }
                        }
                        .padding(8)
                        .background(isCurrent ? UH.Palette.hover : Color.clear, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(isCurrent ? UH.Palette.accentInk.opacity(0.3) : UH.Palette.line, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }

            // Custom Shoe Form Toggle
            Button {
                withAnimation(UH.Motion.standard) {
                    showCustomForm.toggle()
                }
            } label: {
                HStack {
                    Image(systemName: showCustomForm ? "chevron.up" : "plus.circle")
                    Text(showCustomForm ? L("Hide Custom Shoe Input") : L("Add Other Custom Model..."))
                }
                .font(UH.TextStyle.caption.weight(.semibold))
                .foregroundStyle(UH.Palette.secondary)
                .padding(.top, 4)
            }
            .buttonStyle(.plain)

            if showCustomForm {
                VStack(alignment: .leading, spacing: 10) {
                    TextField("Brand (e.g. Brooks)", text: $customBrand)
                        .textFieldStyle(.roundedBorder)
                    TextField("Model (e.g. Ghost 16)", text: $customModel)
                        .textFieldStyle(.roundedBorder)

                    Button {
                        guard !customBrand.isEmpty && !customModel.isEmpty else { return }
                        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                        let newShoe = ShoeItem(
                            slot: slot,
                            brand: customBrand.trimmingCharacters(in: .whitespacesAndNewlines),
                            model: customModel.trimmingCharacters(in: .whitespacesAndNewlines),
                            distanceKm: 0,
                            maxDistanceKm: maxDistanceKm
                        )
                        rotation.setShoe(newShoe)
                        customBrand = ""
                        customModel = ""
                        showCustomForm = false
                    } label: {
                        Text("Save as \(slot.title) Shoe")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(Color.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(customBrand.isEmpty || customModel.isEmpty ? UH.Palette.muted : UH.Palette.accentInk, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    }
                    .buttonStyle(.plain)
                    .disabled(customBrand.isEmpty || customModel.isEmpty)
                }
                .padding(UH.Space.small)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            }
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
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

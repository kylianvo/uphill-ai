import SwiftUI

/// Emerald filled button. Press feedback is instant (scale 0.97).
struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(UH.TextStyle.label)
            .foregroundStyle(UH.Palette.buttonInk)
            .frame(maxWidth: .infinity, minHeight: 48)
            .background(UH.Palette.accent.opacity(isEnabled ? 1 : 0.45),
                        in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.97 : 1)
            .opacity(configuration.isPressed && reduceMotion ? 0.8 : 1)
            .animation(reduceMotion ? nil : UH.Motion.standard, value: configuration.isPressed)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(UH.TextStyle.label)
            .foregroundStyle(UH.Palette.ink)
            .frame(maxWidth: .infinity, minHeight: 48)
            .background(Color.black.opacity(0.06), in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.97 : 1)
            .opacity(configuration.isPressed && reduceMotion ? 0.8 : 1)
            .animation(reduceMotion ? nil : UH.Motion.standard, value: configuration.isPressed)
    }
}

extension ButtonStyle where Self == PrimaryButtonStyle {
    static var uhPrimary: PrimaryButtonStyle { PrimaryButtonStyle() }
}

extension ButtonStyle where Self == SecondaryButtonStyle {
    static var uhSecondary: SecondaryButtonStyle { SecondaryButtonStyle() }
}

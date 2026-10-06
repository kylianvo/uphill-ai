import SwiftUI

extension View {
    /// White panel with the workspace line border, radius 12.
    func uhCard(padding: CGFloat = UH.Space.regular) -> some View {
        self
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(UH.Palette.line, lineWidth: 1))
    }

    /// Training card with radius 16 and soft border for high-touch screens.
    func trainingCard(padding: CGFloat = UH.Space.regular, radius: CGFloat = 16) -> some View {
        self
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: radius))
            .overlay(RoundedRectangle(cornerRadius: radius).stroke(UH.Palette.line, lineWidth: 1))
    }
}

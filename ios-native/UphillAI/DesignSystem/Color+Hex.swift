import SwiftUI

extension Color {
    /// `hex` is "#RRGGBB" or "RRGGBB". Only used with literals from Tokens.swift.
    init(hex: String) {
        let c = Color.rgbComponents(hex) ?? (0, 0, 0)
        self.init(red: c.r, green: c.g, blue: c.b)
    }

    static func rgbComponents(_ hex: String) -> (r: Double, g: Double, b: Double)? {
        let s = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        guard s.count == 6, let v = UInt32(s, radix: 16) else { return nil }
        return (Double((v >> 16) & 0xFF) / 255, Double((v >> 8) & 0xFF) / 255, Double(v & 0xFF) / 255)
    }
}

extension Color {
    /// Follows the system appearance. The app is locked to light today; this is for tokens that already have a dark value.
    init(light: String, dark: String) {
        self.init(uiColor: UIColor { $0.userInterfaceStyle == .dark ? UIColor(Color(hex: dark)) : UIColor(Color(hex: light)) })
    }
}

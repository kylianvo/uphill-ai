import SwiftUI

/// Uphill design tokens. Source: DESIGN.md and the web Phase 1 shell.
enum UH {
    enum Palette {
        static let accent = Color(hex: "#19ce8b")
        static let accentInk = Color(light: "#08764f", dark: "#19ce8b")
        static let buttonInk = Color(hex: "#063e2b")
        static let ink = Color(light: "#172b26", dark: "#e8f1ec")
        static let secondary = Color(light: "#455c52", dark: "#b4c5bb")
        static let muted = Color(light: "#5d7167", dark: "#9fb3a9")
        static let line = Color(light: "#dce5df", dark: "#2f403a")
        static let hover = Color(light: "#edf5f0", dark: "#1f2b26")
        static let surface = Color(light: "#f8faf8", dark: "#0f1613")
        static let card = Color(light: "#ffffff", dark: "#17201c")
        /// Tile behind product photos: dark products need a lighter field than the page in dark mode.
        static let packshot = Color(light: "#f8faf8", dark: "#2c3b35")
        /// Neutral wash for chips and quiet fills; replaces `Color.black.opacity(0.0x)`.
        static let tint = Color(light: "#000000", dark: "#ffffff").opacity(0.07)
        /// Text/icons on solid ink or accent-ink fills, which flip in dark.
        static let onSolid = Color(light: "#ffffff", dark: "#063e2b")
        static let activeFill = Color(hex: "#19ce8b").opacity(0.16)
        static let warningInk = Color(light: "#92400e", dark: "#fbbf24")
        static let warningFill = Color(hex: "#f59e0b").opacity(0.12)
        static let danger = Color(light: "#b42318", dark: "#f97066")
        /// Apple Health's heart pink, used only beside the Apple Health name.
        static let healthPink = Color(hex: "#ff2d55")
    }

    enum Space {
        static let compact: CGFloat = 8
        static let small: CGFloat = 12
        static let regular: CGFloat = 16
        static let medium: CGFloat = 20
        static let section: CGFloat = 24
        static let panel: CGFloat = 28
        static let reading: CGFloat = 32
    }

    enum Radius {
        static let topic: CGFloat = 6
        static let control: CGFloat = 8
        static let workoutDay: CGFloat = 10
        static let panel: CGFloat = 12
        static let landing: CGFloat = 16
    }

    /// System text styles so Dynamic Type works everywhere.
    enum TextStyle {
        static let screenTitle = Font.title.weight(.bold)
        static let sectionTitle = Font.title3.weight(.semibold)
        static let body = Font.body
        static let label = Font.subheadline.weight(.semibold)
        static let caption = Font.footnote
        static let disclosure = Font.footnote.weight(.semibold)
        static let eyebrow = Font.caption.weight(.bold)
        static let metric = Font.title2.weight(.bold).monospacedDigit()
    }

    enum Motion {
        /// Default: critically damped, no overshoot.
        static let standard = Animation.spring(response: 0.35, dampingFraction: 1.0)
        /// Only after a gesture that carried momentum.
        static let momentum = Animation.spring(response: 0.35, dampingFraction: 0.8)
    }
}

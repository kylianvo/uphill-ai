import SwiftUI

/// Uphill design tokens. Source: DESIGN.md and the web Phase 1 shell.
enum UH {
    enum Palette {
        static let accent = Color(hex: "#19ce8b")
        static let accentInk = Color(hex: "#08764f")
        static let buttonInk = Color(hex: "#063e2b")
        static let ink = Color(hex: "#172b26")
        static let secondary = Color(hex: "#455c52")
        static let muted = Color(hex: "#5d7167")
        static let line = Color(hex: "#dce5df")
        static let hover = Color(hex: "#edf5f0")
        static let surface = Color(hex: "#f8faf8")
        static let card = Color.white
        static let activeFill = Color(hex: "#19ce8b").opacity(0.16)
        static let warningInk = Color(hex: "#92400e")
        static let warningFill = Color(hex: "#f59e0b").opacity(0.12)
        static let danger = Color(hex: "#b42318")
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

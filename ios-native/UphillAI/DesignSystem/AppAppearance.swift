import SwiftUI

/// Light / Dark / follow the system, picked in Me and saved on the device.
enum AppAppearance: String, CaseIterable, Identifiable {
    case system, light, dark

    static let storageKey = "appAppearance"

    var id: String { rawValue }
    /// `nil` hands control back to the system setting.
    var colorScheme: ColorScheme? {
        switch self {
        case .system: nil
        case .light: .light
        case .dark: .dark
        }
    }
    var label: LocalizedStringKey {
        switch self {
        case .system: "Match system"
        case .light: "Light mode"
        case .dark: "Dark mode"
        }
    }
}

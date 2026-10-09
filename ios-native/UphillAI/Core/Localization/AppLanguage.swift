import Foundation
import SwiftUI

/// The app's display language, picked in Me and saved on the device. It drives the
/// SwiftUI locale (so `Text("…")` literals resolve from `Localizable.xcstrings`), the
/// `L(…)` lookups for strings built in code, and the `lang` sent to the backend.
enum AppLanguage: String, CaseIterable, Identifiable, Sendable {
    case en, vi

    static let storageKey = "appLanguage"

    var id: String { rawValue }
    var locale: Locale { Locale(identifier: rawValue) }
    /// Shown in its own language, so a user who can't read the current one can still find theirs.
    var nativeName: String {
        switch self {
        case .en: "English"
        case .vi: "Tiếng Việt"
        }
    }

    /// Read on every call: switching language takes effect without a relaunch.
    static var current: AppLanguage {
        UserDefaults.standard.string(forKey: storageKey).flatMap(AppLanguage.init(rawValue:)) ?? .en
    }

    /// The backend's `lang` parameter (`"en"` / `"vi"`).
    static var code: String { current.rawValue }

    fileprivate var bundle: Bundle {
        Bundle.main.path(forResource: rawValue, ofType: "lproj").flatMap(Bundle.init(path:)) ?? .main
    }
}

/// Translates a string built in code (view-model messages, enum labels, errors) into the
/// current language. The English text is the key, so a missing translation shows English.
func L(_ english: String) -> String {
    AppLanguage.current.bundle.localizedString(forKey: english, value: english, table: nil)
}

/// Same as `L`, for a key with format arguments: `L("Week %lld", n)`.
func L(_ english: String, _ args: CVarArg...) -> String {
    String(format: L(english), locale: AppLanguage.current.locale, arguments: args)
}

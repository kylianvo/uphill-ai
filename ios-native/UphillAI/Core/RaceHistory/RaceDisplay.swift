import Foundation

/// Display helpers shared by the race history screens. Numbers follow the app
/// language, not the device region.
enum RaceDisplay {
    static var isVietnamese: Bool { Locale.current.language.languageCode?.identifier == "vi" }
    static var locale: Locale { Locale(identifier: isVietnamese ? "vi_VN" : "en_US") }

    static func number(_ value: Double, vietnamese: Bool = isVietnamese) -> String {
        value.formatted(.number.precision(.fractionLength(0...1)).locale(Locale(identifier: vietnamese ? "vi_VN" : "en_US")))
    }

    static func discipline(_ raw: String, vietnamese: Bool = isVietnamese) -> String {
        raw == "road" ? "Road" : "Trail"
    }

    static func source(_ raw: String, vietnamese: Bool = isVietnamese) -> String {
        switch raw {
        case "manual": return vietnamese ? "Tự nhập" : "Manual entry"
        case "vbm": return "VBM"
        case "utmb": return "UTMB"
        default: return raw.uppercased()
        }
    }

    /// Rounds once, then splits, so 359.5 reads 6:00 rather than 5:60.
    static func pace(_ secPerKm: Double) -> String {
        let seconds = Int(secPerKm.rounded())
        return "\(seconds / 60):\(String(format: "%02d", seconds % 60))"
    }

    /// Pending VBM rows already show the date on their own line.
    static func stripTrailingDate(_ name: String) -> String {
        guard let range = name.range(of: #"\s*\(?\d{1,2}/\d{1,2}/\d{4}\)?\s*$"#, options: .regularExpression) else { return name }
        let stripped = String(name[..<range.lowerBound])
        return stripped.isEmpty ? name : stripped
    }
}

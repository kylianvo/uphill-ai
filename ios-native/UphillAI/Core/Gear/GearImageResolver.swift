import UIKit

enum GearImageResolver {
    /// Resolves the best packshot asset name for a given brand and shoe model.
    /// Falls back to the slot category asset (e.g. shoe_trail) if no specific model asset is bundled.
    static func assetName(brand: String, model: String, slot: ShoeRotationSlot? = nil) -> String {
        let b = brand.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        let m = model.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)

        // 1. Direct sanitized candidate
        let directCandidate = "shoe_" + sanitize("\(b)_\(m)")
        if UIImage(named: directCandidate) != nil {
            return directCandidate
        }

        // 2. Common alias mappings
        if b.contains("salomon") && m.contains("genesis") {
            if UIImage(named: "shoe_salomon_s_lab_genesis_2") != nil {
                return "shoe_salomon_s_lab_genesis_2"
            }
            if UIImage(named: "shoe_salomon_s_lab_genesis") != nil {
                return "shoe_salomon_s_lab_genesis"
            }
        }
        if b.contains("hoka") && m.contains("speedgoat") {
            if UIImage(named: "shoe_hoka_speedgoat_7") != nil {
                return "shoe_hoka_speedgoat_7"
            }
        }
        if b.contains("nike") && m.contains("pegasus") {
            if UIImage(named: "shoe_nike_pegasus_42") != nil {
                return "shoe_nike_pegasus_42"
            }
        }
        if b.contains("saucony") && m.contains("endorphin") && m.contains("speed") {
            if UIImage(named: "shoe_saucony_endorphin_speed_5") != nil {
                return "shoe_saucony_endorphin_speed_5"
            }
        }
        if b.contains("nike") && m.contains("vaporfly") {
            if UIImage(named: "shoe_nike_vaporfly_4") != nil {
                return "shoe_nike_vaporfly_4"
            }
        }
        if b.contains("saucony") && m.contains("edge") {
            if UIImage(named: "shoe_saucony_endorphin_edge") != nil {
                return "shoe_saucony_endorphin_edge"
            }
        }

        // 3. Fallback to category hero asset or default trail
        return slot?.assetName ?? "shoe_trail"
    }

    private static func sanitize(_ str: String) -> String {
        let filtered = str
            .replacingOccurrences(of: "+", with: "_plus")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "-", with: "_")
            .replacingOccurrences(of: ":", with: "_")
            .replacingOccurrences(of: " ", with: "_")
            .filter { $0.isLetter || $0.isNumber || $0 == "_" }
        return String(filtered)
    }
}

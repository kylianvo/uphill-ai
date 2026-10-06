import UIKit

enum NutritionImageResolver {
    /// Resolves the best packshot asset name for a given brand and product name.
    /// Falls back to the format category asset (e.g. nutrition_gel) if no specific product asset is bundled.
    static func assetName(brand: String, name: String, format: ProductFormat? = nil) -> String {
        let b = brand.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        let n = name.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)

        // 1. Direct sanitized candidate
        let directCandidate = "nutrition_" + sanitize("\(b)_\(n)")
        if UIImage(named: directCandidate) != nil {
            return directCandidate
        }

        // 2. Specific known product aliases
        if b.contains("precision") || b.contains("pf") {
            if n.contains("chew") && UIImage(named: "nutrition_pf_30_energy_chew") != nil {
                return "nutrition_pf_30_energy_chew"
            }
            if n.contains("drink") && UIImage(named: "nutrition_pf_carb_electrolyte_drink_mix") != nil {
                return "nutrition_pf_carb_electrolyte_drink_mix"
            }
            if n.contains("gel") && UIImage(named: "nutrition_pf_30_energy_gel") != nil {
                return "nutrition_pf_30_energy_gel"
            }
        }
        if b.contains("maurten") {
            if n.contains("solid") && UIImage(named: "nutrition_maurten_solid_160") != nil {
                return "nutrition_maurten_solid_160"
            }
            if n.contains("100") && n.contains("gel") && UIImage(named: "nutrition_maurten_gel_100") != nil {
                return "nutrition_maurten_gel_100"
            }
            if n.contains("160") && n.contains("mix") && UIImage(named: "nutrition_maurten_drink_mix_160") != nil {
                return "nutrition_maurten_drink_mix_160"
            }
        }

        // 3. Fallback to format asset (e.g. nutrition_gel, nutrition_solid, etc.)
        return format?.assetName ?? "nutrition_gel"
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

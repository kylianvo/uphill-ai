import UIKit

enum NutritionImageResolver {
    /// Resolves the best packshot asset name for a given brand and product name.
    /// Falls back to the format category asset (e.g. nutrition_drink_mix) if no specific product asset is bundled.
    static func assetName(brand: String, name: String, format: ProductFormat? = nil) -> String {
        let b = brand.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        let n = name.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        let combined = "\(b) \(n)"

        // 1. Direct sanitized candidate
        let directCandidate = "nutrition_" + sanitize("\(b)_\(n)")
        if UIImage(named: directCandidate) != nil {
            return directCandidate
        }

        // 2. Specific brand & product matches (ordered from most specific to general)

        // Precision Fuel & Hydration / PF / PH
        if b.contains("precision") || b.contains("pf") || b.contains("ph") || combined.contains("precision fuel") {
            if combined.contains("300") || combined.contains("flow") { return "nutrition_pf_300_flow_gel" }
            if combined.contains("90") { return "nutrition_pf_90_energy_gel" }
            if combined.contains("caffeine") || combined.contains("caf") { return "nutrition_pf_30_caffeine_gel" }
            if combined.contains("60") || (combined.contains("chew") && combined.contains("bar")) { return "nutrition_pf_60_energy_chew_bar" }
            if combined.contains("chew") { return "nutrition_pf_30_energy_chew" }
            if combined.contains("1500") { return "nutrition_ph_1500" }
            if combined.contains("1000") { return "nutrition_ph_1000" }
            if combined.contains("500") { return "nutrition_ph_500" }
            if combined.contains("drink") || combined.contains("carb") || combined.contains("electrolyte") { return "nutrition_pf_carb_electrolyte_drink_mix" }
            if combined.contains("gel") { return "nutrition_pf_30_energy_gel" }
        }

        // Maurten
        if b.contains("maurten") || combined.contains("maurten") {
            if combined.contains("solid") {
                if combined.contains(" c") || combined.contains("-c") || combined.contains("cocoa") {
                    return "nutrition_maurten_solid_160_c"
                }
                return "nutrition_maurten_solid_160"
            }
            if combined.contains("320") {
                if combined.contains("caf") || combined.contains("caffeine") {
                    return "nutrition_maurten_drink_mix_320_caf_100"
                }
                return "nutrition_maurten_drink_mix_320"
            }
            if combined.contains("160") {
                if combined.contains("gel") { return "nutrition_maurten_gel_160" }
                return "nutrition_maurten_drink_mix_160"
            }
            if combined.contains("100") {
                if combined.contains("caf") || combined.contains("caffeine") {
                    return "nutrition_maurten_gel_100_caf_100"
                }
                return "nutrition_maurten_gel_100"
            }
        }

        // GU Energy
        if b.contains("gu") || combined.contains("gu energy") || combined.contains("roctane") {
            if combined.contains("roctane") { return "nutrition_gu_roctane_energy_gel" }
            if combined.contains("chew") { return "nutrition_gu_energy_chews" }
            if combined.contains("gel") { return "nutrition_gu_energy_gel" }
        }

        // Science in Sport / SiS
        if b.contains("sis") || b.contains("science in sport") || combined.contains("beta fuel") {
            if combined.contains("nootropic") { return "nutrition_sis_beta_fuel_plus_nootropics_gel" }
            if combined.contains("chew") { return "nutrition_sis_beta_fuel_chew_bar" }
            if combined.contains("80") || combined.contains("sachet") { return "nutrition_sis_beta_fuel_80_sachet" }
            if combined.contains("beta") { return "nutrition_sis_beta_fuel_energy_gel" }
            if combined.contains("go") || combined.contains("isotonic") { return "nutrition_sis_go_isotonic_energy_gel" }
        }

        // Tailwind Nutrition
        if b.contains("tailwind") || combined.contains("tailwind") {
            if combined.contains("recovery") { return "nutrition_tailwind_recovery_mix" }
            if combined.contains("high carb") || combined.contains("high-carb") { return "nutrition_tailwind_high_carb_fuel" }
            if combined.contains("endurance") { return "nutrition_tailwind_endurance_fuel" }
        }

        // Näak / Naak
        if b.contains("n_ak") || b.contains("naak") || b.contains("näak") || combined.contains("naak") || combined.contains("näak") {
            if combined.contains("waffle") { return "nutrition_n_ak_ultra_energy_waffle_salted_caramel" }
            if combined.contains("maple") { return "nutrition_n_ak_ultra_energy_gel_salted_maple" }
            if combined.contains("drink") { return "nutrition_n_ak_boost_drink_mix_60" }
            return "nutrition_n_ak_boost_gel_30"
        }

        // Hammer Nutrition
        if b.contains("hammer") || combined.contains("hammer") {
            if combined.contains("vegan") || combined.contains("recovery") { return "nutrition_hammer_vegan_recovery_bar" }
            return "nutrition_hammer_bar"
        }

        // Bix
        if b.contains("bix") || combined.contains("bix") {
            return "nutrition_bix_the_big_40_energy_gel"
        }

        // 3. Fallback to format asset (e.g. nutrition_drink_mix, nutrition_solid, nutrition_gel)
        return format?.assetName ?? "nutrition_drink_mix"
    }

    private static func sanitize(_ str: String) -> String {
        let filtered = str
            .replacingOccurrences(of: "+", with: "_plus")
            .replacingOccurrences(of: "&", with: "_")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "-", with: "_")
            .replacingOccurrences(of: ":", with: "_")
            .replacingOccurrences(of: " ", with: "_")
            .filter { $0.isLetter || $0.isNumber || $0 == "_" }
        return String(filtered)
    }
}

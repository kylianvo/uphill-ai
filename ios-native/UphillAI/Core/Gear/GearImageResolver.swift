import UIKit

enum GearImageResolver {
    /// Resolves the best packshot asset name for a given brand and shoe model.
    /// Falls back to the slot category asset (e.g. shoe_trail) if no specific model asset is bundled.
    static func assetName(brand: String, model: String, slot: ShoeRotationSlot? = nil) -> String {
        let b = brand.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        var m = model.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)

        // Strip duplicate brand prefix from model if present (e.g. "Nike Nike Pegasus 41" -> "Pegasus 41")
        if m.hasPrefix(b) {
            m = m.dropFirst(b.count).trimmingCharacters(in: .whitespacesAndNewlines)
        }

        // 1. Direct sanitized candidate
        let directCandidate = "shoe_" + sanitize("\(b)_\(m)")
        if UIImage(named: directCandidate) != nil {
            return directCandidate
        }

        // 2. Specific brand & model matching (high-precision to avoid road vs trail mismatches)

        // Nike
        if b.contains("nike") {
            if m.contains("pegasus") && (m.contains("trail") || slot == .trail) {
                return "shoe_nike_acg_pegasus_trail"
            }
            if m.contains("zegama") { return "shoe_nike_acg_zegama_trail" }
            if m.contains("ultrafly") { return "shoe_nike_acg_ultrafly_trail" }
            if m.contains("alphafly") { return "shoe_nike_alphafly_3" }
            if m.contains("vaporfly") { return "shoe_nike_vaporfly_4" }
            if m.contains("zoom fly") || m.contains("zoomfly") { return "shoe_nike_zoom_fly_6" }
            if m.contains("vomero") {
                if m.contains("plus") { return "shoe_nike_vomero_plus" }
                return "shoe_nike_vomero_18"
            }
            if m.contains("pegasus") { return "shoe_nike_pegasus_42" }
        }

        // Salomon
        if b.contains("salomon") {
            if m.contains("genesis") {
                if m.contains("s/lab") || m.contains("s_lab") || m.contains("slab") {
                    return UIImage(named: "shoe_salomon_s_lab_genesis_2") != nil ? "shoe_salomon_s_lab_genesis_2" : "shoe_salomon_s_lab_genesis"
                }
                return UIImage(named: "shoe_salomon_genesis_2") != nil ? "shoe_salomon_genesis_2" : "shoe_salomon_genesis"
            }
            if m.contains("speedcross") { return "shoe_salomon_speedcross_6" }
            if m.contains("ultra glide") || m.contains("ultraglide") {
                if m.contains("s/lab") || m.contains("s_lab") || m.contains("slab") {
                    return "shoe_salomon_s_lab_ultra_glide_2"
                }
                return "shoe_salomon_ultra_glide_4"
            }
            if m.contains("pulsar") { return "shoe_salomon_s_lab_pulsar_4" }
            if m.contains("phantasm") { return "shoe_salomon_s_lab_phantasm_3" }
            if m.contains("aero glide") {
                if m.contains("grvl") || m.contains("gravel") { return "shoe_salomon_aero_glide_4_grvl" }
                return "shoe_salomon_aero_glide_4"
            }
            if m.contains("aero blaze") {
                if m.contains("grvl") || m.contains("gravel") { return "shoe_salomon_aero_blaze_4_grvl" }
                return "shoe_salomon_aero_blaze_4"
            }
        }

        // Saucony
        if b.contains("saucony") {
            if m.contains("endorphin") {
                if m.contains("azura") { return "shoe_saucony_endorphin_azura" }
                if m.contains("edge") { return "shoe_saucony_endorphin_edge" }
                if m.contains("speed") { return "shoe_saucony_endorphin_speed_5" }
                if m.contains("elite") { return "shoe_saucony_endorphin_elite_2" }
                if m.contains("pro") { return "shoe_saucony_endorphin_pro_5" }
            }
            if m.contains("azura") { return "shoe_saucony_endorphin_azura" }
            if m.contains("peregrine") { return "shoe_saucony_peregrine_16" }
            if m.contains("triumph") { return "shoe_saucony_triumph_23" }
            if m.contains("ride") { return "shoe_saucony_ride_19" }
            if m.contains("guide") { return "shoe_saucony_guide_19" }
        }

        // Hoka
        if b.contains("hoka") {
            if m.contains("speedgoat") { return "shoe_hoka_speedgoat_7" }
            if m.contains("tecton") { return "shoe_hoka_tecton_x_4" }
            if m.contains("mafate") { return "shoe_hoka_mafate_5" }
            if m.contains("clifton") {
                if m.contains("pro") { return "shoe_hoka_clifton_pro" }
                return "shoe_hoka_clifton_11"
            }
            if m.contains("mach") {
                if m.contains("x") { return "shoe_hoka_mach_x_3" }
                return "shoe_hoka_mach_7"
            }
            if m.contains("bondi") { return "shoe_hoka_bondi_9" }
            if m.contains("arahi") { return "shoe_hoka_arahi_8" }
            if m.contains("rocket") { return "shoe_hoka_rocket_x_3" }
            if m.contains("cielo") { return "shoe_hoka_cielo_x1_3_0" }
        }

        // Asics
        if b.contains("asics") {
            if m.contains("sonicblast") { return "shoe_asics_sonicblast_2" }
            if m.contains("metafuji") { return "shoe_asics_metafuji_trail_2" }
            if m.contains("trabuco") { return "shoe_asics_trabuco_14" }
            if m.contains("novablast") { return "shoe_asics_novablast_5" }
            if m.contains("superblast") { return "shoe_asics_superblast_3" }
            if m.contains("nimbus") { return "shoe_asics_gel_nimbus_28" }
            if m.contains("kayano") { return "shoe_asics_gel_kayano_32" }
            if m.contains("metaspeed") {
                if m.contains("edge") { return "shoe_asics_metaspeed_edge_tokyo" }
                return "shoe_asics_metaspeed_sky_tokyo"
            }
        }

        // Brooks
        if b.contains("brooks") {
            if m.contains("cascadia") {
                if m.contains("elite") { return "shoe_brooks_cascadia_elite" }
                return "shoe_brooks_cascadia_19"
            }
            if m.contains("catamount") { return "shoe_brooks_catamount_4" }
            if m.contains("glycerin") {
                if m.contains("max") { return "shoe_brooks_glycerin_max_2" }
                return "shoe_brooks_glycerin_23"
            }
        }

        // Altra
        if b.contains("altra") {
            if m.contains("mont blanc") || m.contains("mont_blanc") {
                if m.contains("carbon") { return "shoe_altra_mont_blanc_carbon" }
                return "shoe_altra_mont_blanc_speed"
            }
            if m.contains("olympus") { return "shoe_altra_olympus_6" }
            if m.contains("timp") { return "shoe_altra_timp_6" }
            if m.contains("torin") { return "shoe_altra_torin_8" }
            if m.contains("experience") {
                if m.contains("wild") {
                    if m.contains("plus") { return "shoe_altra_experience_wild_3_plus" }
                    return "shoe_altra_experience_wild_3"
                }
                return "shoe_altra_experience_flow_3"
            }
            if m.contains("paradigm") { return "shoe_altra_paradigm_8" }
        }

        // NNormal
        if b.contains("nnormal") {
            if m.contains("kjerag") { return "shoe_nnormal_kjerag_02" }
            if m.contains("tomir") { return "shoe_nnormal_tomir_2_0" }
            if m.contains("cadi") { return "shoe_nnormal_cadi" }
        }

        // Norda
        if b.contains("norda") {
            if m.contains("005") { return "shoe_norda_005" }
            if m.contains("055") { return "shoe_norda_055" }
            return "shoe_norda_001a"
        }

        // On
        if b.contains("on") {
            if m.contains("cloudmonster") {
                if m.contains("hyper") { return "shoe_on_cloudmonster_3_hyper" }
                return "shoe_on_cloudmonster_3"
            }
            if m.contains("cloudultra") {
                if m.contains("pro") { return "shoe_on_cloudultra_pro" }
                return "shoe_on_cloudultra_3"
            }
            if m.contains("cloudboom") {
                return "shoe_on_cloudboom_strike_2"
            }
        }

        // Puma
        if b.contains("puma") {
            if m.contains("fast") || m.contains("fast_r") { return "shoe_puma_fast_r_nitro_elite_3" }
            if m.contains("deviate") {
                if m.contains("elite") { return "shoe_puma_deviate_nitro_elite_4" }
                if m.contains("pure") { return "shoe_puma_deviate_nitro_pure" }
                return "shoe_puma_deviate_nitro_4"
            }
            if m.contains("velocity") {
                if m.contains("5") { return "shoe_puma_velocity_nitro_5" }
                return "shoe_puma_velocity_nitro_4"
            }
        }

        // Adidas
        if b.contains("adidas") {
            if m.contains("terrex") || m.contains("agravic") {
                if m.contains("speed ultra") { return "shoe_adidas_terrex_agravic_speed_ultra_2" }
                if m.contains("speed") { return "shoe_adidas_terrex_agravic_speed_2" }
                return "shoe_adidas_terrex_agravic_tt"
            }
            if m.contains("boston") { return "shoe_adidas_adizero_boston_13" }
            if m.contains("evo sl") { return "shoe_adidas_adizero_evo_sl" }
            if m.contains("pro evo") { return "shoe_adidas_adizero_adios_pro_evo_3" }
            if m.contains("adios pro") {
                if m.contains("5") { return "shoe_adidas_adizero_adios_pro_5" }
                return "shoe_adidas_adizero_adios_pro_4"
            }
        }

        // New Balance
        if b.contains("new balance") || b.contains("nb") {
            if m.contains("sc elite") || m.contains("supercomp elite") { return "shoe_new_balance_sc_elite_v6" }
            if m.contains("rebel") {
                if m.contains("v5") { return "shoe_new_balance_fuelcell_rebel_v5" }
                return "shoe_new_balance_supercomp_rebel_v1"
            }
            if m.contains("ellipse") { return "shoe_new_balance_ellipse" }
        }

        // Kailas
        if b.contains("kailas") {
            if m.contains("330") { return "shoe_kailas_fuga_ex330" }
            return "shoe_kailas_fuga_ex_pro"
        }

        // Mount to Coast
        if b.contains("mount to coast") {
            if m.contains("h1") { return "shoe_mount_to_coast_h1" }
            if m.contains("m1") { return "shoe_mount_to_coast_m1" }
            if m.contains("t1") { return "shoe_mount_to_coast_t1" }
            if m.contains("c1") { return "shoe_mount_to_coast_c1" }
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

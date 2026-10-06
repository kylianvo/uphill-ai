import Testing
import Foundation
@testable import UphillAI

@Suite("Product Image & Shoe Rotation Tests")
struct ProductImageAndShoeRotationTests {

    @Test func nutritionImageResolverMatchesAccurately() {
        // Precision Fuel & Hydration
        let pf90 = NutritionImageResolver.assetName(brand: "Precision Fuel & Hydration", name: "PF 90 Energy Gel")
        #expect(pf90 == "nutrition_pf_90_energy_gel")

        let pf300 = NutritionImageResolver.assetName(brand: "Precision Fuel", name: "PF 300 Flow Gel")
        #expect(pf300 == "nutrition_pf_300_flow_gel")

        let pf30Caf = NutritionImageResolver.assetName(brand: "Precision Fuel", name: "PF 30 Caffeine Gel")
        #expect(pf30Caf == "nutrition_pf_30_caffeine_gel")

        let pfChew = NutritionImageResolver.assetName(brand: "PF&H", name: "PF 30 Energy Chew")
        #expect(pfChew == "nutrition_pf_30_energy_chew")

        // Maurten
        let maurten160 = NutritionImageResolver.assetName(brand: "Maurten", name: "Gel 160")
        #expect(maurten160 == "nutrition_maurten_gel_160")

        let maurten320 = NutritionImageResolver.assetName(brand: "Maurten", name: "Drink Mix 320")
        #expect(maurten320 == "nutrition_maurten_drink_mix_320")

        // SiS
        let sisNootropic = NutritionImageResolver.assetName(brand: "Science in Sport", name: "Beta Fuel + Nootropics Gel")
        #expect(sisNootropic == "nutrition_sis_beta_fuel_plus_nootropics_gel")

        let sisChew = NutritionImageResolver.assetName(brand: "SiS", name: "Beta Fuel Chew Bar")
        #expect(sisChew == "nutrition_sis_beta_fuel_chew_bar")

        // GU
        let guRoctane = NutritionImageResolver.assetName(brand: "GU Energy", name: "Roctane Energy Gel")
        #expect(guRoctane == "nutrition_gu_roctane_energy_gel")

        // Fallback format
        let fallback = NutritionImageResolver.assetName(brand: "UnknownBrand", name: "SuperFuel Drink", format: .drinkMix)
        #expect(fallback == "nutrition_drink_mix")
    }

    @Test func gearImageResolverDistinguishesTrailAndRoad() {
        // Nike trail vs road
        let nikeTrail = GearImageResolver.assetName(brand: "Nike", model: "Pegasus Trail 5", slot: .daily)
        #expect(nikeTrail == "shoe_nike_acg_pegasus_trail")

        let nikeRoad = GearImageResolver.assetName(brand: "Nike", model: "Pegasus 41", slot: .daily)
        #expect(nikeRoad == "shoe_nike_pegasus_42")

        let nikeZegama = GearImageResolver.assetName(brand: "Nike", model: "Zegama 2", slot: .race)
        #expect(nikeZegama == "shoe_nike_acg_zegama_trail")

        // Salomon standard Genesis vs S/Lab Genesis
        let salomonGen = GearImageResolver.assetName(brand: "Salomon", model: "Genesis", slot: .daily)
        #expect(salomonGen == "shoe_salomon_genesis")

        let salomonSlab = GearImageResolver.assetName(brand: "Salomon", model: "S/Lab Genesis 2", slot: .race)
        #expect(salomonSlab == "shoe_salomon_s_lab_genesis_2")

        // Hoka trail
        let hokaSpeedgoat = GearImageResolver.assetName(brand: "Hoka", model: "Speedgoat 6", slot: .daily)
        #expect(hokaSpeedgoat == "shoe_hoka_speedgoat_7")
    }

    @Test func shoeRotationSlotMutationAndPresets() {
        var rotation = ShoeRotation.defaultRotation
        #expect(rotation.daily != nil)

        // Slots should have popular presets
        for slot in ShoeRotationSlot.allCases {
            #expect(!slot.popularPresets.isEmpty)
        }

        // Test assigning a new shoe
        let newShoe = ShoeItem(
            slot: .tempo,
            brand: "Saucony",
            model: "Endorphin Speed 4",
            distanceKm: 25.0,
            maxDistanceKm: 650.0
        )
        rotation.setShoe(newShoe)
        #expect(rotation.tempo?.brand == "Saucony")
        #expect(rotation.tempo?.model == "Endorphin Speed 4")
        #expect(rotation.tempo?.distanceKm == 25.0)

        // Test adding mileage
        rotation.addDistance(10.0, for: .tempo)
        #expect(rotation.tempo?.distanceKm == 35.0)

        // Test removing shoe
        rotation.removeShoe(for: .tempo)
        #expect(rotation.tempo == nil)
    }

    @Test func shoeRotationMatchesBackendJSON() throws {
        // Same shape as GET/PUT /api/shoe-rotation (backend/main.py ShoeRotationItem).
        let json = #"{"shoes":[{"slot":"trail","brand":"Hoka","model":"Speedgoat 6","distance_km":42.5,"max_distance_km":700,"is_retired":false,"notes":null}]}"#
        let rotation = try JSONCoding.decoder.decode(ShoeRotation.self, from: Data(json.utf8))
        #expect(rotation.trail?.distanceKm == 42.5)

        let encoded = try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(rotation)) as? [String: Any]
        let shoe = (encoded?["shoes"] as? [[String: Any]])?.first
        #expect(shoe?["distance_km"] as? Double == 42.5)
        #expect(shoe?["max_distance_km"] as? Double == 700)
        #expect(shoe?["is_retired"] as? Bool == false)
    }
}

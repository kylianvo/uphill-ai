import Foundation
import Testing
@testable import UphillAI

@Suite("Phase 5 Foundation Tests")
struct Phase5ModelsTests {

    // MARK: - 5A: Nutrition Lab Tests

    @Test func nutritionPlanDecodingAndCalculations() throws {
        let jsonStr = """
        {
            "products": [
                {
                    "brand": "Maurten",
                    "name": "Gel 100",
                    "total_quantity": 4,
                    "carbs_per_unit": 25.0,
                    "sodium_per_unit": 20.0,
                    "protein_per_unit": 0.0,
                    "tech_notes": "Hydrogel tech"
                },
                {
                    "brand": "Tailwind",
                    "name": "Endurance Fuel Drink Mix",
                    "total_quantity": 2,
                    "carbs_per_unit": 50.0,
                    "sodium_per_unit": 620.0,
                    "protein_per_unit": 0.0,
                    "tech_notes": "Sip regularly"
                }
            ],
            "hourly_plan": [
                { "hour": 1, "action": "Take 1x Gel 100", "carbs": 25.0, "sodium": 20.0 },
                { "hour": 2, "action": "Take 1x Gel 100 & 500ml Tailwind", "carbs": 50.0, "sodium": 330.0 }
            ],
            "tips": ["Drink with water", "Practice in long runs"],
            "feedback_token": "token-xyz"
        }
        """
        let plan = try JSONCoding.decoder.decode(NutritionPlan.self, from: Data(jsonStr.utf8))
        #expect(plan.products.count == 2)
        #expect(plan.products[0].format == .gel)
        #expect(plan.products[1].format == .drinkMix)
        #expect(plan.hourlyPlan.count == 2)
        #expect(plan.totalCarbs == 75.0)
        #expect(plan.totalSodium == 350.0)
        #expect(plan.avgCarbsPerHour == 37.5)
        #expect(plan.avgSodiumPerHour == 175.0)
        #expect(plan.tips.count == 2)
        #expect(plan.feedbackToken == "token-xyz")
    }

    @Test func nutritionServiceCalculateFueling() async throws {
        let client = makeStubClient { _ in
            let responseJson = """
            {
                "products": [
                    {
                        "brand": "GU",
                        "name": "Energy Gel",
                        "total_quantity": 3,
                        "carbs_per_unit": 22.0,
                        "sodium_per_unit": 60.0,
                        "protein_per_unit": 0.0,
                        "tech_notes": ""
                    }
                ],
                "hourly_plan": [
                    { "hour": 1, "action": "Consume 1 gel", "carbs": 22.0, "sodium": 60.0 }
                ],
                "tips": ["Stay hydrated"],
                "feedback_token": "tok123"
            }
            """
            return (200, Data(responseJson.utf8))
        }
        let service = NutritionService(client: client)
        let plan = try await service.calculateFueling(params: NutritionParams(distanceKm: 21.0, targetTimeHours: 2.0))
        #expect(plan.products.count == 1)
        #expect(plan.products.first?.brand == "GU")
        #expect(plan.hourlyPlan.first?.carbs == 22.0)
    }

    @Test func nutritionCatalogDecoding() throws {
        let jsonStr = """
        [
            {
                "id": 1,
                "brand": "Maurten",
                "name": "Gel 100",
                "type": "gel",
                "carbs_grams": 25.0,
                "sodium_mg": 20.0,
                "caffeine_mg": 0.0,
                "water_ratio_ml": 0.0
            }
        ]
        """
        let catalog = try JSONCoding.decoder.decode([CatalogProduct].self, from: Data(jsonStr.utf8))
        #expect(catalog.count == 1)
        #expect(catalog[0].brand == "Maurten")
        #expect(catalog[0].carbsGrams == 25.0)
    }

    // MARK: - 5B: Gear Vault Tests

    @Test func gearPlanDecodingAndShoeWear() throws {
        let jsonStr = """
        {
            "recommendations": [
                {
                    "model": "Speedcross 6",
                    "brand": "Salomon",
                    "foam_material": "EnergyCell+ (EVA)",
                    "outsole_compound": "Mud Contagrip",
                    "lug_depth": "5mm",
                    "drop": "10mm",
                    "stack": "32mm / 22mm",
                    "weight": "298g",
                    "price": "$145",
                    "pros": "Great grip",
                    "cons": "Narrow fit"
                }
            ],
            "tips": ["Test on trail before race day"],
            "feedback_token": "fb-gear-1"
        }
        """
        let gearPlan = try JSONCoding.decoder.decode(GearPlan.self, from: Data(jsonStr.utf8))
        #expect(gearPlan.recommendations.count == 1)
        #expect(gearPlan.recommendations[0].model == "Speedcross 6")
        #expect(gearPlan.recommendations[0].brand == "Salomon")

        // Shoe wear calculations
        let shoe = ShoeItem(slot: .trail, brand: "Salomon", model: "Genesis", distanceKm: 350, maxDistanceKm: 700)
        #expect(shoe.wearRatio == 0.5)
        #expect(shoe.remainingKm == 350.0)

        let rotation = ShoeRotation.previewDefault
        #expect(rotation.shoes.count == 4)
        #expect(rotation.shoe(for: .daily)?.brand == "Nike")
        #expect(rotation.shoe(for: .race)?.model == "Vaporfly 3")
    }

    @Test func gearServiceRecommendShoes() async throws {
        let client = makeStubClient { _ in
            let responseJson = """
            {
                "recommendations": [
                    {
                        "model": "Endorphin Pro 4",
                        "brand": "Saucony",
                        "foam_material": "PWRRUN PB",
                        "outsole_compound": "XT-900",
                        "lug_depth": "0mm",
                        "drop": "8mm",
                        "stack": "39.5mm / 31.5mm",
                        "weight": "212g",
                        "price": "$225",
                        "pros": "Propulsive plate",
                        "cons": "Stiff for slow runs"
                    }
                ],
                "tips": ["Wear thin socks"],
                "feedback_token": "fb-shoe"
            }
            """
            return (200, Data(responseJson.utf8))
        }
        let service = GearService(client: client)
        let plan = try await service.recommendShoes(params: GearParams(surface: "road", cushioning: "plush"))
        #expect(plan.recommendations.count == 1)
        #expect(plan.recommendations.first?.model == "Endorphin Pro 4")
    }

    // MARK: - 5C: Race History & Distance Badges Tests

    @Test func distanceCategoryMatching() {
        #expect(DistanceCategory.match(distanceKm: 5.0) == .fiveK)
        #expect(DistanceCategory.match(distanceKm: 10.0) == .tenK)
        #expect(DistanceCategory.match(distanceKm: 21.1) == .halfMarathon)
        #expect(DistanceCategory.match(distanceKm: 42.195) == .marathon)
        #expect(DistanceCategory.match(distanceKm: 50.0) == .fiftyK)
        #expect(DistanceCategory.match(distanceKm: 100.0) == .hundredK)
        #expect(DistanceCategory.match(distanceKm: 161.0) == .hundredMiles)
        #expect(DistanceCategory.match(distanceKm: 2.0) == nil)
    }

    @Test func distanceBadgeDerivation() throws {
        let results = [
            RaceResult(
                id: 1,
                raceName: "Parkrun 5K",
                raceDate: "2024-03-01",
                discipline: "road",
                distanceKm: 5.0,
                finishTimeSec: 1245, // 20:45
                selected: true
            ),
            RaceResult(
                id: 2,
                raceName: "City 10K",
                raceDate: "2024-04-10",
                discipline: "road",
                distanceKm: 10.0,
                finishTimeSec: 2580, // 43:00
                selected: true
            ),
            RaceResult(
                id: 3,
                raceName: "Vietnam Trail Marathon 50K",
                raceDate: "2024-01-20",
                discipline: "trail",
                distanceKm: 50.0,
                finishTimeSec: 21600, // 6:00:00
                selected: true
            ),
            RaceResult(
                id: 4,
                raceName: "Failed Ultra",
                raceDate: "2023-11-01",
                discipline: "trail",
                distanceKm: 100.0,
                finishTimeSec: nil,
                isDnf: true,
                selected: true
            )
        ]

        let badges = DistanceBadge.deriveBadges(from: results)
        #expect(badges.count == 7)

        let fiveK = badges.first { $0.category == .fiveK }
        #expect(fiveK?.unlocked == true)
        #expect(fiveK?.bestTimeSec == 1245)
        #expect(fiveK?.formattedPB == "20:45")

        let tenK = badges.first { $0.category == .tenK }
        #expect(tenK?.unlocked == true)
        #expect(tenK?.bestTimeSec == 2580)
        #expect(tenK?.formattedPB == "43:00")

        let hm = badges.first { $0.category == .halfMarathon }
        #expect(hm?.unlocked == false)
        #expect(hm?.formattedPB == "—")

        let fiftyK = badges.first { $0.category == .fiftyK }
        #expect(fiftyK?.unlocked == true)
        #expect(fiftyK?.bestTimeSec == 21600)
        #expect(fiftyK?.formattedPB == "6:00:00")

        let hundredK = badges.first { $0.category == .hundredK }
        #expect(hundredK?.unlocked == false) // DNF doesn't unlock
    }

    @Test func raceHistoryResponseDecoding() throws {
        let jsonStr = """
        {
            "claims": [
                {
                    "id": 10,
                    "source": "utmb",
                    "display_name": "Runner Name",
                    "sync_status": "ok",
                    "sync_error": null,
                    "verified": true,
                    "verification_methods": ["index"]
                }
            ],
            "results": [
                {
                    "id": 101,
                    "claim_id": 10,
                    "source": "utmb",
                    "race_name": "Ultra Trail Mount Fuji",
                    "race_date": "2023-04-21",
                    "discipline": "trail",
                    "distance_km": 164.0,
                    "elevation_gain_m": 7500.0,
                    "finish_time_sec": 108000,
                    "is_dnf": false,
                    "bib": "1234",
                    "selected": true,
                    "hidden": false,
                    "user_note": "Great race",
                    "verified": true,
                    "verification_methods": ["utmb_index"],
                    "rank_overall": 42,
                    "total_overall": 1200
                }
            ],
            "summary": {
                "trail_finishes": 1,
                "trail_dnfs": 0,
                "ultras": 1,
                "longest_finish": null,
                "road_hm_pr": null,
                "road_fm_pr": null
            }
        }
        """
        let response = try JSONCoding.decoder.decode(RaceHistoryResponse.self, from: Data(jsonStr.utf8))
        #expect(response.claims.count == 1)
        #expect(response.claims[0].source == "utmb")
        #expect(response.results.count == 1)
        #expect(response.results[0].category == .hundredMiles)
        #expect(response.results[0].formattedDuration == "30:00:00")
        #expect(response.summary.ultras == 1)
    }

    // MARK: - 5D: Goal Determiner Tests

    @Test func goalEstimateDecodingAndHelpers() throws {
        let jsonStr = """
        {
            "race_name": "UTMB 100M",
            "distance_km": 171.0,
            "elevation_gain_m": 10000.0,
            "base_flat_pace_min_km": 5.2,
            "predicted_time_mins": 1920.0,
            "adjusted_time_mins": 1800.0,
            "improvement_pct": 6.25,
            "goals": {
                "ambitious": 1692.0,
                "realistic": 1800.0,
                "safe": 1944.0
            },
            "benchmarks": [
                {
                    "year": 2023,
                    "finishers": 1750,
                    "finishers_men": 1500,
                    "finishers_women": 250,
                    "winner_time": "19:37:43",
                    "winner_time_women": "23:29:14",
                    "conditions_note": "Clear and dry",
                    "percentiles": {
                        "overall": {
                            "p5": "23:45:00",
                            "p10": "25:30:00",
                            "p50": "34:10:00",
                            "p90": "44:00:00"
                        }
                    }
                }
            ],
            "rank_transfer_mins": 1820.0,
            "percentile_transfer_mins": 1790.0,
            "target_profile_source": "gpx",
            "reference_profile_source": "gpx",
            "reference_confidence": "high"
        }
        """
        let estimate = try JSONCoding.decoder.decode(GoalEstimate.self, from: Data(jsonStr.utf8))
        #expect(estimate.raceName == "UTMB 100M")
        #expect(estimate.distanceKm == 171.0)
        #expect(estimate.goals?.realistic == 1800.0)
        #expect(estimate.benchmarks?.count == 1)
        #expect(estimate.benchmarks?[0].year == 2023)
        #expect(estimate.benchmarks?[0].percentiles?["overall"]?.p50 == "34:10:00")

        // Time parsing helpers
        let mins = GoalEstimate.parseTimeToMinutes("20:30")
        #expect(mins == 1230.0)

        let minsHms = GoalEstimate.parseTimeToMinutes("1:30:00")
        #expect(minsHms == 90.0)

        let formatted = GoalEstimate.formatMinutes(1230.0)
        #expect(formatted == "20:30")

        // Pace parsing helpers (m:ss -> decimal minutes/km)
        let pace630 = GoalEstimate.parsePaceToMinutes("6:30")
        #expect(pace630 == 6.5)

        let pace628 = GoalEstimate.parsePaceToMinutes("6:28.5")
        #expect(abs((pace628 ?? 0) - 6.475) < 0.001)

        let pace500 = GoalEstimate.parsePaceToMinutes("5:00")
        #expect(pace500 == 5.0)

        let paceDecimal = GoalEstimate.parsePaceToMinutes("5.5")
        #expect(paceDecimal == 5.5)
    }

    @Test func goalEstimateService() async throws {
        let client = makeStubClient { _ in
            let responseJson = """
            {
                "race_name": "Sapa 21K",
                "distance_km": 21.0,
                "elevation_gain_m": 1200.0,
                "goals": {"a": 160.0, "b": 170.0, "c": 185.0},
                "confidence": "medium",
                "reasoning": ["Anchored on your Sapa 2025 finish"],
                "sources": [{"key": "watch", "label": "Watch: 40 km/wk", "included": true}],
                "context": {"race": {"profile_source": "gpx"}, "athlete": {"easy_pace_min_km": 6.25}}
            }
            """
            return (200, Data(responseJson.utf8))
        }
        let service = GoalEstimateService(client: client)
        let res = try await service.estimateGoal(request: GoalEstimateRequest(raceName: "Sapa 21K", distanceKm: 21.0, elevationGainM: 1200.0))
        #expect(res.raceName == "Sapa 21K")
        #expect(res.goals?.ambitious == 160.0)
        #expect(res.goals?.safe == 185.0)
        #expect(res.referenceConfidence == "medium")
        #expect(res.baseFlatPaceMinKm == 6.25)
        #expect(res.targetProfileSource == "gpx")
        #expect(res.sources?.first?.key == "watch")
    }
}

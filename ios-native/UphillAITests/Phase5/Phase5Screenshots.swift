import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct Phase5Screenshots {
    private let outDir = "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/phase5"

    private func save<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 402, height: 874), scale: CGFloat = 2.0) {
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        controller.view.bounds = CGRect(origin: .zero, size: size)
        controller.view.backgroundColor = .systemBackground

        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()

        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let img = renderer.image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        try? img.pngData()?.write(to: url)
    }

    private func makeApp() throws -> AppModel {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let base = StubURLProtocol.register { _ in (200, json([:])) }
        let tokenStore = InMemoryTokenStore("tok")
        let app = AppModel(tokenStore: tokenStore, baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(user)
        return app
    }

    private func makeTestPlan() -> Plan {
        TestData.plan([
            "id": 101,
            "race_name": "Dalat Ultra Trail 50K",
            "race_date": "2026-11-20",
            "goal_type": "finish",
            "total_weeks": 12,
            "current_week": 4,
            "start_date": "2026-09-01",
            "plan_status": "active"
        ])
    }

    @Test func renderNutritionLabTimeline() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = NutritionService(client: client)

        let samplePlan = NutritionPlan(
            products: [
                NutritionProduct(brand: "Precision Fuel", name: "PF 30 Gel", totalQuantity: 4, carbsPerUnit: 30, sodiumPerUnit: 200, proteinPerUnit: 0, techNotes: "High-carb glucose:fructose formulation"),
                NutritionProduct(brand: "Maurten", name: "Drink Mix 160", totalQuantity: 2, carbsPerUnit: 40, sodiumPerUnit: 400, proteinPerUnit: 0, techNotes: "Hydrogel tech with 500ml water"),
                NutritionProduct(brand: "Precision", name: "Chews", totalQuantity: 2, carbsPerUnit: 30, sodiumPerUnit: 150, proteinPerUnit: 0, techNotes: "Solid chew for technical climbs")
            ],
            hourlyPlan: [
                HourlyEntry(hour: 1, action: "1x PF 30 Gel + 250ml water", carbs: 30, sodium: 200),
                HourlyEntry(hour: 2, action: "1x Drink Mix 160 (500ml) + 1x Chew", carbs: 70, sodium: 550),
                HourlyEntry(hour: 3, action: "1x PF 30 Gel + 250ml water", carbs: 30, sodium: 200),
                HourlyEntry(hour: 4, action: "1x Drink Mix 160 (500ml) + 1x PF 30 Gel", carbs: 70, sodium: 600)
            ],
            tips: [
                "Start fueling early at min 25 — do not wait until you feel drained.",
                "Sip 100-150ml fluid every 15-20 min in warm temperatures (22-26°C).",
                "Practice high-carb gut tolerance during your long weekend run."
            ]
        )

        let view = NutritionLabSheet(service: service, activePlan: makeTestPlan(), initialPlan: samplePlan)
        save(view, name: "phase5-nutrition-lab-timeline")
    }

    @Test func renderNutritionLabProducts() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = NutritionService(client: client)

        let samplePlan = NutritionPlan(
            products: [
                NutritionProduct(brand: "Maurten", name: "Gel 100", totalQuantity: 4, carbsPerUnit: 25, sodiumPerUnit: 20, proteinPerUnit: 0, techNotes: "Hydrogel tech 1:0.8 fructose ratio"),
                NutritionProduct(brand: "Maurten", name: "Drink Mix 160", totalQuantity: 2, carbsPerUnit: 40, sodiumPerUnit: 400, proteinPerUnit: 0, techNotes: "Hydrogel sports drink mix with 500ml water"),
                NutritionProduct(brand: "Precision Fuel", name: "Energy Chews", totalQuantity: 2, carbsPerUnit: 30, sodiumPerUnit: 150, proteinPerUnit: 0, techNotes: "2x2 gummy bite format for technical climbs"),
                NutritionProduct(brand: "Maurten", name: "Solid 160", totalQuantity: 1, carbsPerUnit: 40, sodiumPerUnit: 100, proteinPerUnit: 4, techNotes: "Oat and rice-based real food chew bar")
            ],
            hourlyPlan: [
                HourlyEntry(hour: 1, action: "1x Gel 100", carbs: 25, sodium: 20),
                HourlyEntry(hour: 2, action: "1x Drink Mix 160", carbs: 40, sodium: 400)
            ],
            tips: ["Practice fueling in training"]
        )

        let view = NutritionLabSheet(service: service, activePlan: makeTestPlan(), initialPlan: samplePlan, initialTab: .products)
        save(view, name: "phase5-nutrition-lab-products")
    }

    @Test func renderNutritionLabForm() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = NutritionService(client: client)
        let view = NutritionLabSheet(service: service, activePlan: makeTestPlan())
        save(view, name: "phase5-nutrition-lab-form")
    }

    @Test func renderGearVaultRecommendations() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = GearService(client: client)

        let samplePlan = GearPlan(
            recommendations: [
                ShoeRecommendation(
                    model: "S/LAB Genesis",
                    brand: "Salomon",
                    foamMaterial: "Energy Foam",
                    outsoleCompound: "Contagrip MA",
                    lugDepth: "4.5mm",
                    drop: "8mm",
                    stack: "30mm / 22mm",
                    weight: "258g",
                    price: "$200",
                    pros: "Superb rock grip, durable Matryx upper, lockdown comfort",
                    cons: "Snug fit for wider feet"
                ),
                ShoeRecommendation(
                    model: "Speedgoat 6",
                    brand: "Hoka",
                    foamMaterial: "CMEVA",
                    outsoleCompound: "Vibram Megagrip",
                    lugDepth: "5.0mm",
                    drop: "4mm",
                    stack: "33mm / 29mm",
                    weight: "278g",
                    price: "$155",
                    pros: "Plush all-day cushion, grippy Vibram traction on mud and wet roots",
                    cons: "Slightly bulky on technical scree scrambles"
                ),
                ShoeRecommendation(
                    model: "Endorphin Edge",
                    brand: "Saucony",
                    foamMaterial: "PWRRUN PB",
                    outsoleCompound: "PWRTRAC",
                    lugDepth: "4.0mm",
                    drop: "6mm",
                    stack: "35mm / 29mm",
                    weight: "255g",
                    price: "$200",
                    pros: "Carbitex AFX flexible carbon plate, high energy return on runnable sections",
                    cons: "High stack requires ankle awareness on off-camber terrain"
                )
            ],
            tips: [
                "Rotate between 2 pairs during training to allow foam recovery and reduce overuse injuries.",
                "Test trail shoes on a 25K+ simulation run with race-day socks before race week."
            ]
        )

        let view = GearVaultSheet(service: service, activePlan: makeTestPlan(), initialPlan: samplePlan)
        save(view, name: "phase5-gear-vault-recs")
    }

    @Test func renderGoalDeterminerForm() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = GoalEstimateService(client: client)
        let pacingService = PacingService(client: client)

        let view = GoalDeterminerSheet(
            service: service,
            pacingService: pacingService,
            activePlan: makeTestPlan()
        )
        save(view, name: "phase5-goal-determiner-form")
    }

    @Test func renderGoalDeterminer() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = GoalEstimateService(client: client)
        let pacingService = PacingService(client: client)

        let sampleEstimate = GoalEstimate(
            raceName: "Dalat Ultra Trail 50K",
            distanceKm: 50.0,
            elevationGainM: 2200.0,
            baseFlatPaceMinKm: 4.8,
            predictedTimeMins: 330.0,
            adjustedTimeMins: 330.0,
            improvementPct: 4.5,
            goals: GoalEstimateTiers(ambitious: 295.0, realistic: 330.0, safe: 375.0),
            benchmarks: [
                RaceBenchmark(
                    year: 2025,
                    finishers: 840,
                    finishersMen: 620,
                    finishersWomen: 220,
                    winnerTime: "4:05:22",
                    winnerTimeWomen: "4:48:10",
                    percentiles: [
                        "overall": PercentileSet(
                            p5: "4:32:00",
                            p10: "4:50:00",
                            p25: "5:18:00",
                            p50: "5:58:00",
                            p75: "6:45:00",
                            p90: "7:30:00"
                        )
                    ]
                )
            ],
            targetProfileSource: "gpx",
            referenceConfidence: "high",
            reasoning: [
                "Strong aerobic base from recent 50k and 100k race finishes.",
                "Course profile matches your strength in sustained moderate climbs.",
                "Targeting 5:30:00 places you squarely within the top 32% of the historical field."
            ]
        )

        let viewGoals = GoalDeterminerSheet(
            service: service,
            pacingService: pacingService,
            activePlan: makeTestPlan(),
            initialEstimate: sampleEstimate,
            initialTab: .goals
        )
        save(viewGoals, name: "phase5-goal-determiner")

        let viewUsed = GoalDeterminerSheet(
            service: service,
            pacingService: pacingService,
            activePlan: makeTestPlan(),
            initialEstimate: sampleEstimate,
            initialTab: .whatWeUsed
        )
        save(viewUsed, name: "phase5-goal-determiner-used")
    }

    @Test func renderPaceStrategy() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let pacingService = PacingService(client: client)
        let user = try? Fixture.decode(User.self, "auth_me.json")

        let view = PaceStrategySheet(
            service: pacingService,
            activePlan: makeTestPlan(),
            user: user,
            initialTargetMins: 330.0
        )
        save(view, name: "phase5-pace-strategy")
    }

    @Test func renderKnowledgeHub() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = KnowledgeService(client: client)

        let view = NavigationStack {
            KnowledgeHubScreen(service: service, initialCards: KnowledgeService.curatedCards)
        }
        save(view, name: "phase5-knowledge-hub")
    }

    @Test func renderRaceHistoryScreen() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = RaceHistoryService(client: client)

        let response = RaceHistoryResponse(
            claims: [
                RaceClaim(
                    id: 1,
                    source: "utmb",
                    displayName: "Viet Vo (UTMB Index 512)",
                    syncStatus: "synced",
                    verified: true,
                    verificationMethods: ["index_lookup"]
                )
            ],
            results: [
                RaceResult(
                    id: 101,
                    source: "utmb",
                    raceName: "UTMB CCC 100K",
                    raceDate: "2025-08-29",
                    discipline: "trail",
                    distanceKm: 101.5,
                    elevationGainM: 6100,
                    finishTimeSec: 52440,
                    rankOverall: 214,
                    totalOverall: 1900
                ),
                RaceResult(
                    id: 102,
                    source: "vbm",
                    raceName: "Dalat Ultra Trail 50K",
                    raceDate: "2025-03-15",
                    discipline: "trail",
                    distanceKm: 52.0,
                    elevationGainM: 2300,
                    finishTimeSec: 20880,
                    rankOverall: 42,
                    totalOverall: 840
                ),
                RaceResult(
                    id: 103,
                    source: "manual",
                    raceName: "Danang International Marathon (FM)",
                    raceDate: "2024-08-11",
                    discipline: "road",
                    distanceKm: 42.195,
                    elevationGainM: 120,
                    finishTimeSec: 11820,
                    rankOverall: 88,
                    totalOverall: 1200
                ),
                RaceResult(
                    id: 104,
                    source: "manual",
                    raceName: "VnExpress Midnight HM",
                    raceDate: "2024-11-24",
                    discipline: "road",
                    distanceKm: 21.0975,
                    elevationGainM: 40,
                    finishTimeSec: 5340,
                    rankOverall: 65,
                    totalOverall: 2500
                )
            ],
            summary: HistorySummary(
                trailFinishes: 2,
                trailDnfs: 0,
                ultras: 2,
                longestFinish: nil,
                roadHmPr: PRTime(timeSec: 5340),
                roadFmPr: PRTime(timeSec: 11820)
            )
        )

        let view = NavigationStack {
            RaceHistoryScreen(service: service, initialHistory: response)
        }
        save(view, name: "phase5-race-history")
    }

    @Test func renderProfileWithBadgesAndGear() throws {
        let app = try makeApp()
        app.shoeRotation = ShoeRotation.previewDefault

        let results = [
            RaceResult(id: 1, raceName: "Parkrun 5K", raceDate: "2024-05-12", distanceKm: 5.0, finishTimeSec: 1220),
            RaceResult(id: 2, raceName: "City 10K", raceDate: "2024-06-20", distanceKm: 10.0, finishTimeSec: 2540),
            RaceResult(id: 3, raceName: "Midnight HM", raceDate: "2024-11-24", distanceKm: 21.1, finishTimeSec: 5340),
            RaceResult(id: 4, raceName: "Danang Marathon", raceDate: "2024-08-11", distanceKm: 42.2, finishTimeSec: 11820),
            RaceResult(id: 5, raceName: "Dalat Trail 50K", raceDate: "2025-03-15", distanceKm: 52.0, finishTimeSec: 20880),
            RaceResult(id: 6, raceName: "UTMB CCC 100K", raceDate: "2025-08-29", distanceKm: 101.5, finishTimeSec: 52440)
        ]
        let badges = DistanceBadge.deriveBadges(from: results)

        let view = ProfileView(app: app, initialBadges: badges)
        save(view, name: "phase5-profile-with-badges-and-gear")
    }

    @Test func renderConnectedAccounts() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = DeviceConnectionService(client: client)

        let initialStatus = DeviceConnectionStatus(
            coros: CorosConnectionStatus(
                connected: true,
                lastSyncAt: "2026-10-06T08:30:00Z",
                deviceModel: "COROS APEX 2 Pro"
            )
        )

        let view = VStack(alignment: .leading, spacing: 16) {
            ConnectedAccountsView(service: service, initialStatus: initialStatus)
        }
        .padding(16)
        .background(UH.Palette.surface)
        save(view, name: "phase5-connected-accounts")
    }

    @Test func renderCorosPushButton() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let service = DeviceConnectionService(client: client)

        let initialStatus = CorosPushStatus(
            connected: true,
            lastPushedAt: "2026-10-06T09:00:00Z",
            outOfDate: false,
            partial: false,
            lastSummary: CorosPushSummary(
                daysSent: 14,
                workoutsSent: 10,
                leftInUphill: 2,
                lockedDays: 1,
                invalid: 0,
                windowEnd: "2026-10-20",
                planStart: "2026-10-06"
            )
        )

        let view = VStack(alignment: .leading, spacing: 12) {
            Text("Plan Header Action").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
            CorosPushButton(service: service, initialStatus: initialStatus)
            CorosAttribution(deviceModel: "COROS APEX 2 Pro")
        }
        .padding(16)
        .background(UH.Palette.surface)
        save(view, name: "phase5-coros-push-button")
    }

    @Test func renderCalendarExportSheet() async throws {
        let fake = FakePlanService()
        let plan = makeTestPlan()
        let workouts = [
            TestData.workout(["id": 1, "week_number": 1, "day_of_week": "Monday", "title": "Easy Aerobic Run", "type": "Easy", "duration_minutes": 50, "phase": "Build"]),
            TestData.workout(["id": 2, "week_number": 1, "day_of_week": "Wednesday", "title": "Hill Repeats", "type": "Workout", "duration_minutes": 60, "phase": "Build"]),
            TestData.workout(["id": 3, "week_number": 1, "day_of_week": "Saturday", "title": "Long Run", "type": "Long", "duration_minutes": 150, "phase": "Build"]),
            TestData.workout(["id": 4, "week_number": 1, "day_of_week": "Sunday", "title": "Rest & Recovery", "type": "Rest", "duration_minutes": 0, "phase": "Build"])
        ]
        let snapshot = PlanSnapshot(plan: plan, workouts: workouts)
        fake.activeResult.withLock { $0 = .success(snapshot) }

        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(secondsFromGMT: 0)!
        var c = DateComponents()
        c.year = 2026; c.month = 10; c.day = 5
        let now = cal.date(from: c)!

        let model = PlanViewModel(
            service: fake,
            cache: .inMemory(),
            now: { now },
            calendar: cal
        )
        await model.load()

        let sheet = ExportCalendarSheet(model: model)
        save(sheet, name: "phase5-calendar-export")
    }

    @Test func renderPaceStrategyWithGpx() throws {
        let client = makeStubClient { _ in (200, json([:])) }
        let pacingService = PacingService(client: client)
        let user = try? Fixture.decode(User.self, "auth_me.json")

        let gpxXml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" creator="Uphill AI">
          <wpt lat="22.3300" lon="103.8500"><ele>1620.0</ele><name>CP1 - Cat Cat</name></wpt>
          <wpt lat="22.3600" lon="103.8800"><ele>1850.0</ele><name>CP2 - Sin Chai</name></wpt>
          <trk><name>Sa Pa Trail 25K</name><trkseg>
            <trkpt lat="22.3000" lon="103.8200"><ele>1500.0</ele></trkpt>
            <trkpt lat="22.3100" lon="103.8300"><ele>1550.0</ele></trkpt>
            <trkpt lat="22.3200" lon="103.8400"><ele>1600.0</ele></trkpt>
            <trkpt lat="22.3300" lon="103.8500"><ele>1620.0</ele></trkpt>
            <trkpt lat="22.3400" lon="103.8600"><ele>1700.0</ele></trkpt>
            <trkpt lat="22.3500" lon="103.8700"><ele>1780.0</ele></trkpt>
            <trkpt lat="22.3600" lon="103.8800"><ele>1850.0</ele></trkpt>
            <trkpt lat="22.3700" lon="103.8900"><ele>1800.0</ele></trkpt>
            <trkpt lat="22.3800" lon="103.9000"><ele>1720.0</ele></trkpt>
          </trkseg></trk>
        </gpx>
        """
        let data = gpxXml.data(using: .utf8)!
        let parsed = try? GpxCourseParser.parse(data: data, fileName: "sapa_trail_25k.gpx", intervalKm: 3.0)

        let view = PaceStrategySheet(
            service: pacingService,
            activePlan: makeTestPlan(),
            user: user,
            initialTargetMins: 165.0,
            initialGpxResult: parsed
        )
        save(view, name: "phase5-pace-strategy-gpx")
    }
}

import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Whole-tab renders of the five Progress states. Written only when SCREENSHOT_DIR is set;
/// SCREENSHOT_DARK renders dark, SCREENSHOT_VI renders Vietnamese.
@MainActor
struct ProgressScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String, height: CGFloat = 1400) {
        guard let outDir else { return }
        let suffix = (ProcessInfo.processInfo.environment["SCREENSHOT_DARK"] != nil ? "-dark" : "")
            + (ProcessInfo.processInfo.environment["SCREENSHOT_VI"] != nil ? "-vi" : "")
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        if ProcessInfo.processInfo.environment["SCREENSHOT_DARK"] != nil { controller.overrideUserInterfaceStyle = .dark }
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.3))
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let img = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try? img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/progress-\(name)\(suffix).png"))
    }

    private func response(_ object: [String: Any]) throws -> ProgressResponse {
        try JSONCoding.decoder.decode(ProgressResponse.self, from: JSONSerialization.data(withJSONObject: object))
    }

    private func screen(_ response: ProgressResponse, section: ProgressSection, goal: GoalPath? = nil) async -> some View {
        let model = ProgressViewModel(service: Fixed(response: response))
        await model.select(section)
        return ProgressTabView(model: model, goalPath: goal, deviceService: NoDevices(), onBuildPlan: {})
            .environment(\.locale, AppLanguage.current.locale)
    }

    private func corosTraining() throws -> ProgressResponse {
        let base = try JSONSerialization.jsonObject(with: Fixture.data("progress_training.json")) as! [String: Any]
        let weekly: [[String: Any]] = (1...6).map { ["week": $0, "done": $0 == 4 ? 3 : 4, "planned": 4] }
        var volume: [[String: Any]] = []
        var pace: [[String: Any]] = []
        for week in 1...6 {
            let km: Double = 40 + Double(week) * 3
            volume.append(["week": week, "km": km, "km_planned": km + 5, "climb_m": 900, "climb_planned": 1000])
            let p: Double = 6.4 - Double(week) * 0.05
            pace.append(["week": week, "pace": p])
        }
        let tomorrow = Calendar(identifier: .gregorian).date(byAdding: .day, value: 1, to: Date())!
        let nextDay = ProgressPoint.day.string(from: tomorrow)
        var cards: [[String: Any]] = [
            ["key": "today", "series": [], "note": ["key": "today", "health": "health.off", "contributors": ["hrv"],
                                                     "next": ["title": "Tempo 3×10 min", "type": "Tempo", "date": nextDay,
                                                              "duration_minutes": 60, "target_pace": "4:55-5:05"],
                                                     "adjust": ["kind": "cap"],
                                                     "tonight": ["target_min": 510, "usual_min": 470, "debt_min": 100,
                                                                 "long_run_tomorrow": false]]],
            ["key": "goal", "series": [], "note": [:]],
            responseCard("response.load.loading", hrvZ: -0.9, rhrZ: 0.7, hrvPct: -6, rhrDelta: 2),
            ["key": "week_review", "series": [], "note": ["key": "week_review", "week": 5, "facts": [
                ["kind": "short_sleep_long_run", "count": 1, "total": 1],
                ["kind": "hard_on_good_days", "count": 2, "total": 3],
                ["kind": "sessions", "count": 5, "total": 6],
            ]]],
            ["key": "aerobic_speed", "value": 6.1, "unit": "min/km", "series": pace,
             "note": ["key": "aerobic_speed", "b": "on", "a": "behind", "measured_pct": 3.2]],
            ["key": "consistency", "value": 96.0, "unit": "%", "series": weekly,
             "note": ["key": "consistency", "pct": 96, "top_missed_reason": "busy"]],
            ["key": "volume", "value": 58.0, "unit": "km", "series": volume, "note": ["key": "volume"]],
        ]
        cards += base["cards"] as! [[String: Any]]
        return try response(["section": "training", "connected": true, "has_plan": true, "plan_id": 3, "cards": cards, "pending": []])
    }

    /// 35 days: Base then Build, with this week's HRV dipping and resting HR rising as in a loading week.
    private func responseCard(_ key: String, phase: String = "Build", hrvZ: Double, rhrZ: Double,
                              hrvPct: Int, rhrDelta: Int) -> [String: Any] {
        let cal = Calendar(identifier: .gregorian)
        let series: [[String: Any]] = (0..<35).reversed().map { i in
            let day = cal.date(byAdding: .day, value: -i, to: Date())!
            let recent = i < 7
            let wobble = Double((i * 7) % 5) - 2
            return ["date": ProgressPoint.day.string(from: day),
                    "phase": i >= 21 ? "Base" : (i < 7 ? phase : "Build"),
                    "hrv": (recent ? 60.0 * (1 + Double(hrvPct) / 100) : 60.0) + wobble,
                    "rhr": (recent ? 48.0 + Double(rhrDelta) : 48.0) + wobble / 2]
        }
        return ["key": "response", "series": series, "band": [56.5, 63.5], "as_of": series.last!["date"]!,
                "source": "coros",
                "note": ["key": key, "phase": phase, "week": 6, "hrv_pct": hrvPct, "rhr_delta": rhrDelta,
                         "hrv_z": hrvZ, "rhr_z": rhrZ, "rhr_band": [46.6, 49.4]]]
    }

    @Test func renderTrainingResponse() async throws {
        if ProcessInfo.processInfo.environment["SCREENSHOT_VI"] != nil {
            UserDefaults.standard.set("vi", forKey: AppLanguage.storageKey)
        }
        defer { UserDefaults.standard.removeObject(forKey: AppLanguage.storageKey) }
        let states: [(String, String, String, Double, Double, Int, Int)] = [
            ("loading", "response.load.loading", "Build", -0.9, 0.7, -6, 2),
            ("adapting", "response.load.adapting", "Build", 0.9, -0.8, 5, -1),
            ("strained", "response.load.strained", "Peak", -1.9, 1.7, -13, 4),
            ("taper-stuck", "response.down.loading", "Taper", -0.8, 0.6, -5, 1),
        ]
        for (name, key, phase, hz, rz, pct, delta) in states {
            let card = try JSONCoding.decoder.decode(
                ProgressCard.self,
                from: JSONSerialization.data(withJSONObject: responseCard(key, phase: phase, hrvZ: hz, rhrZ: rz,
                                                                          hrvPct: pct, rhrDelta: delta)))
            save(TrainingResponseCardView(card: card).padding(UH.Space.regular)
                    .background(Color(.systemGroupedBackground)), name: "response-\(name)", height: 470)
            if name == "loading" {
                save(NavigationStack { TrainingResponseDetailView(card: card) }, name: "response-detail", height: 1250)
                // A scrubbed day on each kind of chart: the response signal and a generic daily card.
                let picked = Calendar(identifier: .gregorian).date(byAdding: .day, value: -3, to: Date())!
                let days = card.series.compactMap { row -> SignalChart.Day? in
                    guard let s = row["date"]?.stringValue, let d = ProgressPoint.day.date(from: s) else { return nil }
                    return SignalChart.Day(date: d, value: row["hrv"]?.doubleValue, phase: row["phase"]?.stringValue ?? "")
                }
                save(SignalChart(title: "HRV", unit: "ms", days: days, band: card.band, initialSelection: picked)
                        .padding(UH.Space.regular).background(Color(.systemGroupedBackground)),
                     name: "response-scrub", height: 330)
                let rhr = try JSONSerialization.jsonObject(with: Fixture.data("progress_health.json")) as! [String: Any]
                let rhrCard = try JSONCoding.decoder.decode(ProgressCard.self, from: JSONSerialization.data(
                    withJSONObject: (rhr["cards"] as! [[String: Any]]).first { $0["key"] as? String == "resting_hr" }!))
                let rhrDay = rhrCard.points.dropLast(4).last.flatMap { if case .day(let d) = $0.x { d } else { nil } }
                save(ProgressChart(card: rhrCard, detailed: true, initialSelection: rhrDay)
                        .padding(UH.Space.regular).background(Color(.systemGroupedBackground)),
                     name: "chart-scrub", height: 300)
            }
        }
    }

    private let goal = GoalPath(b: "on", a: "behind", measuredPct: 3.2, expectedPct: 2.5, weeks: 6, confidence: "medium")

    @Test func renderAllStates() async throws {
        if ProcessInfo.processInfo.environment["SCREENSHOT_VI"] != nil {
            UserDefaults.standard.set("vi", forKey: AppLanguage.storageKey)
        }
        defer { UserDefaults.standard.removeObject(forKey: AppLanguage.storageKey) }

        // 1. COROS athlete with a plan: every card.
        save(await screen(try corosTraining(), section: .training, goal: goal), name: "coros-training", height: 1900)
        save(await screen(try Fixture.decode(ProgressResponse.self, "progress_health.json"), section: .health),
             name: "coros-health", height: 1500)
        // 2. Apple Health only: health cards from Apple, no load or durability.
        let health = try JSONSerialization.jsonObject(with: Fixture.data("progress_health.json")) as! [String: Any]
        let appleCards = (health["cards"] as! [[String: Any]]).filter { $0["key"] as? String != "hrv" }.map {
            var c = $0; if c["source"] is String { c["source"] = "apple_health" }; return c
        }
        save(await screen(try response(["section": "health", "connected": true, "has_plan": true, "plan_id": 3,
                                        "cards": appleCards, "pending": [["key": "hrv", "needs": 14, "have": 9]]]),
                          section: .health), name: "apple-health", height: 1200)
        // 3. No device: Health is one connect card.
        save(await screen(try Fixture.decode(ProgressResponse.self, "progress_empty.json"), section: .health),
             name: "no-device", height: 700)
        // 4. No plan: Training is one create-plan card plus whatever the watch alone supports.
        save(await screen(try Fixture.decode(ProgressResponse.self, "progress_training.json"), section: .training),
             name: "no-plan", height: 1000)
        // 5. Brand-new athlete: nothing yet.
        save(await screen(try response(["section": "training", "connected": false, "has_plan": false, "plan_id": NSNull(),
                                        "cards": [], "pending": [["key": "durability", "needs": 3, "have": 0]]]),
                          section: .training), name: "brand-new", height: 700)
        // Largest accessibility text on the health section.
        save(await screen(try Fixture.decode(ProgressResponse.self, "progress_health.json"), section: .health)
                .dynamicTypeSize(.accessibility2), name: "coros-health-xl", height: 2600)
    }
}

private struct Fixed: ProgressServicing {
    let response: ProgressResponse
    func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse { response }
}

private struct NoDevices: DeviceConnectionServicing {
    struct Unused: Error {}
    func fetchStatus() async throws -> DeviceConnectionStatus { throw Unused() }
    func connectCorosURL() async throws -> URL { throw Unused() }
    func completeCoros(state: String, token: String) async throws -> Bool { false }
    func syncNow(days: Int) async throws -> DeviceSyncResult { throw Unused() }
    func syncFitness() async throws -> FitnessSyncResult { throw Unused() }
    func disconnectCoros() async throws {}
    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus { throw Unused() }
    func pushToCoros(clientToday: String, lang: String) async throws -> CorosPushOutcome { throw Unused() }
}

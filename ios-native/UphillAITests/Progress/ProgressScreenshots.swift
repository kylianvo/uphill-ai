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
                                                              "duration_minutes": 60]]],
            ["key": "goal", "series": [], "note": [:]],
            ["key": "aerobic_speed", "value": 6.1, "unit": "min/km", "series": pace,
             "note": ["key": "aerobic_speed", "b": "on", "a": "behind", "measured_pct": 3.2]],
            ["key": "consistency", "value": 96.0, "unit": "%", "series": weekly,
             "note": ["key": "consistency", "pct": 96, "top_missed_reason": "busy"]],
            ["key": "volume", "value": 58.0, "unit": "km", "series": volume, "note": ["key": "volume"]],
        ]
        cards += base["cards"] as! [[String: Any]]
        return try response(["section": "training", "connected": true, "has_plan": true, "plan_id": 3, "cards": cards, "pending": []])
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

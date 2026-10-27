import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// B-race screens: the Next races card, adding a risky race, the debrief. Written only when SCREENSHOT_DIR is set.
@MainActor
@Suite(.serialized)
struct BRaceScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String, height: CGFloat, wait: Int = 300) async throws {
        guard let outDir else { return }
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(wait))
        let img = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    private func decode<T: Decodable>(_ type: T.Type, _ object: [String: Any]) throws -> T {
        try JSONCoding.decoder.decode(T.self, from: JSONSerialization.data(withJSONObject: object))
    }

    @Test func renderBRaceScreens() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }

        let past = BRaceDecodingTests.race(level: "good", ["race_date": "2026-10-25", "opinion": "Good test. 25 km fits your training. Run it as a rehearsal: the same fuel, gear and pacing you will use on race day."])
        let risky = BRaceDecodingTests.race(level: "risky", ["id": 4, "race_name": "Sapa Mountain Race", "race_date": "2026-11-22",
                                                               "distance_km": 50, "effort": "training"])
        let plan = TestData.plan(["id": 5, "goal_type": "time", "race_name": "VMM 70K", "race_date": "2026-12-13",
                                  "start_date": "2026-09-28", "current_week": 5, "b_races": [past, risky]])
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: [TestData.workout(["plan_id": 5, "week_number": 5])])) }
        service.assessResult.withLock {
            $0 = .success(try! decode(BRaceAssessment.self, [
                "race": ["distance_km": 50, "elevation_gain_m": 2500, "options_km": [21, 50]],
                "predicted": ["low_sec": 23400, "high_sec": 27000],
                "verdict": ["level": "risky", "reasons": ["overlaps_taper", "longer_than_trained"], "taper_days": 3, "recovery_days": 10,
                            "suggestion": ["distance_km": 21, "effort": "training"],
                            "cost": ["changed": [["week": 9, "day": "Saturday", "title_before": "Mountain Long Run", "title_after": "Easy Recovery Run",
                                                  "minutes_before": 300, "minutes_after": 45]]]],
            ]))
        }
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        let now = cal.date(from: DateComponents(year: 2026, month: 10, day: 27, hour: 7))!
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        await model.load()
        let raceModel = try #require(model.bRaces.first)
        let riskyModel = try #require(model.bRaces.last)

        // The race list knows Dalat Ultra Trail and its distances, as /api/kb/match-race does in production.
        let base = StubURLProtocol.register { _ in
            (200, json(["matched": true, "auto_apply": true, "candidates": [],
                        "match": ["race_name": "Dalat Ultra Trail", "distances": [
                            ["label": "21km", "distance_km": 21, "elevation_gain_m": 900],
                            ["label": "50km", "distance_km": 50, "elevation_gain_m": 2300],
                            ["label": "75km", "distance_km": 75, "elevation_gain_m": 3600],
                            ["label": "100km", "distance_km": 100, "elevation_gain_m": 5000]]]]))
        }
        let raceMatch = RaceMatchService(client: APIClient(baseURL: { base }, tokenStore: InMemoryTokenStore(), session: StubURLProtocol.session()))
        let dalat = try decode(BRace.self, BRaceDecodingTests.race(level: "risky", ["id": 6, "race_name": "Dalat Ultra Trail", "race_date": "2026-11-28",
                                                                                     "distance_km": 50, "elevation_gain_m": 2300]))

        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let s = lang.rawValue
            try await save(NextRacesCard(model: model, onAdd: {}, onOpen: { _ in }, onDebrief: { _ in }).padding().environment(\.locale, lang.locale),
                           name: "brace-next-races-\(s)", height: 360)
            try await save(AddBRaceSheet(model: model, race: riskyModel).environment(\.locale, lang.locale), name: "brace-add-risky-\(s)", height: 1300, wait: 1200)
            try await save(AddBRaceSheet(model: model, race: raceModel).environment(\.locale, lang.locale), name: "brace-open-good-\(s)", height: 900, wait: 300)
            try await save(RaceDebriefSheet(model: model, race: raceModel).environment(\.locale, lang.locale), name: "brace-debrief-\(s)", height: 874)
            try await save(AddBRaceSheet(model: model, race: dalat, raceMatch: raceMatch).environment(\.locale, lang.locale),
                           name: "brace-add-matched-\(s)", height: 1300, wait: 2000)
            // The card lives in Manage now; the Plan screen only carries the due-debrief prompt.
            try await save(PlanView(model: model, generation: GenerationCenter(service: FakeGenerationService(), defaults: UserDefaults(suiteName: UUID().uuidString)!), onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list)
                .environment(\.locale, lang.locale), name: "brace-plan-debrief-prompt-\(s)", height: 1100, wait: 800)
            try await save(ManagePlanSheet(model: model, onStartNew: {}, onRaces: {}, initialPlans: [])
                .environment(\.locale, lang.locale), name: "brace-manage-races-row-\(s)", height: 700)
            try await save(RacesSheet(model: model).environment(\.locale, lang.locale), name: "brace-races-sheet-\(s)", height: 600)
        }
    }
}

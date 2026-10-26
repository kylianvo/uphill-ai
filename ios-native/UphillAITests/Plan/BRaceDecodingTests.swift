import Foundation
import Testing
@testable import UphillAI

@Suite("BRaceDecodingTests")
struct BRaceDecodingTests {
    static func race(level: String, _ overrides: [String: Any] = [:]) -> [String: Any] {
        var base: [String: Any] = [
            "id": 3, "plan_id": 1, "race_name": "Ta Xua Trail", "race_date": "2026-11-01", "distance_km": 25,
            "elevation_gain_m": 1000, "options_km": [15, 25], "effort": "race", "status": "planned",
            "kept_against": NSNull(), "opinion": "Good test.", "predicted": ["low_sec": 11100, "high_sec": 12300],
            "result_seconds": NSNull(), "debrief": NSNull(), "week": 5, "day": "Sunday",
            "verdict": [
                "level": level, "reasons": ["longer_than_trained"], "taper_days": 3, "recovery_days": 5,
                "numbers": ["effort_km": 35, "load_ratio": NSNull()],
                "suggestion": ["distance_km": 15, "effort": "training"],
                "cost": ["changed": [["week": 5, "day": "Sunday", "title_before": "Long Run", "title_after": "Ta Xua Trail",
                                      "minutes_before": 180, "minutes_after": 195]],
                         "peak_week_minutes": NSNull()],
            ],
        ]
        base.merge(overrides) { _, new in new }
        return base
    }

    @Test func decodesEveryLevel() {
        for (raw, level) in [("good", BRaceLevel.good), ("conditions", .conditions), ("risky", .risky), ("not_recommended", .notRecommended)] {
            let plan = TestData.plan(["b_races": [Self.race(level: raw)]])
            let race = plan.bRaces?.first
            #expect(race?.verdict.level == level)
            #expect(race?.verdict.suggestion == BRaceSuggestion(distanceKm: 15, effort: .training))
            #expect(race?.verdict.cost?.changed.first?.titleAfter == "Ta Xua Trail")
            #expect(race?.predicted?.lowSec == 11100 && race?.optionsKm == [15, 25])
        }
    }

    @Test func planWithoutRacesHasNone() {
        #expect(TestData.plan().bRaces == nil)
    }

    @Test func pastRaceAsksForADebriefOnce() {
        let plan = TestData.plan(["b_races": [Self.race(level: "good")]])
        let race = try! #require(plan.bRaces?.first)
        let day = { (s: String) in PlanCalendar.day(from: s)! }
        #expect(!race.needsDebrief(today: day("2026-10-31")))
        #expect(race.needsDebrief(today: day("2026-11-02")))
        let done = TestData.plan(["b_races": [Self.race(level: "good", ["debrief": ["text": "Nice."]])]]).bRaces!.first!
        #expect(!done.needsDebrief(today: day("2026-11-02")))
    }
}

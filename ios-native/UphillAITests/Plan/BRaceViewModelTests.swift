import Foundation
import Testing
@testable import UphillAI

@Suite("BRaceViewModelTests")
@MainActor
struct BRaceViewModelTests {
    private func verdict(_ level: String, suggestion: [String: Any]? = nil) -> BRaceVerdict {
        let object: [String: Any] = ["level": level, "reasons": [], "taper_days": 3, "recovery_days": 5,
                                     "suggestion": suggestion as Any? ?? NSNull(), "cost": NSNull()]
        return try! JSONCoding.decoder.decode(BRaceVerdict.self, from: JSONSerialization.data(withJSONObject: object))
    }

    private func makeModel(races: [[String: Any]], goal: String = "time") -> (PlanViewModel, FakePlanService) {
        let plan = TestData.plan(["id": 5, "goal_type": goal, "race_name": "VMM 70K", "race_date": "2026-12-13", "b_races": races])
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: [TestData.workout(["plan_id": 5])])) }
        return (PlanViewModel(service: service, cache: .inMemory()), service)
    }

    @Test func nextRacesSortedWithARaceLast() async {
        let (model, _) = makeModel(races: [BRaceDecodingTests.race(level: "good", ["id": 4, "race_date": "2026-11-22", "race_name": "Sapa"]),
                                           BRaceDecodingTests.race(level: "risky")])
        await model.load()
        #expect(model.nextRaces.map(\.name) == ["Ta Xua Trail", "Sapa", "VMM 70K"])
        #expect(model.nextRaces.last?.isGoal == true)
    }

    @Test func nonRacePlanHasNoNextRaces() async {
        let (model, _) = makeModel(races: [], goal: "start_running")
        await model.load()
        #expect(model.nextRaces.isEmpty && !model.canAddRaces)
    }

    @Test func riskyVerdictMakesSuggestionPrimary() {
        let input = BRaceInput(raceName: "Sapa", raceDate: "2026-11-22", distanceKm: 50, elevationGainM: 2500, effort: .race)
        let plan = BRaceChoice.options(for: verdict("risky", suggestion: ["distance_km": 21, "effort": "training"]), input: input)
        #expect(plan.primary.input.distanceKm == 21 && plan.primary.input.effort == .training)
        #expect(plan.primary.input.elevationGainM == 1050)  // climbing scales with the shorter distance
        #expect(plan.secondary?.input == input && plan.secondary?.isWarning == true)
    }

    @Test func notRecommendedAddsAsTraining() {
        let input = BRaceInput(raceName: "Late", raceDate: "2026-12-03", distanceKm: 25, elevationGainM: nil, effort: .race)
        let plan = BRaceChoice.options(for: verdict("not_recommended"), input: input)
        #expect(plan.primary.input.effort == .training && plan.secondary == nil)
    }

    @Test func goodVerdictAddsAsIs() {
        let input = BRaceInput(raceName: "Ta Xua", raceDate: "2026-11-01", distanceKm: 25, elevationGainM: 1000, effort: .race)
        #expect(BRaceChoice.options(for: verdict("good"), input: input).primary.input == input)
    }

    @Test func cancelCallsServiceAndReloads() async throws {
        let (model, service) = makeModel(races: [BRaceDecodingTests.race(level: "good")])
        await model.load()
        service.raceChangeResult.withLock {
            $0 = .success(try! JSONCoding.decoder.decode(BRaceChange.self, from: JSONSerialization.data(withJSONObject: [
                "race": BRaceDecodingTests.race(level: "good", ["status": "cancelled"]), "rebuild_job_ids": [],
            ])))
        }
        let error = await model.cancelRace(3)
        #expect(error == nil)
        let calls = service.calls.withLock { $0 }
        let cancel = try #require(calls.firstIndex(of: "race cancel 3"))
        #expect(calls[(cancel + 1)...].contains("active"))  // reloaded after the cancel
    }

    @Test func setupSendsOnlyCompleteRacesForRacePlans() throws {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        let day = { (s: String) in PlanCalendar.day(from: s, calendar: cal)! }
        var d = PlanSetupDraft(prefill: nil, today: day("2026-10-07"), calendar: cal)
        d.goal = SetupGoal.race
        d.raceDate = day("2026-12-13")
        d.bRaces = [SetupBRace(name: "Ta Xua", date: day("2026-11-01"), distanceKm: 25),
                    SetupBRace(name: "  ", date: day("2026-11-08"), distanceKm: nil)]
        let races = try #require(d.setupRaces(calendar: cal))
        #expect(races == [BRaceInput(raceName: "Ta Xua", raceDate: "2026-11-01", distanceKm: 25)])
        let body = try #require(try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(d.planBody(calendar: cal))) as? [String: Any])
        #expect((body["b_races"] as? [[String: Any]])?.first?["race_name"] as? String == "Ta Xua")
        d.goal = SetupGoal.returning
        #expect(d.setupRaces(calendar: cal) == nil)
    }
}

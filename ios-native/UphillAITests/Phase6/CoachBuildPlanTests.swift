import Foundation
import Testing
@testable import UphillAI

/// A coach building a plan for a runner: the request goes to the runner, the coach's own session is untouched,
/// and the coach then sees the draft on the runner's Plan tab.
@MainActor
struct CoachBuildPlanTests {
    @Test func testCoachSetupNeverTouchesCoachSession() async throws {
        let coach = try Fixture.decode(User.self, "coaching_coach_me.json")
        let athlete = try Fixture.decode(User.self, "coaching_athlete_profile.json")
        let paths = PathRecorder()
        let base = StubURLProtocol.register { request in
            paths.append(request.url?.path ?? "")
            return (200, Data(#"{"job_id":"job-7"}"#.utf8))
        }
        let app = AppModel(tokenStore: InMemoryTokenStore("tok"), baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(coach)

        let setup = app.makeSetup(mode: .newPlan, athlete: athlete)
        setup.selectGoal(.startRunning)
        await setup.submit()

        #expect(setup.didStart)
        #expect(paths.all.contains("/api/coaching/athletes/\(athlete.id)/generate-plan"))
        #expect(!paths.all.contains("/api/coach/generate-plan"))
        #expect(app.session.user?.id == coach.id)
        app.generation.reset()
    }

    @Test func testScopedActivePlanFallsBackToDraft() async throws {
        let draft = try Fixture.data("coaching_athlete_draft_plan.json")
        let service = PlanService(client: makeStubClient { request in
            let path = request.url?.path ?? ""
            if path.hasSuffix("/active-plan") { return (200, Data(#"{"active":false}"#.utf8)) }
            if path.hasSuffix("/plans/draft") { return (200, draft) }
            return (404, Data())
        }).scoped(toAthlete: 3)
        let snapshot = try #require(try await service.activePlan())
        #expect(snapshot.plan.planStatus == "draft")
        #expect(!snapshot.workouts.isEmpty)
    }

    @Test func testOwnActivePlanNeverFallsBackToDraft() async throws {
        let service = PlanService(client: makeStubClient { request in
            (request.url?.path ?? "").hasSuffix("/active-plan") ? (200, Data(#"{"active":false}"#.utf8)) : (500, Data())
        })
        #expect(try await service.activePlan() == nil)
    }
}

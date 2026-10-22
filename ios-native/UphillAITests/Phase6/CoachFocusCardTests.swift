import Foundation
import Testing
@testable import UphillAI

@MainActor
struct CoachFocusCardTests {
    private func athlete(_ code: String, _ sev: CoachSeverity) -> CoachOverviewAthlete {
        var a = CoachOverviewAthlete(athleteId: 7, name: "Minh")
        a.signals = [CoachSignal(code: code, severity: sev, params: [:])]
        return a
    }

    @Test func testCardActionsFollowSituation() {
        #expect(CoachFocus.primary(athlete("reported_pain", .actNow), planStatus: "active") == .adaptWeek)
        #expect(CoachFocus.primary(athlete("plan_to_review", .reviewBuild), planStatus: "active") == .reviewPlan)
        #expect(CoachFocus.primary(athlete("needs_plan", .reviewBuild), planStatus: nil) == .buildPlan)
        // The plan the coach is looking at decides over a stale overview: a draft is published.
        #expect(CoachFocus.primary(athlete("needs_plan", .reviewBuild), planStatus: "draft") == .openDraft)
        #expect(CoachFocus.primary(nil, planStatus: "draft") == .openDraft)
        #expect(CoachFocus.primary(athlete("race_soon", .highlight), planStatus: "active") == nil)
        #expect(CoachFocus.label(.reviewPlan) == "Mark reviewed")
        #expect(CoachFocus.label(.openDraft) == "Publish plan")
        #expect(CoachFocus.label(.reviewChanges) == "Approve changes")
    }

    @Test func testIssueSentencesEnViWithFallback() {
        let jump = PlanReviewIssue(code: "VOLUME_JUMP", week: 9, message: "raw model text")
        #expect(PlanReviewText.sentence(jump, lang: .en) == "Week 9: volume jumps too fast")
        #expect(PlanReviewText.sentence(jump, lang: .vi) == "Tuần 9: khối lượng tăng quá nhanh")
        let unknown = PlanReviewIssue(code: "SOMETHING_NEW", week: 2, message: "Week 2 does something new")
        #expect(PlanReviewText.sentence(unknown, lang: .en) == "Week 2 does something new")
        for code in PlanReviewText.codes {
            for lang in AppLanguage.allCases {
                let text = PlanReviewText.sentence(PlanReviewIssue(code: code, week: 3, message: "x"), lang: lang)
                #expect(text != "x", "\(code) \(lang)")
            }
        }
    }

    @Test func testPendingActionConsumedOnce() throws {
        let app = AppModel(tokenStore: InMemoryTokenStore("tok"), baseURL: { URL(string: "http://localhost")! },
                           session: StubURLProtocol.session(), cache: .inMemory())
        app.pendingCoachAction = .adaptWeek
        #expect(app.takePendingCoachAction() == .adaptWeek)
        #expect(app.takePendingCoachAction() == nil)
    }

    @Test func testReviewAndPublishRoutes() async throws {
        let paths = PathRecorder()
        let review = #"{"generated_block":2,"reviewed_block":1,"reviewed_at":null,"reviewed_by":null,"issues":[{"code":"VOLUME_JUMP","week":2,"message":"m"}],"feasibility":"stretch","levers":["Add a day"]}"#
        let service = CoachingService(client: makeStubClient { request in
            paths.append("\(request.httpMethod ?? "") \(request.url?.path ?? "")")
            if request.url?.path.hasSuffix("/publish") == true {
                return (200, Data(#"{"plan_id":5,"plan_status":"active","approved_count":3}"#.utf8))
            }
            return (200, Data(review.utf8))
        })
        let got = try await service.planReview(athleteId: 7, planId: 5)
        #expect(got.generatedBlock == 2 && got.reviewedBlock == 1 && got.issues.first?.code == "VOLUME_JUMP")
        #expect(got.feasibility == "stretch")
        _ = try await service.markReviewed(athleteId: 7, planId: 5, note: "ok")
        let pub = try await service.publish(athleteId: 7, planId: 5)
        #expect(pub.approvedCount == 3 && pub.planStatus == "active")
        #expect(paths.all == ["GET /api/coaching/athletes/7/plans/5/review", "POST /api/coaching/athletes/7/plans/5/review",
                              "POST /api/coaching/athletes/7/plans/5/publish"])
    }
}

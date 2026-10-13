import Foundation
import Testing
@testable import UphillAI

struct RaceDetailServiceTests {
    @Test func detailUsesOwnerPathAndCourseChoice() async throws {
        let client = makeStubClient { request in
            #expect(request.url?.path == "/api/race-history/results/7/detail")
            #expect(URLComponents(url: request.url!, resolvingAgainstBaseURL: false)?.queryItems?.first?.value == "10")
            return (200, try Fixture.data("race_detail.json"))
        }
        let detail = try await RaceHistoryService(client: client).detail(id: 7, courseId: 10, athleteId: nil)
        #expect(detail.result.id == 7)
        #expect(detail.courseContext.course?.editionStatus == "different")
        #expect(detail.performance.genderTopPct == nil)
    }
    @Test func coachUsesScopedPath() async throws {
        let client = makeStubClient { request in
            #expect(request.url?.path == "/api/coaching/athletes/3/race-history/results/7/detail")
            return (200, try Fixture.data("race_detail_missing.json"))
        }
        let detail = try await RaceHistoryService(client: client).detail(id: 7, courseId: nil, athleteId: 3)
        #expect(detail.courseContext.status == "missing")
    }
    @Test func inaccessibleResultDoesNotProduceDetail() async {
        let client = makeStubClient { _ in (404, json(["detail": "Not found"])) }
        await #expect(throws: APIError.self) {
            _ = try await RaceHistoryService(client: client).detail(id: 7, courseId: nil, athleteId: nil)
        }
    }
    @Test func ambiguousChoicesDecode() throws {
        let detail = try JSONCoding.decoder.decode(RaceDetailResponse.self, from: Fixture.data("race_detail_ambiguous.json"))
        #expect(detail.courseContext.candidates.count == 2)
        #expect(detail.courseContext.course == nil)
    }
    @Test func editionStatesDecodeWithoutInventingYear() throws {
        let data = try Fixture.data("race_detail.json")
        var object = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        var context = object["course_context"] as! [String: Any]
        var course = context["course"] as! [String: Any]
        for status in ["same", "unknown"] {
            course["edition_status"] = status
            course["edition_year"] = status == "unknown" ? NSNull() : 2024
            context["course"] = course; object["course_context"] = context
            let detail = try JSONCoding.decoder.decode(RaceDetailResponse.self, from: JSONSerialization.data(withJSONObject: object))
            #expect(detail.courseContext.course?.editionStatus == status)
            if status == "unknown" { #expect(detail.courseContext.course?.editionYear == nil) }
        }
    }
    @Test func comparisonLabels() {
        #expect(raceTimeDifference(-846) == "14:06 faster")
        #expect(raceTimeDifference(846) == "14:06 slower")
        #expect(raceTimeDifference(0) == "Same finish time")
    }
}

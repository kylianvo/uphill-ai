import Foundation
import Testing
@testable import UphillAI

@MainActor
struct RaceHistoryViewModelTests {
    @Test func savedWriteWithFailedRefreshRetainsOldHistory() async throws {
        let pending = RaceResult(id: 7, source: "vbm", raceName: "City Marathon", raceDate: "2023-12-03", discipline: "road", distanceKm: 42.195, finishTimeSec: 13154, selected: false)
        let history = RaceHistoryResponse(results: [pending])
        let client = makeStubClient { request in
            if request.httpMethod == "PATCH" {
                #expect(request.url?.path == "/api/race-history/results/7")
                return (200, try JSONCoding.encoder.encode(pending))
            }
            return (500, json(["detail": "Unavailable"]))
        }
        let model = RaceHistoryViewModel(service: RaceHistoryService(client: client), history: history)
        await model.confirm(id: 7, selected: true)
        #expect(model.history == history)
        #expect(model.errorMessage == "Saved, but refresh failed. Retry.")
        #expect(!model.isMutating)
    }
    @Test func missingRoadRecordsDecodeAsEmptyCards() throws {
        let body = json(["trail_finishes": 0, "trail_dnfs": 0, "ultras": 0,
                         "road_prs": ["5k": NSNull(), "10k": NSNull(), "hm": NSNull(),
                                      "fm": ["result_id": 7, "time_sec": 13154, "date": "2023-12-03", "stale": true]]])
        let summary = try JSONCoding.decoder.decode(HistorySummary.self, from: body)
        #expect(summary.roadPrs?["fm"]??.resultId == 7)
    }
}

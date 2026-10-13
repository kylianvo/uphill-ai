import Foundation
import Testing
@testable import UphillAI

@MainActor
struct RaceDetailViewModelTests {
    @Test func newerResponseWins() async throws {
        let fixture = try JSONCoding.decoder.decode(RaceDetailResponse.self, from: Fixture.data("race_detail.json"))
        let model = RaceDetailViewModel { id, _, _ in
            try? await Task.sleep(for: .milliseconds(id == 7 ? 100 : 1))
            var object = try JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(fixture)) as! [String: Any]
            var result = object["result"] as! [String: Any]
            result["id"] = id
            object["result"] = result
            return try JSONCoding.decoder.decode(RaceDetailResponse.self, from: JSONSerialization.data(withJSONObject: object))
        }
        let first = Task { await model.load(id: 7) }
        await Task.yield()
        await model.load(id: 8)
        await first.value
        #expect(model.detail?.result.id == 8)
        #expect(!model.isLoading)
    }
}

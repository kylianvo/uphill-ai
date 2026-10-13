import Testing
@testable import UphillAI

struct ManualRaceDraftTests {
    @Test func optionalFieldsClearAndDnfHasNoTime() throws {
        var draft = ManualRaceDraft()
        draft.raceName = "Manual race"
        draft.distance = "42.195"
        draft.duration = "3:39:14"
        draft.discipline = "road"
        #expect(try draft.payload().elevationGainM == nil)
        draft.elevation = "0"
        #expect(try draft.payload().elevationGainM == 0)
        draft.isDnf = true
        let changes = try draft.payload().patchChanges()
        #expect(changes["finish_time_sec"] == .null)
        #expect(changes["location"] == .null)
        #expect(changes["result_url"] == .null)
    }
    @Test func invalidRankAndUrlPreventSaving() {
        var draft = ManualRaceDraft()
        draft.raceName = "Manual race"; draft.distance = "42.195"; draft.duration = "3:39:14"
        draft.rankOverall = "11"; draft.totalOverall = "10"
        #expect(throws: (any Error).self) { try draft.payload() }
        draft.rankOverall = "3"; draft.resultUrl = "javascript:alert(1)"
        #expect(throws: (any Error).self) { try draft.payload() }
    }
}

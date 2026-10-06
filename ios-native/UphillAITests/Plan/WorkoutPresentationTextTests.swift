import Testing
@testable import UphillAI

struct WorkoutPresentationTextTests {
    @Test(arguments: [("Zone 1", "Zone 1"), ("Z2", "Zone 2"), ("2", "Zone 2"), ("zone 3", "Zone 3"), ("Z1-2", "Zone 1-2")])
    func zoneLabelNeverDoublesTheWord(raw: String, expected: String) {
        #expect(WorkoutTypePresentation.zoneLabel(raw) == expected)
    }

    @Test func restAndEmptyZonesHaveNoLabel() {
        #expect(WorkoutTypePresentation.zoneLabel("Rest") == nil)
        #expect(WorkoutTypePresentation.zoneLabel("  ") == nil)
        #expect(WorkoutTypePresentation.zoneLabel("Recovery") == "Recovery")
    }

    @Test func zoneShort() {
        #expect(WorkoutTypePresentation.zoneShort("Zone 1") == "Z1")
        #expect(WorkoutTypePresentation.zoneShort("Z4") == "Z4")
        #expect(WorkoutTypePresentation.zoneShort("Rest") == nil)
    }

    @Test func paceTileDropsUnitAndTightensRange() {
        #expect(WorkoutTypePresentation.paceTileValue("6:24 - 5:42 /km") == "6:24–5:42")
        #expect(WorkoutTypePresentation.paceTileValue("5:30 /km") == "5:30")
        #expect(WorkoutTypePresentation.paceTileValue("6:24–5:42/KM") == "6:24–5:42")
        #expect(WorkoutTypePresentation.paceTileValue(nil) == "—")
        #expect(WorkoutTypePresentation.paceTileValue("") == "—")
    }
}

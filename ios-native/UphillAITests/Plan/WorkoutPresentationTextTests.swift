import SwiftUI
import UIKit
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

    @Test func easyHillSprintsKeepAerobicPaceSeparateFromMaximalReps() {
        let w = TestData.workout(["type": "Easy", "title": "Easy + Hill Sprints", "target_zone": "Zone 2",
                                 "target_pace": "8:26 - 7:44 /km", "elevation_gain_m": 594.0,
                                 "interval_reps": 8, "interval_rep_value": 10.0, "interval_rep_unit": "s"])
        #expect(WorkoutTypePresentation.sessionPaceValue(for: w) == "8:26–7:44")
        let steps = WorkoutStepParser.parseSteps(workout: w, description: WorkoutStepParser.parseDescription(w.description), isTreadmill: false)
        #expect(steps[1].target == "8 × 10 s")
        let sprint = TestData.workout(["type": "Interval", "title": "Hill Sprints", "target_zone": "Zone 5", "target_pace": "4:00 /km"])
        #expect(WorkoutTypePresentation.sessionPaceValue(for: sprint) == "—")
    }

    @Test func paceTileDropsUnitAndTightensRange() {
        #expect(WorkoutTypePresentation.paceTileValue("6:24 - 5:42 /km") == "6:24–5:42")
        #expect(WorkoutTypePresentation.paceTileValue("5:30 /km") == "5:30")
        #expect(WorkoutTypePresentation.paceTileValue("6:24–5:42/KM") == "6:24–5:42")
        #expect(WorkoutTypePresentation.paceTileValue(nil) == "—")
        #expect(WorkoutTypePresentation.paceTileValue("") == "—")
    }
}

@MainActor
struct WorkoutColorTests {
    private func rgb(_ type: String, zone: String) -> [CGFloat] {
        let w = TestData.workout(["type": type, "target_zone": zone])
        let ui = UIColor(WorkoutTypePresentation.zoneColor(for: w)).resolvedColor(with: UITraitCollection(userInterfaceStyle: .light))
        var (r, g, b, a): (CGFloat, CGFloat, CGFloat, CGFloat) = (0, 0, 0, 0)
        ui.getRed(&r, green: &g, blue: &b, alpha: &a)
        return [r, g, b, a]
    }

    @Test func easyKeepsOneColourWhateverTheZoneRange() {
        let base = rgb("Easy Run", zone: "Z2")
        #expect(rgb("Easy Run", zone: "Z1-Z2") == base)
        #expect(rgb("Easy Run", zone: "Zone 2-3") == base)
        #expect(rgb("Aerobic Base Building", zone: "Z1-Z2") == base)
    }

    @Test func recoveryStaysDistinctFromEasy() {
        #expect(rgb("Recovery Run", zone: "Z1") != rgb("Easy Run", zone: "Z2"))
    }
}

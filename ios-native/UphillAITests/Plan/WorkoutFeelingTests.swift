import XCTest
@testable import UphillAI

final class WorkoutFeelingTests: XCTestCase {
    func testRpeMapping() {
        XCTAssertEqual(WorkoutFeeling.from(rpe: nil), nil)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 1), .veryLight)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 2), .veryLight)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 3), .light)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 4), .light)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 5), .moderate)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 6), .moderate)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 7), .hard)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 8), .hard)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 9), .maxEffort)
        XCTAssertEqual(WorkoutFeeling.from(rpe: 10), .maxEffort)
    }

    func testFeelingProperties() {
        XCTAssertEqual(WorkoutFeeling.veryLight.rpe, 2)
        XCTAssertEqual(WorkoutFeeling.light.rpe, 4)
        XCTAssertEqual(WorkoutFeeling.moderate.rpe, 6)
        XCTAssertEqual(WorkoutFeeling.hard.rpe, 8)
        XCTAssertEqual(WorkoutFeeling.maxEffort.rpe, 10)

        XCTAssertEqual(WorkoutFeeling.veryLight.label, "Very Light")
        XCTAssertEqual(WorkoutFeeling.light.label, "Light")
        XCTAssertEqual(WorkoutFeeling.moderate.label, "Moderate")
        XCTAssertEqual(WorkoutFeeling.hard.label, "Hard")
        XCTAssertEqual(WorkoutFeeling.maxEffort.label, "Max Effort")
    }
}

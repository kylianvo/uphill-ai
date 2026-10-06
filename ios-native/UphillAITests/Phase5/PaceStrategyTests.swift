import Testing
import Foundation
@testable import UphillAI

@Suite("PaceStrategyTests")
struct PaceStrategyTests {

    @Test func testSynthesizeCourse() {
        let cps = PacingCalculator.synthesizeCourse(distanceKm: 50.0, gainM: 2000.0, intervalKm: 5.0)
        #expect(cps.count == 11)
        #expect(cps.first?.name == "Start")
        #expect(cps.first?.distanceMeters == 0)
        #expect(cps.last?.distanceMeters == 50000.0)
        #expect(cps.last?.name == "KM 50")
    }

    @Test func testGradePaceMultiplier() {
        let flat = PacingCalculator.gradePaceMultiplier(grade: 0.0)
        #expect(abs(flat - 1.0) < 0.01)

        let uphill = PacingCalculator.gradePaceMultiplier(grade: 0.15)
        #expect(uphill > 1.5)

        let downhill = PacingCalculator.gradePaceMultiplier(grade: -0.10)
        #expect(downhill < 1.0)
    }

    @Test func testCalculateCheckpointPaces() {
        let cps = PacingCalculator.synthesizeCourse(distanceKm: 20.0, gainM: 1000.0, intervalKm: 5.0)
        let paced = PacingCalculator.calculateCheckpointPaces(
            checkpoints: cps,
            targetTimeMins: 140.0,
            splitBias: 0.0,
            runnerWeightKg: 68.0
        )

        #expect(paced.count == cps.count)
        #expect(paced.first?.targetPace == "—")
        #expect(paced.last?.cumulativeTimeMins ?? 0 > 80.0)
        #expect(paced.last?.energyKcal ?? 0 > 500)
    }

    @Test func testAddClockEtas() {
        let cps = PacingCalculator.synthesizeCourse(distanceKm: 10.0, gainM: 400.0, intervalKm: 5.0)
        let paced = PacingCalculator.calculateCheckpointPaces(checkpoints: cps, targetTimeMins: 60.0)

        let rest: [Int: Int] = [1: 10] // 10 min rest at aid station 1
        let etas = PacingCalculator.addClockEtas(paced: paced, restMins: rest, startClock: "06:00")

        #expect(etas.count == paced.count)
        #expect(etas.first == "06:00")
    }

    @Test func testSliderBounds() {
        let bounds = PacingCalculator.sliderBoundsMins(distanceKm: 50.0, gainM: 2200.0)
        #expect(bounds.min > 120.0)
        #expect(bounds.max > bounds.min)
    }
}

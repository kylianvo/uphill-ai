import Testing
@testable import UphillAI

struct RaceAchievementTests {
    @Test func hiddenFinishStillUnlocksAchievement() {
        let result = RaceResult(id: 1, raceName: "Trail 50", raceDate: "2026-05-16", distanceKm: 51, finishTimeSec: 22191, hidden: true)
        #expect(DistanceBadge.deriveBadges(from: [result]).first { $0.category == .fiftyK }?.unlocked == true)
    }
    @Test func latestFinishIsAnAchievementNotACrossCoursePb() {
        let older = RaceResult(id: 1, raceName: "Fast trail", raceDate: "2025-05-01", distanceKm: 51, finishTimeSec: 19000)
        let newer = RaceResult(id: 2, raceName: "Technical trail", raceDate: "2026-05-16", distanceKm: 51, finishTimeSec: 22191)
        #expect(DistanceBadge.deriveBadges(from: [older, newer]).first { $0.category == .fiftyK }?.resultId == 2)
    }
}

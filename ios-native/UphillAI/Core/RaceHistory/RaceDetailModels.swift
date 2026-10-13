import Foundation

struct RaceDetailResponse: Codable, Sendable {
    let result: RaceResult
    let performance: RacePerformance
    let previousFinish: PreviousRaceFinish?
    let courseContext: RaceCourseContext
    let historicalField: [String: JSONValue]?
}
struct RacePerformance: Codable, Sendable {
    let overallTopPct: Double?
    let genderTopPct: Double?
    let ageGroupTopPct: Double?
    let averagePaceSecKm: Double?
    let roadPbKey: String?
}
struct PreviousRaceFinish: Codable, Sendable {
    let resultId: Int
    let raceDate: String
    let finishTimeSec: Int
    let deltaSec: Int
}
struct RaceCourseContext: Codable, Sendable {
    let status: String
    let course: RaceCourse?
    let candidates: [RaceCourseCandidate]
    let message: String?
}
struct RaceCourseCandidate: Codable, Sendable, Identifiable {
    let id: Int
    let raceName: String
    let distanceLabel: String
}
struct RaceCourse: Codable, Sendable {
    let id: Int
    let raceName: String
    let distanceLabel: String
    let distanceKm: Double
    let elevationGainM: Double?
    let location: String?
    let terrain: [String]
    let keyClimbs: [String]
    let climate: [String: JSONValue]
    let runnerReviews: [String]
    let sourceLabel: String?
    let sourceUrls: [String]
    let verifiedAt: String?
    let editionYear: Int?
    let editionStatus: String
}
func raceTimeDifference(_ seconds: Int) -> String {
    guard seconds != 0 else { return "Same finish time" }
    let value = abs(seconds)
    let duration = value >= 3600 ? String(format: "%d:%02d:%02d", value / 3600, value / 60 % 60, value % 60) : String(format: "%d:%02d", value / 60, value % 60)
    return "\(duration) \(seconds < 0 ? "faster" : "slower")"
}

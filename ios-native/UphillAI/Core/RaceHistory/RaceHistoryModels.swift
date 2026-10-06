import Foundation

enum DistanceCategory: String, Codable, Sendable, CaseIterable, Identifiable {
    case fiveK = "5km"
    case tenK = "10km"
    case halfMarathon = "HM"
    case marathon = "FM"
    case fiftyK = "50km"
    case hundredK = "100km"
    case hundredMiles = "100 miles"

    var id: String { rawValue }

    var shortLabel: String { rawValue }

    var fullLabel: String {
        switch self {
        case .fiveK: return "5 km"
        case .tenK: return "10 km"
        case .halfMarathon: return "Half Marathon"
        case .marathon: return "Full Marathon"
        case .fiftyK: return "50 km Ultra"
        case .hundredK: return "100 km Ultra"
        case .hundredMiles: return "100 Miles"
        }
    }

    var targetKm: Double {
        switch self {
        case .fiveK: return 5.0
        case .tenK: return 10.0
        case .halfMarathon: return 21.0975
        case .marathon: return 42.195
        case .fiftyK: return 50.0
        case .hundredK: return 100.0
        case .hundredMiles: return 160.934
        }
    }

    static func match(distanceKm: Double) -> DistanceCategory? {
        switch distanceKm {
        case 4.0..<7.5: return .fiveK
        case 7.5..<15.0: return .tenK
        case 18.0..<30.0: return .halfMarathon
        case 38.0..<48.0: return .marathon
        case 48.0..<75.0: return .fiftyK
        case 85.0..<130.0: return .hundredK
        case 140.0...: return .hundredMiles
        default: return nil
        }
    }
}

struct DistanceBadge: Codable, Sendable, Identifiable, Equatable {
    var id: String { category.rawValue }
    let category: DistanceCategory
    let unlocked: Bool
    let bestTimeSec: Int?
    let bestRaceName: String?
    let bestRaceDate: String?
    let resultId: Int?

    init(
        category: DistanceCategory,
        unlocked: Bool,
        bestTimeSec: Int? = nil,
        bestRaceName: String? = nil,
        bestRaceDate: String? = nil,
        resultId: Int? = nil
    ) {
        self.category = category
        self.unlocked = unlocked
        self.bestTimeSec = bestTimeSec
        self.bestRaceName = bestRaceName
        self.bestRaceDate = bestRaceDate
        self.resultId = resultId
    }

    var formattedPB: String {
        guard let bestTimeSec else { return "—" }
        return Self.formatTime(bestTimeSec)
    }

    static func formatTime(_ seconds: Int) -> String {
        let h = seconds / 3600
        let m = (seconds % 3600) / 60
        let s = seconds % 60
        if h > 0 {
            return String(format: "%d:%02d:%02d", h, m, s)
        } else {
            return String(format: "%02d:%02d", m, s)
        }
    }

    static func deriveBadges(from results: [RaceResult]) -> [DistanceBadge] {
        let validResults = results.filter { $0.selected && !$0.hidden && !$0.isDnf && ($0.finishTimeSec ?? 0) > 0 }

        return DistanceCategory.allCases.map { category in
            let matching = validResults.filter { result in
                DistanceCategory.match(distanceKm: result.distanceKm) == category
            }
            if let best = matching.min(by: { ($0.finishTimeSec ?? Int.max) < ($1.finishTimeSec ?? Int.max) }),
               let time = best.finishTimeSec {
                return DistanceBadge(
                    category: category,
                    unlocked: true,
                    bestTimeSec: time,
                    bestRaceName: best.raceName,
                    bestRaceDate: best.raceDate,
                    resultId: best.id
                )
            } else {
                return DistanceBadge(category: category, unlocked: false)
            }
        }
    }
}

struct RaceClaim: Codable, Sendable, Identifiable, Equatable {
    let id: Int
    let source: String
    let displayName: String
    let syncStatus: String
    let syncError: String?
    let verified: Bool
    let verificationMethods: [String]
    let meta: [String: JSONValue]?

    init(
        id: Int,
        source: String,
        displayName: String,
        syncStatus: String,
        syncError: String? = nil,
        verified: Bool = false,
        verificationMethods: [String] = [],
        meta: [String: JSONValue]? = nil
    ) {
        self.id = id
        self.source = source
        self.displayName = displayName
        self.syncStatus = syncStatus
        self.syncError = syncError
        self.verified = verified
        self.verificationMethods = verificationMethods
        self.meta = meta
    }
}

struct PRTime: Codable, Sendable, Equatable {
    let timeSec: Int
    let stale: Bool

    init(timeSec: Int, stale: Bool = false) {
        self.timeSec = timeSec
        self.stale = stale
    }
}

struct HistorySummary: Codable, Sendable, Equatable {
    let trailFinishes: Int
    let trailDnfs: Int
    let ultras: Int
    let longestFinish: RaceResult?
    let roadHmPr: PRTime?
    let roadFmPr: PRTime?

    init(
        trailFinishes: Int = 0,
        trailDnfs: Int = 0,
        ultras: Int = 0,
        longestFinish: RaceResult? = nil,
        roadHmPr: PRTime? = nil,
        roadFmPr: PRTime? = nil
    ) {
        self.trailFinishes = trailFinishes
        self.trailDnfs = trailDnfs
        self.ultras = ultras
        self.longestFinish = longestFinish
        self.roadHmPr = roadHmPr
        self.roadFmPr = roadFmPr
    }
}

struct RaceResult: Codable, Sendable, Identifiable, Equatable {
    let id: Int
    let claimId: Int?
    let source: String
    let raceName: String
    let raceDate: String
    let discipline: String
    let distanceKm: Double
    let elevationGainM: Double?
    let finishTimeSec: Int?
    let isDnf: Bool
    let bib: String?
    let selected: Bool
    let hidden: Bool
    let userNote: String?
    let verified: Bool
    let verificationMethods: [String]
    let rankOverall: Int?
    let totalOverall: Int?

    init(
        id: Int,
        claimId: Int? = nil,
        source: String = "manual",
        raceName: String,
        raceDate: String,
        discipline: String = "trail",
        distanceKm: Double,
        elevationGainM: Double? = nil,
        finishTimeSec: Int? = nil,
        isDnf: Bool = false,
        bib: String? = nil,
        selected: Bool = true,
        hidden: Bool = false,
        userNote: String? = nil,
        verified: Bool = false,
        verificationMethods: [String] = [],
        rankOverall: Int? = nil,
        totalOverall: Int? = nil
    ) {
        self.id = id
        self.claimId = claimId
        self.source = source
        self.raceName = raceName
        self.raceDate = raceDate
        self.discipline = discipline
        self.distanceKm = distanceKm
        self.elevationGainM = elevationGainM
        self.finishTimeSec = finishTimeSec
        self.isDnf = isDnf
        self.bib = bib
        self.selected = selected
        self.hidden = hidden
        self.userNote = userNote
        self.verified = verified
        self.verificationMethods = verificationMethods
        self.rankOverall = rankOverall
        self.totalOverall = totalOverall
    }

    var formattedDuration: String {
        if isDnf { return "DNF" }
        guard let finishTimeSec, finishTimeSec > 0 else { return "—" }
        return DistanceBadge.formatTime(finishTimeSec)
    }

    var formattedDistance: String {
        if distanceKm == floor(distanceKm) {
            return "\(Int(distanceKm)) km"
        } else {
            return String(format: "%.1f km", distanceKm)
        }
    }

    var category: DistanceCategory? {
        DistanceCategory.match(distanceKm: distanceKm)
    }
}

struct RaceHistoryResponse: Codable, Sendable, Equatable {
    let claims: [RaceClaim]
    let results: [RaceResult]
    let summary: HistorySummary

    init(claims: [RaceClaim] = [], results: [RaceResult] = [], summary: HistorySummary = .init()) {
        self.claims = claims
        self.results = results
        self.summary = summary
    }
}

struct RaceCandidate: Codable, Sendable, Identifiable, Equatable {
    var id: String { externalId }
    let externalId: String
    let displayName: String
    let ageGroup: String?
    let index: Double?

    init(externalId: String, displayName: String, ageGroup: String? = nil, index: Double? = nil) {
        self.externalId = externalId
        self.displayName = displayName
        self.ageGroup = ageGroup
        self.index = index
    }
}

struct ManualResultPayload: Codable, Sendable {
    var raceName: String
    var raceDate: String
    var discipline: String
    var distanceKm: Double
    var elevationGainM: Double?
    var finishTimeSec: Int?
    var isDnf: Bool
    var rankOverall: Int?
    var totalOverall: Int?

    init(
        raceName: String,
        raceDate: String,
        discipline: String = "trail",
        distanceKm: Double,
        elevationGainM: Double? = nil,
        finishTimeSec: Int? = nil,
        isDnf: Bool = false,
        rankOverall: Int? = nil,
        totalOverall: Int? = nil
    ) {
        self.raceName = raceName
        self.raceDate = raceDate
        self.discipline = discipline
        self.distanceKm = distanceKm
        self.elevationGainM = elevationGainM
        self.finishTimeSec = finishTimeSec
        self.isDnf = isDnf
        self.rankOverall = rankOverall
        self.totalOverall = totalOverall
    }
}

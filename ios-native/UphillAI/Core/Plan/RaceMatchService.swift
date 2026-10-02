import Foundation

struct RaceMatch: Decodable, Sendable, Equatable {
    let raceName: String
    let distanceLabel: String?
    let distanceKm: Double?
    let elevationGainM: Double?
}

struct RaceMatchResponse: Decodable, Sendable {
    let matched: Bool
    let autoApply: Bool?
    let match: RaceMatch?
    let candidates: [RaceMatch]?
}

struct RaceMatchService: Sendable {
    let client: APIClient
    func match(name: String) async throws -> RaceMatchResponse {
        try await client.send(.get("/api/kb/match-race", query: [URLQueryItem(name: "name", value: name)], requiresAuth: false))
    }
}

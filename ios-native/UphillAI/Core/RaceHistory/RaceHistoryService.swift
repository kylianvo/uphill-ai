import Foundation

protocol RaceHistoryServicing: Sendable {
    func history() async throws -> RaceHistoryResponse
    func searchCandidates(source: String, query: String) async throws -> [RaceCandidate]
    func addClaim(source: String, externalId: String) async throws
    func deleteClaim(id: Int) async throws
    func verifyBib(claimId: Int, bib: String) async throws
    func refreshClaim(id: Int) async throws
    func addResult(payload: ManualResultPayload) async throws -> RaceResult
    func updateResult(id: Int, changes: [String: JSONValue]) async throws -> RaceResult
    func deleteResult(id: Int) async throws
}

struct RaceHistoryService: RaceHistoryServicing {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    private struct ClaimBody: Encodable {
        let source: String
        let externalId: String
    }

    private struct BibBody: Encodable {
        let bib: String
    }

    func history() async throws -> RaceHistoryResponse {
        try await client.send(.get("/api/race-history"))
    }

    func searchCandidates(source: String, query: String) async throws -> [RaceCandidate] {
        let queryItems = [
            URLQueryItem(name: "source", value: source),
            URLQueryItem(name: "q", value: query)
        ]
        return try await client.send(.get("/api/race-history/search", query: queryItems))
    }

    func addClaim(source: String, externalId: String) async throws {
        let body = ClaimBody(source: source, externalId: externalId)
        let endpoint = try Endpoint<EmptyResponse>.send(.post, "/api/race-history/claims", body: body)
        _ = try await client.send(endpoint)
    }

    func deleteClaim(id: Int) async throws {
        _ = try await client.send(Endpoint<EmptyResponse>.delete("/api/race-history/claims/\(id)"))
    }

    func verifyBib(claimId: Int, bib: String) async throws {
        let body = BibBody(bib: bib)
        let endpoint = try Endpoint<EmptyResponse>.send(.post, "/api/race-history/claims/\(claimId)/verify-bib", body: body)
        _ = try await client.send(endpoint)
    }

    func refreshClaim(id: Int) async throws {
        let endpoint = Endpoint<EmptyResponse>.post("/api/race-history/claims/\(id)/refresh")
        _ = try await client.send(endpoint)
    }

    func addResult(payload: ManualResultPayload) async throws -> RaceResult {
        let endpoint = try Endpoint<RaceResult>.send(.post, "/api/race-history/results", body: payload)
        return try await client.send(endpoint)
    }

    func updateResult(id: Int, changes: [String: JSONValue]) async throws -> RaceResult {
        let endpoint = try Endpoint<RaceResult>.send(.patch, "/api/race-history/results/\(id)", body: changes)
        return try await client.send(endpoint)
    }

    func deleteResult(id: Int) async throws {
        _ = try await client.send(Endpoint<EmptyResponse>.delete("/api/race-history/results/\(id)"))
    }
}

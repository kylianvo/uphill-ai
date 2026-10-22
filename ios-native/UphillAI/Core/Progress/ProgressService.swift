import Foundation

protocol ProgressServicing: Sendable {
    func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse
}

struct ProgressService: ProgressServicing {
    let client: APIClient

    func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse {
        try await client.send(.get("/api/progress", query: [
            URLQueryItem(name: "section", value: section.rawValue),
            URLQueryItem(name: "days", value: "\(days)"),
        ]))
    }
}

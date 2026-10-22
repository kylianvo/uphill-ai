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
            // The athlete's own date: ahead of UTC, last night is "tomorrow" on the server.
            URLQueryItem(name: "client_today", value: Date().formatted(Date.ISO8601FormatStyle(timeZone: .current).year().month().day())),
        ]))
    }
}

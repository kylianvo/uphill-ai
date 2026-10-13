import Foundation
import Observation

@MainActor @Observable
final class RaceDetailViewModel {
    private(set) var detail: RaceDetailResponse?
    private(set) var isLoading = false
    private(set) var errorMessage: String?
    private var revision = 0
    private let fetch: @Sendable (Int, Int?, Int?) async throws -> RaceDetailResponse

    init(service: any RaceHistoryServicing) {
        fetch = { try await service.detail(id: $0, courseId: $1, athleteId: $2) }
    }
    init(fetch: @escaping @Sendable (Int, Int?, Int?) async throws -> RaceDetailResponse) { self.fetch = fetch }
    func load(id: Int, courseId: Int? = nil, athleteId: Int? = nil) async {
        revision += 1
        let request = revision
        isLoading = true; errorMessage = nil
        do {
            let response = try await fetch(id, courseId, athleteId)
            guard request == revision, !Task.isCancelled else { return }
            detail = response
        } catch {
            guard request == revision, !Task.isCancelled else { return }
            errorMessage = error.raceHistoryMessage
        }
        if request == revision { isLoading = false }
    }
}

import Foundation
import Observation

@Observable
@MainActor
final class ProgressViewModel {
    enum LoadState: Equatable { case loading, empty, loaded, failed(String) }

    private(set) var state: LoadState = .loading
    private(set) var response: ProgressResponse?
    private(set) var section: ProgressSection = .training
    /// 28 on the tab; a detail screen asks for 90 (3M).
    private(set) var days = 28

    private let service: any ProgressServicing

    init(service: any ProgressServicing) {
        self.service = service
    }

    func select(_ section: ProgressSection) async {
        self.section = section
        await load()
    }

    func load() async {
        if response?.section != section.rawValue { state = .loading }
        do {
            let result = try await service.progress(section: section, days: days)
            response = result
            state = .loaded
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    /// Sign-out: the next account must never see this athlete's health data.
    func reset() {
        response = nil
        section = .training
        state = .loading
    }

    /// A detail screen's range; reads independently so the tab's own data stays at 28 days.
    func detail(days: Int) async throws -> ProgressResponse {
        try await service.progress(section: section, days: days)
    }
}

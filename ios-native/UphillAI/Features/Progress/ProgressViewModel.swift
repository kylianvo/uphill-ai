import Foundation
import Observation

@Observable
@MainActor
final class ProgressViewModel {
    enum LoadState: Equatable { case loading, empty, loaded, failed(String) }

    private(set) var state: LoadState = .loading
    /// Both sections stay cached: switching shows the last reply at once and refreshes behind it.
    private var responses: [ProgressSection: ProgressResponse] = [:]
    var response: ProgressResponse? { responses[section] }
    private(set) var section: ProgressSection = .training
    /// 28 on the tab; a detail screen asks for 90 (3M).
    private(set) var days = 28

    private let service: any ProgressServicing
    /// Bumped on sign-out (and on each new load): a reply for an older revision is dropped,
    /// so a request still in flight can't show one athlete's health data to the next account.
    private var revision = 0

    init(service: any ProgressServicing) {
        self.service = service
    }

    func select(_ section: ProgressSection) async {
        self.section = section
        state = responses[section] == nil ? .loading : .loaded
        await load()
    }

    func load() async {
        let requested = section
        if responses[requested] == nil { state = .loading }
        revision += 1
        let mine = revision
        do {
            let result = try await service.progress(section: requested, days: days)
            guard mine == revision else { return }
            responses[requested] = result
            if section == requested { state = .loaded }
        } catch {
            guard mine == revision else { return }
            // A failed refresh keeps the cached cards on screen; only an empty section shows the error.
            if section == requested && responses[requested] == nil { state = .failed(error.localizedDescription) }
        }
        let other: ProgressSection = requested == .training ? .health : .training
        if mine == revision, responses[other] == nil { await prefetch(other, revision: mine) }
    }

    /// Fills the other section once, so the first switch to it is instant too.
    private func prefetch(_ other: ProgressSection, revision mine: Int) async {
        guard let result = try? await service.progress(section: other, days: days), mine == revision else { return }
        responses[other] = result
    }

    /// Sign-out: the next account must never see this athlete's health data.
    func reset() {
        revision += 1
        responses = [:]
        section = .training
        state = .loading
    }

    /// A detail screen's range; reads independently so the tab's own data stays at 28 days.
    func detail(days: Int) async throws -> ProgressResponse {
        try await service.progress(section: section, days: days)
    }
}

import Foundation
import Observation

@MainActor @Observable
final class RaceHistoryViewModel {
    private let service: any RaceHistoryServicing
    var history: RaceHistoryResponse?
    var isLoading = false
    var isMutating = false
    var errorMessage: String?
    init(service: any RaceHistoryServicing, history: RaceHistoryResponse? = nil) {
        self.service = service; self.history = history
    }
    func load() async {
        isLoading = history == nil
        defer { isLoading = false }
        do { history = try await service.history(); errorMessage = nil }
        catch { errorMessage = error.raceHistoryMessage }
    }
    func confirm(id: Int, selected: Bool) async {
        guard !isMutating else { return }
        isMutating = true; errorMessage = nil
        defer { isMutating = false }
        do { _ = try await service.updateResult(id: id, changes: ["selected": .bool(selected)]) }
        catch { errorMessage = error.raceHistoryMessage; return }
        do { history = try await service.history() }
        catch { errorMessage = "Saved, but refresh failed. Retry." }
    }
    func deleteManual(id: Int) async {
        guard !isMutating, history?.results.first(where: { $0.id == id })?.source == "manual" else { return }
        isMutating = true; errorMessage = nil
        defer { isMutating = false }
        do { try await service.deleteResult(id: id) }
        catch { errorMessage = error.raceHistoryMessage; return }
        do { history = try await service.history() }
        catch { errorMessage = "Saved, but refresh failed. Retry." }
    }
    @discardableResult
    func perform(_ operation: () async throws -> Void) async -> Bool {
        guard !isMutating else { return false }
        isMutating = true; errorMessage = nil
        defer { isMutating = false }
        do { try await operation() }
        catch { errorMessage = error.raceHistoryMessage; return false }
        do { history = try await service.history(); return true }
        catch { errorMessage = "Saved, but refresh failed. Retry."; return false }
    }
    func reloadAfterSave() async {
        await load()
        if errorMessage != nil { errorMessage = "Saved, but refresh failed. Retry." }
    }
}

extension Error {
    /// Readable text for race-history failures; `APIError` has no localized description of its own.
    var raceHistoryMessage: String {
        guard let api = self as? APIError else { return localizedDescription }
        switch api {
        case .http(_, let message?, _): return message
        case .unauthorized: return "Your session expired. Please sign in again."
        default: return "Couldn't reach Uphill AI. Check your connection and try again."
        }
    }
}

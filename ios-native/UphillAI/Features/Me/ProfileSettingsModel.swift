import Foundation
import Observation

@Observable @MainActor
final class ProfileSettingsModel {
    var draft: ProfileDraft
    private(set) var error: String?
    private(set) var saved = false
    private(set) var isSaving = false
    private(set) var zones: PaceZones?
    private var transportFailed = false
    let section: TrainingDestination
    private let service: ProfileService
    private let session: SessionStore
    private let userID: Int
    private let isOffline: () -> Bool

    init(user: User, section: TrainingDestination, service: ProfileService, session: SessionStore, isOffline: @escaping () -> Bool) {
        draft = ProfileDraft(user: user)
        userID = user.id
        self.section = section
        self.service = service
        self.session = session
        self.isOffline = isOffline
    }

    func save() async {
        guard !isSaving else { return }
        saved = false
        if isOffline() || transportFailed { error = PlanViewModel.offlineMessage; return }
        guard let user = session.user, user.id == userID else { return }
        let body = draft.body(merging: user, section: section)
        if let message = body.heartRateError { error = message; return }
        isSaving = true
        error = nil
        defer { isSaving = false }
        do {
            let updated = try await service.update(body)
            guard session.user?.id == userID else { return }
            session.setUser(updated)
            draft = ProfileDraft(user: updated)
            saved = true
            if section == .paces { await loadZones() }
        } catch let e as APIError {
            if case .transport = e { transportFailed = true; error = PlanViewModel.offlineMessage }
            else { error = e.userMessage }
        } catch { self.error = error.localizedDescription }
    }

    func loadZones() async {
        do { zones = try await service.zones(model: draft.paceZoneModel) }
        catch let e as APIError { error = e.userMessage }
        catch { self.error = error.localizedDescription }
    }
}

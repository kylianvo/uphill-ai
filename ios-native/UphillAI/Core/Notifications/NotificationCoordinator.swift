import Foundation
import Observation
import UIKit
import UserNotifications

@Observable @MainActor
final class NotificationCoordinator {
    static weak var current: NotificationCoordinator?
    static var pendingLaunchData: Data?
    /// "Less like this" taps that arrived before a coordinator existed; sent once one does.
    static var pendingFeedback: [UUID] = []
    let service: any NotificationServicing
    let installationID: UUID
    var preferences = NotificationPreferences()
    var permission = "notDetermined"
    var error: String?
    var saving = false
    var pendingRoute: NotificationRoute?
    var pendingID: UUID?
    var visibleRoute: NotificationRoute?
    var userID: Int?
    private var token: String?
    private let defaults: UserDefaults

    init(service: any NotificationServicing, defaults: UserDefaults = .standard) {
        self.service = service
        self.defaults = defaults
        let key = "UPHILL_NOTIFICATION_INSTALLATION"
        let id = defaults.string(forKey: key).flatMap(UUID.init(uuidString:)) ?? UUID()
        installationID = id
        defaults.set(id.uuidString, forKey: key)
        Self.current = self
        // "coaching" pushes offer "Less like this"; the server picks the category per notification kind.
        UNUserNotificationCenter.current().setNotificationCategories([
            UNNotificationCategory(identifier: "coaching", actions: [UNNotificationAction(identifier: "LESS", title: L("Less like this"), options: [])], intentIdentifiers: [], options: []),
            UNNotificationCategory(identifier: "plain", actions: [], intentIdentifiers: [], options: []),
        ])
        if let data = Self.pendingLaunchData { receive(data: data); Self.pendingLaunchData = nil }
        let feedback = Self.pendingFeedback
        Self.pendingFeedback = []
        if !feedback.isEmpty { Task { for id in feedback { await lessLikeThis(id: id) } } }
    }

    func refresh(userID: Int?) async {
        guard let userID else { return }
        if self.userID != userID, let cached = defaults.data(forKey: "UPHILL_NOTIFICATION_PREFS_\(userID)"), let value = try? JSONCoding.decoder.decode(NotificationPreferences.self, from: cached) {
            preferences = value
        }
        self.userID = userID
        do {
            if defaults.integer(forKey: "UPHILL_NOTIFICATION_PENDING_REMOVAL") == userID {
                try await service.removeInstallation(id: installationID)
                defaults.removeObject(forKey: "UPHILL_NOTIFICATION_PENDING_REMOVAL")
            }
            let remote = try await service.preferences()
            guard self.userID == userID else { return }
            preferences = remote
            let settings = await UNUserNotificationCenter.current().notificationSettings()
            guard self.userID == userID else { return }
            permission = Self.permissionName(settings.authorizationStatus)
            if preferences.timezone != TimeZone.current.identifier || preferences.language != AppLanguage.code {
                preferences.timezone = TimeZone.current.identifier
                preferences.language = AppLanguage.code
                let saved = try await service.updatePreferences(preferences)
                guard self.userID == userID else { return }
                preferences = saved
            }
            let snoozeKey = "UPHILL_NOTIFICATION_SNOOZE_IMPORTED_\(userID)"
            if !defaults.bool(forKey: snoozeKey) {
                let at = defaults.double(forKey: SharpenChecklistCard.snoozeKey)
                let until = Date(timeIntervalSince1970: at).addingTimeInterval(14 * 86_400)
                if at > 0 && until > .now && until > (Self.date(preferences.checklistSnoozedUntil) ?? .distantPast) {
                    preferences.checklistSnoozedUntil = ISO8601DateFormatter().string(from: until)
                    let saved = try await service.updatePreferences(preferences)
                guard self.userID == userID else { return }
                preferences = saved
                }
                defaults.set(true, forKey: snoozeKey)
            }
            guard self.userID == userID else { return }
            if permission == "authorized" || permission == "provisional" {
                UIApplication.shared.registerForRemoteNotifications()
            }
            try await registerIfPossible()
            cachePreferences()
            error = nil
        } catch { self.error = L("Couldn't update notifications. Try again.") }
    }

    func save(_ value: NotificationPreferences, requestPermission: Bool = false) async {
        guard let expectedUser = userID else { return }
        saving = true
        defer { saving = false }
        do {
            if requestPermission && (value.workoutsEnabled || value.coachingEnabled || value.resultsEnabled) {
                let allowed = try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound])
                guard userID == expectedUser else { return }
                guard allowed else { permission = "denied"; return }
                permission = "authorized"
                UIApplication.shared.registerForRemoteNotifications()
            }
            var next = value
            next.timezone = TimeZone.current.identifier
            next.language = AppLanguage.code
            guard userID == expectedUser else { return }
            let saved = try await service.updatePreferences(next)
            guard userID == expectedUser else { return }
            preferences = saved
            try await registerIfPossible()
            cachePreferences()
            error = nil
        } catch { self.error = L("Couldn't update notifications. Try again.") }
    }

    /// The single switch: every category follows it.
    func setEnabled(_ on: Bool, requestPermission: Bool = true) async {
        var next = preferences
        next.workoutsEnabled = on
        next.coachingEnabled = on
        next.resultsEnabled = on
        await save(next, requestPermission: requestPermission && on)
    }

    func unmute(_ kind: String) async {
        var next = preferences
        next.mutedKinds = (next.mutedKinds ?? []).filter { $0 != kind }
        await save(next)
    }

    func lessLikeThis(id: UUID) async {
        do {
            try await service.feedback(id: id)
            preferences = try await service.preferences()
            cachePreferences()
        } catch { self.error = L("Couldn't update notifications. Try again.") }
    }

    func didRegister(token data: Data) async {
        token = data.map { String(format: "%02x", $0) }.joined()
        do { try await registerIfPossible() }
        catch { self.error = L("Couldn't update notifications. Try again.") }
    }

    private func registerIfPossible() async throws {
        guard userID != nil, let token else { return }
        try await service.registerInstallation(id: installationID, token: token, permission: permission)
    }

    func receive(data: Data) {
        guard let payload = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let route = NotificationRoute(payload: payload),
              let id = (payload["notification_id"] as? String).flatMap(UUID.init(uuidString:)) else { return }
        pendingRoute = route
        pendingID = id
    }

    func didOpen() async {
        if let id = pendingID { try? await service.opened(id: id) }
        pendingID = nil
        pendingRoute = nil
    }

    func unregister() async {
        do {
            try await service.removeInstallation(id: installationID)
            defaults.removeObject(forKey: "UPHILL_NOTIFICATION_PENDING_REMOVAL")
        } catch {
            defaults.set(userID, forKey: "UPHILL_NOTIFICATION_PENDING_REMOVAL")
        }
        reset()
    }

    func reset() {
        userID = nil
        pendingRoute = nil
        pendingID = nil
        visibleRoute = nil
        preferences = NotificationPreferences()
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
    }

    private func cachePreferences() {
        guard let userID, let data = try? JSONCoding.encoder.encode(preferences) else { return }
        defaults.set(data, forKey: "UPHILL_NOTIFICATION_PREFS_\(userID)")
    }

    func snoozeChecklist() async {
        var next = preferences
        next.checklistSnoozedUntil = ISO8601DateFormatter().string(from: Date.now.addingTimeInterval(14 * 86_400))
        preferences = next
        cachePreferences()
        if let userID { defaults.removeObject(forKey: "UPHILL_NOTIFICATION_SNOOZE_IMPORTED_\(userID)") }
        await save(next)
    }

    static func date(_ value: String?) -> Date? {
        guard let value else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: value) ?? ISO8601DateFormatter().date(from: value)
    }

    static func permissionName(_ value: UNAuthorizationStatus) -> String {
        switch value {
        case .authorized: "authorized"
        case .provisional, .ephemeral: "provisional"
        case .denied: "denied"
        default: "notDetermined"
        }
    }
}

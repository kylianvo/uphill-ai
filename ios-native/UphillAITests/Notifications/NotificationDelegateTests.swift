import Foundation
import Testing
import UserNotifications
@testable import UphillAI

/// iOS calls the delegate through its Objective-C completion-handler selectors and UIKit aborts unless
/// that handler runs on the main thread (TestFlight 2026102402 crashed on every notification tap).
// Serialized: these tests drive the shared NotificationCoordinator.current through the real delegate.
@MainActor
@Suite(.serialized)
struct NotificationDelegateTests {
    private func notification() throws -> UNNotification {
        let content = UNMutableNotificationContent()
        content.userInfo = ["v": 1, "notification_id": UUID().uuidString, "destination": ["kind": "workout", "plan_id": 2, "workout_id": 3]]
        let request = UNNotificationRequest(identifier: "test", content: content, trigger: nil)
        // No public initializers; these private factories are only used to build test fixtures.
        let made = (UNNotification.self as AnyObject).perform(NSSelectorFromString("notificationWithRequest:date:"), with: request, with: Date())
        return try #require(made?.takeUnretainedValue() as? UNNotification)
    }

    private func response(_ notification: UNNotification, action: String = UNNotificationDefaultActionIdentifier) throws -> UNNotificationResponse {
        let made = (UNNotificationResponse.self as AnyObject).perform(
            NSSelectorFromString("responseWithNotification:actionIdentifier:"), with: notification, with: action)
        return try #require(made?.takeUnretainedValue() as? UNNotificationResponse)
    }

    @Test func tapCompletesOnMainThreadBeforeReturning() throws {
        let delegate: UNUserNotificationCenterDelegate = NotificationAppDelegate()
        var onMain: Bool?
        delegate.userNotificationCenter?(.current(), didReceive: try response(notification())) { onMain = Thread.isMainThread }
        #expect(onMain == true)
    }

    @Test func foregroundPresentationCompletesOnMainThreadBeforeReturning() throws {
        let delegate: UNUserNotificationCenterDelegate = NotificationAppDelegate()
        var onMain: Bool?
        delegate.userNotificationCenter?(.current(), willPresent: try notification()) { _ in onMain = Thread.isMainThread }
        #expect(onMain == true)
    }

    @Test func lessLikeThisFinishesFeedbackBeforeCompletingOnMain() async throws {
        let recorder = FeedbackRecorder()
        NotificationCoordinator.pendingLaunchData = nil  // an earlier tap with no coordinator stashes its payload here
        let coordinator = NotificationCoordinator(service: RecordingNotificationService(recorder: recorder), defaults: UserDefaults(suiteName: "less-\(UUID())")!)
        let delegate: UNUserNotificationCenterDelegate = NotificationAppDelegate()
        let less = try response(notification(), action: "LESS")
        // Suites run in parallel and each coordinator claims `current`; reclaim it with no suspension before the call.
        NotificationCoordinator.current = coordinator
        var completion: (onMain: Bool, sent: Int)?
        delegate.userNotificationCenter?(.current(), didReceive: less) { completion = (Thread.isMainThread, recorder.ids.count) }
        for _ in 0..<50 where completion == nil { try await Task.sleep(for: .milliseconds(20)) }
        // iOS may suspend the app as soon as the handler runs, so the POST must already be done.
        #expect(completion?.onMain == true && completion?.sent == 1)
        #expect(coordinator.pendingRoute == nil)  // the action mutes; it does not navigate
    }

    @Test func lessLikeThisWithoutCoordinatorIsKeptForLater() throws {
        let saved = NotificationCoordinator.current
        defer { NotificationCoordinator.current = saved }
        NotificationCoordinator.current = nil
        NotificationCoordinator.pendingFeedback = []
        var done = false
        let delegate: UNUserNotificationCenterDelegate = NotificationAppDelegate()
        delegate.userNotificationCenter?(.current(), didReceive: try response(notification(), action: "LESS")) { done = true }
        #expect(done && NotificationCoordinator.pendingFeedback.count == 1)
        NotificationCoordinator.pendingFeedback = []
    }
}

@MainActor final class FeedbackRecorder { var ids: [UUID] = [] }

struct RecordingNotificationService: NotificationServicing {
    let recorder: FeedbackRecorder
    func preferences() async throws -> NotificationPreferences { NotificationPreferences() }
    func updatePreferences(_ value: NotificationPreferences) async throws -> NotificationPreferences { value }
    func registerInstallation(id: UUID, token: String, permission: String) async throws {}
    func removeInstallation(id: UUID) async throws {}
    func opened(id: UUID) async throws {}
    func feedback(id: UUID) async throws { await MainActor.run { recorder.ids.append(id) } }
}

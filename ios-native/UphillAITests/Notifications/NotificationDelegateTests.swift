import Foundation
import Testing
import UserNotifications
@testable import UphillAI

/// iOS calls the delegate through its Objective-C completion-handler selectors and UIKit aborts unless
/// that handler runs on the main thread (TestFlight 2026102402 crashed on every notification tap).
@MainActor
struct NotificationDelegateTests {
    private func notification() throws -> UNNotification {
        let content = UNMutableNotificationContent()
        content.userInfo = ["v": 1, "notification_id": UUID().uuidString, "destination": ["kind": "workout", "plan_id": 2, "workout_id": 3]]
        let request = UNNotificationRequest(identifier: "test", content: content, trigger: nil)
        // No public initializers; these private factories are only used to build test fixtures.
        let made = (UNNotification.self as AnyObject).perform(NSSelectorFromString("notificationWithRequest:date:"), with: request, with: Date())
        return try #require(made?.takeUnretainedValue() as? UNNotification)
    }

    private func response(_ notification: UNNotification) throws -> UNNotificationResponse {
        let made = (UNNotificationResponse.self as AnyObject).perform(
            NSSelectorFromString("responseWithNotification:actionIdentifier:"), with: notification, with: UNNotificationDefaultActionIdentifier)
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
}

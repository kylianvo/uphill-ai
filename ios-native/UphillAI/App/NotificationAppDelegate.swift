import UIKit
import UserNotifications

final class NotificationAppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Task { @MainActor in await NotificationCoordinator.current?.didRegister(token: deviceToken) }
    }
}

// Synchronous main-actor callbacks: the earlier nonisolated async versions finished on a background thread,
// and UIKit aborts when the system's completion handler is called there (crashed every notification tap).
extension NotificationAppDelegate: @preconcurrency UNUserNotificationCenterDelegate {
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
        if response.actionIdentifier == "LESS" {
            let id = (response.notification.request.content.userInfo["notification_id"] as? String).flatMap(UUID.init(uuidString:))
            guard let id else { return completionHandler() }
            // Background action: iOS may suspend us once the handler runs, so finish the POST first (still on main).
            guard let coordinator = NotificationCoordinator.current else {
                NotificationCoordinator.pendingFeedback.append(id)
                return completionHandler()
            }
            Task {
                await coordinator.lessLikeThis(id: id)
                completionHandler()
            }
            return
        }
        defer { completionHandler() }
        guard let data = try? JSONSerialization.data(withJSONObject: response.notification.request.content.userInfo) else { return }
        if let coordinator = NotificationCoordinator.current { coordinator.receive(data: data) }
        else { NotificationCoordinator.pendingLaunchData = data }
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        guard let data = try? JSONSerialization.data(withJSONObject: notification.request.content.userInfo),
              let payload = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let route = NotificationRoute(payload: payload) else { return completionHandler([.banner, .sound]) }
        completionHandler(NotificationCoordinator.current?.visibleRoute == route ? [] : [.banner, .sound])
    }
}

import UIKit
import UserNotifications

final class NotificationAppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Task { @MainActor in await NotificationCoordinator.current?.didRegister(token: deviceToken) }
    }

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse) async {
        guard let data = try? JSONSerialization.data(withJSONObject: response.notification.request.content.userInfo) else { return }
        await MainActor.run {
            if let coordinator = NotificationCoordinator.current { coordinator.receive(data: data) }
            else { NotificationCoordinator.pendingLaunchData = data }
        }
    }

    nonisolated func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification) async -> UNNotificationPresentationOptions {
        let data = try? JSONSerialization.data(withJSONObject: notification.request.content.userInfo)
        let visible = await MainActor.run {
            guard let data, let payload = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any], let route = NotificationRoute(payload: payload) else { return false }
            return NotificationCoordinator.current?.visibleRoute == route
        }
        return visible ? [] : [.banner, .sound]
    }
}

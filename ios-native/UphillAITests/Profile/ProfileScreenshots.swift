import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct ProfileScreenshots {
    private let outDir = "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/profile"

    private func save<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 402, height: 874), scale: CGFloat = 2.0) {
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        controller.view.bounds = CGRect(origin: .zero, size: size)
        controller.view.backgroundColor = .systemBackground

        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()

        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let img = renderer.image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        try? img.pngData()?.write(to: url)
    }

    private func makeApp() throws -> AppModel {
        let user = try Fixture.decode(User.self, "auth_me.json")
        let paceZonesData = try Fixture.data("pace_zones.json")

        let base = StubURLProtocol.register { req in
            if req.url?.path.contains("pace-zones") == true {
                return (200, paceZonesData)
            }
            return (200, json([:]))
        }

        let tokenStore = InMemoryTokenStore("tok")
        let app = AppModel(tokenStore: tokenStore, baseURL: { base }, session: StubURLProtocol.session(), cache: .inMemory())
        app.session.setUser(user)
        return app
    }

    @Test func renderProfileMeTab() throws {
        let app = try makeApp()
        let view = ProfileView(app: app)
        save(view, name: "profile-tab-me")
    }

    @Test func renderTrainingZonesHeartRate() throws {
        let app = try makeApp()
        let view = NavigationStack {
            ProfileSettingsScreen(app: app, section: .trainingZones)
        }
        save(view, name: "profile-training-zones-hr")
    }

    @Test func renderTrainingZonesPaces() throws {
        let app = try makeApp()
        let paceZones = try Fixture.decode(PaceZones.self, "pace_zones.json")
        let model = ProfileSettingsModel(
            user: app.session.user!,
            section: .trainingZones,
            service: ProfileService(client: app.client),
            session: app.session,
            isOffline: { false }
        )
        model.selectedZoneTab = .paces
        model.loadZonesDirectlyForScreenshot(paceZones)

        let view = NavigationStack {
            ProfileSettingsScreen(app: app, section: .trainingZones, preloadedModel: model)
        }
        save(view, name: "profile-training-zones-paces")
    }
}

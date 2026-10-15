import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Sign-in and launch in light and dark. Only writes when SCREENSHOT_DIR is set.
@MainActor
struct AuthScreenshots {
    private func save<V: View>(_ view: V, name: String, dark: Bool) {
        guard let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"] else { return }
        let size = CGSize(width: 402, height: 874)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        controller.overrideUserInterfaceStyle = dark ? .dark : .light
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let img = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try? img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name)-\(dark ? "dark" : "light").png"))
    }

    @Test func renderAuthScreens() throws {
        let model = SignInViewModel(auth: FakeAuthService(.success(try Fixture.decode(AuthResponse.self, "auth_login.json"))),
                                    session: SessionStore(tokenStore: InMemoryTokenStore()))
        for dark in [false, true] {
            save(SignInView(model: model), name: "sign-in", dark: dark)
            save(LaunchView(error: nil, onRetry: {}), name: "launch", dark: dark)
            save(LaunchView(error: "Couldn't reach Uphill AI. Check your connection and try again.", onRetry: {}), name: "launch-error", dark: dark)
        }
    }

    /// Launch over real video frames (the test host can't draw AVPlayerLayer). Frames come from SCREENSHOT_FRAMES: "<dir>" holding light.png / dark.png.
    @Test func renderLaunchOverVideo() {
        guard let dir = ProcessInfo.processInfo.environment["SCREENSHOT_FRAMES"] else { return }
        for dark in [false, true] {
            guard let frame = UIImage(contentsOfFile: "\(dir)/\(dark ? "dark" : "light").png") else { continue }
            save(LaunchView(error: nil, onRetry: {}, still: frame), name: "launch-video", dark: dark)
            save(LaunchView(error: "Couldn't reach Uphill AI. Check your connection and try again.", onRetry: {}, still: frame), name: "launch-video-error", dark: dark)
        }
    }
}

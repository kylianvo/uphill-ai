import GoogleSignIn
import SwiftUI

@main
struct UphillAIApp: App {
    @State private var app = AppModel(tokenStore: KeychainTokenStore())

    var body: some Scene {
        WindowGroup {
            RootView(app: app)
                .tint(UH.Palette.accentInk)
                .onOpenURL { url in
                    if GIDSignIn.sharedInstance.handle(url) {
                        return
                    }
                    Task {
                        await app.handleOpenURL(url)
                    }
                }
        }
    }
}

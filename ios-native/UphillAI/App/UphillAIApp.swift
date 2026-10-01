import GoogleSignIn
import SwiftUI

@main
struct UphillAIApp: App {
    @State private var app = AppModel(tokenStore: KeychainTokenStore())

    var body: some Scene {
        WindowGroup {
            RootView(app: app)
                .tint(UH.Palette.accentInk)
                .onOpenURL { GIDSignIn.sharedInstance.handle($0) }
        }
    }
}

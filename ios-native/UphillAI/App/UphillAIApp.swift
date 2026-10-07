import GoogleSignIn
import SwiftUI

@main
struct UphillAIApp: App {
    @State private var app = AppModel(tokenStore: KeychainTokenStore())

    var body: some Scene {
        WindowGroup {
            RootView(app: app)
                .preferredColorScheme(.light)
                .tint(UH.Palette.accentInk)
                .onAppear { KeyboardDismissal.install() }
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

/// Tapping anywhere outside a text input ends editing, app-wide. The
/// recognizer doesn't cancel touches, so buttons and lists still get them.
@MainActor
enum KeyboardDismissal {
    private static let delegate = Delegate()

    static func install() {
        let windows = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap(\.windows)
        for window in windows where !(window.gestureRecognizers ?? []).contains(where: { $0.delegate === delegate }) {
            let tap = UITapGestureRecognizer(target: window, action: #selector(UIView.endEditing(_:)))
            tap.cancelsTouchesInView = false
            tap.delegate = delegate
            window.addGestureRecognizer(tap)
        }
    }

    private final class Delegate: NSObject, UIGestureRecognizerDelegate {
        func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
            var view = touch.view
            while let v = view {
                if v is UITextField || v is UITextView { return false }
                view = v.superview
            }
            return true
        }

        func gestureRecognizer(
            _ gestureRecognizer: UIGestureRecognizer,
            shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer
        ) -> Bool { true }
    }
}

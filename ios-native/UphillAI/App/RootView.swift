import SwiftUI

struct RootView: View {
    let app: AppModel
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Group {
            switch app.session.state {
            case .signedOut:
                SignInScreen(app: app)
            case .restoring:
                restoringView
            case .signedIn:
                ProfileView(app: app)
            }
        }
        .animation(reduceMotion ? nil : UH.Motion.standard, value: app.session.state)
        .task { await app.restore() }
    }

    private var restoringView: some View {
        VStack(spacing: UH.Space.regular) {
            if let error = app.restoreError {
                Text(error)
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.secondary)
                    .multilineTextAlignment(.center)
                Button("Try again") { Task { await app.restore() } }
                    .buttonStyle(.uhPrimary)
                    .frame(maxWidth: 220)
            } else {
                ProgressView()
            }
        }
        .padding(UH.Space.section)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(UH.Palette.surface.ignoresSafeArea())
    }
}

/// Owns the sign-in view model. Leaving `.signedOut` removes this view, so the
/// next sign-out starts with a fresh model and empty fields.
private struct SignInScreen: View {
    @State private var model: SignInViewModel

    init(app: AppModel) {
        _model = State(initialValue: SignInViewModel(auth: app.auth, session: app.session))
    }

    var body: some View {
        SignInView(model: model)
    }
}

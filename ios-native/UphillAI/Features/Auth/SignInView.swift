import AuthenticationServices
import GoogleSignIn
import SwiftUI

struct SignInView: View {
    @Bindable var model: SignInViewModel
    @FocusState private var focused: Field?
    typealias Field = SignInViewModel.Field
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: UH.Space.section) {
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text("Uphill AI")
                        .font(UH.TextStyle.screenTitle)
                        .foregroundStyle(UH.Palette.ink)
                    Text("Your adaptive training plan for the mountains.")
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.top, UH.Space.reading)

                SignInWithAppleButton(.continue) { request in
                    request.requestedScopes = [.fullName, .email]
                } onCompletion: { result in
                    Task { await handleApple(result) }
                }
                .signInWithAppleButtonStyle(.black)
                .frame(height: 48)
                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))

                Button {
                    Task { await handleGoogle() }
                } label: {
                    Label("Continue with Google", systemImage: "g.circle.fill")
                }
                .buttonStyle(.uhSecondary)

                divider
                emailForm

                if let error = model.errorMessage {
                    Text(error)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.danger)
                }
            }
            .padding(.horizontal, UH.Space.medium)
            .disabled(model.isBusy)
        }
        .background(UH.Palette.surface.ignoresSafeArea())
        // Short content doesn't scroll, so swiping alone can't dismiss: also allow bounce,
        // tap-outside and a Done button above the keyboard.
        .scrollDismissesKeyboard(.immediately)
        .scrollBounceBehavior(.always)
        .simultaneousGesture(TapGesture().onEnded { focused = nil })
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Done") { focused = nil }
                    .accessibilityIdentifier("signin.keyboardDone")
            }
        }
        .sensoryFeedback(.error, trigger: model.errorMessage) { _, new in new != nil }
    }

    private var divider: some View {
        HStack {
            Rectangle().fill(UH.Palette.line).frame(height: 1)
            Text("or").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
            Rectangle().fill(UH.Palette.line).frame(height: 1)
        }
        .accessibilityHidden(true)
    }

    private var emailForm: some View {
        VStack(spacing: UH.Space.small) {
            if model.mode == .register {
                textField("Name", text: $model.name, field: .name)
                    .textContentType(.name)
                    .accessibilityIdentifier("signin.name")
            }
            textField("Email", text: $model.email, field: .email)
                .accessibilityIdentifier("signin.email")
                .textContentType(Self.autofillDisabled ? nil : .username)
                .keyboardType(.emailAddress)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            SecureField("Password (8+ characters)", text: $model.password)
                .textContentType(Self.autofillDisabled ? nil : (model.mode == .register ? .newPassword : .password))
                .focused($focused, equals: .password)
                .submitLabel(.go)
                .onSubmit { handleReturn(in: .password) }
                .inputBox()
                .accessibilityIdentifier("signin.password")

            Button {
                Task { await model.submitEmail() }
            } label: {
                if model.isBusy {
                    ProgressView()
                } else {
                    Text(model.mode == .signIn ? "Sign in" : "Create account")
                }
            }
            .buttonStyle(.uhPrimary)
            .disabled(!model.canSubmit)
            .accessibilityIdentifier("signin.submit")

            Button(model.mode == .signIn ? "New to Uphill? Create an account" : "Have an account? Sign in") {
                withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                    model.mode = model.mode == .signIn ? .register : .signIn
                }
            }
            .font(UH.TextStyle.label)
            .foregroundStyle(UH.Palette.accentInk)
            .frame(minHeight: 44)
        }
    }

    /// UI tests launch with `-UITEST_NO_AUTOFILL YES` so iOS never offers "Save Password?".
    /// Debug builds only; release builds always keep autofill.
    private static var autofillDisabled: Bool {
        #if DEBUG
        UserDefaults.standard.bool(forKey: "UITEST_NO_AUTOFILL")
        #else
        false
        #endif
    }

    private func textField(_ title: String, text: Binding<String>, field: Field) -> some View {
        TextField(title, text: text)
            .focused($focused, equals: field)
            .submitLabel(.next)
            .onSubmit { handleReturn(in: field) }
            .inputBox()
    }

    private func handleReturn(in field: Field) {
        switch model.returnAction(in: field) {
        case .focus(let next): focused = next
        case .submit:
            focused = nil
            Task { await model.submitEmail() }
        case .none: break
        }
    }

    private func handleApple(_ result: Result<ASAuthorization, Error>) async {
        switch result {
        case .success(let authorization):
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let tokenData = credential.identityToken,
                  let token = String(data: tokenData, encoding: .utf8)
            else {
                model.show("Apple sign-in did not return a token. Please try again.")
                return
            }
            let name = credential.fullName.map { PersonNameComponentsFormatter().string(from: $0) } ?? ""
            await model.completeApple(identityToken: token, fullName: name.isEmpty ? nil : name)
        case .failure(let error):
            if (error as? ASAuthorizationError)?.code == .canceled { return }
            model.show(error.localizedDescription)
        }
    }

    private func handleGoogle() async {
        do {
            let token = try await GoogleSignInProvider.signIn()
            await model.completeGoogle(idToken: token)
        } catch let error as GIDSignInError where error.code == .canceled {
            return
        } catch {
            model.show("Google sign-in failed. Please try again.")
        }
    }
}

private extension View {
    func inputBox() -> some View {
        self
            .padding(UH.Space.small)
            .frame(minHeight: 48)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }
}

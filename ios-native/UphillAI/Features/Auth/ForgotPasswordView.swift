import SwiftUI

struct ForgotPasswordView: View {
    @Bindable var model: ForgotPasswordViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.small) {
                    Text(model.step == .email
                         ? L("Enter your account email and we'll send you a 6-digit code.")
                         : L("If an account exists for this email, we sent a code. It expires in 15 minutes."))
                        .font(UH.TextStyle.body)
                        .foregroundStyle(UH.Palette.secondary)

                    if let error = model.errorMessage {
                        Text(error)
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.danger)
                            .accessibilityIdentifier("forgot.error")
                    }

                    TextField("Email", text: $model.email)
                        .textContentType(.username)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .disabled(model.step == .code)
                        .inputBox()
                        .accessibilityIdentifier("forgot.email")

                    if model.step == .email {
                        Button(L("Send code")) { Task { await model.sendCode() } }
                            .buttonStyle(.uhPrimary)
                            .disabled(!model.canSendCode)
                            .accessibilityIdentifier("forgot.send")
                    } else {
                        TextField(L("6-digit code"), text: $model.code)
                            .textContentType(.oneTimeCode)
                            .keyboardType(.numberPad)
                            .inputBox()
                            .accessibilityIdentifier("forgot.code")
                        SecureField(L("New password (8+ characters)"), text: $model.newPassword)
                            .textContentType(.newPassword)
                            .inputBox()
                            .accessibilityIdentifier("forgot.newPassword")
                        Button(L("Reset and sign in")) { Task { await model.reset() } }
                            .buttonStyle(.uhPrimary)
                            .disabled(!model.canReset)
                            .accessibilityIdentifier("forgot.reset")
                        TimelineView(.periodic(from: .now, by: 1)) { context in
                            Button(L("Resend code")) { Task { await model.sendCode() } }
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.accentInk)
                                .frame(minHeight: 44)
                                .disabled(!model.canResend(at: context.date))
                        }
                    }
                }
                .padding(UH.Space.medium)
                .disabled(model.isBusy)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle(L("Reset password"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button(L("Cancel")) { dismiss() } }
            }
        }
    }
}

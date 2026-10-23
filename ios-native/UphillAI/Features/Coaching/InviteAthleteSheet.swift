import SwiftUI

/// The toolbar ＋: invite a runner who already has an Uphill AI account.
struct InviteAthleteSheet: View {
    let service: any CoachingServicing
    let onInvited: (CoachedAthleteRow) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var sending = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Runner's account email", text: $email)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .accessibilityIdentifier("athletes.invite.email")
                } footer: {
                    Text(error ?? L("The runner must already have an Uphill AI account."))
                        .foregroundStyle(error == nil ? UH.Palette.muted : UH.Palette.danger)
                }
            }
            .navigationTitle("Invite runner")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Invite") { Task { await send() } }
                        .disabled(email.trimmingCharacters(in: .whitespaces).isEmpty || sending)
                }
            }
        }
        .presentationDetents([.medium])
    }

    private func send() async {
        sending = true
        defer { sending = false }
        do {
            onInvited(try await service.sendInvite(athleteEmail: email.trimmingCharacters(in: .whitespaces)))
            dismiss()
        } catch {
            self.error = error.localizedDescription
        }
    }
}

/// A one-way coach note to a runner (coach_notes, target 'general').
struct CoachNoteSheet: View {
    let athleteName: String
    let send: (String) async throws -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var text = ""
    @State private var sending = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Write a note", text: $text, axis: .vertical)
                        .lineLimit(4...8)
                } footer: {
                    if let error { Text(error).foregroundStyle(UH.Palette.danger) }
                }
            }
            .navigationTitle(L("Note to %@", athleteName))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Send") {
                        Task {
                            sending = true
                            defer { sending = false }
                            do { try await send(text); dismiss() } catch { self.error = error.localizedDescription }
                        }
                    }
                    .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || sending)
                }
            }
        }
        .presentationDetents([.medium])
    }
}

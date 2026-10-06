import SwiftUI

struct ChatInputBar: View {
    @Binding var text: String
    let isExecuting: Bool
    let onSend: () -> Void

    @FocusState private var isFocused: Bool

    var body: some View {
        HStack(spacing: 8) {
            TextField("Ask Coach Uphill…", text: $text, axis: .vertical)
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.ink)
                .lineLimit(1...5)
                .focused($isFocused)
                .submitLabel(.send)
                .accessibilityIdentifier("chat.inputField")
                .onSubmit {
                    if canSend {
                        onSend()
                    }
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)

            Button {
                if canSend {
                    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
                    onSend()
                }
            } label: {
                Group {
                    if isExecuting {
                        ProgressView()
                            .controlSize(.small)
                            .tint(UH.Palette.buttonInk)
                    } else {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundStyle(canSend ? UH.Palette.buttonInk : UH.Palette.muted)
                    }
                }
                .frame(width: 36, height: 36)
                .background(canSend ? UH.Palette.accent : Color.black.opacity(0.06), in: Circle())
            }
            .accessibilityIdentifier("chat.sendButton")
            .disabled(!canSend)
            .padding(.trailing, 6)
            .accessibilityLabel("Send message")
        }
        .background(Color.white.opacity(0.92), in: RoundedRectangle(cornerRadius: 22))
        .overlay(RoundedRectangle(cornerRadius: 22).stroke(UH.Palette.line, lineWidth: 1))
        .padding(.horizontal, UH.Space.regular)
        .padding(.vertical, 6)
    }

    private var canSend: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isExecuting
    }
}

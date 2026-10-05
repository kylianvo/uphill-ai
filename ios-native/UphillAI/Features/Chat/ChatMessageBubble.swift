import SwiftUI

struct ChatMessageBubble: View {
    let message: ChatMessage
    let proposalStates: [Int: String]
    let onApplyProposal: (Int) async -> Void
    let onDiscardProposal: (Int) async -> Void
    let onViewSources: (Int) -> Void
    let onFeedback: (Int, Int) -> Void

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if message.role == .user {
                Spacer(minLength: 44)
                userBubble
            } else {
                assistantBubble
                Spacer(minLength: 24)
            }
        }
        .padding(.horizontal, UH.Space.regular)
        .padding(.vertical, 4)
    }

    private var userBubble: some View {
        VStack(alignment: .trailing, spacing: 4) {
            Text(message.content)
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.ink)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(UH.Palette.accent.opacity(0.2), in: RoundedRectangle(cornerRadius: 16))
                .overlay(RoundedRectangle(cornerRadius: 16).stroke(UH.Palette.accent.opacity(0.4), lineWidth: 1))
        }
    }

    private var assistantBubble: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            // Header
            HStack(spacing: 6) {
                Image(systemName: "figure.run.circle.fill")
                    .foregroundStyle(UH.Palette.accentInk)
                    .font(.subheadline)
                Text("Coach Uphill")
                    .font(UH.TextStyle.disclosure)
                    .foregroundStyle(UH.Palette.secondary)
            }

            // Body text with markdown parsing
            if !message.content.isEmpty {
                Text(LocalizedStringKey(message.content))
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.ink)
                    .lineSpacing(3)
                    .fixedSize(horizontal: false, vertical: true)
            }

            // Interrupted pill
            if message.interrupted == true {
                Text("(Interrupted)")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.warningInk)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(UH.Palette.warningFill, in: Capsule())
            }

            // Rich tool cards
            if let toolCalls = message.toolCalls, !toolCalls.isEmpty {
                VStack(spacing: UH.Space.compact) {
                    ForEach(toolCalls) { toolCall in
                        ChatRichCardView(
                            payload: toolCall,
                            proposalStates: proposalStates,
                            onApplyProposal: onApplyProposal,
                            onDiscardProposal: onDiscardProposal
                        )
                    }
                }
                .padding(.top, 4)
            }

            // Footer actions (sources + feedback)
            HStack(spacing: 12) {
                if let citations = message.citations, !citations.isEmpty, let msgId = message.numericId {
                    Button {
                        onViewSources(msgId)
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "book.pages")
                            Text("Sources (\(citations.count))")
                        }
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.accentInk)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(UH.Palette.activeFill, in: Capsule())
                    }
                    .accessibilityLabel("View \(citations.count) sources")
                    .accessibilityIdentifier("chat.sourcesButton")
                }

                Spacer()

                if let msgId = message.numericId {
                    feedbackButtons(messageId: msgId)
                }
            }
            .padding(.top, 4)
        }
        .padding(14)
        .background(Color.white, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(UH.Palette.line, lineWidth: 1))
    }

    private func feedbackButtons(messageId: Int) -> some View {
        HStack(spacing: 8) {
            Button {
                UIImpactFeedbackGenerator(style: .light).impactOccurred()
                let next = message.feedback == 1 ? 0 : 1
                onFeedback(messageId, next)
            } label: {
                Image(systemName: message.feedback == 1 ? "hand.thumbsup.fill" : "hand.thumbsup")
                    .font(.caption)
                    .foregroundStyle(message.feedback == 1 ? UH.Palette.accentInk : UH.Palette.muted)
                    .frame(width: 44, height: 44).contentShape(Rectangle())
            }
            .accessibilityLabel("Helpful response")
            .accessibilityIdentifier("chat.thumbsUp")

            Button {
                UIImpactFeedbackGenerator(style: .light).impactOccurred()
                let next = message.feedback == -1 ? 0 : -1
                onFeedback(messageId, next)
            } label: {
                Image(systemName: message.feedback == -1 ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                    .font(.caption)
                    .foregroundStyle(message.feedback == -1 ? UH.Palette.danger : UH.Palette.muted)
                    .frame(width: 44, height: 44).contentShape(Rectangle())
            }
            .accessibilityLabel("Unhelpful response")
            .accessibilityIdentifier("chat.thumbsDown")
        }
    }
}

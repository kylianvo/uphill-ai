import SwiftUI

struct ChatView: View {
    let service: ChatService
    let plan: Plan?
    var planModel: PlanViewModel? = nil

    @State private var inputText = ""
    @State private var showClearAlert = false
    @State private var sourcesSheetTarget: MessageSourcesResponse?
    @State private var selectedWorkoutID: Int?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private var starterChips: [String] {
        if let plan {
            let week = plan.currentWeek ?? 1
            return [
                L("What's on for week %lld?", week),
                L("How should I pace %@?", plan.raceName),
                L("Review last week's training"),
                L("Explain the 80/20 training rule")
            ]
        } else {
            return [
                L("Explain Zone 2 heart rate training"),
                L("How to prevent muscle cramps in ultras?"),
                L("What is Muscular Endurance (ME)?"),
                L("How much elevation gain should I train for?")
            ]
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Error banner
                if let error = service.error {
                    errorBanner(error)
                }

                // Message area
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 10) {
                            if service.hasMore {
                                loadOlderButton
                            }

                            if service.messages.isEmpty && !service.isExecuting {
                                emptyState
                            } else {
                                ForEach(service.messages) { message in
                                    ChatMessageBubble(
                                        message: message,
                                        proposalStates: service.proposalStates,
                                        rebuildDiffs: service.rebuildDiffs,
                                        onLoadRebuild: { id in
                                            await service.pollRebuild(proposalId: id)
                                        },
                                        onSelectWorkout: { id in
                                            selectedWorkoutID = id
                                        },
                                        onApplyProposal: { id in
                                            await service.applyProposal(proposalId: id)
                                        },
                                        onDiscardProposal: { id in
                                            _ = await service.discardProposal(proposalId: id)
                                        },
                                        onViewSources: { msgId in
                                            Task {
                                                await service.fetchMessageSources(messageId: msgId)
                                                sourcesSheetTarget = service.selectedMessageSources
                                            }
                                        },
                                        onFeedback: { msgId, val in
                                            Task {
                                                await service.sendFeedback(messageId: msgId, value: val)
                                            }
                                        }
                                    )
                                    .id(message.id)
                                }

                                if isThinkingBeforeTokens {
                                    typingIndicatorBubble
                                        .id("typing_indicator")
                                }
                            }
                        }
                        .padding(.vertical, UH.Space.small)
                    }
                    .onChange(of: service.messages.count) { _, _ in
                        scrollToBottom(proxy: proxy)
                    }
                    .onChange(of: service.messages.last?.content) { _, _ in
                        scrollToBottom(proxy: proxy)
                    }
                }

                // Clarification chips
                if let options = service.clarifyOptions, !options.isEmpty {
                    ClarificationChipsView(
                        options: options,
                        onSelect: { chosen in
                            Task {
                                await service.send(text: chosen)
                            }
                        },
                        onDismiss: {
                            service.dismissClarify()
                        }
                    )
                }

                // Input bar dock
                ChatInputBar(
                    text: $inputText,
                    isExecuting: service.isExecuting,
                    onSend: {
                        let textToSend = inputText
                        inputText = ""
                        Task {
                            await service.send(text: textToSend)
                        }
                    }
                )
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            .navigationTitle("Coach Uphill")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    VStack(spacing: 2) {
                        Text("Coach Uphill")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                        HStack(spacing: 4) {
                            Circle()
                                .fill(statusColor)
                                .frame(width: 6, height: 6)
                            Text(statusLabel)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundStyle(UH.Palette.secondary)
                        }
                    }
                }

                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showClearAlert = true
                    } label: {
                        Image(systemName: "trash")
                            .font(.subheadline)
                            .foregroundStyle(UH.Palette.muted)
                    }
                    .accessibilityIdentifier("chat.clearButton")
                    .disabled(service.messages.isEmpty || service.isExecuting)
                    .accessibilityLabel("Clear conversation")
                }
            }
            .alert("Clear Conversation?", isPresented: $showClearAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Clear", role: .destructive) {
                    Task {
                        _ = await service.clear()
                    }
                }
            } message: {
                Text("All messages in this conversation will be permanently removed.")
            }
            .sheet(item: $sourcesSheetTarget) { sources in
                ChatSourcesSheet(sources: sources)
            }
            .sheet(isPresented: Binding(
                get: { selectedWorkoutID != nil && planModel != nil },
                set: { if !$0 { selectedWorkoutID = nil } }
            )) {
                if let id = selectedWorkoutID, let planModel {
                    WorkoutDetailSheet(model: planModel, workoutID: id)
                }
            }
            .task {
                await service.loadInitial(planId: plan?.id)
            }
        }
    }

    private var isThinkingBeforeTokens: Bool {
        service.isExecuting && (service.status == .admitting || service.status == .retrieving) && (service.messages.last?.role != .assistant)
    }

    private var statusIndicator: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)

            Text(statusLabel)
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
        }
    }

    private var statusColor: Color {
        switch service.status {
        case .idle, .done:
            return UH.Palette.accent
        case .retrieving, .generating, .admitting:
            return Color.orange
        case .error:
            return UH.Palette.danger
        case .interrupted:
            return UH.Palette.muted
        }
    }

    private var statusLabel: String {
        switch service.status {
        case .idle, .done:
            return L("Ready")
        case .retrieving:
            return L("Retrieving…")
        case .generating:
            return L("Generating…")
        case .admitting:
            return L("Connecting…")
        case .error:
            return L("Error")
        case .interrupted:
            return L("Interrupted")
        }
    }

    private var loadOlderButton: some View {
        Button {
            Task {
                await service.loadOlder()
            }
        } label: {
            HStack(spacing: 6) {
                if service.isLoadingOlder {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Image(systemName: "arrow.up.circle")
                }
                Text("Load earlier messages")
            }
            .font(UH.TextStyle.disclosure)
            .foregroundStyle(UH.Palette.accentInk)
            .padding(.horizontal, 14)
            .padding(.vertical, 6)
            .background(UH.Palette.activeFill, in: Capsule())
        }
        .disabled(service.isLoadingOlder)
        .padding(.vertical, 4)
    }

    private var emptyState: some View {
        VStack(spacing: UH.Space.regular) {
            Spacer(minLength: 24)

            ZStack {
                Circle()
                    .fill(UH.Palette.activeFill)
                    .frame(width: 72, height: 72)
                Image(systemName: "figure.run.circle.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(UH.Palette.accentInk)
            }

            VStack(spacing: 6) {
                Text("Coach Uphill (AI)")
                    .font(UH.TextStyle.sectionTitle)
                    .foregroundStyle(UH.Palette.ink)

                Text("Trail & ultra endurance coaching grounded in science.")
                    .font(UH.TextStyle.body)
                    .foregroundStyle(UH.Palette.secondary)
                    .multilineTextAlignment(.center)
            }

            // Starter chips
            VStack(spacing: 8) {
                Text("Suggested Questions")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)

                FlowLayout(spacing: 8) {
                    ForEach(starterChips, id: \.self) { chip in
                        Button {
                            UIImpactFeedbackGenerator(style: .light).impactOccurred()
                            Task {
                                await service.send(text: chip)
                            }
                        } label: {
                            Text(chip)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 8)
                                .background(Color.white, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                        }
                        .accessibilityIdentifier("chat.starterChip")
                    }
                }
                .padding(.horizontal, UH.Space.regular)
            }
            .padding(.top, 12)

            Text("Coach Uphill provides training suggestions based on endurance principles. Always listen to your body and consult medical professionals for injuries.")
                .font(.system(size: 11))
                .foregroundStyle(UH.Palette.muted)
                .italic()
                .multilineTextAlignment(.center)
                .padding(.horizontal, UH.Space.section)
                .padding(.top, 16)

            Spacer(minLength: 24)
        }
    }

    private var typingIndicatorBubble: some View {
        HStack {
            HStack(spacing: 5) {
                Circle().fill(UH.Palette.muted).frame(width: 6, height: 6)
                Circle().fill(UH.Palette.muted).frame(width: 6, height: 6)
                Circle().fill(UH.Palette.muted).frame(width: 6, height: 6)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(Color.white, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(UH.Palette.line, lineWidth: 1))

            Spacer()
        }
        .padding(.horizontal, UH.Space.regular)
    }

    private func errorBanner(_ err: ChatError) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.circle.fill")
                .foregroundStyle(UH.Palette.danger)

            Text(err.message ?? L("An error occurred."))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.danger)
                .lineLimit(2)

            Spacer()
        }
        .padding(UH.Space.small)
        .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .padding(.horizontal, UH.Space.regular)
        .padding(.top, 4)
    }

    private func scrollToBottom(proxy: ScrollViewProxy) {
        if let last = service.messages.last {
            withAnimation(reduceMotion ? nil : UH.Motion.standard) {
                proxy.scrollTo(last.id, anchor: .bottom)
            }
        }
    }
}

/// Simple flow layout for starter chips
struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? 300
        var height: CGFloat = 0
        var rowWidth: CGFloat = 0
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if rowWidth + size.width > width {
                height += rowHeight + spacing
                rowWidth = size.width + spacing
                rowHeight = size.height
            } else {
                rowWidth += size.width + spacing
                rowHeight = max(rowHeight, size.height)
            }
        }
        height += rowHeight
        return CGSize(width: width, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > bounds.maxX {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = size.height
            } else {
                rowHeight = max(rowHeight, size.height)
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
            x += size.width + spacing
        }
    }
}

extension MessageSourcesResponse: Identifiable {
    var id: Int { messageId }
}

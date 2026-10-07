import SwiftUI

public struct CorosPushButton: View {
    public let service: any DeviceConnectionServicing
    public var onReconnect: (() -> Void)? = nil

    @State private var status: CorosPushStatus?
    @State private var isSending: Bool = false
    @State private var outcomeMessage: String? = nil
    @State private var errorMessage: String? = nil

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    public init(
        service: any DeviceConnectionServicing,
        initialStatus: CorosPushStatus? = nil,
        onReconnect: (() -> Void)? = nil
    ) {
        self.service = service
        self.onReconnect = onReconnect
        _status = State(initialValue: initialStatus)
    }

    // Without an initial status the button used to render nothing, and SwiftUI
    // never runs .task on an empty view, so the status was never fetched. A
    // spinner keeps the view on screen until the status arrives.
    public var body: some View {
        content.task {
            if status?.lastSummary == nil {
                await refreshPushStatus()
            }
        }
    }

    @ViewBuilder
    private var content: some View {
        if let status, status.connected {
            VStack(alignment: .leading, spacing: 4) {
                Button {
                    Task { await sendPush() }
                } label: {
                    HStack(spacing: 6) {
                        if UIImage(named: "coros_mark") != nil {
                            Image("coros_mark")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 14, height: 14)
                        } else {
                            Image(systemName: "applewatch")
                                .font(.system(size: 13, weight: .bold))
                        }

                        if isSending {
                            ProgressView()
                                .controlSize(.small)
                            Text("Sending…")
                                .font(.system(size: 12, weight: .semibold))
                        } else {
                            Text("Send to COROS")
                                .font(.system(size: 12, weight: .semibold))
                        }
                    }
                    .foregroundStyle(UH.Palette.ink)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(UH.Palette.card, in: Capsule())
                    .overlay(Capsule().stroke(UH.Palette.line))
                }
                .buttonStyle(.plain)
                .disabled(isSending)
                .accessibilityIdentifier("coros.pushButton")

                // Status Indicator
                if status.partial == true {
                    Text("Partly sent. Try again.")
                        .font(.system(size: 11))
                        .foregroundStyle(UH.Palette.danger)
                } else if status.outOfDate == true {
                    Text("Changes not on your watch yet")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(UH.Palette.warningInk)
                } else if let when = formattedWhen(status.lastPushedAt) {
                    Text("Sent to COROS · \(when)")
                        .font(.system(size: 11))
                        .foregroundStyle(UH.Palette.secondary)
                }

                // Push Outcome Message
                if let outcomeMessage {
                    HStack(spacing: 4) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(UH.Palette.accentInk)
                            .font(.system(size: 11))
                        Text(outcomeMessage)
                            .font(.system(size: 11))
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    .transition(.opacity)
                }

                if let errorMessage {
                    HStack(spacing: 4) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(UH.Palette.danger)
                            .font(.system(size: 11))
                        Text(errorMessage)
                            .font(.system(size: 11))
                            .foregroundStyle(UH.Palette.danger)
                    }
                    .transition(.opacity)
                }
            }
        } else if status == nil {
            ProgressView()
                .controlSize(.small)
        }
    }

    private func formattedWhen(_ iso: String?) -> String? {
        guard let iso, let date = ISO8601DateFormatter().date(from: iso) else { return nil }
        let f = DateFormatter()
        f.dateFormat = "EEE HH:mm"
        return f.string(from: date)
    }

    private func refreshPushStatus() async {
        let today = Self.dateFormatter.string(from: Date())
        if let s = try? await service.fetchPushStatus(clientToday: today) {
            withAnimation(UH.Motion.standard) {
                self.status = s
            }
        }
    }

    private func sendPush() async {
        isSending = true
        outcomeMessage = nil
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        let today = Self.dateFormatter.string(from: Date())
        do {
            let outcome = try await service.pushToCoros(clientToday: today, lang: "en")
            if outcome.isSuccess {
                UINotificationFeedbackGenerator().notificationOccurred(.success)
                let workouts = outcome.summary?.workoutsSent ?? 0
                let end = outcome.summary?.windowEnd ?? "upcoming window"
                withAnimation(UH.Motion.standard) {
                    self.outcomeMessage = "Sent \(workouts) workouts to COROS through \(end)."
                }
                await refreshPushStatus()
            } else {
                UINotificationFeedbackGenerator().notificationOccurred(.error)
                withAnimation(UH.Motion.standard) {
                    self.errorMessage = outcome.errorMessage ?? "Could not send workouts to COROS."
                }
            }
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            withAnimation(UH.Motion.standard) {
                self.errorMessage = error.localizedDescription
            }
        }
        isSending = false
    }
}

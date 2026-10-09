import SwiftUI
import AuthenticationServices

public struct ConnectedAccountsView: View {
    public let service: any DeviceConnectionServicing
    public var onUpdatedUser: ((FitnessSyncResult) -> Void)? = nil

    @State private var status: DeviceConnectionStatus?
    @State private var isLoading: Bool = false
    @State private var isSyncing: Bool = false
    @State private var isSyncingFitness: Bool = false
    @State private var noticeMessage: String? = nil
    @State private var errorMessage: String? = nil
    @State private var showDisconnectConfirm: Bool = false

    public init(
        service: any DeviceConnectionServicing,
        initialStatus: DeviceConnectionStatus? = nil,
        onUpdatedUser: ((FitnessSyncResult) -> Void)? = nil
    ) {
        self.service = service
        self.onUpdatedUser = onUpdatedUser
        _status = State(initialValue: initialStatus)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            // Header
            HStack(spacing: 6) {
                Image(systemName: "applewatch")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundStyle(UH.Palette.accentInk)

                Text("CONNECTED ACCOUNTS")
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .tracking(0.6)
                    .foregroundStyle(UH.Palette.muted)
            }

            Text("Connect your watch so completed runs are matched to your plan automatically.")
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)

            // COROS Integration Row Card
            corosRowCard

            // Live Notices
            if let noticeMessage {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 12))
                        .foregroundStyle(UH.Palette.accentInk)
                    Text(noticeMessage)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .transition(.opacity)
            }

            if let errorMessage {
                HStack(spacing: 6) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 12))
                        .foregroundStyle(UH.Palette.danger)
                    Text(errorMessage)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.danger)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(UH.Palette.danger.opacity(0.1), in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .transition(.opacity)
            }

            Text("When disconnecting, data received from COROS is permanently deleted within 24 hours.")
                .font(.system(size: 10))
                .foregroundStyle(UH.Palette.muted)
                .padding(.top, 2)
        }
        .trainingCard()
        .task {
            if status == nil {
                await loadStatus()
            }
        }
        .confirmationDialog(
            "Disconnect COROS?",
            isPresented: $showDisconnectConfirm,
            titleVisibility: .visible
        ) {
            Button("Disconnect COROS", role: .destructive) {
                Task { await handleDisconnect() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Your past workouts and health metrics from COROS will no longer automatically sync.")
        }
    }

    // MARK: - COROS Device Row

    private var corosRowCard: some View {
        let isConnected = status?.isCorosConnected ?? false

        return VStack(alignment: .leading, spacing: 10) {
            // Header Row: Brand Logo + Status Badge
            HStack(alignment: .center) {
                if UIImage(named: "coros_logo") != nil {
                    Image("coros_logo")
                        .resizable()
                        .scaledToFit()
                        .frame(height: 18)
                } else {
                    Text("COROS")
                        .font(.system(size: 15, weight: .black, design: .monospaced))
                        .foregroundStyle(UH.Palette.ink)
                }

                Spacer()

                if isLoading && status == nil {
                    Text("Checking connection…")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                } else if isConnected {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(UH.Palette.accentInk)
                            .frame(width: 6, height: 6)
                        Text(status?.coros?.lastSyncAt != nil ? L("Synced") : L("Connected"))
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(UH.Palette.accentInk)
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(UH.Palette.activeFill, in: Capsule())
                } else {
                    Text("Not connected")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(UH.Palette.muted)
                }
            }

            // Sync Date & Legal Attribution
            if isConnected {
                VStack(alignment: .leading, spacing: 4) {
                    if let lastSync = status?.coros?.lastSyncAt, let formatted = formatSyncDate(lastSync) {
                        Text("Last synced \(formatted)")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    CorosAttribution()
                }
            }

            // Actions Row
            if isConnected {
                Divider().overlay(UH.Palette.line.opacity(0.6))

                HStack(spacing: 8) {
                    Button {
                        Task { await handleSyncFitness() }
                    } label: {
                        HStack(spacing: 4) {
                            if isSyncingFitness {
                                ProgressView().controlSize(.mini)
                            } else {
                                Image(systemName: "bolt.fill")
                                    .font(.system(size: 10))
                            }
                            Text("Sync EvoLab")
                                .font(.system(size: 11, weight: .bold))
                                .fixedSize()
                        }
                        .foregroundStyle(UH.Palette.ink)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                    }
                    .buttonStyle(.plain)
                    .disabled(isSyncing || isSyncingFitness)

                    Button {
                        Task { await handleSyncNow() }
                    } label: {
                        HStack(spacing: 4) {
                            if isSyncing {
                                ProgressView().controlSize(.mini)
                            } else {
                                Image(systemName: "arrow.triangle.2.circlepath")
                                    .font(.system(size: 10))
                            }
                            Text(isSyncing ? L("Syncing…") : L("Sync now"))
                                .font(.system(size: 11, weight: .bold))
                                .fixedSize()
                        }
                        .foregroundStyle(UH.Palette.ink)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
                    }
                    .buttonStyle(.plain)
                    .disabled(isSyncing || isSyncingFitness)

                    Spacer()

                    Button {
                        showDisconnectConfirm = true
                    } label: {
                        Text("Disconnect")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(UH.Palette.danger)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                    .disabled(isSyncing || isSyncingFitness)
                }
            } else {
                Button {
                    Task { await handleConnect() }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "link")
                            .font(.system(size: 11, weight: .bold))
                        Text("Connect COROS Account")
                            .font(.system(size: 12, weight: .bold))
                    }
                    .foregroundStyle(UH.Palette.buttonInk)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(UH.Palette.accent, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }
                .buttonStyle(.plain)
                .disabled(isLoading)
            }
        }
        .padding(12)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
    }

    private func formatSyncDate(_ iso: String) -> String? {
        guard let date = ISO8601DateFormatter().date(from: iso) else { return nil }
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f.string(from: date)
    }

    private func loadStatus() async {
        isLoading = true
        do {
            let s = try await service.fetchStatus()
            withAnimation(UH.Motion.standard) {
                self.status = s
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func handleConnect() async {
        isLoading = true
        errorMessage = nil
        noticeMessage = nil

        let result = await CorosOAuthCoordinator.shared.connect(via: service)
        switch result {
        case .success:
            await loadStatus()
            withAnimation(UH.Motion.standard) {
                noticeMessage = L("Connected to COROS · Syncing activities...")
            }
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        case .cancelled:
            break
        case .failed(let msg):
            errorMessage = msg
        }
        isLoading = false
    }

    private func handleSyncNow() async {
        isSyncing = true
        noticeMessage = nil
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        do {
            let result = try await service.syncNow(days: 30)
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            withAnimation(UH.Motion.standard) {
                self.noticeMessage = L("Sync successful: fetched %lld workouts and %lld days of health data.", result.activities, result.dailyMetrics)
            }
            await loadStatus()
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            errorMessage = L("Sync failed. Please try again.")
        }
        isSyncing = false
    }

    private func handleSyncFitness() async {
        isSyncingFitness = true
        noticeMessage = nil
        errorMessage = nil
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()

        do {
            let result = try await service.syncFitness()
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            withAnimation(UH.Motion.standard) {
                let pace = result.thresholdPace ?? "—"
                let vo2 = result.corosVo2max != nil ? "\(Int(result.corosVo2max!))" : "—"
                self.noticeMessage = L("EvoLab synced successfully: threshold pace %@/km, VO2max %@.", pace, vo2)
            }
            onUpdatedUser?(result)
            await loadStatus()
        } catch {
            UINotificationFeedbackGenerator().notificationOccurred(.error)
            errorMessage = L("EvoLab sync failed. Please try again.")
        }
        isSyncingFitness = false
    }

    private func handleDisconnect() async {
        isLoading = true
        noticeMessage = nil
        errorMessage = nil

        do {
            try await service.disconnectCoros()
            withAnimation(UH.Motion.standard) {
                self.status = DeviceConnectionStatus(coros: nil)
                self.noticeMessage = L("Disconnected from COROS.")
            }
        } catch {
            errorMessage = L("Could not disconnect.")
        }
        isLoading = false
    }
}

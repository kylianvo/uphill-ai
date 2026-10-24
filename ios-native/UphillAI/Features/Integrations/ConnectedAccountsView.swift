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
    @State private var garminConsent: Bool = false
    @State private var showGarminDisconnectConfirm: Bool = false

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

            // Hidden until the backend turns Garmin on (GARMIN_ENABLED).
            if let garmin = status?.garmin, garmin.enabled {
                garminRowCard(garmin)
            }

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
        .confirmationDialog(
            "Disconnect Garmin?",
            isPresented: $showGarminDisconnectConfirm,
            titleVisibility: .visible
        ) {
            Button("Disconnect Garmin", role: .destructive) {
                Task { await handleGarminDisconnect() }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This also withdraws your AI consent. Your Garmin data is deleted within 24 hours.")
        }
    }

    // MARK: - Garmin Device Row

    /// Garmin Agreement s15.10: explicit consent to AI coaching on Garmin data before
    /// connecting, withdrawable at any time. Every coaching feature is AI, so withdrawing
    /// consent is disconnecting. Starter access has no history: data starts at the next watch sync.
    private func garminRowCard(_ garmin: GarminConnectionStatus) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .center) {
                Text(verbatim: "Garmin Connect™")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundStyle(UH.Palette.ink)

                Spacer()

                if garmin.connected {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(UH.Palette.accentInk)
                            .frame(width: 6, height: 6)
                        Text("Connected")
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

            if garmin.connected {
                VStack(alignment: .leading, spacing: 4) {
                    if let last = garmin.lastSyncAt, let formatted = formatSyncDate(last) {
                        Text("Last data received \(formatted)")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    } else {
                        Text("Data arrives after your next watch sync.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                    Text(verbatim: "Garmin")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundStyle(UH.Palette.muted)
                }

                Divider().overlay(UH.Palette.line.opacity(0.6))

                HStack {
                    Spacer()
                    Button {
                        showGarminDisconnectConfirm = true
                    } label: {
                        Text("Disconnect")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(UH.Palette.danger)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                    .disabled(isLoading)
                }
            } else {
                Button {
                    garminConsent.toggle()
                } label: {
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: garminConsent ? "checkmark.square.fill" : "square")
                            .font(.system(size: 16))
                            .foregroundStyle(garminConsent ? UH.Palette.accentInk : UH.Palette.muted)
                        Text("I agree that Uphill AI's AI coach uses my Garmin data to build and adapt my plan. Withdrawing consent disconnects Garmin and deletes its data within 24 hours.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .multilineTextAlignment(.leading)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(garminConsent ? [.isSelected] : [])

                if let url = URL(string: "https://uphill-ai.io.vn/privacy") {
                    Link("Privacy notice", destination: url)
                        .font(UH.TextStyle.caption)
                        .padding(.leading, 24)
                }

                Button {
                    Task { await handleGarminConnect() }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "link")
                            .font(.system(size: 11, weight: .bold))
                        Text("Connect Garmin Account")
                            .font(.system(size: 12, weight: .bold))
                    }
                    .foregroundStyle(UH.Palette.buttonInk)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(UH.Palette.accent, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .opacity(garminConsent ? 1 : 0.45)
                }
                .buttonStyle(.plain)
                .disabled(isLoading || !garminConsent)
            }
        }
        .padding(12)
        .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
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

    private func handleGarminConnect() async {
        isLoading = true
        errorMessage = nil
        noticeMessage = nil

        let result = await CorosOAuthCoordinator.shared.connect(via: service, provider: .garmin)
        switch result {
        case .success:
            await loadStatus()
            garminConsent = false
            withAnimation(UH.Motion.standard) {
                noticeMessage = L("Connected to Garmin. Data arrives after your next watch sync.")
            }
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        case .cancelled:
            break
        case .failed(let msg):
            errorMessage = msg
        }
        isLoading = false
    }

    private func handleGarminDisconnect() async {
        isLoading = true
        noticeMessage = nil
        errorMessage = nil
        do {
            try await service.disconnectGarmin()
            await loadStatus()
            withAnimation(UH.Motion.standard) {
                noticeMessage = L("Disconnected from Garmin.")
            }
        } catch {
            errorMessage = L("Could not disconnect.")
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
                self.status = DeviceConnectionStatus(coros: nil, appleHealth: status?.appleHealth, garmin: status?.garmin)
                self.noticeMessage = L("Disconnected from COROS.")
            }
        } catch {
            errorMessage = L("Could not disconnect.")
        }
        isLoading = false
    }
}

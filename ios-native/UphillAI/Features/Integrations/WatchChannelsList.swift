import SwiftUI

/// The watch sources Uphill reads from: COROS today, the rest listed so athletes
/// on other watches know where they stand. Used by onboarding's watch step.
struct WatchChannelsList: View {
    let connected: Bool
    /// False when no device service is wired (previews, tests): the connect button hides.
    let available: Bool
    let healthConnected: Bool
    /// False when Apple Health can't be offered (no HealthKit, feature off, previews): its block hides.
    let healthAvailable: Bool
    /// Runs the COROS connection; returns an error message to show, or nil.
    let connect: () async -> String?
    /// Runs the Apple Health connection; returns an error message to show, or nil.
    let connectHealth: () async -> String?

    @State private var isConnecting = false
    @State private var error: String?
    @State private var isConnectingHealth = false
    @State private var healthError: String?

    static let upcoming: [(name: String, symbol: String)] = [
        ("Garmin", "watch.analog"),
        ("Suunto", "watch.analog"),
        ("Polar", "watch.analog"),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                HStack(spacing: UH.Space.regular) {
                    channelBadge(symbol: "watch.analog", live: true)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(verbatim: "COROS").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        Text("Runs, weekly mileage and fitness, synced automatically.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Spacer(minLength: 0)
                    if connected {
                        Label("Connected", systemImage: "checkmark.circle.fill")
                            .labelStyle(.iconOnly)
                            .font(.title2)
                            .foregroundStyle(UH.Palette.accentInk)
                            .accessibilityLabel("COROS connected")
                    }
                }

                if connected {
                    Text("Connected. I'll use your recent runs to set your starting mileage.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.accentInk)
                } else if available {
                    Button {
                        Task {
                            isConnecting = true
                            error = await connect()
                            isConnecting = false
                        }
                    } label: {
                        if isConnecting { ProgressView() } else { Text("Connect COROS") }
                    }
                    .buttonStyle(.uhPrimary)
                    .disabled(isConnecting)
                    .accessibilityIdentifier("setup.connectCoros")
                }

                if let error {
                    Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger)
                }
            }
            .trainingCard()

            if healthAvailable { appleHealthCard }

            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text("Coming soon").font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                VStack(spacing: 0) {
                    ForEach(Array(Self.upcoming.enumerated()), id: \.offset) { index, channel in
                        if index > 0 { Divider() }
                        HStack(spacing: UH.Space.regular) {
                            channelBadge(symbol: channel.symbol, live: false)
                            Text(verbatim: channel.name).font(UH.TextStyle.label).foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Text("Soon")
                                .font(UH.TextStyle.caption.weight(.semibold))
                                .foregroundStyle(UH.Palette.muted)
                        }
                        .frame(minHeight: 52)
                        .accessibilityElement(children: .combine)
                        .accessibilityLabel(L("%@, coming soon", channel.name))
                    }
                }
                .padding(.horizontal, UH.Space.regular)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line, lineWidth: 1))

                Text("No watch? Skip this. You can connect one later in Me → Connected accounts.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var appleHealthCard: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            HStack(spacing: UH.Space.regular) {
                channelBadge(symbol: "heart.fill", live: true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(verbatim: "Apple Health").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text("Runs, hikes and strength sessions from your iPhone, Apple Watch or any app that saves to Health.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer(minLength: 0)
                if healthConnected {
                    Label("Connected", systemImage: "checkmark.circle.fill")
                        .labelStyle(.iconOnly)
                        .font(.title2)
                        .foregroundStyle(UH.Palette.accentInk)
                        .accessibilityLabel(L("Apple Health connected"))
                }
            }

            if healthConnected {
                Text("Connected. I'll use your recent workouts to set your starting mileage.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.accentInk)
                    .fixedSize(horizontal: false, vertical: true)
            } else {
                Button {
                    Task {
                        isConnectingHealth = true
                        healthError = await connectHealth()
                        isConnectingHealth = false
                    }
                } label: {
                    if isConnectingHealth { ProgressView() } else { Text("Connect Apple Health") }
                }
                .buttonStyle(.uhPrimary)
                .disabled(isConnectingHealth)
                .accessibilityIdentifier("setup.connectAppleHealth")
            }

            if let healthError {
                Text(healthError)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.danger)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .trainingCard()
    }

    private func channelBadge(symbol: String, live: Bool) -> some View {
        Image(systemName: symbol)
            .font(.title3.weight(.semibold))
            .foregroundStyle(live ? UH.Palette.accentInk : UH.Palette.muted)
            .frame(width: 44, height: 44)
            .background(live ? UH.Palette.accent.opacity(0.12) : UH.Palette.surface,
                        in: RoundedRectangle(cornerRadius: UH.Radius.control))
    }
}

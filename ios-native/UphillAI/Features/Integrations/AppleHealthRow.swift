import SwiftUI

/// Me → Connected accounts: connect, sync, or disconnect Apple Health. Styled after the COROS card.
struct AppleHealthRow: View {
    let app: AppModel
    @State private var showExplainer = false
    @State private var showDisconnect = false

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            HStack(alignment: .top, spacing: UH.Space.small) {
                Image(systemName: "heart.fill")
                    .foregroundStyle(UH.Palette.accentInk)
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(verbatim: "Apple Health").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text(subtitle).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("health.subtitle")
                }
                Spacer(minLength: 0)
                if app.appleHealthSyncing { ProgressView().controlSize(.small) }
            }
            if let message = app.appleHealthMessage {
                let isError = app.appleHealthMessageIsError
                HStack(alignment: .top, spacing: 6) {
                    Image(systemName: isError ? "exclamationmark.triangle.fill" : "info.circle.fill").accessibilityHidden(true)
                    Text(message).fixedSize(horizontal: false, vertical: true)
                }
                .font(UH.TextStyle.caption)
                .foregroundStyle(isError ? UH.Palette.danger : UH.Palette.warningInk)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(isError ? UH.Palette.danger.opacity(0.1) : UH.Palette.warningFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .accessibilityIdentifier("health.message")
            }
            if app.appleHealthConnected {
                Divider().overlay(UH.Palette.line.opacity(0.6))
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 8) { syncButton; Spacer(minLength: 0); disconnectButton }
                    VStack(alignment: .leading, spacing: 8) { syncButton; disconnectButton }
                }
            } else {
                Button { showExplainer = true } label: {
                    Text("Connect Apple Health")
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.buttonInk)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .padding(.horizontal, UH.Space.small)
                        .background(UH.Palette.accent.opacity(app.appleHealthSyncing ? 0.45 : 1),
                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }
                .buttonStyle(.plain)
                .disabled(app.appleHealthSyncing)
                .accessibilityIdentifier("health.connect")
            }
        }
        .trainingCard()
        .sheet(isPresented: $showExplainer) {
            AppleHealthExplainerSheet { Task { await app.connectAppleHealth() } }
        }
        .confirmationDialog("Disconnect Apple Health?", isPresented: $showDisconnect, titleVisibility: .visible) {
            Button("Disconnect", role: .destructive) { Task { await app.disconnectAppleHealth() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Workouts received from Apple Health are deleted from Uphill AI. To stop sharing completely, turn off access in Settings → Health → Data Access & Devices.")
        }
    }

    /// "Sync now" re-runs connect, which is idempotent and also repairs a phone that isn't observing.
    private var syncButton: some View {
        Button { Task { await app.connectAppleHealth() } } label: {
            Text("Sync now")
                .font(UH.TextStyle.disclosure)
                .foregroundStyle(UH.Palette.ink)
                .padding(.horizontal, 10)
                .frame(minHeight: 44)
                .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line))
        }
        .buttonStyle(.plain)
        .disabled(app.appleHealthSyncing)
        .accessibilityIdentifier("health.syncNow")
    }

    private var disconnectButton: some View {
        Button { showDisconnect = true } label: {
            Text("Disconnect")
                .font(UH.TextStyle.disclosure)
                .foregroundStyle(UH.Palette.danger)
                .padding(.horizontal, 6)
                .frame(minHeight: 44)
        }
        .buttonStyle(.plain)
        .disabled(app.appleHealthSyncing)
        .accessibilityIdentifier("health.disconnect")
    }

    private var subtitle: String {
        if app.appleHealthSyncing { return L("Syncing…") }
        if app.appleHealthConnected {
            if let last = app.appleHealthLastSync, let formatted = Self.formatSyncDate(last) {
                return L("Last synced %@", formatted)
            }
            return L("Connected")
        }
        return L("Runs, hikes and strength sessions from your iPhone, Apple Watch or any app that saves to Health.")
    }

    /// Same output as the COROS card, but accepts the backend's fractional-second timestamps
    /// ("2026-10-13T14:29:30.427957+00:00"), which a plain ISO8601DateFormatter rejects.
    static func formatSyncDate(_ iso: String) -> String? {
        let parser = ISO8601DateFormatter()
        parser.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        var parsed = parser.date(from: iso)
        if parsed == nil {
            parser.formatOptions = [.withInternetDateTime]
            parsed = parser.date(from: iso)
        }
        guard let date = parsed else { return nil }
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f.string(from: date)
    }
}

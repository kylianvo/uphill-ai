import SwiftUI

struct ProfileView: View {
    let app: AppModel
    @State private var showDeveloperMenu = false
    @State private var path: [TrainingDestination] = []
    @State private var showSchedule = false

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if let user = app.session.user {
                    Section {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(user.name).font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)
                            Text(user.email).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                    Section("Training") {
                        NavigationLink("About you", value: TrainingDestination.aboutYou)
                        NavigationLink("Heart rate", value: TrainingDestination.heartRate)
                        NavigationLink("Paces", value: TrainingDestination.paces)
                    }
                    Section("Training profile") {
                        row("Weekly volume", user.currentWeeklyKm.map { "\(Int($0.rounded())) km" })
                        row("Days per week", user.daysPerWeek.map(String.init))
                        row("Long run day", user.longRunDay.flatMap { $0.isEmpty ? nil : $0 })
                        row("Aerobic threshold HR", user.aetHr.map { "\($0) bpm" })
                        row("Anaerobic threshold HR", user.antHr.map { "\($0) bpm" })
                        row("Zone 2 pace", zone2(user))
                    }
                }
                Section("Account") {
                    if app.session.user?.provider == "email" {
                        NavigationLink("Change password") { ChangePasswordScreen(app: app) }
                    }
                    Button("Sign out", role: .destructive) {
                        Task { await app.signOut() }
                    }
                }
                Section {
                    Text(versionLabel)
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.muted)
                        .frame(maxWidth: .infinity)
                        .onLongPressGesture { showDeveloperMenu = DeveloperMenu.isAvailable }
                }
                .listRowBackground(Color.clear)
            }
            .navigationTitle("Me")
            .navigationDestination(for: TrainingDestination.self) { section in
                if app.session.user != nil { ProfileSettingsScreen(app: app, section: section) }
            }
            .onChange(of: app.trainingDestination, initial: true) { _, destination in
                guard let destination else { return }
                app.trainingDestination = nil
                if destination == .schedule { showSchedule = true }
                else { path.append(destination) }
            }
            .sheet(isPresented: $showSchedule) { ScheduleChangeSheet(model: app.plan) }
            .sheet(isPresented: $showDeveloperMenu) { DeveloperMenu() }
        }
    }

    private func row(_ title: String, _ value: String?) -> some View {
        LabeledContent(title, value: value ?? "Not set")
            .foregroundStyle(UH.Palette.ink)
    }

    private func zone2(_ user: User) -> String? {
        guard let min = user.zone2PaceMin, let max = user.zone2PaceMax else { return nil }
        return "\(min)–\(max) /km"
    }

    private var versionLabel: String {
        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "?"
        let build = info?["CFBundleVersion"] as? String ?? "?"
        return "Uphill AI \(version) (\(build))"
    }
}

import SwiftUI

/// Debug-only backend switcher. Long-press the version label in Me to open it.
struct DeveloperMenu: View {
    @AppStorage(AppEnvironment.defaultsKey) private var selected = AppEnvironment.local.rawValue
    @AppStorage(SampleHealthStore.defaultsKey) private var sampleHealth = false
    @Environment(\.dismiss) private var dismiss

    static var isAvailable: Bool {
        #if DEBUG
        true
        #else
        false
        #endif
    }

    var body: some View {
        NavigationStack {
            Form {
                Picker("Backend", selection: $selected) {
                    ForEach(AppEnvironment.allCases) { env in
                        Text("\(env.rawValue) — \(env.baseURL.absoluteString)").tag(env.rawValue)
                    }
                }
                .pickerStyle(.inline)
                Text("Sign out after switching: sessions don't carry across backends.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
                Section {
                    Toggle("Sample Health data", isOn: $sampleHealth)
                } footer: {
                    Text("Uses three made-up workouts instead of HealthKit. Relaunch the app after changing it.")
                }
            }
            .navigationTitle("Developer")
            .toolbar { Button("Done") { dismiss() } }
        }
    }
}

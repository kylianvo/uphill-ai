import SwiftUI

struct NotificationSettingsView: View {
    @Bindable var model: NotificationCoordinator

    private static let kindNames: [String: LocalizedStringKey] = [
        "week_brief": "Monday briefs",
        "planning": "Coaching notes",
        "taper": "Coaching notes",
        "race": "Coaching notes",
        "recognition": "Session recognition",
        "unlogged": "Missed sessions",
        "checklist": "Profile tips",
        "knowledge": "Knowledge tips",
    ]

    private var enabled: Bool {
        let p = model.preferences
        return p.workoutsEnabled || p.coachingEnabled || p.resultsEnabled
    }

    var body: some View {
        Form {
            Section {
                Toggle("Notifications", isOn: Binding(get: { enabled }, set: { on in Task { await model.setEnabled(on) } }))
            } footer: {
                Text("Workout reminders, a Monday week brief and the occasional coaching note. At most one a day, never at night.")
            }
            if enabled {
                Section {
                    if NotificationCoordinator.date(model.preferences.pausedUntil).map({ $0 > .now }) == true {
                        Button("Resume notifications") {
                            var value = model.preferences
                            value.pausedUntil = nil
                            Task { await model.save(value) }
                        }
                    } else {
                        Button("Pause for a week") {
                            var value = model.preferences
                            value.pausedUntil = ISO8601DateFormatter().string(from: .now.addingTimeInterval(7 * 86_400))
                            Task { await model.save(value) }
                        }
                    }
                }
            }
            if let muted = model.preferences.mutedKinds, !muted.isEmpty {
                Section("Muted") {
                    ForEach(muted, id: \.self) { kind in
                        HStack {
                            Text(Self.kindNames[kind] ?? "Coaching notes")
                            Spacer()
                            Button { Task { await model.unmute(kind) } } label: { Image(systemName: "xmark.circle.fill") }
                                .buttonStyle(.borderless)
                                .foregroundStyle(UH.Palette.secondary)
                                .accessibilityLabel(Text("Unmute"))
                        }
                    }
                }
            }
            if model.permission == "denied" || model.error != nil {
                Section {
                    if model.permission == "denied" {
                        Button("Open notification settings") {
                            if let url = URL(string: UIApplication.openNotificationSettingsURLString) { UIApplication.shared.open(url) }
                        }
                    }
                    if let error = model.error { Text(error).foregroundStyle(UH.Palette.danger) }
                }
            }
        }
        .navigationTitle("Notifications")
        .disabled(model.saving)
    }
}

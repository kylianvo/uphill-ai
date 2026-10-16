import SwiftUI

struct NotificationSettingsView: View {
    @Bindable var model: NotificationCoordinator

    var body: some View {
        Form {
            Section {
                toggle("Workout reminders", \.workoutsEnabled)
                toggle("Coaching tips", \.coachingEnabled)
                toggle("Plan ready updates", \.resultsEnabled)
            } footer: { Text("At most one coaching reminder a day. Requested plan updates are separate.") }
            Section("Timing") {
                timePicker("Workout reminder", \.workoutTime)
                timePicker("Coaching reminder", \.coachingTime)
                timePicker("Quiet hours start", \.quietStart)
                timePicker("Quiet hours end", \.quietEnd)
                Picker("Distance units", selection: binding(\.distanceUnit)) {
                    Text("km").tag("km")
                    Text("mi").tag("mi")
                }
            }
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
                if model.permission == "denied" {
                    Button("Open notification settings") {
                        if let url = URL(string: UIApplication.openNotificationSettingsURLString) { UIApplication.shared.open(url) }
                    }
                }
                if let error = model.error { Text(error).foregroundStyle(UH.Palette.danger) }
            }
        }
        .navigationTitle("Notifications")
        .disabled(model.saving)
    }

    private func binding<T>(_ key: WritableKeyPath<NotificationPreferences, T>) -> Binding<T> {
        Binding(get: { model.preferences[keyPath: key] }, set: { next in
            var value = model.preferences
            value[keyPath: key] = next
            Task { await model.save(value) }
        })
    }

    private func toggle(_ title: LocalizedStringKey, _ key: WritableKeyPath<NotificationPreferences, Bool>) -> some View {
        Toggle(title, isOn: Binding(get: { model.preferences[keyPath: key] }, set: { enabled in
            var value = model.preferences
            value[keyPath: key] = enabled
            Task { await model.save(value, requestPermission: enabled) }
        }))
    }

    private func timePicker(_ title: LocalizedStringKey, _ key: WritableKeyPath<NotificationPreferences, String>) -> some View {
        DatePicker(title, selection: Binding(get: {
            let parts = model.preferences[keyPath: key].split(separator: ":").compactMap { Int($0) }
            return Calendar.current.date(from: DateComponents(hour: parts.first ?? 7, minute: parts.last ?? 0)) ?? .now
        }, set: { date in
            let components = Calendar.current.dateComponents([.hour, .minute], from: date)
            binding(key).wrappedValue = String(format: "%02d:%02d", components.hour ?? 7, components.minute ?? 0)
        }), displayedComponents: .hourAndMinute)
    }
}

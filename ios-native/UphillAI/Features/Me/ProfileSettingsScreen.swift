import SwiftUI

/// Uses ios-native/docs/design-baseline.md and native grouped form navigation.
struct ProfileSettingsScreen: View {
    @State private var model: ProfileSettingsModel
    @State private var showGuide = false

    init(app: AppModel, section: TrainingDestination) {
        _model = State(initialValue: ProfileSettingsModel(user: app.session.user!, section: section,
            service: ProfileService(client: app.client), session: app.session,
            isOffline: { app.isOffline || app.plan.cachedAt != nil }))
    }

    private var title: String {
        switch model.section {
        case .aboutYou: "About you"
        case .heartRate: "Heart rate"
        case .paces: "Paces"
        case .schedule: "Schedule"
        }
    }

    var body: some View {
        Form {
            switch model.section {
            case .aboutYou:
                Section {
                    number("Age", value: $model.draft.age, unit: "years")
                    Picker("Sex", selection: $model.draft.gender) {
                        Text("Prefer not to say").tag(String?.none)
                        Text("Female").tag(String?("female"))
                        Text("Male").tag(String?("male"))
                        Text("Other").tag(String?("other"))
                    }
                    optionalNumber("Height", value: $model.draft.heightCm, unit: "cm")
                    optionalNumber("Weight", value: $model.draft.weightKg, unit: "kg")
                }
                Section("Injuries and notes for Coach Uphill") {
                    TextField("Injuries and notes for Coach Uphill", text: text($model.draft.athleteNotes), axis: .vertical)
                        .lineLimit(3...8)
                }
            case .heartRate:
                Section {
                    number("Max heart rate", value: $model.draft.maxHr, unit: "bpm")
                    number("Resting heart rate", value: $model.draft.restingHr, unit: "bpm")
                    number("Aerobic threshold (AeT)", value: $model.draft.aetHr, unit: "bpm")
                    number("Anaerobic threshold (AnT)", value: $model.draft.antHr, unit: "bpm")
                }
                Section { Button("How to find these") { showGuide = true }.frame(minHeight: 44) }
            case .paces:
                Section {
                    Picker("Zone model", selection: $model.draft.paceZoneModel) {
                        Text("5 zones").tag("5_zone"); Text("4 zones").tag("4_zone")
                    }
                    pace("Threshold pace", value: $model.draft.thresholdPace)
                    pace("Zone 2 Pace Min", value: $model.draft.zone2PaceMin)
                    pace("Zone 2 Pace Max", value: $model.draft.zone2PaceMax)
                }
                Section("Your Training Zones") {
                    if let zones = model.zones {
                        ForEach(zones.rows) { row in
                            VStack(alignment: .leading, spacing: UH.Space.compact) {
                                LabeledContent("Zone \(row.id)", value: row.pace)
                                if let hr = row.hr { Text(hr).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary) }
                            }
                        }
                    } else { ProgressView() }
                }
            case .schedule: EmptyView()
            }
            Section {
                if let error = model.error { Text(error).foregroundStyle(UH.Palette.danger).accessibilityAddTraits(.updatesFrequently) }
                if model.saved { Text("Saved. Your next week will use these.").foregroundStyle(UH.Palette.accentInk) }
                Button { Task { await model.save() } } label: {
                    if model.isSaving { ProgressView() } else { Text("Save") }
                }.buttonStyle(.uhPrimary).disabled(model.isSaving)
            }
        }
        .navigationTitle(title).navigationBarTitleDisplayMode(.inline)
        .scrollContentBackground(.hidden).background(UH.Palette.surface)
        .tint(UH.Palette.accentInk)
        .sheet(isPresented: $showGuide) { WatchZonesGuideSheet() }
        .task(id: model.draft.paceZoneModel) { if model.section == .paces { await model.loadZones() } }
    }

    private func text(_ value: Binding<String?>) -> Binding<String> {
        Binding(get: { value.wrappedValue ?? "" }, set: { value.wrappedValue = $0 })
    }
    private func pace(_ title: String, value: Binding<String?>) -> some View {
        LabeledContent(title) { TextField("m:ss /km", text: text(value)).multilineTextAlignment(.trailing).keyboardType(.numbersAndPunctuation) }
    }
    private func number(_ title: String, value: Binding<Int>, unit: String) -> some View {
        LabeledContent(title) { HStack { TextField(title, value: value, format: .number).multilineTextAlignment(.trailing).keyboardType(.numberPad); Text(unit).foregroundStyle(UH.Palette.secondary) } }
    }
    private func optionalNumber(_ title: String, value: Binding<Double?>, unit: String) -> some View {
        LabeledContent(title) { HStack { TextField(title, value: value, format: .number).multilineTextAlignment(.trailing).keyboardType(.decimalPad); Text(unit).foregroundStyle(UH.Palette.secondary) } }
    }
}

struct ChangePasswordScreen: View {
    let app: AppModel
    @State private var password = ""
    @State private var confirmation = ""
    @State private var message: String?
    @State private var saving = false

    var body: some View {
        Form {
            Section {
                SecureField("New Password", text: $password).textContentType(.newPassword)
                SecureField("Confirm New Password", text: $confirmation).textContentType(.newPassword)
                Text("Min 8 characters").font(UH.TextStyle.caption)
            }
            Section {
                if let message { Text(message) }
                Button("Change password") { Task { await save() } }.disabled(saving).frame(minHeight: 44)
            }
        }.navigationTitle("Change password").navigationBarTitleDisplayMode(.inline)
    }
    private func save() async {
        if app.isOffline || app.plan.cachedAt != nil { message = PlanViewModel.offlineMessage; return }
        guard password == confirmation else { message = "Passwords do not match."; return }
        guard password.count >= 8 else { message = "Password must be at least 8 characters."; return }
        saving = true
        defer { saving = false }
        do {
            try await ProfileService(client: app.client).changePassword(password)
            password = ""; confirmation = ""
            message = "Password updated successfully."
        } catch let e as APIError { message = e.userMessage }
        catch { message = error.localizedDescription }
    }
}

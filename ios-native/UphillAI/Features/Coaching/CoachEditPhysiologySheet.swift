import SwiftUI

/// A coach sets an athlete's heart-rate and pace numbers. Only fields the coach
/// actually changed are sent; the athlete is told on their next app open.
struct CoachEditPhysiologySheet: View {
    let athleteId: Int
    let athleteName: String
    let profile: User
    let service: any CoachingServicing
    let onSaved: (User) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var restingHr: String
    @State private var maxHr: String
    @State private var aetHr: String
    @State private var antHr: String
    @State private var z2Slow: String
    @State private var z2Fast: String
    @State private var threshold: String
    @State private var isSaving = false
    @State private var serverError: String?

    init(athleteId: Int, athleteName: String, profile: User, service: any CoachingServicing, onSaved: @escaping (User) -> Void) {
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.profile = profile
        self.service = service
        self.onSaved = onSaved
        _restingHr = State(initialValue: profile.restingHr.map(String.init) ?? "")
        _maxHr = State(initialValue: profile.maxHr.map(String.init) ?? "")
        _aetHr = State(initialValue: profile.aetHr.map(String.init) ?? "")
        _antHr = State(initialValue: profile.antHr.map(String.init) ?? "")
        _z2Slow = State(initialValue: profile.zone2PaceMin ?? "")
        _z2Fast = State(initialValue: profile.zone2PaceMax ?? "")
        _threshold = State(initialValue: profile.thresholdPace ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.section) {
                    // Above the fields: the number pad covers anything below them.
                    if let problem = validationProblem ?? serverError {
                        Label(problem, systemImage: "exclamationmark.triangle.fill")
                            .font(UH.TextStyle.caption.weight(.semibold))
                            .foregroundStyle(UH.Palette.danger)
                            .padding(10)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(UH.Palette.danger.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            .transition(.opacity)
                    }

                    section(L("Heart rate")) {
                        HStack(spacing: UH.Space.small) {
                            hrField("resting_hr", $restingHr)
                            hrField("max_hr", $maxHr)
                        }
                        HStack(spacing: UH.Space.small) {
                            hrField("aet_hr", $aetHr)
                            hrField("ant_hr", $antHr)
                        }
                    }

                    section(L("Pace")) {
                        HStack(spacing: UH.Space.small) {
                            paceField("zone2_pace_min", $z2Slow)
                            paceField("zone2_pace_max", $z2Fast)
                        }
                        paceField("threshold_pace", $threshold)
                    }

                    Label {
                        Text(L("%@ will see what you changed. Workouts already in the plan keep their targets; new ones use these numbers.", athleteName))
                    } icon: {
                        Image(systemName: "bell")
                    }
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                }
                .padding(UH.Space.regular)
            }
            .scrollDismissesKeyboard(.interactively)
            .animation(UH.Motion.standard, value: validationProblem ?? serverError)
            .background(UH.Palette.surface)
            .navigationTitle(L("Edit zones"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L("Cancel")) { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button(L("Save")) { Task { await save() } }
                            .fontWeight(.semibold)
                            .disabled(payload == nil || validationProblem != nil)
                    }
                }
            }
        }
    }

    // MARK: Fields

    private func section(_ title: String, @ViewBuilder content: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.small) {
            Text(title)
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.ink)
            content()
        }
    }

    private func hrField(_ field: String, _ text: Binding<String>) -> some View {
        numberField(field, text, placeholder: "—", keyboard: .numberPad)
    }

    private func paceField(_ field: String, _ text: Binding<String>) -> some View {
        numberField(field, text, placeholder: "5:30", keyboard: .numbersAndPunctuation)
    }

    private func numberField(_ field: String, _ text: Binding<String>, placeholder: String, keyboard: UIKeyboardType) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(ProfileField.label(field))
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.secondary)
            HStack(spacing: 6) {
                TextField(placeholder, text: text)
                    .keyboardType(keyboard)
                    .font(.body.weight(.semibold).monospacedDigit())
                    .foregroundStyle(UH.Palette.ink)
                Text(ProfileField.unit(field))
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.muted)
            }
            .padding(.horizontal, 12)
            .frame(minHeight: 44)
            .background(UH.Palette.card)
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.control)
                    .stroke(changed(field, text.wrappedValue) ? UH.Palette.accent : UH.Palette.line, lineWidth: 1)
            )
            ProvenanceLine(source: profile.fieldSources?[field])
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: Values

    private func trimmed(_ s: String) -> String { s.trimmingCharacters(in: .whitespaces) }

    private func original(_ field: String) -> String {
        switch field {
        case "resting_hr": profile.restingHr.map(String.init) ?? ""
        case "max_hr": profile.maxHr.map(String.init) ?? ""
        case "aet_hr": profile.aetHr.map(String.init) ?? ""
        case "ant_hr": profile.antHr.map(String.init) ?? ""
        case "zone2_pace_min": profile.zone2PaceMin ?? ""
        case "zone2_pace_max": profile.zone2PaceMax ?? ""
        default: profile.thresholdPace ?? ""
        }
    }

    private func changed(_ field: String, _ value: String) -> Bool {
        let v = trimmed(value)
        return !v.isEmpty && v != original(field)
    }

    private func hrIfChanged(_ field: String, _ value: String) -> Int? {
        changed(field, value) ? Int(trimmed(value)) : nil
    }

    private func paceIfChanged(_ field: String, _ value: String) -> String? {
        changed(field, value) ? trimmed(value) : nil
    }

    /// nil when nothing changed.
    private var payload: CoachProfileUpdatePayload? {
        let p = CoachProfileUpdatePayload(
            restingHr: hrIfChanged("resting_hr", restingHr),
            maxHr: hrIfChanged("max_hr", maxHr),
            aetHr: hrIfChanged("aet_hr", aetHr),
            antHr: hrIfChanged("ant_hr", antHr),
            zone2PaceMin: paceIfChanged("zone2_pace_min", z2Slow),
            zone2PaceMax: paceIfChanged("zone2_pace_max", z2Fast),
            thresholdPace: paceIfChanged("threshold_pace", threshold)
        )
        return p == CoachProfileUpdatePayload() ? nil : p
    }

    private static func paceSeconds(_ s: String) -> Int? {
        let parts = s.split(separator: ":")
        guard parts.count == 2, let m = Int(parts[0]), let sec = Int(parts[1]), parts[1].count == 2, sec < 60 else { return nil }
        return m * 60 + sec
    }

    /// Mirrors the server's checks so the coach sees the problem before saving.
    private var validationProblem: String? {
        let hrs: [(String, String)] = [("resting_hr", restingHr), ("aet_hr", aetHr), ("ant_hr", antHr), ("max_hr", maxHr)]
        for (field, value) in hrs where !trimmed(value).isEmpty && Int(trimmed(value)) == nil {
            return L("%@ must be a whole number.", ProfileField.label(field))
        }
        let known = hrs.compactMap { f, v in Int(trimmed(v)).map { (f, $0) } }
        for (a, b) in zip(known, known.dropFirst()) where a.1 >= b.1 {
            return L("%@ must be below %@.", ProfileField.label(a.0), ProfileField.label(b.0))
        }
        let paces = [("zone2_pace_min", z2Slow), ("zone2_pace_max", z2Fast), ("threshold_pace", threshold)]
        for (field, value) in paces where !trimmed(value).isEmpty && Self.paceSeconds(trimmed(value)) == nil {
            return L("%@ must look like 5:30.", ProfileField.label(field))
        }
        let slow = Self.paceSeconds(trimmed(z2Slow)), fast = Self.paceSeconds(trimmed(z2Fast)), thr = Self.paceSeconds(trimmed(threshold))
        if let slow, let fast, slow < fast { return L("Zone 2 slow end must be slower than the fast end.") }
        if let fast, let thr, thr >= fast { return L("Threshold pace must be faster than Zone 2.") }
        return nil
    }

    private func save() async {
        guard let payload else { return }
        isSaving = true
        serverError = nil
        do {
            let updated = try await service.updateAthleteProfile(athleteId: athleteId, payload: payload)
            onSaved(updated)
            dismiss()
        } catch {
            serverError = error.localizedDescription
        }
        isSaving = false
    }
}

import SwiftUI

struct CoachEditWorkoutSheet: View {
    let athleteId: Int
    let planId: Int
    let workout: Workout
    let service: any CoachingServicing
    let onSaved: (Workout) -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var title: String
    @State private var type: String
    @State private var targetZone: String
    @State private var distanceKmText: String
    @State private var durationMinutesText: String
    @State private var descriptionText: String
    @State private var isSubmitting = false
    @State private var errorMessage: String? = nil

    private let zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Rest"]

    init(
        athleteId: Int,
        planId: Int,
        workout: Workout,
        service: any CoachingServicing,
        onSaved: @escaping (Workout) -> Void
    ) {
        self.athleteId = athleteId
        self.planId = planId
        self.workout = workout
        self.service = service
        self.onSaved = onSaved
        _title = State(initialValue: workout.title)
        _type = State(initialValue: workout.type)
        _targetZone = State(initialValue: workout.targetZone ?? "Zone 2")
        _distanceKmText = State(initialValue: workout.distanceKm.map { String(format: "%.1f", $0) } ?? "")
        _durationMinutesText = State(initialValue: "\(Int(workout.durationMinutes))")
        _descriptionText = State(initialValue: workout.description ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text("Edit Workout")
                        .font(UH.TextStyle.sectionTitle)
                        .foregroundStyle(UH.Palette.ink)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Workout Type").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        CoachWorkoutTypePicker(selection: $type)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Title").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        TextField("Title", text: $title)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.hover)
                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Distance (km)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            TextField("e.g. 10.0", text: $distanceKmText)
                                .keyboardType(.decimalPad)
                                .font(UH.TextStyle.body)
                                .padding(10)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Duration (min)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            TextField("e.g. 60", text: $durationMinutesText)
                                .keyboardType(.numberPad)
                                .font(UH.TextStyle.body)
                                .padding(10)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        }
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Target Intensity Zone").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        Picker("Zone", selection: $targetZone) {
                            ForEach(zones, id: \.self) { z in
                                Text(z).tag(z)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Description & Execution Steps").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        TextField("Instructions...", text: $descriptionText, axis: .vertical)
                            .lineLimit(4...8)
                            .font(UH.TextStyle.body)
                            .padding(10)
                            .background(UH.Palette.hover)
                            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(Color.red)
                    }
                }
                .padding(UH.Space.regular)
                .trainingCard()
                .padding(UH.Space.regular)
            }
            .navigationTitle("Edit Session")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task { await saveChanges() }
                    }
                    .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSubmitting)
                }
            }
        }
    }

    private func saveChanges() async {
        isSubmitting = true
        errorMessage = nil
        do {
            let dist = Double(distanceKmText.replacingOccurrences(of: ",", with: "."))
            let dur = Double(durationMinutesText) ?? workout.durationMinutes
            let payload = CoachWorkoutUpdatePayload(
                title: title.trimmingCharacters(in: .whitespacesAndNewlines),
                type: type,
                durationMinutes: dur,
                distanceKm: dist,
                targetZone: targetZone,
                description: descriptionText.isEmpty ? nil : descriptionText
            )
            let updated = try await service.editWorkout(athleteId: athleteId, planId: planId, workoutId: workout.id, payload: payload)
            onSaved(updated)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
        isSubmitting = false
    }
}

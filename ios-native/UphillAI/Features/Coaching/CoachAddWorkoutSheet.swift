import SwiftUI

struct CoachAddWorkoutSheet: View {
    let athleteId: Int
    let planId: Int
    let initialWeek: Int
    let initialDay: String
    let service: any CoachingServicing
    let onAdded: (Workout) -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var weekNumber: Int
    @State private var dayOfWeek: String
    @State private var title = ""
    @State private var type = "Easy"
    @State private var targetZone = "Zone 2"
    @State private var distanceKmText = "8.0"
    @State private var durationMinutesText = "50"
    @State private var descriptionText = ""
    @State private var isSubmitting = false
    @State private var isAiGenerating = false
    @State private var aiPrompt = ""
    @State private var showAiPrompt = false
    @State private var errorMessage: String? = nil

    private let days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    private let zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Rest"]

    init(
        athleteId: Int,
        planId: Int,
        initialWeek: Int = 1,
        initialDay: String = "Wednesday",
        service: any CoachingServicing,
        onAdded: @escaping (Workout) -> Void
    ) {
        self.athleteId = athleteId
        self.planId = planId
        self.initialWeek = initialWeek
        self.initialDay = initialDay
        self.service = service
        self.onAdded = onAdded
        _weekNumber = State(initialValue: initialWeek)
        _dayOfWeek = State(initialValue: initialDay)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: UH.Space.medium) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Label("Coach AI Co-Creation", systemImage: "sparkles")
                                .font(UH.TextStyle.sectionTitle)
                                .foregroundStyle(UH.Palette.accent)
                            Spacer()
                            Button(showAiPrompt ? "Manual form" : "Use AI generator") {
                                withAnimation { showAiPrompt.toggle() }
                            }
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.accent)
                        }

                        if showAiPrompt {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Describe the intended session:")
                                    .font(UH.TextStyle.caption)
                                    .foregroundStyle(UH.Palette.secondary)
                                TextField("Session intent or prompt...", text: $aiPrompt, axis: .vertical)
                                    .lineLimit(3...5)
                                    .font(UH.TextStyle.body)
                                    .padding(10)
                                    .background(UH.Palette.hover)
                                    .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))

                                Button {
                                    Task { await generateWithAi() }
                                } label: {
                                    if isAiGenerating {
                                        ProgressView().frame(maxWidth: .infinity)
                                    } else {
                                        Label("Generate & Insert Session", systemImage: "wand.and.stars")
                                            .font(UH.TextStyle.label)
                                            .frame(maxWidth: .infinity)
                                    }
                                }
                                .buttonStyle(.uhPrimary)
                                .disabled(aiPrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isAiGenerating)
                            }
                            .padding(.top, 4)
                        }
                    }
                    .trainingCard()

                    VStack(alignment: .leading, spacing: 14) {
                        Text("Session Details")
                            .font(UH.TextStyle.sectionTitle)
                            .foregroundStyle(UH.Palette.ink)

                        HStack(spacing: 12) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Week").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                Picker("Week", selection: $weekNumber) {
                                    ForEach(1...24, id: \.self) { w in
                                        Text("Week \(w)").tag(w)
                                    }
                                }
                                .pickerStyle(.menu)
                                .padding(8)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text("Day").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                Picker("Day", selection: $dayOfWeek) {
                                    ForEach(days, id: \.self) { d in
                                        Text(d).tag(d)
                                    }
                                }
                                .pickerStyle(.menu)
                                .padding(8)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Workout Type").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            CoachWorkoutTypePicker(selection: $type)
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Title").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            TextField("e.g. Aerobic Base Run + Strides", text: $title)
                                .font(UH.TextStyle.body)
                                .padding(10)
                                .background(UH.Palette.hover)
                                .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                        }

                        HStack(spacing: 12) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Distance (km)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                TextField("8.0", text: $distanceKmText)
                                    .keyboardType(.decimalPad)
                                    .font(UH.TextStyle.body)
                                    .padding(10)
                                    .background(UH.Palette.hover)
                                    .clipShape(RoundedRectangle(cornerRadius: UH.Radius.control))
                            }

                            VStack(alignment: .leading, spacing: 4) {
                                Text("Duration (min)").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                                TextField("50", text: $durationMinutesText)
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
                            Text("Instructions / Execution Description").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                            TextField("Warm up 10 min easy, then...", text: $descriptionText, axis: .vertical)
                                .lineLimit(3...6)
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
                    .trainingCard()
                }
                .padding(UH.Space.regular)
            }
            .navigationTitle("Add Workout")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        Task { await submitManual() }
                    }
                    .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSubmitting)
                }
            }
        }
    }

    private func submitManual() async {
        isSubmitting = true
        errorMessage = nil
        do {
            let dist = Double(distanceKmText.replacingOccurrences(of: ",", with: "."))
            let dur = Double(durationMinutesText) ?? 50.0
            let payload = CoachWorkoutCreatePayload(
                weekNumber: weekNumber,
                dayOfWeek: dayOfWeek,
                phase: "Specific",
                title: title.trimmingCharacters(in: .whitespacesAndNewlines),
                type: type,
                durationMinutes: dur,
                targetZone: targetZone,
                distanceKm: dist,
                description: descriptionText.isEmpty ? nil : descriptionText
            )
            let created = try await service.addWorkout(athleteId: athleteId, planId: planId, payload: payload)
            onAdded(created)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
        isSubmitting = false
    }

    private func generateWithAi() async {
        isAiGenerating = true
        errorMessage = nil
        do {
            let dur = Double(durationMinutesText) ?? 50.0
            let payload = CoachWorkoutAiCreatePayload(
                weekNumber: weekNumber,
                dayOfWeek: dayOfWeek,
                workoutType: type,
                durationMinutes: dur
            )
            let created = try await service.aiCreateWorkout(athleteId: athleteId, planId: planId, payload: payload)
            onAdded(created)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
        isAiGenerating = false
    }
}

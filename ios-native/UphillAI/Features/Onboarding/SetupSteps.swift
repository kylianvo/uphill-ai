import SwiftUI

struct SetupSteps: View {
    @Bindable var model: PlanSetupViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            switch model.step {
            case .goal: SetupGoalStep(model: model)
            case .details: SetupDetailsStep(model: model)
            case .schedule: SetupScheduleStep(model: model)
            case .aboutYou: SetupAboutStep(model: model)
            case .review: SetupReviewStep(model: model)
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct SetupGoalStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        Text("What are you training for?").font(.system(size: 34, weight: .heavy)).tracking(-0.6)
        ForEach(SetupGoal.allCases, id: \.self) { goal in
            SetupOption(title: goal.title, subtitle: goal.subtitle, symbol: goal.systemImage, selected: model.draft.goal == goal) {
                model.selectGoal(goal)
            }.accessibilityIdentifier("goal.\(goal.rawValue)")
        }
        SetupError(model: model, field: .goal)
    }
}

private struct SetupDetailsStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        switch model.draft.goal {
        case .race, .distance:
            event
        case .returning:
            Text("How long have you been away?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.timeAwayOptions, selection: $model.draft.timeAway)
            SetupError(model: model, field: .timeAway)
            Text("How do you feel right now?").font(UH.TextStyle.sectionTitle)
            options(PlanSetupDraft.fitnessFeelOptions, selection: $model.draft.fitnessFeel)
            SetupError(model: model, field: .fitnessFeel)
        case .recovery:
            Text("Which race did you just finish?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.raceDistanceOptions, selection: $model.draft.raceDistanceCompleted)
            SetupError(model: model, field: .raceCompleted)
            Stepper("Days since the race: \(model.draft.daysSinceRace)", value: $model.draft.daysSinceRace, in: 0...60)
            SetupError(model: model, field: .daysSinceRace)
            Text("How does your body feel?").font(UH.TextStyle.sectionTitle)
            options(PlanSetupDraft.recoveryFeelOptions, selection: $model.draft.recoveryFeel)
            SetupError(model: model, field: .recoveryFeel)
        case .startRunning, nil: EmptyView()
        }
    }

    private var event: some View {
        Group {
            Text(model.draft.goal == .race ? "Tell us about your race" : "Which distance?").font(UH.TextStyle.screenTitle)
            if model.draft.goal == .race {
                SetupFieldBox("Race name") { TextField("Race name", text: $model.draft.raceName).textFieldStyle(.roundedBorder) }.id(SetupField.raceName)
                SetupError(model: model, field: .raceName)
            }
            SetupFieldBox("Race date") {
                DatePicker("Race date", selection: Binding(get: { model.draft.raceDate ?? model.earliestRaceDate }, set: { model.draft.raceDate = $0 }), in: model.earliestRaceDate..., displayedComponents: .date).labelsHidden()
            }.id(SetupField.raceDate)
            SetupError(model: model, field: .raceDate)
            SetupFieldBox("Distance (km)") { TextField("Distance (km)", value: $model.draft.distanceKm, format: .number).keyboardType(.decimalPad).textFieldStyle(.roundedBorder) }.id(SetupField.distance)
            SetupError(model: model, field: .distance)
            SetupFieldBox("Elevation gain (m)") { TextField("Optional", value: $model.draft.elevationGainM, format: .number).keyboardType(.numberPad).textFieldStyle(.roundedBorder) }
            SetupFieldBox("Terrain") {
                Picker("Terrain", selection: $model.draft.terrain) { ForEach(Terrain.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) } }.pickerStyle(.segmented)
            }
            Text("Goal").font(UH.TextStyle.label)
            ForEach(RaceGoal.allCases, id: \.self) { goal in
                SetupOption(title: goal.title, selected: model.draft.raceGoal == goal) { model.selectRaceGoal(goal) }
            }
            if model.draft.raceGoal == .time {
                SetupFieldBox("Target time") {
                    HStack {
                        Picker("Hours", selection: Binding(get: { (model.draft.targetMinutes ?? 390) / 60 }, set: { model.draft.targetMinutes = $0 * 60 + (model.draft.targetMinutes ?? 390) % 60 })) {
                            ForEach(0...120, id: \.self) { Text("\($0) h").tag($0) }
                        }
                        Picker("Minutes", selection: Binding(get: { (model.draft.targetMinutes ?? 390) % 60 }, set: { model.draft.targetMinutes = (model.draft.targetMinutes ?? 390) / 60 * 60 + $0 })) {
                            ForEach(0...59, id: \.self) { Text("\($0) min").tag($0) }
                        }
                    }.pickerStyle(.menu)
                }.id(SetupField.targetTime)
                SetupError(model: model, field: .targetTime)
            }
        }
    }

    private func options(_ values: [String], selection: Binding<String?>) -> some View {
        ForEach(values, id: \.self) { value in
            SetupOption(title: value, selected: selection.wrappedValue == value) { selection.wrappedValue = value }
        }
    }
}

private struct SetupScheduleStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        Text("Your training week").font(UH.TextStyle.screenTitle)
        Stepper("Runs per week: \(model.draft.daysPerWeek)", value: Binding(get: { model.draft.daysPerWeek }, set: model.setDaysPerWeek), in: 3...7)
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 70))], spacing: UH.Space.compact) {
            ForEach(Weekday.allCases) { day in
                Button { model.toggleDay(day) } label: {
                    Text(day.short).font(UH.TextStyle.label).frame(maxWidth: .infinity, minHeight: 44)
                        .background(model.draft.preferredDays.contains(day) ? UH.Palette.accent : UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                }
                .accessibilityLabel("\(day.rawValue), \(model.draft.preferredDays.contains(day) ? "selected" : "not selected")")
                .sensoryFeedback(.selection, trigger: model.draft.preferredDays.contains(day))
            }
        }.id(SetupField.preferredDays)
        SetupError(model: model, field: .preferredDays)
        SetupFieldBox("Long run day") {
            Picker("Long run day", selection: $model.draft.longRunDay) { ForEach(model.draft.orderedDays) { Text($0.rawValue).tag($0) } }.pickerStyle(.menu)
        }.id(SetupField.longRunDay)
        SetupError(model: model, field: .longRunDay)
        SetupFieldBox("Current weekly distance (km)") {
            TextField("Current weekly distance (km)", value: $model.draft.currentWeeklyKm, format: .number).keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
            Stepper("\(Int(model.draft.currentWeeklyKm)) km", value: $model.draft.currentWeeklyKm, in: 0...250, step: 5)
        }.id(SetupField.weeklyKm)
        SetupError(model: model, field: .weeklyKm)
        SetupFieldBox("Where you train") {
            Picker("Where you train", selection: $model.draft.environment) { ForEach(TrainingEnvironment.allCases, id: \.self) { Text($0.rawValue.capitalized).tag($0) } }.pickerStyle(.segmented)
        }
        Toggle("I have gym access", isOn: $model.draft.hasGymAccess)
        SetupFieldBox("Start date") { DatePicker("Start date", selection: $model.draft.startDate, in: model.today..., displayedComponents: .date).labelsHidden() }.id(SetupField.startDate)
        SetupError(model: model, field: .startDate)
    }
}

private struct SetupAboutStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        Text("A bit about you").font(UH.TextStyle.screenTitle)
        Text("Optional. Helps set your heart rate zones; we estimate anything you skip.").foregroundStyle(UH.Palette.secondary)
        SetupFieldBox("Birth date") {
            Toggle("Add birth date", isOn: Binding(get: { model.draft.birthDate != nil }, set: { model.draft.birthDate = $0 ? Calendar.current.date(byAdding: .year, value: -30, to: model.today) : nil }))
            if model.draft.birthDate != nil {
                DatePicker("Birth date", selection: Binding(get: { model.draft.birthDate ?? model.today }, set: { model.draft.birthDate = $0 }), in: ...model.today, displayedComponents: .date).labelsHidden()
            }
        }
        SetupFieldBox("Gender") {
            Picker("Gender", selection: $model.draft.gender) {
                Text("Prefer not to say").tag(String?.none)
                Text("Female").tag(String?("female")); Text("Male").tag(String?("male")); Text("Other").tag(String?("other"))
            }.pickerStyle(.menu)
        }
        SetupFieldBox("Height (cm)") { TextField("Optional", value: $model.draft.heightCm, format: .number).keyboardType(.decimalPad).textFieldStyle(.roundedBorder) }.id(SetupField.height)
        SetupError(model: model, field: .height)
        SetupFieldBox("Weight (kg)") { TextField("Optional", value: $model.draft.weightKg, format: .number).keyboardType(.decimalPad).textFieldStyle(.roundedBorder) }.id(SetupField.weight)
        SetupError(model: model, field: .weight)
        SetupFieldBox("Max heart rate") { TextField("Optional", value: $model.draft.maxHr, format: .number).keyboardType(.numberPad).textFieldStyle(.roundedBorder) }.id(SetupField.maxHr)
        SetupError(model: model, field: .maxHr)
        SetupFieldBox("Resting heart rate") { TextField("Optional", value: $model.draft.restingHr, format: .number).keyboardType(.numberPad).textFieldStyle(.roundedBorder) }.id(SetupField.restingHr)
        SetupError(model: model, field: .restingHr)
        SetupFieldBox("Injuries or niggles") { TextField("Optional", text: $model.draft.injuryHistory, axis: .vertical).textFieldStyle(.roundedBorder) }
        SetupFieldBox("Anything else your coach should know") { TextField("Optional", text: $model.draft.notes, axis: .vertical).textFieldStyle(.roundedBorder) }
    }
}

private struct SetupReviewStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        Text("Ready to build your plan").font(UH.TextStyle.screenTitle)
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            ForEach(Array(model.draft.summaryLines.enumerated()), id: \.offset) { index, line in
                Button { model.jump(to: model.draft.goal?.isEvent == true && index < 2 ? .details : .schedule) } label: {
                    HStack { Text(line).multilineTextAlignment(.leading); Spacer(); Image(systemName: "chevron.right") }.frame(minHeight: 44)
                }
            }
        }.padding(UH.Space.regular).uhCard()
        Text("Coach Uphill builds your first weeks now and adds each new week as you train.").foregroundStyle(UH.Palette.secondary)
    }
}

private struct SetupFieldBox<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content
    init(_ title: String, @ViewBuilder content: @escaping () -> Content) { self.title = title; self.content = content }
    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.label)
            content()
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct SetupError: View {
    let model: PlanSetupViewModel
    let field: SetupField
    var body: some View {
        if let error = model.issue(for: field) { Text(error).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.danger) }
    }
}

private struct SetupOption: View {
    let title: String
    var subtitle: String? = nil
    var symbol: String? = nil
    let selected: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: UH.Space.small) {
                if let symbol {
                    Image(systemName: symbol).font(.title2.weight(.semibold)).frame(width: 36)
                        .foregroundStyle(selected ? UH.Palette.buttonInk : UH.Palette.accentInk)
                }
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text(title).font(.title3.weight(.bold))
                    if let subtitle {
                        Text(subtitle).font(UH.TextStyle.caption)
                            .foregroundStyle(selected ? UH.Palette.buttonInk : UH.Palette.secondary)
                    }
                }
                Spacer(minLength: 0)
                if selected { Image(systemName: "checkmark.circle.fill").font(.title2).foregroundStyle(UH.Palette.buttonInk) }
            }
            .foregroundStyle(selected ? UH.Palette.buttonInk : UH.Palette.ink)
            .multilineTextAlignment(.leading).padding(UH.Space.regular).frame(maxWidth: .infinity, minHeight: 72)
            .background(selected ? UH.Palette.accent : UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.panel))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.panel).stroke(selected ? Color.clear : UH.Palette.line, lineWidth: 1))
        }.buttonStyle(.plain).sensoryFeedback(.selection, trigger: selected)
    }
}

import SwiftUI

struct SetupSteps: View {
    @Bindable var model: PlanSetupViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            Label(coachLine, systemImage: "mountain.2.fill")
                .font(.callout).foregroundStyle(UH.Palette.secondary)
            switch model.step {
            case .goal:
                Text("What are you training for?").font(UH.TextStyle.screenTitle)
                goal("A trail race", .race, terrain: .trail, symbol: "mountain.2")
                goal("A road race", .race, terrain: .road, symbol: "flag.checkered")
                goal("Getting started", .startRunning, symbol: "figure.walk")
                goal("Coming back after a break", .returning, symbol: "arrow.uturn.forward")
                goal("Recovering from a race", .recovery, symbol: "bed.double")
            case .details:
                details
            case .raceDate:
                Text("When is it?").font(UH.TextStyle.screenTitle)
                DatePicker("Race date", selection: Binding(get: { model.draft.raceDate ?? model.earliestRaceDate }, set: { model.draft.raceDate = $0 }), in: model.earliestRaceDate..., displayedComponents: .date)
                Text("That's \(model.weeksToRace) weeks away").foregroundStyle(UH.Palette.secondary)
                SetupError(model: model, field: .raceDate)
            case .fitnessFeel:
                Text("How do you feel right now?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.fitnessFeelOptions, selection: $model.draft.fitnessFeel)
            case .daysSinceRace:
                Text("When did you finish?").font(UH.TextStyle.screenTitle)
                Picker("Days since the race", selection: $model.draft.daysSinceRace) {
                    ForEach(0...60, id: \.self) { Text("\($0) days ago").tag($0) }
                }
            case .recoveryFeel:
                Text("How does your body feel?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.recoveryFeelOptions, selection: $model.draft.recoveryFeel)
            case .schedule:
                Text("How much do you run now?").font(UH.TextStyle.screenTitle)
                Stepper("Runs per week: \(model.draft.daysPerWeek)", value: Binding(get: { model.draft.daysPerWeek }, set: model.setDaysPerWeek), in: 3...7)
                Stepper("\(Int(model.draft.currentWeeklyKm)) km a week", value: $model.draft.currentWeeklyKm, in: 0...250, step: 5)
                SetupError(model: model, field: .weeklyKm)
            case .startDate:
                Text("When do you want to start?").font(UH.TextStyle.screenTitle)
                DatePicker("Start date", selection: $model.draft.startDate, in: model.today...model.latestStartDate, displayedComponents: .date)
                SetupError(model: model, field: .startDate)
            case .aboutYou: EmptyView()
            case .review: SetupReviewStep(model: model)
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
        .task(id: model.draft.raceName) { await model.searchRace() }
    }

    private var coachLine: String {
        switch model.step {
        case .goal: "This sets the shape of your whole plan."
        case .details where model.draft.goal?.isEvent == true: "If I know the race, I know its distance and climbing."
        case .details, .fitnessFeel, .daysSinceRace, .recoveryFeel: "So I don't start you too hard."
        case .raceDate: "I'll count the weeks back from race day."
        case .schedule: "Your first week starts close to what you already do."
        case .startDate: "Pick today or any day in the next two weeks."
        case .review, .aboutYou: "You can add heart rate, paces and injuries after this. They make each new week more accurate."
        }
    }

    private func goal(_ title: String, _ goal: SetupGoal, terrain: Terrain = .trail, symbol: String) -> some View {
        SetupOption(title: title, symbol: symbol, selected: model.draft.goal == goal && model.draft.terrain == terrain) {
            model.draft.terrain = terrain
            model.selectGoal(goal)
        }.accessibilityIdentifier(goal == .race ? "goal.race.\(terrain.rawValue)" : "goal.\(goal.rawValue)")
    }

    @ViewBuilder private var details: some View {
        if model.draft.goal?.isEvent == true {
            Text("Which race?").font(UH.TextStyle.screenTitle)
            SetupFieldBox("Race name") {
                TextField("Race name", text: $model.draft.raceName).textFieldStyle(.roundedBorder)
            }.id(SetupField.raceName)
            SetupError(model: model, field: .raceName)
            ForEach(Array(model.raceCandidates.enumerated()), id: \.offset) { _, race in
                SetupOption(title: race.raceName, subtitle: race.distanceLabel ?? "", selected: false) { model.selectRace(race) }
            }
            if let race = model.selectedRace {
                Label("\(race.raceName) · \(race.distanceLabel ?? "")", systemImage: "checkmark.circle")
            } else {
                SetupFieldBox("Distance (km)") {
                    TextField("Distance (km)", value: $model.draft.distanceKm, format: .number).keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
                }.id(SetupField.distance)
                SetupError(model: model, field: .distance)
                SetupFieldBox("Elevation gain (m)") {
                    TextField("Optional", value: $model.draft.elevationGainM, format: .number).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                }
            }
        } else if model.draft.goal == .returning {
            Text("How long have you been away?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.timeAwayOptions, selection: $model.draft.timeAway)
        } else {
            Text("Which race did you just finish?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.raceDistanceOptions, selection: $model.draft.raceDistanceCompleted)
        }
    }

    private func options(_ values: [String], selection: Binding<String?>) -> some View {
        ForEach(values, id: \.self) { value in
            SetupOption(title: value, selected: selection.wrappedValue == value) { selection.wrappedValue = value }
        }
    }
}

private struct SetupReviewStep: View {
    @Bindable var model: PlanSetupViewModel
    var body: some View {
        Text("Here's what I'll build from").font(UH.TextStyle.screenTitle)
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

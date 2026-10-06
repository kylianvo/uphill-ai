import SwiftUI

struct SetupSteps: View {
    @Bindable var model: PlanSetupViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            // Coach Uphill Banner
            HStack(alignment: .top, spacing: UH.Space.small) {
                Image(systemName: "figure.run.circle.fill")
                    .font(.title3)
                    .foregroundStyle(UH.Palette.accentInk)
                Text(coachLine)
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.horizontal, UH.Space.regular)
            .padding(.vertical, UH.Space.small)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(UH.Palette.card)
            .clipShape(RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.line, lineWidth: 1))

            switch model.step {
            case .goal:
                Text("What are you training for?").font(UH.TextStyle.screenTitle)
                VStack(spacing: UH.Space.small) {
                    goal("A trail race", .race, terrain: .trail, symbol: "mountain.2")
                    goal("A road race", .race, terrain: .road, symbol: "flag.checkered")
                    goal("Getting started", .startRunning, symbol: "figure.walk")
                    goal("Coming back after a break", .returning, symbol: "arrow.uturn.forward")
                    goal("Recovering from a race", .recovery, symbol: "bed.double")
                }
            case .details:
                details
            case .raceDate:
                Text("When is it?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("EVENT DATE").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        Text("Coach Uphill will count back your training phases from race day.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    DatePicker(
                        "Race date",
                        selection: Binding(get: { model.draft.raceDate ?? model.earliestRaceDate }, set: { model.draft.raceDate = $0 }),
                        in: model.earliestRaceDate...,
                        displayedComponents: .date
                    )
                    .datePickerStyle(.graphical)
                    .tint(UH.Palette.accentInk)
                    .id(SetupField.raceDate)

                    HStack(spacing: 8) {
                        Image(systemName: "calendar.badge.clock")
                            .font(.headline)
                            .foregroundStyle(UH.Palette.accentInk)
                        Text("That's \(model.weeksToRace) weeks away")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.ink)
                    }
                    .padding(UH.Space.small)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.control))

                    SetupError(model: model, field: .raceDate)
                }
                .trainingCard()

            case .fitnessFeel:
                Text("How do you feel right now?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.fitnessFeelOptions, selection: $model.draft.fitnessFeel)
            case .daysSinceRace:
                Text("When did you finish?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("TIME SINCE RACE").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        Text("Used to calculate your remaining acute fatigue and recovery phase.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    HStack(alignment: .firstTextBaseline) {
                        Text("\(model.draft.daysSinceRace)")
                            .font(.system(size: 40, weight: .bold, design: .rounded))
                            .foregroundStyle(UH.Palette.ink)
                        Text(model.draft.daysSinceRace == 1 ? "day ago" : "days ago")
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.secondary)
                        Spacer()
                        Stepper("Days since the race", value: $model.draft.daysSinceRace, in: 0...60)
                            .labelsHidden()
                    }

                    Picker("Days since the race", selection: $model.draft.daysSinceRace) {
                        ForEach(0...60, id: \.self) { Text("\($0) days ago").tag($0) }
                    }
                    .pickerStyle(.wheel)
                    .frame(height: 110)
                }
                .trainingCard()

            case .recoveryFeel:
                Text("How does your body feel?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.recoveryFeelOptions, selection: $model.draft.recoveryFeel)
            case .schedule:
                Text("How much do you run now?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("RUNS PER WEEK").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        HStack(alignment: .firstTextBaseline) {
                            Text("\(model.draft.daysPerWeek)")
                                .font(.system(size: 36, weight: .bold, design: .rounded))
                                .foregroundStyle(UH.Palette.ink)
                            Text("runs / week")
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.secondary)
                            Spacer()
                            Stepper("Runs per week: \(model.draft.daysPerWeek)", value: Binding(get: { model.draft.daysPerWeek }, set: model.setDaysPerWeek), in: 3...7)
                                .labelsHidden()
                        }
                    }

                    // Visual day dots
                    HStack(spacing: 8) {
                        ForEach(0..<7, id: \.self) { index in
                            Circle()
                                .fill(index < model.draft.daysPerWeek ? UH.Palette.accent : UH.Palette.line)
                                .frame(height: 10)
                        }
                    }
                }
                .trainingCard()

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("WEEKLY VOLUME").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        HStack(alignment: .center, spacing: 8) {
                            HStack(spacing: 4) {
                                TextField("40", value: $model.draft.currentWeeklyKm, format: .number)
                                    .keyboardType(.numberPad)
                                    .font(.system(size: 32, weight: .bold, design: .rounded))
                                    .foregroundStyle(UH.Palette.ink)
                                    .frame(width: 72)
                                Text("km / week")
                                    .font(UH.TextStyle.label)
                                    .foregroundStyle(UH.Palette.secondary)
                            }
                            Spacer()
                            HStack(spacing: 8) {
                                Button {
                                    if model.draft.currentWeeklyKm >= 5 {
                                        model.draft.currentWeeklyKm -= 5
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "minus.circle")
                                        .font(.system(size: 24))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                                Button {
                                    if model.draft.currentWeeklyKm <= 245 {
                                        model.draft.currentWeeklyKm += 5
                                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                                    }
                                } label: {
                                    Image(systemName: "plus.circle")
                                        .font(.system(size: 24))
                                        .foregroundStyle(UH.Palette.ink)
                                }
                            }
                        }
                    }
                    SetupError(model: model, field: .weeklyKm)
                }
                .trainingCard()

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("WHERE YOU TRAIN").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        Text("Hill sessions, climbing long runs and strength work are placed where you can actually do them.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Terrain near me").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        Picker("Terrain", selection: $model.draft.environment) {
                            Text("Mostly flat").tag(TrainingEnvironment.flat)
                            Text("Hilly").tag(TrainingEnvironment.hilly)
                            Text("A mix").tag(TrainingEnvironment.mixed)
                        }
                        .pickerStyle(.segmented)
                    }
                    TrainingVenueSection(
                        mountainDays: $model.draft.mountainDays,
                        stairAccess: $model.draft.stairAccess,
                        treadmillMaxIncline: nil
                    )
                }
                .trainingCard()

            case .startDate:
                Text("When do you want to start?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("START DATE").font(UH.TextStyle.eyebrow).foregroundStyle(UH.Palette.secondary)
                        Text("Pick today or any day in the next two weeks.")
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }

                    DatePicker(
                        "Start date",
                        selection: $model.draft.startDate,
                        in: model.today...model.latestStartDate,
                        displayedComponents: .date
                    )
                    .datePickerStyle(.graphical)
                    .tint(UH.Palette.accentInk)
                    .id(SetupField.startDate)

                    SetupError(model: model, field: .startDate)
                }
                .trainingCard()

            case .aboutYou:
                EmptyView()
            case .review:
                SetupReviewStep(model: model)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
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

            VStack(alignment: .leading, spacing: UH.Space.regular) {
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text("Race name").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    HStack(spacing: 8) {
                        Image(systemName: "magnifyingglass")
                            .foregroundStyle(UH.Palette.muted)
                        TextField("Search race name or enter manually", text: $model.draft.raceName)
                    }
                    .padding(UH.Space.small)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                }
                .id(SetupField.raceName)

                SetupError(model: model, field: .raceName)
            }
            .trainingCard()

            ForEach(Array(model.raceCandidates.enumerated()), id: \.offset) { _, race in
                SetupOption(title: race.raceName, subtitle: race.distanceLabel ?? "", symbol: "flag.checkered", selected: false) {
                    model.selectRace(race)
                }
            }

            if let race = model.selectedRace {
                HStack(spacing: 12) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(UH.Palette.accentInk)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(race.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        if let dist = race.distanceLabel {
                            Text(dist).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                        }
                    }
                    Spacer()
                    Button("Change") {
                        model.selectedRace = nil
                    }
                    .font(UH.TextStyle.caption.weight(.semibold))
                    .foregroundStyle(UH.Palette.accentInk)
                }
                .padding(UH.Space.regular)
                .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.accent, lineWidth: 1))
            } else {
                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    Text("Manual Course Profile").font(UH.TextStyle.sectionTitle).foregroundStyle(UH.Palette.ink)

                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Distance (km)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        TextField("Distance (km)", value: $model.draft.distanceKm, format: .number)
                            .keyboardType(.decimalPad)
                            .padding(UH.Space.small)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                    }
                    .id(SetupField.distance)

                    SetupError(model: model, field: .distance)

                    VStack(alignment: .leading, spacing: UH.Space.compact) {
                        Text("Elevation gain (m)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                        TextField("Optional (meters)", value: $model.draft.elevationGainM, format: .number)
                            .keyboardType(.numberPad)
                            .padding(UH.Space.small)
                            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
                    }
                }
                .trainingCard()
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
        VStack(spacing: UH.Space.small) {
            ForEach(values, id: \.self) { value in
                SetupOption(
                    title: value,
                    symbol: optionSymbol(for: value),
                    selected: selection.wrappedValue == value
                ) {
                    selection.wrappedValue = value
                }
            }
        }
    }

    private func optionSymbol(for value: String) -> String {
        switch value {
        case "< 2 weeks": return "clock.arrow.circlepath"
        case "2–6 weeks": return "calendar.badge.clock"
        case "1–3 months": return "calendar"
        case "3–6 months": return "moon.stars.fill"
        case "6+ months": return "hourglass"
        case "Feeling good, just need structure": return "flame.fill"
        case "A bit rusty, slightly deconditioned": return "figure.walk"
        case "Significant deconditioning — starting nearly fresh": return "heart.text.square.fill"
        case "5k": return "figure.run"
        case "10k": return "figure.run.circle"
        case "Half Marathon": return "medal"
        case "Marathon": return "medal.fill"
        case "Ultra (< 60k)": return "mountain.2"
        case "Ultra (60k+)": return "mountain.2.fill"
        case "Feeling great, minimal soreness": return "sparkles"
        case "Moderate fatigue, some soreness": return "battery.50percent"
        case "Very fatigued — need real rest": return "bed.double.fill"
        default: return "circle.fill"
        }
    }
}

private struct SetupReviewStep: View {
    @Bindable var model: PlanSetupViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: UH.Space.section) {
            Text("Here's what I'll build from").font(UH.TextStyle.screenTitle)

            VStack(alignment: .leading, spacing: UH.Space.regular) {
                HStack(spacing: 8) {
                    Image(systemName: "list.bullet.clipboard.fill")
                        .foregroundStyle(UH.Palette.accentInk)
                    Text("PLAN BLUEPRINT")
                        .font(UH.TextStyle.eyebrow)
                        .foregroundStyle(UH.Palette.secondary)
                }

                ForEach(Array(model.draft.summaryLines.enumerated()), id: \.offset) { index, line in
                    if index > 0 { Divider() }
                    Button {
                        model.jump(to: model.draft.goal?.isEvent == true && index < 2 ? .details : .schedule)
                    } label: {
                        HStack(spacing: UH.Space.small) {
                            Image(systemName: reviewIcon(index: index, line: line))
                                .font(.subheadline)
                                .foregroundStyle(UH.Palette.accentInk)
                                .frame(width: 24)
                            Text(line)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                                .multilineTextAlignment(.leading)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(UH.Palette.muted)
                        }
                        .frame(minHeight: 44)
                    }
                    .buttonStyle(.plain)
                }
            }
            .trainingCard()

            HStack(alignment: .top, spacing: UH.Space.small) {
                Image(systemName: "sparkles")
                    .foregroundStyle(UH.Palette.accentInk)
                Text("Coach Uphill builds your first weeks now and adds each new week as you train.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.horizontal, 4)
        }
    }

    private func reviewIcon(index: Int, line: String) -> String {
        if line.contains("race") || line.contains("Race") { return "flag.checkered" }
        if line.contains("km") || line.contains("volume") { return "chart.bar.fill" }
        if line.contains("run") || line.contains("days") { return "figure.run" }
        if line.contains("Start") || line.contains("date") { return "calendar" }
        return "checkmark.seal.fill"
    }
}

private struct SetupError: View {
    let model: PlanSetupViewModel
    let field: SetupField

    var body: some View {
        if let error = model.issue(for: field) {
            Text(error)
                .font(UH.TextStyle.caption)
                .foregroundStyle(UH.Palette.danger)
        }
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
            HStack(spacing: UH.Space.regular) {
                if let symbol {
                    ZStack {
                        RoundedRectangle(cornerRadius: UH.Radius.control)
                            .fill(selected ? UH.Palette.accentInk : UH.Palette.accent.opacity(0.12))
                            .frame(width: 44, height: 44)
                        Image(systemName: symbol)
                            .font(.title3.weight(.semibold))
                            .foregroundStyle(selected ? Color.white : UH.Palette.accentInk)
                    }
                }
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    if let subtitle, !subtitle.isEmpty {
                        Text(subtitle)
                            .font(UH.TextStyle.caption)
                            .foregroundStyle(UH.Palette.secondary)
                    }
                }
                Spacer(minLength: 0)
                if selected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title2)
                        .foregroundStyle(UH.Palette.accentInk)
                }
            }
            .padding(UH.Space.regular)
            .frame(maxWidth: .infinity, minHeight: 64)
            .background(selected ? UH.Palette.activeFill : UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
            .overlay(
                RoundedRectangle(cornerRadius: UH.Radius.landing)
                    .stroke(selected ? UH.Palette.accent : UH.Palette.line, lineWidth: selected ? 1.5 : 1)
            )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .sensoryFeedback(.selection, trigger: selected)
    }
}

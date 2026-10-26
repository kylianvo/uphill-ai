import SwiftUI

struct SetupSteps: View {
    @Bindable var model: PlanSetupViewModel
    @State private var showGoalDeterminer = false
    @State private var showLinkProfile = false
    @State private var showZonesGuide = false
    @State private var includeBirthDate = false

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
                    goal("A distance", .distance, symbol: "point.topleft.down.to.point.bottomright.curvepath",
                         subtitle: "No race yet, like your first 21 km or 50 km.")
                    goal("Getting started", .startRunning, symbol: "figure.walk")
                }
            case .details:
                details
            case .raceDate:
                Text("When is it?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
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

            case .raceGoal:
                raceGoal
            case .fitnessFeel:
                Text("How do you feel right now?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.fitnessFeelOptions, selection: $model.draft.fitnessFeel)
            case .daysSinceRace:
                Text("When did you finish?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
                    HStack(alignment: .firstTextBaseline) {
                        Text("\(model.draft.daysSinceRace)")
                            .font(.system(size: 40, weight: .bold, design: .rounded))
                            .foregroundStyle(UH.Palette.ink)
                        Text(model.draft.daysSinceRace == 1 ? L("day ago") : L("days ago"))
                            .font(UH.TextStyle.label)
                            .foregroundStyle(UH.Palette.secondary)
                        Spacer()
                        Stepper("Days since the race", value: $model.draft.daysSinceRace, in: 0...60)
                            .labelsHidden()
                    }
                    Text("Used to work out how much fatigue is left.")
                        .font(UH.TextStyle.caption)
                        .foregroundStyle(UH.Palette.secondary)
                }
                .trainingCard()

            case .recoveryFeel:
                Text("How does your body feel?").font(UH.TextStyle.screenTitle)
                options(PlanSetupDraft.recoveryFeelOptions, selection: $model.draft.recoveryFeel)
            case .schedule:
                week
            case .venues:
                venues
            case .body:
                bodyStep
            case .trainingZones:
                trainingZones
            case .watch:
                Text("Connect your watch").font(UH.TextStyle.screenTitle)
                WatchChannelsList(connected: model.corosConnected, available: model.deviceService != nil,
                                  healthConnected: model.appleHealthConnected, healthAvailable: model.canConnectAppleHealth,
                                  connect: { await model.connectCoros() },
                                  connectHealth: { await model.connectAppleHealth() },
                                  garminConnected: model.garminConnected, garminAvailable: model.garminAvailable,
                                  connectGarmin: { await model.connectGarmin() })
            case .raceHistory:
                raceHistory
            case .startDate:
                Text("When do you want to start?").font(UH.TextStyle.screenTitle)

                VStack(alignment: .leading, spacing: UH.Space.regular) {
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

            case .review:
                SetupReviewStep(model: model)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .task(id: model.draft.raceName) { await model.searchRace() }
        .sheet(isPresented: $showGoalDeterminer) {
            if let service = model.goalEstimateService {
                NavigationStack {
                    GoalDeterminerSheet(
                        service: service,
                        isPresentedInSheet: true,
                        raceHistoryService: model.raceHistoryService,
                        onApplyGoal: { minutes in
                            model.applyEstimatedGoal(minutes: minutes)
                            showGoalDeterminer = false
                        },
                        prefill: GoalPrefill(raceName: model.draft.raceName, distanceKm: model.draft.distanceKm,
                                             elevationGainM: model.draft.elevationGainM, raceDate: model.draft.raceDate)
                    )
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) { Button("Close") { showGoalDeterminer = false } }
                    }
                }
            }
        }
        .sheet(isPresented: $showZonesGuide) { WatchZonesGuideSheet() }
        .sheet(isPresented: $showLinkProfile) {
            if let service = model.raceHistoryService {
                LinkProfileSheet(service: service) { model.linkedRaceHistory = true }
            }
        }
    }

    private var coachLine: String {
        switch model.step {
        case .goal: L("This sets the shape of your whole plan.")
        case .details where model.draft.goal == .race: L("If I know the race, I know its distance and climbing.")
        case .details where model.draft.goal == .distance: L("Distance and climbing set how long your key runs get.")
        case .details, .fitnessFeel, .daysSinceRace, .recoveryFeel: L("So I don't start you too hard.")
        case .raceDate: L("I'll count the weeks back from race day.")
        case .raceGoal: L("A clear goal sets how hard your key sessions are.")
        case .schedule: L("Your first week starts close to what you already do.")
        case .venues: L("Hill sessions and strength work go where you can actually do them.")
        case .trainingZones: L("Your thresholds and easy pace help set workout intensity.")
        case .body: L("Injury history sets how fast I add volume.")
        case .raceHistory: L("Past results tell me what you can already do.")
        case .watch: L("Your runs show me what you really do, not just what you remember.")
        case .startDate: L("Pick today or any day in the next two weeks.")
        case .review: L("You can change any of this later from your plan.")
        }
    }

    private func goal(_ title: String, _ goal: SetupGoal, terrain: Terrain = .trail, symbol: String, subtitle: String? = nil) -> some View {
        SetupOption(title: title, subtitle: subtitle, symbol: symbol, selected: model.draft.goal == goal && (goal != .race || model.draft.terrain == terrain)) {
            model.draft.terrain = terrain
            model.selectGoal(goal)
        }.accessibilityIdentifier(goal == .race ? "goal.race.\(terrain.rawValue)" : "goal.\(goal.rawValue)")
    }

    // MARK: Race or distance

    @ViewBuilder private var details: some View {
        if model.draft.goal == .race {
            Text("Which race?").font(UH.TextStyle.screenTitle)

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Race name").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(UH.Palette.muted)
                    TextField("Search race name or enter manually", text: $model.draft.raceName)
                        .textInputAutocapitalization(.words)
                        .autocorrectionDisabled()
                }
                .padding(UH.Space.small)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
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
                selectedRace(race)
            }
        } else if model.draft.goal == .distance {
            Text("What distance?").font(UH.TextStyle.screenTitle)
        } else if model.draft.goal == .returning {
            Text("How long have you been away?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.timeAwayOptions, selection: $model.draft.timeAway)
        } else {
            Text("Which race did you just finish?").font(UH.TextStyle.screenTitle)
            options(PlanSetupDraft.raceDistanceOptions, selection: $model.draft.raceDistanceCompleted)
        }

        if model.draft.goal?.isEvent == true {
            course
        }
    }

    private func selectedRace(_ race: RaceMatch) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            HStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.title2)
                    .foregroundStyle(UH.Palette.accentInk)
                Text(race.raceName).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Spacer()
                Button("Change") {
                    model.selectedRace = nil
                    model.draft.distanceLabel = nil
                }
                .font(UH.TextStyle.caption.weight(.semibold))
                .foregroundStyle(UH.Palette.accentInk)
                .frame(minHeight: 44)
            }

            if model.raceDistances.count > 1 {
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text("Which distance are you running?").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    ForEach(model.raceDistances, id: \.self) { distance in
                        distanceRow(distance)
                    }
                }
            }
        }
        .padding(UH.Space.regular)
        .background(UH.Palette.activeFill, in: RoundedRectangle(cornerRadius: UH.Radius.landing))
        .overlay(RoundedRectangle(cornerRadius: UH.Radius.landing).stroke(UH.Palette.accent, lineWidth: 1))
    }

    private func distanceRow(_ distance: RaceDistance) -> some View {
        let picked = model.isPicked(distance)
        let km = distance.distanceKm.formatted(.number.precision(.fractionLength(0...1)).locale(AppLanguage.current.locale))
        let detail = distance.elevationGainM.map { L("%@ km · %@ m D+", km, Int($0).formatted(.number.locale(AppLanguage.current.locale))) } ?? L("%@ km", km)
        return Button { model.pickDistance(distance) } label: {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(distance.label ?? L("%@ km", km)).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                    Text(detail).font(UH.TextStyle.caption.monospacedDigit()).foregroundStyle(UH.Palette.secondary)
                }
                Spacer()
                Image(systemName: picked ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundStyle(picked ? UH.Palette.accentInk : UH.Palette.muted)
            }
            .padding(.horizontal, UH.Space.small)
            .frame(minHeight: 52)
            .background(UH.Palette.card, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(picked ? UH.Palette.accent : UH.Palette.line, lineWidth: picked ? 1.5 : 1))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(picked ? .isSelected : [])
        .sensoryFeedback(.selection, trigger: picked)
    }

    /// Distance, climbing and surface. Prefilled from the race when it's known, always editable.
    private var course: some View {
        VStack(alignment: .leading, spacing: UH.Space.regular) {
            if model.draft.goal == .distance {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 64))], spacing: 8) {
                    ForEach(PlanSetupDraft.distancePresets, id: \.self) { km in
                        let picked = model.draft.distanceKm == km
                        Button { model.draft.distanceKm = km } label: {
                            Text(L("%@ km", km.formatted()))
                                .font(UH.TextStyle.label.monospacedDigit())
                                .frame(maxWidth: .infinity, minHeight: 44)
                                .foregroundStyle(picked ? UH.Palette.buttonInk : UH.Palette.ink)
                                .background(picked ? UH.Palette.activeFill : UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(picked ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                        }
                        .buttonStyle(.plain)
                        .accessibilityAddTraits(picked ? .isSelected : [])
                    }
                }
            }

            HStack(alignment: .top, spacing: UH.Space.small) {
                numberField("Distance (km)", placeholder: "42", value: $model.draft.distanceKm)
                    .id(SetupField.distance)
                numberField("Climbing (m D+)", placeholder: L("Optional"), value: $model.draft.elevationGainM)
            }
            SetupError(model: model, field: .distance)

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Surface").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Picker("Surface", selection: $model.draft.terrain) {
                    Text("Trail").tag(Terrain.trail)
                    Text("Road").tag(Terrain.road)
                    Text("Mixed").tag(Terrain.mixed)
                }
                .pickerStyle(.segmented)
            }
        }
        .trainingCard()
    }

    private func numberField(_ title: LocalizedStringKey, placeholder: String, value: Binding<Double?>) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            TextField(placeholder, value: value, format: .number)
                .keyboardType(.decimalPad)
                .font(.body.monospacedDigit())
                .padding(UH.Space.small)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: Race goal

    @ViewBuilder private var raceGoal: some View {
        Text("What's your goal on race day?").font(UH.TextStyle.screenTitle)

        VStack(spacing: UH.Space.small) {
            SetupOption(title: RaceGoal.finish.title, subtitle: "Arrive healthy and finish feeling in control.",
                        symbol: "flag.checkered", selected: model.draft.raceGoal == .finish) { model.selectRaceGoal(.finish) }
            SetupOption(title: RaceGoal.time.title, subtitle: "Train toward a finish time you choose.",
                        symbol: "stopwatch", selected: model.draft.raceGoal == .time) { model.selectRaceGoal(.time) }
            SetupOption(title: RaceGoal.optimal.title, subtitle: "Coach Uphill sets the target from your fitness as you train.",
                        symbol: "chart.line.uptrend.xyaxis", selected: model.draft.raceGoal == .optimal) { model.selectRaceGoal(.optimal) }
        }

        if model.draft.raceGoal == .time {
            VStack(alignment: .leading, spacing: UH.Space.small) {
                Text("Target finish time").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                HStack(spacing: 0) {
                    Picker("Hours", selection: targetHours) {
                        ForEach(0...60, id: \.self) { Text(L("%lld h", $0)).tag($0) }
                    }
                    Picker("Minutes", selection: targetMins) {
                        ForEach(0...59, id: \.self) { Text(L("%lld min", $0)).tag($0) }
                    }
                }
                .pickerStyle(.wheel)
                .frame(height: 130)
                .id(SetupField.targetTime)
                SetupError(model: model, field: .targetTime)
            }
            .trainingCard()
        }

        if model.goalEstimateService != nil {
            Button {
                showGoalDeterminer = true
            } label: {
                HStack(spacing: UH.Space.small) {
                    Image(systemName: "target")
                    Text("Not sure? Estimate it from your results")
                    Spacer()
                    Image(systemName: "chevron.right").font(.footnote.weight(.semibold))
                }
                .font(UH.TextStyle.label)
                .foregroundStyle(UH.Palette.accentInk)
                .frame(minHeight: 44)
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("setup.goalDeterminer")
        }
    }

    private var targetHours: Binding<Int> {
        Binding(get: { (model.draft.targetMinutes ?? 0) / 60 },
                set: { model.draft.targetMinutes = $0 * 60 + (model.draft.targetMinutes ?? 0) % 60 })
    }

    private var targetMins: Binding<Int> {
        Binding(get: { (model.draft.targetMinutes ?? 0) % 60 },
                set: { model.draft.targetMinutes = (model.draft.targetMinutes ?? 0) / 60 * 60 + $0 })
    }

    // MARK: Week

    @ViewBuilder private var week: some View {
        Text("What does your week look like?").font(UH.TextStyle.screenTitle)

        VStack(alignment: .leading, spacing: UH.Space.regular) {
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

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Run days").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                DayGrid(selected: model.draft.preferredDays, available: Set(Weekday.allCases), label: "run day") { model.toggleDay($0) }
                    .id(SetupField.preferredDays)
                SetupError(model: model, field: .preferredDays)
            }

            HStack {
                Text("Long run").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Spacer()
                Picker("Long run", selection: $model.draft.longRunDay) {
                    ForEach(model.draft.orderedDays) { Text(L($0.rawValue)).tag($0) }
                }
                .pickerStyle(.menu)
                .tint(UH.Palette.accentInk)
            }
            .frame(minHeight: 44)
        }
        .trainingCard()

        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text("Running now").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
            HStack(alignment: .center, spacing: 8) {
                TextField("km", value: Binding(get: { model.draft.currentWeeklyKm }, set: model.setWeeklyKm), format: .number)
                    .keyboardType(.numberPad)
                    .font(.system(size: 32, weight: .bold, design: .rounded))
                    .foregroundStyle(UH.Palette.ink)
                    .frame(width: 80)
                Text("km / week")
                    .font(UH.TextStyle.label)
                    .foregroundStyle(UH.Palette.secondary)
                Spacer()
                Stepper("Weekly km", value: Binding(get: { model.draft.currentWeeklyKm ?? 0 }, set: { model.setWeeklyKm($0) }), in: 0...250, step: 5)
                    .labelsHidden()
            }
            if model.draft.weeklyKmFromWatch, let km = model.watchWeeklyKm {
                Label(model.watchVolumeSource == "apple_health"
                      ? L("From Apple Health: %lld km a week over the last 4 full weeks", Int(km))
                      : model.watchVolumeSource == "garmin"
                      ? L("From Garmin: %lld km a week over the last 4 full weeks", Int(km))
                      : L("From your COROS: %lld km a week over the last 4 full weeks", Int(km)),
                      systemImage: "applewatch.radiowaves.left.and.right")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.accentInk)
                    .accessibilityIdentifier("setup.weeklyKmFromWatch")
            } else {
                Text("Your average over the last month. Your first week starts close to it.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
            Button("No running yet") { model.setWeeklyKm(0) }
                .font(UH.TextStyle.caption)
                .tint(UH.Palette.accentInk)
                .accessibilityIdentifier("setup.noRunning")
            SetupError(model: model, field: .weeklyKm)
        }
        .trainingCard()

        DisclosureGroup {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                DayGrid(selected: model.draft.doubleSessionDays, available: model.draft.preferredDays, label: "double-session day") {
                    model.toggleDoubleDay($0)
                }
                Text("Up to 2 of your run days can carry a second short session.")
                    .font(UH.TextStyle.caption)
                    .foregroundStyle(UH.Palette.secondary)
            }
            .padding(.top, UH.Space.small)
        } label: {
            Text("Double sessions (optional)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
        }
        .tint(UH.Palette.accentInk)
        .trainingCard()
    }

    // MARK: Venues

    @ViewBuilder private var venues: some View {
        Text("Where do you train?").font(UH.TextStyle.screenTitle)

        VStack(alignment: .leading, spacing: UH.Space.regular) {
            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Terrain near home").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                Picker("Terrain near home", selection: $model.draft.environment) {
                    Text("Mostly flat").tag(TrainingEnvironment.flat)
                    Text("Hilly").tag(TrainingEnvironment.hilly)
                    Text("A mix").tag(TrainingEnvironment.mixed)
                }
                .pickerStyle(.segmented)
            }
            TrainingVenueSection(
                mountainDays: $model.draft.mountainDays,
                trainingMountain: $model.draft.trainingMountain,
                mountainMinMinutes: $model.draft.mountainMinMinutes,
                stairAccess: $model.draft.stairAccess,
                useTreadmill: $model.draft.useTreadmill,
                treadmillMaxIncline: model.draft.useTreadmill ? $model.draft.treadmillMaxIncline : nil,
                courseSteepness: model.draft.courseSteepness
            )
        }
        .trainingCard()

        VStack(spacing: UH.Space.small) {
            Toggle("I can use a gym", isOn: $model.draft.hasGymAccess)
        }
        .font(UH.TextStyle.label)
        .tint(UH.Palette.accent)
        .trainingCard()
    }

    // MARK: Body

    @ViewBuilder private var bodyStep: some View {
        Text("How does your body hold up?").font(UH.TextStyle.screenTitle)

        VStack(spacing: UH.Space.small) {
            ForEach(PlanSetupDraft.injuryOptions, id: \.value) { option in
                SetupOption(title: option.title, subtitle: option.subtitle, symbol: injurySymbol(option.value),
                            selected: model.draft.injuryHistory == option.value) {
                    model.draft.injuryHistory = option.value
                }
            }
        }

        optionalProfile
    }

    @ViewBuilder private var trainingZones: some View {
        Text("Set your training zones").font(UH.TextStyle.screenTitle)
        Text("Optional. Add values you know; leave the rest blank. You can update them in Profile later.")
            .font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary)
        Button { showZonesGuide = true } label: {
            Label("Find values from your watch or a test", systemImage: "questionmark.circle")
                .font(UH.TextStyle.label).frame(minHeight: 44, alignment: .leading)
        }
        .accessibilityIdentifier("setup.zonesGuide")
        .tint(UH.Palette.accentInk)

        Picker("Zone Category", selection: $model.showPaceInputs) {
            Text("Heart Rate").tag(false)
            Text("Paces").tag(true)
        }
        .pickerStyle(.segmented)
        if !model.showPaceInputs {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Heart rate anchors").font(UH.TextStyle.label)
                TrainingZoneBar(aetHr: model.draft.aetHr, antHr: model.draft.antHr,
                                restingHr: model.draft.restingHr, maxHr: model.draft.maxHr)
                HStack(alignment: .top, spacing: UH.Space.small) {
                    hrField("Max", placeholder: L("Optional"), value: $model.draft.maxHr)
                        .accessibilityIdentifier("setup.maxHr")
                    hrField("Resting", placeholder: L("Optional"), value: $model.draft.restingHr)
                        .accessibilityIdentifier("setup.restingHr")
                }
                hrField("Aerobic Threshold (AeT)", placeholder: L("Optional"), value: $model.draft.aetHr)
                    .accessibilityIdentifier("setup.aetHr")
                hrField("Anaerobic Threshold (AnT)", placeholder: L("Optional"), value: $model.draft.antHr)
                    .accessibilityIdentifier("setup.antHr")
                if model.draft.aetHr != nil || model.draft.antHr != nil {
                    Text("How were these measured?").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                    Menu {
                        Button("Not sure") { model.draft.thresholdSource = "unknown" }
                        Button("Watch estimate") { model.draft.thresholdSource = "estimated" }
                        Button("Field test") { model.draft.thresholdSource = "field" }
                        Button("Lab test") { model.draft.thresholdSource = "lab" }
                    } label: {
                        HStack {
                            Text(thresholdSourceTitle).fixedSize(horizontal: false, vertical: true)
                            Spacer()
                            Image(systemName: "chevron.up.chevron.down")
                        }
                        .font(UH.TextStyle.label)
                        .frame(minHeight: 44)
                    }
                    .tint(UH.Palette.accentInk)
                    .accessibilityLabel("How were these measured?")
                    .accessibilityValue(Text(thresholdSourceTitle))
                    Text("Choose Field test or Lab test only when both thresholds were measured that way.")
                        .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                }
        }
            .trainingCard()
        } else {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Text("Running pace (min/km)").font(UH.TextStyle.label)
                paceField("Easy pace, slower end", value: $model.draft.zone2PaceMin, identifier: "setup.easySlow")
                paceField("Easy pace, faster end", value: $model.draft.zone2PaceMax, identifier: "setup.easyFast")
                paceField("Threshold pace", value: $model.draft.thresholdPace, identifier: "setup.thresholdPace")
                Text("Use flat-ground running pace, not your trail race average. Enter m:ss, for example 6:30.")
                    .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
        }
            .trainingCard()
            paceZonePreview
        }
        SetupError(model: model, field: .trainingZones).id(SetupField.trainingZones)
    }

    private var paceZonePreview: some View {
        let names = ["Zone 1 · Recovery", "Zone 2 · Easy / Aerobic", "Zone 3 · Tempo", "Zone 4 · Threshold", "Zone 5 · VO2max / Speed"]
        let colors = ["#0ea5e9", "#10b981", "#f59e0b", "#f97316", "#ef4444"]
        let ranges = OnboardingPacePreview.ranges(draft: model.draft)
        return VStack(alignment: .leading, spacing: UH.Space.regular) {
            Text("Pace zone preview").font(UH.TextStyle.label)
            Text(ranges == nil ? L("Add Threshold Pace or both easy pace bounds to preview your zones.") : L("Estimated from your inputs. Threshold Pace takes priority over the easy pace range."))
                .font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)
            ForEach(0..<5, id: \.self) { index in
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    ViewThatFits(in: .horizontal) {
                        HStack {
                            Text(L(names[index])).font(UH.TextStyle.caption.weight(.semibold))
                            Spacer()
                            Text(ranges.map { "\($0[index]) /km" } ?? "—").font(UH.TextStyle.caption.monospacedDigit())
                        }
                        VStack(alignment: .leading) {
                            Text(L(names[index])).font(UH.TextStyle.caption.weight(.semibold))
                            Text(ranges.map { "\($0[index]) /km" } ?? "—").font(UH.TextStyle.caption.monospacedDigit())
                        }
                    }
                    GeometryReader { geometry in
                        Capsule().fill(UH.Palette.line)
                            .overlay(alignment: .leading) {
                                Capsule().fill(Color(hex: colors[index]))
                                    .frame(width: geometry.size.width * CGFloat(index + 1) / 5)
                            }
                    }.frame(height: 6).accessibilityHidden(true)
                }
            }
        }.trainingCard()
    }

    private var thresholdSourceTitle: String {
        switch model.draft.thresholdSource {
        case "estimated": L("Watch estimate")
        case "field": L("Field test")
        case "lab": L("Lab test")
        default: L("Not sure")
        }
    }

    private func paceField(_ title: LocalizedStringKey, value: Binding<String>, identifier: String) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            TextField(L("Optional"), text: value)
                .font(.body.monospacedDigit())
                .keyboardType(.numbersAndPunctuation)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .accessibilityIdentifier(identifier)
                .accessibilityLabel(Text(title))
                .padding(UH.Space.small)
                .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
        }
    }

    @ViewBuilder private var optionalProfile: some View {
        DisclosureGroup {
            VStack(alignment: .leading, spacing: UH.Space.regular) {
                Toggle("Add birth date", isOn: $includeBirthDate)
                    .onChange(of: includeBirthDate) { _, include in
                        model.draft.birthDate = include ? (model.draft.birthDate ?? Calendar.current.date(byAdding: .year, value: -30, to: model.today)) : nil
                    }
                if includeBirthDate {
                    DatePicker("Birth date", selection: Binding(get: { model.draft.birthDate ?? model.today }, set: { model.draft.birthDate = $0 }),
                               in: ...model.today, displayedComponents: .date)
                }
                Picker("Gender", selection: Binding(get: { model.draft.gender ?? "" }, set: { model.draft.gender = $0.isEmpty ? nil : $0 })) {
                    Text("Not set").tag("")
                    Text("Male").tag("male")
                    Text("Female").tag("female")
                    Text("Other").tag("other")
                }
                HStack(alignment: .top, spacing: UH.Space.small) {
                    numberField("Height (cm)", placeholder: L("Optional"), value: $model.draft.heightCm)
                    numberField("Weight (kg)", placeholder: L("Optional"), value: $model.draft.weightKg)
                }
            }
            .padding(.top, UH.Space.small)
        } label: {
            Text("More about you (optional)").font(UH.TextStyle.label)
        }
        .onAppear { includeBirthDate = model.draft.birthDate != nil }
        .trainingCard()
    }

    private func injurySymbol(_ value: String) -> String {
        switch value {
        case "rarely": "checkmark.shield"
        case "minor": "bandage"
        default: "cross.case"
        }
    }

    private func hrField(_ title: LocalizedStringKey, placeholder: String, value: Binding<Int?>) -> some View {
        VStack(alignment: .leading, spacing: UH.Space.compact) {
            Text(title).font(UH.TextStyle.caption).foregroundStyle(UH.Palette.secondary)
            HStack(spacing: 4) {
                TextField(placeholder, value: value, format: .number)
                    .accessibilityLabel(Text(title))
                    .keyboardType(.numberPad)
                    .font(.body.monospacedDigit())
                Text("bpm").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
            }
            .padding(UH.Space.small)
            .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
            .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: Race history

    @ViewBuilder private var raceHistory: some View {
        Text("Have you raced before?").font(UH.TextStyle.screenTitle)

        VStack(alignment: .leading, spacing: UH.Space.regular) {
            Text("Link your UTMB or Vietnam race profile and I'll read your past finishes. They shape your starting load and race-day goal.")
                .font(UH.TextStyle.body)
                .foregroundStyle(UH.Palette.secondary)
                .fixedSize(horizontal: false, vertical: true)

            if model.linkedRaceHistory {
                HStack(spacing: UH.Space.small) {
                    Image(systemName: "checkmark.circle.fill").font(.title2).foregroundStyle(UH.Palette.accentInk)
                    Text("Profile linked. Your results are syncing.").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                }
                .frame(minHeight: 44)
            } else if model.raceHistoryService != nil {
                Button("Find my profile") { showLinkProfile = true }
                    .buttonStyle(.uhPrimary)
                    .accessibilityIdentifier("setup.linkRaceHistory")
            }
        }
        .trainingCard()
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

            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(model.draft.summaryItems.filter { model.steps.contains($0.step) }.enumerated()), id: \.offset) { index, item in
                    if index > 0 { Divider() }
                    Button {
                        model.jump(to: item.step)
                    } label: {
                        HStack(spacing: UH.Space.small) {
                            Image(systemName: icon(for: item.step))
                                .font(.subheadline)
                                .foregroundStyle(UH.Palette.accentInk)
                                .frame(width: 24)
                            Text(item.text)
                                .font(UH.TextStyle.label)
                                .foregroundStyle(UH.Palette.ink)
                                .multilineTextAlignment(.leading)
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(UH.Palette.muted)
                        }
                        .frame(minHeight: 48)
                    }
                    .buttonStyle(.plain)
                    .accessibilityHint("Edit")
                }
            }
            .trainingCard()

            VStack(alignment: .leading, spacing: UH.Space.compact) {
                Text("Anything else I should know? (optional)").font(UH.TextStyle.label).foregroundStyle(UH.Palette.ink)
                TextField("Travel, work shifts, a training camp, a niggle…", text: $model.draft.notes, axis: .vertical)
                    .lineLimit(3...6)
                    .padding(UH.Space.small)
                    .background(UH.Palette.surface, in: RoundedRectangle(cornerRadius: UH.Radius.control))
                    .overlay(RoundedRectangle(cornerRadius: UH.Radius.control).stroke(UH.Palette.line, lineWidth: 1))
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

    private func icon(for step: SetupStep) -> String {
        switch step {
        case .details: "flag.checkered"
        case .raceGoal: "target"
        case .schedule: "figure.run"
        default: "checkmark.seal.fill"
        }
    }
}

/// Seven weekday toggles; days outside `available` are dimmed and inert.
private struct DayGrid: View {
    let selected: Set<Weekday>
    let available: Set<Weekday>
    let label: String
    let toggle: (Weekday) -> Void

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 44))], spacing: 8) {
            ForEach(Weekday.allCases) { day in
                let isAvailable = available.contains(day)
                let isSelected = selected.contains(day)
                Button { toggle(day) } label: {
                    Text(L(day.short))
                        .font(UH.TextStyle.label)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .foregroundStyle(isSelected ? UH.Palette.buttonInk : (isAvailable ? UH.Palette.ink : UH.Palette.muted))
                        .background(isSelected ? UH.Palette.activeFill : UH.Palette.surface,
                                    in: RoundedRectangle(cornerRadius: UH.Radius.control))
                        .overlay(RoundedRectangle(cornerRadius: UH.Radius.control)
                            .stroke(isSelected ? UH.Palette.accent : UH.Palette.line, lineWidth: 1))
                        .opacity(isAvailable ? 1 : 0.45)
                }
                .buttonStyle(.plain)
                .disabled(!isAvailable)
                .accessibilityLabel("\(L(day.rawValue)) \(L(label))")
                .accessibilityAddTraits(isSelected ? .isSelected : [])
            }
        }
        .sensoryFeedback(.selection, trigger: selected)
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
                            .foregroundStyle(selected ? UH.Palette.onSolid : UH.Palette.accentInk)
                    }
                }
                VStack(alignment: .leading, spacing: 3) {
                    Text(L(title))
                        .font(UH.TextStyle.label)
                        .foregroundStyle(UH.Palette.ink)
                    if let subtitle, !subtitle.isEmpty {
                        Text(L(subtitle))
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

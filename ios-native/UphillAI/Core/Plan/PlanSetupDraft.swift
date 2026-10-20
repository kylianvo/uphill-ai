import Foundation

enum SetupGoal: String, CaseIterable, Sendable {
    case race, distance, startRunning = "start_running", returning = "return", recovery

    var title: String {
        switch self {
        case .race: L("A specific race")
        case .distance: L("A distance")
        case .startRunning: L("Start running")
        case .returning: L("Come back after a break")
        case .recovery: L("Recover from a race")
        }
    }

    var subtitle: String {
        switch self {
        case .race: L("Build toward a race on a set date.")
        case .distance: L("Be ready for a distance, like your first 21 km.")
        case .startRunning: L("From walk-run to running 30 minutes.")
        case .returning: L("Rebuild safely after time off.")
        case .recovery: L("Easy weeks after a hard effort.")
        }
    }

    var systemImage: String {
        switch self {
        case .race: "flag.checkered"
        case .distance: "point.topleft.down.to.point.bottomright.curvepath"
        case .startRunning: "figure.walk"
        case .returning: "arrow.uturn.forward"
        case .recovery: "bed.double"
        }
    }

    var isEvent: Bool { self == .race || self == .distance }
}

enum RaceGoal: String, CaseIterable, Sendable {
    case finish, time, optimal

    var title: String {
        switch self {
        case .finish: L("Finish strong")
        case .time: L("Hit a target time")
        case .optimal: L("My best possible time")
        }
    }
}

enum Terrain: String, CaseIterable, Sendable { case trail, road, mixed }
enum TrainingEnvironment: String, CaseIterable, Sendable {
    case flat, hilly, mixed
    var title: String {
        switch self {
        case .flat: L("Mostly flat")
        case .hilly: L("Hilly")
        case .mixed: L("A mix")
        }
    }
}

enum SetupStep: Equatable, Sendable {
    case goal, details, raceDate, raceGoal, fitnessFeel, daysSinceRace, recoveryFeel
    case watch, schedule, venues, body, trainingZones, raceHistory, startDate, review

    /// Watch, body and race history are profile answers, asked once at onboarding and edited in Profile afterwards.
    /// The watch comes before the week so a fresh COROS sync can fill in current mileage.
    static func steps(for goal: SetupGoal?, includeProfile: Bool) -> [SetupStep] {
        guard let goal else { return [.goal] }
        let questions: [SetupStep]
        switch goal {
        case .race, .distance: questions = [.details, .raceDate, .raceGoal]
        case .returning: questions = [.details, .fitnessFeel]
        case .recovery: questions = [.details, .daysSinceRace, .recoveryFeel]
        case .startRunning: questions = []
        }
        let profile: [SetupStep] = includeProfile ? [.body, .trainingZones, .raceHistory] : []
        let watch: [SetupStep] = includeProfile ? [.watch] : []
        return [.goal] + questions + watch + [.schedule, .venues] + profile + [.startDate, .review]
    }
}

enum SetupField: Hashable, Sendable {
    case goal, raceName, raceDate, distance, targetTime, timeAway, fitnessFeel, raceCompleted, daysSinceRace, recoveryFeel
    case preferredDays, longRunDay, weeklyKm, startDate, height, weight, maxHr, restingHr, trainingZones
}

struct SetupIssue: Equatable, Sendable {
    let field: SetupField
    let message: String
}

/// Answers shared by onboarding and "Start new plan". Free-text option values
/// are sent verbatim: the backend passes them into the generation prompt, same as the web.
struct PlanSetupDraft: Equatable, Sendable {
    static let timeAwayOptions = ["< 2 weeks", "2–6 weeks", "1–3 months", "3–6 months", "6+ months"]
    static let fitnessFeelOptions = [
        "Feeling good, just need structure",
        "A bit rusty, slightly deconditioned",
        "Significant deconditioning — starting nearly fresh",
    ]
    static let raceDistanceOptions = ["5k", "10k", "Half Marathon", "Marathon", "Ultra (< 60k)", "Ultra (60k+)"]
    static let injuryOptions: [(value: String, title: String, subtitle: String)] = [
        ("rarely", "Rarely or never injured", "I bounce back quickly from hard efforts."),
        ("minor", "Minor or past injury", "Mostly resolved, I'm careful at times."),
        ("frequent", "Often or recently injured", "I need a careful, conservative build."),
    ]
    static let distancePresets: [Double] = [10, 21, 42, 50, 70, 100]
    static let recoveryFeelOptions = [
        "Feeling great, minimal soreness",
        "Moderate fatigue, some soreness",
        "Very fatigued — need real rest",
    ]

    private let summaryTimeZone: TimeZone
    var goal: SetupGoal?
    // Race / distance
    var raceName = ""
    var raceDate: Date?
    var distanceKm: Double?
    var elevationGainM: Double?
    var terrain: Terrain = .trail
    var raceGoal: RaceGoal = .finish
    var targetMinutes: Int?
    /// Label of the race distance picked from the matched race's list, if any.
    var distanceLabel: String?
    // Return
    var timeAway: String?
    var fitnessFeel: String?
    // Recovery
    var raceDistanceCompleted: String?
    var daysSinceRace = 7
    var recoveryFeel: String?
    // Schedule
    var daysPerWeek = 4
    var preferredDays: Set<Weekday> = [.tuesday, .thursday, .saturday, .sunday]
    var longRunDay: Weekday = .saturday
    var currentWeeklyKm: Double? = 30
    /// True while `currentWeeklyKm` is the untouched COROS 4-week average.
    var weeklyKmFromWatch = false
    var environment: TrainingEnvironment = .flat
    var mountainDays: Set<Weekday> = []
    var trainingMountain: String?
    var mountainMinMinutes: Int?
    var stairAccess = false
    var hasGymAccess = false
    var useTreadmill = false
    var treadmillMaxIncline = 15
    var doubleSessionDays: Set<Weekday> = []
    var startDate: Date
    // About you (optional)
    var birthDate: Date?
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var maxHr: Int?
    var restingHr: Int?
    var aetHr: Int?
    var antHr: Int?
    var thresholdSource = "unknown"
    var zone2PaceMin = ""
    var zone2PaceMax = ""
    var thresholdPace = ""
    var injuryHistory = ""
    var notes = ""

    init(prefill user: User?, today: Date, calendar: Calendar) {
        summaryTimeZone = calendar.timeZone
        startDate = calendar.startOfDay(for: today)
        guard let user else { return }
        if let days = user.daysPerWeek, (3...7).contains(days) { daysPerWeek = days }
        if let km = user.currentWeeklyKm {
            currentWeeklyKm = !user.onboardingComplete && user.goalType == nil && km == 30 ? nil : km
        }
        if let data = user.preferredRunDays?.data(using: .utf8),
           let names = try? JSONDecoder().decode([String].self, from: data) {
            let days = Set(names.compactMap(Weekday.init(rawValue:)))
            if days.count == daysPerWeek { preferredDays = days }
        }
        if let long = user.longRunDay.flatMap(Weekday.init(rawValue:)) { longRunDay = long }
        if preferredDays.count != daysPerWeek { preferredDays = Self.defaultDays(count: daysPerWeek) }
        if !preferredDays.contains(longRunDay) { longRunDay = preferredDays.contains(.saturday) ? .saturday : orderedDays.last! }
        heightCm = user.heightCm
        weightKg = user.weightKg
        maxHr = user.fieldSources?["max_hr"]?.source == "default" ? nil : user.maxHr
        restingHr = user.fieldSources?["resting_hr"]?.source == "default" ? nil : user.restingHr
        aetHr = user.fieldSources?["aet_hr"]?.source == "default" ? nil : user.aetHr
        antHr = user.fieldSources?["ant_hr"]?.source == "default" ? nil : user.antHr
        thresholdSource = user.fieldSources?["aet_hr"]?.method ?? "unknown"
        zone2PaceMin = user.fieldSources?["zone2_pace_min"]?.source == "default" ? "" : (user.zone2PaceMin ?? "")
        zone2PaceMax = user.fieldSources?["zone2_pace_max"]?.source == "default" ? "" : (user.zone2PaceMax ?? "")
        thresholdPace = user.fieldSources?["threshold_pace"]?.source == "default" ? "" : (user.thresholdPace ?? "")
        gender = user.gender
        birthDate = PlanCalendar.day(from: user.dob, calendar: calendar)
        injuryHistory = user.injuryHistory ?? ""
    }

    /// Spread runs through the week with the long run on Saturday.
    static func defaultDays(count: Int) -> Set<Weekday> {
        switch count {
        case 3: [.tuesday, .thursday, .saturday]
        case 4: [.tuesday, .thursday, .saturday, .sunday]
        case 5: [.monday, .tuesday, .thursday, .saturday, .sunday]
        case 6: [.monday, .tuesday, .wednesday, .thursday, .saturday, .sunday]
        default: Set(Weekday.allCases)
        }
    }

    var orderedDays: [Weekday] { Weekday.allCases.filter(preferredDays.contains) }
    private var requestDays: [Weekday] {
        let days = preferredDays.count == daysPerWeek ? preferredDays : Self.defaultDays(count: daysPerWeek)
        return Weekday.allCases.filter(days.contains)
    }
    private var requestDoubleDays: [String] {
        Weekday.allCases.filter { doubleSessionDays.contains($0) && requestDays.contains($0) }.map(\.rawValue)
    }
    private var requestLongRunDay: Weekday {
        requestDays.contains(longRunDay) ? longRunDay : requestDays.last!
    }

    // MARK: Validation

    func issues(for step: SetupStep, today: Date, calendar: Calendar) -> [SetupIssue] {
        var issues: [SetupIssue] = []
        func add(_ field: SetupField, _ message: String) { issues.append(SetupIssue(field: field, message: message)) }
        let start = calendar.startOfDay(for: today)

        switch step {
        case .goal:
            if goal == nil { add(.goal, L("Choose what you're training for.")) }
        case .details:
            if goal?.isEvent == true {
                if goal == .race, raceName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    add(.raceName, L("Add the race name."))
                }
                if !(1...400).contains(distanceKm ?? 0) { add(.distance, L("Enter a distance between 1 and 400 km.")) }
            }
        case .raceDate:
            let earliest = calendar.date(byAdding: .day, value: 14, to: start)!
            if raceDate.map({ $0 < earliest }) ?? true {
                add(.raceDate, L("Pick a date at least 2 weeks away so the plan has room to build."))
            }
        case .raceGoal:
            if raceGoal == .time, !(1...6000).contains(targetMinutes ?? 0) {
                add(.targetTime, L("Set your target finish time."))
            }
        case .schedule:
            if preferredDays.count != daysPerWeek {
                add(.preferredDays, L("Pick %lld run days.", daysPerWeek))
            }
            if currentWeeklyKm == nil || !(0...250).contains(currentWeeklyKm ?? -1) { add(.weeklyKm, L("Enter 0 to 250 km.")) }
        case .trainingZones:
            if let error = trainingZonesError { add(.trainingZones, error) }
        case .startDate:
            let latest = latestStartDate(today: start, calendar: calendar)
            if !(start...latest).contains(calendar.startOfDay(for: startDate)) {
                add(.startDate, goal?.isEvent == true ? L("Start at least 2 weeks before your goal date.") : L("Start today or later."))
            }
        case .watch, .venues, .body, .raceHistory, .fitnessFeel, .daysSinceRace, .recoveryFeel, .review:
            break
        }
        return issues
    }

    func latestStartDate(today: Date, calendar: Calendar) -> Date {
        let start = calendar.startOfDay(for: today)
        let latest = calendar.date(byAdding: .day, value: 14, to: start)!
        guard goal?.isEvent == true, let raceDate else { return latest }
        return max(start, min(latest, calendar.date(byAdding: .day, value: -14, to: raceDate)!))
    }

    var hasTrainingZones: Bool {
        maxHr != nil || restingHr != nil || aetHr != nil || antHr != nil || [zone2PaceMin, zone2PaceMax, thresholdPace].contains { nonEmpty($0) != nil }
    }

    var needsZoneEstimateWarning: Bool {
        !hasTrainingZones || maxHr == nil || restingHr == nil || aetHr == nil || antHr == nil || thresholdSource == "unknown"
    }

    var trainingZonesError: String? {
        if let maxHr, !(120...240).contains(maxHr) { return L("Enter Max HR between 120 and 240 bpm.") }
        if let restingHr, !(30...120).contains(restingHr) { return L("Enter Resting HR between 30 and 120 bpm.") }
        if let aetHr, !(80...220).contains(aetHr) { return L("Enter AeT between 80 and 220 bpm.") }
        if let antHr, !(90...225).contains(antHr) { return L("Enter AnT between 90 and 225 bpm.") }
        let known = [restingHr, aetHr, antHr, maxHr].compactMap { $0 }
        if zip(known, known.dropFirst()).contains(where: { $0 >= $1 }) {
            return L("Heart rates must increase from Resting to AeT to AnT to Max.")
        }
        let paces = [zone2PaceMin, zone2PaceMax, thresholdPace].map { nonEmpty($0) }
        for pace in paces.compactMap({ $0 }) {
            if pace.range(of: #"^\d{1,2}:[0-5]\d$"#, options: .regularExpression) == nil || paceSeconds(pace) == 0 {
                return L("Enter pace as m:ss per km, for example 6:30.")
            }
        }
        if let slow = paces[0], let fast = paces[1], paceSeconds(slow) < paceSeconds(fast) {
            return L("Easy pace, slower end must be slower than the faster end.")
        }
        if let threshold = paces[2], paces.prefix(2).compactMap({ $0 }).contains(where: { paceSeconds(threshold) >= paceSeconds($0) }) {
            return L("Threshold pace must be faster than easy pace.")
        }
        return nil
    }

    private func paceSeconds(_ pace: String) -> Int {
        let parts = pace.split(separator: ":").compactMap { Int($0) }
        return parts.count == 2 ? parts[0] * 60 + parts[1] : 0
    }

    // MARK: Request bodies

    private var trimmedName: String { raceName.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var eventName: String? {
        guard goal?.isEvent == true else { return nil }
        if goal == .race, !trimmedName.isEmpty { return trimmedName }
        guard let km = distanceKm else { return nil }
        return km.formatted(.number.precision(.fractionLength(0...1)).locale(Locale(identifier: "en_US_POSIX"))) + " km goal"
    }

    private var targetText: String? {
        guard goal?.isEvent == true, raceGoal == .time, let m = targetMinutes else { return nil }
        return "\(m / 60):\(String(format: "%02d", m % 60))"
    }

    private func nonEmpty(_ s: String) -> String? {
        let t = s.trimmingCharacters(in: .whitespacesAndNewlines)
        return t.isEmpty ? nil : t
    }

    func onboardingBody(skipPlan: Bool, calendar: Calendar) -> OnboardingBody {
        let event = goal?.isEvent == true
        return OnboardingBody(
            lang: AppLanguage.code,
            dob: birthDate.map { PlanCalendar.ymd($0, calendar: calendar) },
            gender: gender,
            heightCm: heightCm,
            weightKg: weightKg,
            goalType: goal?.rawValue ?? SetupGoal.startRunning.rawValue,
            maxHr: maxHr,
            restingHr: restingHr,
            aetHr: aetHr,
            antHr: antHr,
            thresholdSource: aetHr != nil && antHr != nil ? thresholdSource : "unknown",
            zone2PaceMin: nonEmpty(zone2PaceMin),
            zone2PaceMax: nonEmpty(zone2PaceMax),
            thresholdPace: nonEmpty(thresholdPace),
            injuryHistory: nonEmpty(injuryHistory),
            raceName: event ? eventName : nil,
            raceDate: event ? raceDate.map { PlanCalendar.ymd($0, calendar: calendar) } : nil,
            courseDistanceKm: event ? distanceKm : nil,
            courseElevationGainM: event ? elevationGainM : nil,
            terrain: terrain.rawValue,
            raceGoal: raceGoal.rawValue,
            expectedFinishTime: targetText,
            daysPerWeek: daysPerWeek,
            preferredRunDays: requestDays.map(\.rawValue),
            longRunDay: requestLongRunDay.rawValue,
            currentWeeklyKm: currentWeeklyKm ?? 0,
            hasGymAccess: hasGymAccess,
            useTreadmill: useTreadmill,
            trainingEnvironment: environment.rawValue,
            mountainDays: Weekday.allCases.filter(mountainDays.contains).map(\.rawValue),
            trainingMountain: trainingMountain,
            mountainMinMinutes: mountainMinMinutes,
            stairAccess: stairAccess,
            treadmillMaxIncline: useTreadmill ? treadmillMaxIncline : nil,
            doubleSessionDays: requestDoubleDays,
            timeAway: goal == .returning ? timeAway : nil,
            fitnessFeel: goal == .returning ? fitnessFeel : nil,
            raceDistanceCompleted: goal == .recovery ? raceDistanceCompleted : nil,
            daysSinceRace: goal == .recovery ? daysSinceRace : nil,
            recoveryFeel: goal == .recovery ? recoveryFeel : nil,
            skipPlan: skipPlan,
            planStartDate: PlanCalendar.ymd(startDate, calendar: calendar),
            athleteNotes: nonEmpty(notes)
        )
    }

    func planBody(calendar: Calendar) -> PlanBody {
        let event = goal?.isEvent == true
        return PlanBody(
            lang: AppLanguage.code,
            raceName: event ? eventName : nil,
            raceDate: event ? raceDate.map { PlanCalendar.ymd($0, calendar: calendar) } : nil,
            goalType: event ? raceGoal.rawValue : (goal ?? .startRunning).rawValue,
            currentWeeklyKm: currentWeeklyKm ?? 0,
            weeklyKmFromWatch: weeklyKmFromWatch,
            targetTimeHours: (event && raceGoal == .time) ? targetMinutes.map { Double($0) / 60 } : nil,
            terrain: terrain.rawValue,
            courseDistanceKm: event ? distanceKm : nil,
            courseElevationGainM: event ? elevationGainM : nil,
            preferredDays: requestDays.map(\.rawValue),
            longRunDay: requestLongRunDay.rawValue,
            daysPerWeek: daysPerWeek,
            hasGymAccess: hasGymAccess,
            useTreadmill: useTreadmill,
            trainingEnvironment: environment.rawValue,
            mountainDays: Weekday.allCases.filter(mountainDays.contains).map(\.rawValue),
            trainingMountain: trainingMountain,
            mountainMinMinutes: mountainMinMinutes,
            stairAccess: stairAccess,
            treadmillMaxIncline: useTreadmill ? treadmillMaxIncline : nil,
            doubleSessionDays: requestDoubleDays,
            planStartDate: PlanCalendar.ymd(startDate, calendar: calendar),
            timeAway: goal == .returning ? timeAway : nil,
            fitnessFeel: goal == .returning ? fitnessFeel : nil,
            raceDistanceCompleted: goal == .recovery ? raceDistanceCompleted : nil,
            daysSinceRace: goal == .recovery ? daysSinceRace : nil,
            recoveryFeel: goal == .recovery ? recoveryFeel : nil,
            athleteNotes: nonEmpty(notes)
        )
    }

    /// Facts the plan is built from, shown while it generates. Inputs, not invented progress.
    var summaryLines: [String] { summaryItems.map(\.text) }

    /// Review rows, each with the step that edits it.
    var summaryItems: [(text: String, step: SetupStep)] {
        var items: [(text: String, step: SetupStep)] = []
        if goal?.isEvent == true, let name = eventName {
            if let date = raceDate {
                let style = Date.FormatStyle(date: .omitted, time: .omitted, locale: AppLanguage.current == .vi ? AppLanguage.vi.locale : Locale(identifier: "en_GB"),
                                             calendar: Calendar(identifier: .gregorian), timeZone: summaryTimeZone)
                    .weekday(.abbreviated).day().month(.abbreviated)
                items.append((L("%@ on %@", name, date.formatted(style)), .details))
            } else {
                items.append((name, .details))
            }
            if let course = courseLine { items.append((course, .details)) }
            if let target = targetText {
                items.append((L("Target time %@", target), .raceGoal))
            } else {
                items.append((raceGoal.title, .raceGoal))
            }
        } else if let goal {
            items.append((goal.title, .goal))
        }
        items.append((L("%lld runs a week, long run on %@", daysPerWeek, L(longRunDay.rawValue)), .schedule))
        if let currentWeeklyKm { items.append((L("Starting from %lld km a week", Int(currentWeeklyKm.rounded())), .schedule)) }
        items.append((L("Terrain near home: %@", environment.title), .venues))
        if hasGymAccess { items.append((L("Gym access"), .venues)) }
        if useTreadmill { items.append((L("Treadmill up to %lld%%", treadmillMaxIncline), .venues)) }
        if stairAccess { items.append((L("Stair access"), .venues)) }
        if !mountainDays.isEmpty {
            items.append((L("Hill / trail days: %@", Weekday.allCases.filter(mountainDays.contains).map { L($0.short) }.joined(separator: ", ")), .venues))
        }
        if !doubleSessionDays.isEmpty {
            items.append((L("Double sessions: %@", Weekday.allCases.filter(doubleSessionDays.contains).map { L($0.short) }.joined(separator: ", ")), .schedule))
        }
        if let aetHr { items.append((L("AeT: %lld bpm", aetHr), .trainingZones)) }
        if let antHr { items.append((L("AnT: %lld bpm", antHr), .trainingZones)) }
        if let pace = nonEmpty(zone2PaceMin) { items.append((L("Easy pace, slower end: %@ /km", pace), .trainingZones)) }
        if let pace = nonEmpty(zone2PaceMax) { items.append((L("Easy pace, faster end: %@ /km", pace), .trainingZones)) }
        if let pace = nonEmpty(thresholdPace) { items.append((L("Threshold pace: %@ /km", pace), .trainingZones)) }
        return items
    }

    /// The course's climb in m D+/km, or nil before a distance and a gain are set.
    var courseSteepness: Double? {
        guard let km = distanceKm, km > 0, let gain = elevationGainM, gain > 0 else { return nil }
        return gain / km
    }

    /// "50 km · 3,200 m D+", or nil before a distance is set.
    var courseLine: String? {
        guard let km = distanceKm else { return nil }
        let kmText = km.formatted(.number.precision(.fractionLength(0...1)).locale(AppLanguage.current.locale))
        guard let gain = elevationGainM, gain > 0 else { return L("%@ km", kmText) }
        return L("%@ km · %@ m D+", kmText, Int(gain).formatted(.number.locale(AppLanguage.current.locale)))
    }
}

/// POST /api/auth/onboarding. Nil fields are omitted from the JSON.
struct OnboardingBody: Encodable, Sendable {
    var lang: String
    var dob: String?
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var goalType: String
    var maxHr: Int?
    var restingHr: Int?
    var aetHr: Int?
    var antHr: Int?
    var thresholdSource: String?
    var zone2PaceMin: String?
    var zone2PaceMax: String?
    var thresholdPace: String?
    var injuryHistory: String?
    var raceName: String?
    var raceDate: String?
    var courseDistanceKm: Double?
    var courseElevationGainM: Double?
    var terrain: String?
    var raceGoal: String?
    var expectedFinishTime: String?
    var daysPerWeek: Int
    var preferredRunDays: [String]
    var longRunDay: String
    var currentWeeklyKm: Double
    var hasGymAccess: Bool
    var useTreadmill: Bool
    var trainingEnvironment: String
    var mountainDays: [String]
    var trainingMountain: String? = nil
    var mountainMinMinutes: Int? = nil
    var stairAccess: Bool
    var treadmillMaxIncline: Int?
    var doubleSessionDays: [String]
    var timeAway: String?
    var fitnessFeel: String?
    var raceDistanceCompleted: String?
    var daysSinceRace: Int?
    var recoveryFeel: String?
    var skipPlan: Bool
    var planStartDate: String
    var athleteNotes: String?
}

/// POST /api/coach/generate-plan. Nil fields are omitted from the JSON.
struct PlanBody: Encodable, Sendable {
    var lang: String
    var raceName: String?
    var raceDate: String?
    var goalType: String
    var currentWeeklyKm: Double
    var weeklyKmFromWatch: Bool
    var targetTimeHours: Double?
    var terrain: String?
    var courseDistanceKm: Double?
    var courseElevationGainM: Double?
    var preferredDays: [String]
    var longRunDay: String
    var daysPerWeek: Int
    var hasGymAccess: Bool
    var useTreadmill: Bool
    var trainingEnvironment: String
    var mountainDays: [String]
    var trainingMountain: String? = nil
    var mountainMinMinutes: Int? = nil
    var stairAccess: Bool
    var treadmillMaxIncline: Int?
    var doubleSessionDays: [String]
    var planStartDate: String
    var timeAway: String?
    var fitnessFeel: String?
    var raceDistanceCompleted: String?
    var daysSinceRace: Int?
    var recoveryFeel: String?
    var athleteNotes: String?
}

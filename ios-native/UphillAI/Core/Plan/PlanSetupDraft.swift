import Foundation

enum SetupGoal: String, CaseIterable, Sendable {
    case race, distance, startRunning = "start_running", returning = "return", recovery

    var title: String {
        switch self {
        case .race: "A specific race"
        case .distance: "A distance"
        case .startRunning: "Start running"
        case .returning: "Come back after a break"
        case .recovery: "Recover from a race"
        }
    }

    var subtitle: String {
        switch self {
        case .race: "Build toward a race on a set date."
        case .distance: "Be ready for a distance, like your first 21 km."
        case .startRunning: "From walk-run to running 30 minutes."
        case .returning: "Rebuild safely after time off."
        case .recovery: "Easy weeks after a hard effort."
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
        case .finish: "Finish strong"
        case .time: "Hit a target time"
        case .optimal: "My best possible time"
        }
    }
}

enum Terrain: String, CaseIterable, Sendable { case trail, road, mixed }
enum TrainingEnvironment: String, CaseIterable, Sendable { case flat, hilly, mixed }

enum SetupStep: Equatable, Sendable {
    case goal, details, raceDate, fitnessFeel, daysSinceRace, recoveryFeel, schedule, startDate, aboutYou, review

    static func steps(for goal: SetupGoal?, includeAboutYou: Bool) -> [SetupStep] {
        guard let goal else { return [.goal] }
        let questions: [SetupStep]
        switch goal {
        case .race, .distance: questions = [.details, .raceDate]
        case .returning: questions = [.details, .fitnessFeel]
        case .recovery: questions = [.details, .daysSinceRace, .recoveryFeel]
        case .startRunning: questions = []
        }
        return [.goal] + questions + [.schedule, .startDate, .review]
    }
}

enum SetupField: Hashable, Sendable {
    case goal, raceName, raceDate, distance, targetTime, timeAway, fitnessFeel, raceCompleted, daysSinceRace, recoveryFeel
    case preferredDays, longRunDay, weeklyKm, startDate, height, weight, maxHr, restingHr
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
    var currentWeeklyKm: Double = 30
    var environment: TrainingEnvironment = .flat
    var mountainDays: Set<Weekday> = []
    var stairAccess = false
    var hasGymAccess = false
    var startDate: Date
    // About you (optional)
    var birthDate: Date?
    var gender: String?
    var heightCm: Double?
    var weightKg: Double?
    var maxHr: Int?
    var restingHr: Int?
    var injuryHistory = ""
    var notes = ""

    init(prefill user: User?, today: Date, calendar: Calendar) {
        summaryTimeZone = calendar.timeZone
        startDate = calendar.startOfDay(for: today)
        guard let user else { return }
        if let days = user.daysPerWeek, (3...7).contains(days) { daysPerWeek = days }
        if let km = user.currentWeeklyKm { currentWeeklyKm = km }
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
        maxHr = user.maxHr
        restingHr = user.restingHr
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
            if goal == nil { add(.goal, "Choose what you're training for.") }
        case .details:
            if goal?.isEvent == true {
                if goal == .race, raceName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    add(.raceName, "Add the race name.")
                }
                if !(1...400).contains(distanceKm ?? 0) { add(.distance, "Enter a distance between 1 and 400 km.") }
            }
        case .raceDate:
            let earliest = calendar.date(byAdding: .day, value: 14, to: start)!
            if raceDate.map({ $0 < earliest }) ?? true {
                add(.raceDate, "Pick a date at least 2 weeks away so the plan has room to build.")
            }
        case .schedule:
            if !(0...250).contains(currentWeeklyKm) { add(.weeklyKm, "Enter 0 to 250 km.") }
        case .startDate:
            let latest = calendar.date(byAdding: .day, value: 14, to: start)!
            if !(start...latest).contains(calendar.startOfDay(for: startDate)) { add(.startDate, "Start today or later.") }
        case .aboutYou, .fitnessFeel, .daysSinceRace, .recoveryFeel, .review:
            break
        }
        return issues
    }

    // MARK: Request bodies

    private var trimmedName: String { raceName.trimmingCharacters(in: .whitespacesAndNewlines) }
    private var eventName: String? {
        guard goal?.isEvent == true else { return nil }
        if !trimmedName.isEmpty { return trimmedName }
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
            currentWeeklyKm: currentWeeklyKm,
            hasGymAccess: hasGymAccess,
            trainingEnvironment: environment.rawValue,
            mountainDays: Weekday.allCases.filter(mountainDays.contains).map(\.rawValue),
            stairAccess: stairAccess,
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
            currentWeeklyKm: currentWeeklyKm,
            targetTimeHours: (event && raceGoal == .time) ? targetMinutes.map { Double($0) / 60 } : nil,
            terrain: terrain.rawValue,
            courseDistanceKm: event ? distanceKm : nil,
            courseElevationGainM: event ? elevationGainM : nil,
            preferredDays: requestDays.map(\.rawValue),
            longRunDay: requestLongRunDay.rawValue,
            daysPerWeek: daysPerWeek,
            hasGymAccess: hasGymAccess,
            trainingEnvironment: environment.rawValue,
            mountainDays: Weekday.allCases.filter(mountainDays.contains).map(\.rawValue),
            stairAccess: stairAccess,
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
    var summaryLines: [String] {
        var lines: [String] = []
        if goal?.isEvent == true, let name = eventName {
            if let date = raceDate {
                let style = Date.FormatStyle(date: .omitted, time: .omitted, locale: Locale(identifier: "en_GB"),
                                             calendar: Calendar(identifier: .gregorian), timeZone: summaryTimeZone)
                    .weekday(.abbreviated).day().month(.abbreviated)
                lines.append("\(name) on \(date.formatted(style))")
            } else {
                lines.append(name)
            }
            if let target = targetText { lines.append("Target time \(target)") }
        } else if let goal {
            lines.append(goal.title)
        }
        lines.append("\(daysPerWeek) runs a week, long run on \(longRunDay.rawValue)")
        lines.append("Starting from \(Int(currentWeeklyKm.rounded())) km a week")
        return lines
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
    var trainingEnvironment: String
    var mountainDays: [String]
    var stairAccess: Bool
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
    var targetTimeHours: Double?
    var terrain: String?
    var courseDistanceKm: Double?
    var courseElevationGainM: Double?
    var preferredDays: [String]
    var longRunDay: String
    var daysPerWeek: Int
    var hasGymAccess: Bool
    var trainingEnvironment: String
    var mountainDays: [String]
    var stairAccess: Bool
    var planStartDate: String
    var timeAway: String?
    var fitnessFeel: String?
    var raceDistanceCompleted: String?
    var daysSinceRace: Int?
    var recoveryFeel: String?
    var athleteNotes: String?
}

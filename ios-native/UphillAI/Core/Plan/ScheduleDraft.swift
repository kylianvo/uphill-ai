import Foundation

struct ScheduleDraft {
    private let initialPlan: Plan?
    var daysPerWeek: Int
    var preferredDays: Set<Weekday>
    var longRunDay: Weekday?
    var doubleSessionDays: Set<Weekday>
    var hasGymAccess: Bool
    var useTreadmill: Bool
    var environment: TrainingEnvironment
    /// Weekdays the athlete can reach hills or trails (e.g. weekend trips from a flat city).
    var mountainDays: Set<Weekday>
    var trainingMountain: String?
    var mountainMinMinutes: Int?
    /// Fire stairs in a tall building, a stadium, or a Stairmaster.
    var stairAccess: Bool
    /// The treadmill's top incline in %: 15 on a standard gym treadmill, 25+ on an incline trainer.
    var treadmillMaxIncline: Int
    var maxContinuousJogMin: Int
    var isGettingStarted: Bool { initialPlan?.goalType == "start_running" }

    init(plan: Plan?) {
        initialPlan = plan
        daysPerWeek = plan?.daysPerWeek ?? 4
        preferredDays = Self.days(plan?.preferredRunDays)
        longRunDay = plan?.longRunDay.flatMap(Weekday.init(rawValue:))
        doubleSessionDays = Self.days(plan?.doubleSessionDays)
        hasGymAccess = plan?.hasGymAccess ?? false
        useTreadmill = plan?.useTreadmill ?? false
        environment = plan?.trainingEnvironment.flatMap(TrainingEnvironment.init(rawValue:)) ?? .flat
        mountainDays = Self.days(plan?.mountainDays)
        trainingMountain = plan?.trainingMountain
        mountainMinMinutes = plan?.mountainMinMinutes
        stairAccess = plan?.stairAccess ?? false
        treadmillMaxIncline = plan?.treadmillMaxIncline ?? 15
        maxContinuousJogMin = plan?.maxContinuousJogMin ?? 0
    }

    private static func days(_ raw: String?) -> Set<Weekday> {
        guard let data = raw?.data(using: .utf8), let values = try? JSONDecoder().decode([String].self, from: data) else { return [] }
        return Set(values.compactMap(Weekday.init(rawValue:)))
    }

    var orderedDays: [Weekday] { Weekday.allCases.filter(preferredDays.contains) }

    var validationMessage: String? {
        let before = ScheduleDraft(plan: initialPlan)
        // An unchanged empty list means the server chooses the run days (older web plans).
        let unspecified = preferredDays.isEmpty && before.preferredDays.isEmpty
        guard (3...7).contains(daysPerWeek), unspecified || preferredDays.count == daysPerWeek else {
            return L("Pick %lld run days.", daysPerWeek)
        }
        if let longRunDay, !unspecified, !preferredDays.contains(longRunDay) { return L("Choose a long run day from your run days.") }
        if doubleSessionDays.count > 2 || !doubleSessionDays.isSubset(of: preferredDays) { return L("Pick up to 2 run days for double sessions.") }
        if let mountainMinMinutes, mountainMinMinutes < 0 { return L("Minimum minutes must be zero or more.") }
        if isGettingStarted && !(0...120).contains(maxContinuousJogMin) { return L("Enter 0 to 120 minutes.") }
        return nil
    }

    mutating func setDaysPerWeek(_ count: Int) {
        daysPerWeek = min(max(count, 3), 7)
        preferredDays = PlanSetupDraft.defaultDays(count: daysPerWeek)
        reconcileDays()
    }

    mutating func toggleDay(_ day: Weekday) {
        if preferredDays.contains(day) { preferredDays.remove(day) } else { preferredDays.insert(day) }
        daysPerWeek = min(max(preferredDays.count, 3), 7)
        reconcileDays()
    }

    private mutating func reconcileDays() {
        doubleSessionDays.formIntersection(preferredDays)
        if let longRunDay, !preferredDays.contains(longRunDay) {
            self.longRunDay = preferredDays.contains(.saturday) ? .saturday : orderedDays.last
        }
    }

    func applyChanges(to body: inout AdaptWeekBody) {
        let before = ScheduleDraft(plan: initialPlan)
        if preferredDays != before.preferredDays { body.preferredDays = Weekday.allCases.filter(preferredDays.contains).map(\.rawValue) }
        if longRunDay != before.longRunDay { body.longRunDay = longRunDay?.rawValue }
        if daysPerWeek != before.daysPerWeek { body.daysPerWeek = daysPerWeek }
        if doubleSessionDays != before.doubleSessionDays { body.doubleSessionDays = Weekday.allCases.filter(doubleSessionDays.contains).map(\.rawValue) }
        if hasGymAccess != before.hasGymAccess { body.hasGymAccess = hasGymAccess }
        if useTreadmill != before.useTreadmill { body.useTreadmill = useTreadmill }
        if environment != before.environment { body.trainingEnvironment = environment.rawValue }
        if mountainDays != before.mountainDays { body.mountainDays = Weekday.allCases.filter(mountainDays.contains).map(\.rawValue) }
        if trainingMountain != before.trainingMountain { body.trainingMountain = .some(trainingMountain) }
        if mountainMinMinutes != before.mountainMinMinutes { body.mountainMinMinutes = .some(mountainMinMinutes) }
        if stairAccess != before.stairAccess { body.stairAccess = stairAccess }
        if treadmillMaxIncline != before.treadmillMaxIncline { body.treadmillMaxIncline = treadmillMaxIncline }
        if isGettingStarted && maxContinuousJogMin != before.maxContinuousJogMin { body.maxContinuousJogMin = maxContinuousJogMin }
    }

    func applyChanges(to body: inout NextBlockBody) {
        let before = ScheduleDraft(plan: initialPlan)
        if preferredDays != before.preferredDays { body.preferredDays = Weekday.allCases.filter(preferredDays.contains).map(\.rawValue) }
        if longRunDay != before.longRunDay { body.longRunDay = longRunDay?.rawValue }
        if daysPerWeek != before.daysPerWeek { body.daysPerWeek = daysPerWeek }
        if doubleSessionDays != before.doubleSessionDays { body.doubleSessionDays = Weekday.allCases.filter(doubleSessionDays.contains).map(\.rawValue) }
        if hasGymAccess != before.hasGymAccess { body.hasGymAccess = hasGymAccess }
        if useTreadmill != before.useTreadmill { body.useTreadmill = useTreadmill }
        if environment != before.environment { body.trainingEnvironment = environment.rawValue }
        if mountainDays != before.mountainDays { body.mountainDays = Weekday.allCases.filter(mountainDays.contains).map(\.rawValue) }
        if trainingMountain != before.trainingMountain { body.trainingMountain = .some(trainingMountain) }
        if mountainMinMinutes != before.mountainMinMinutes { body.mountainMinMinutes = .some(mountainMinMinutes) }
        if stairAccess != before.stairAccess { body.stairAccess = stairAccess }
        if treadmillMaxIncline != before.treadmillMaxIncline { body.treadmillMaxIncline = treadmillMaxIncline }
    }

    var hasChanges: Bool {
        let before = ScheduleDraft(plan: initialPlan)
        return preferredDays != before.preferredDays || longRunDay != before.longRunDay || daysPerWeek != before.daysPerWeek
            || doubleSessionDays != before.doubleSessionDays || hasGymAccess != before.hasGymAccess
            || useTreadmill != before.useTreadmill || environment != before.environment
            || trainingMountain != before.trainingMountain || mountainMinMinutes != before.mountainMinMinutes
            || mountainDays != before.mountainDays || stairAccess != before.stairAccess
            || treadmillMaxIncline != before.treadmillMaxIncline
            || (isGettingStarted && maxContinuousJogMin != before.maxContinuousJogMin)
    }

    func hasHardDayBeforeLongRun(workouts: [Workout]) -> Bool {
        guard let longRunDay else { return false }
        let preceding = (longRunDay.offset + 6) % 7
        return workouts.contains { workout in
            let type = workout.type.lowercased()
            return workout.weekday.offset == preceding && (type == "me" || type.contains("interval") || type.contains("tempo") || type.contains("threshold") || type.contains("hill"))
        }
    }
}

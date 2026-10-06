import Foundation

struct CoachOverviewAthlete: Codable, Sendable, Identifiable, Equatable {
    var id: Int { athleteId }
    let athleteId: Int
    let name: String
    let runnerLevel: String
    let needsAttention: Bool
    let activePlan: CoachAthleteActivePlan?
    let adherencePct: Double?
    let lastCompleted: CoachLastCompletedWorkout?
    let missedStreak: Int

    init(
        athleteId: Int,
        name: String,
        runnerLevel: String = "intermediate",
        needsAttention: Bool = false,
        activePlan: CoachAthleteActivePlan? = nil,
        adherencePct: Double? = nil,
        lastCompleted: CoachLastCompletedWorkout? = nil,
        missedStreak: Int = 0
    ) {
        self.athleteId = athleteId
        self.name = name
        self.runnerLevel = runnerLevel
        self.needsAttention = needsAttention
        self.activePlan = activePlan
        self.adherencePct = adherencePct
        self.lastCompleted = lastCompleted
        self.missedStreak = missedStreak
    }
}

struct CoachAthleteActivePlan: Codable, Sendable, Equatable {
    let planId: Int
    let raceName: String
    let raceDate: String
    let currentWeek: Int
    let totalWeeks: Int

    init(planId: Int, raceName: String, raceDate: String, currentWeek: Int, totalWeeks: Int) {
        self.planId = planId
        self.raceName = raceName
        self.raceDate = raceDate
        self.currentWeek = currentWeek
        self.totalWeeks = totalWeeks
    }
}

struct CoachLastCompletedWorkout: Codable, Sendable, Equatable {
    let weekNumber: Int
    let dayOfWeek: String

    init(weekNumber: Int, dayOfWeek: String) {
        self.weekNumber = weekNumber
        self.dayOfWeek = dayOfWeek
    }
}

struct CoachActionItems: Codable, Sendable, Equatable {
    let draftPlans: [CoachDraftPlanItem]
    let pendingWorkoutApprovals: [CoachPendingApprovalItem]

    init(draftPlans: [CoachDraftPlanItem] = [], pendingWorkoutApprovals: [CoachPendingApprovalItem] = []) {
        self.draftPlans = draftPlans
        self.pendingWorkoutApprovals = pendingWorkoutApprovals
    }
}

struct CoachDraftPlanItem: Codable, Sendable, Identifiable, Equatable {
    var id: Int { planId }
    let planId: Int
    let athleteId: Int
    let athleteName: String
    let raceName: String

    init(planId: Int, athleteId: Int, athleteName: String, raceName: String) {
        self.planId = planId
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.raceName = raceName
    }
}

struct CoachPendingApprovalItem: Codable, Sendable, Identifiable, Equatable {
    var id: Int { workoutId }
    let workoutId: Int
    let planId: Int
    let athleteId: Int
    let athleteName: String
    let title: String

    init(workoutId: Int, planId: Int, athleteId: Int, athleteName: String, title: String) {
        self.workoutId = workoutId
        self.planId = planId
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.title = title
    }
}

struct CoachPhaseAlert: Codable, Sendable, Identifiable, Equatable {
    var id: String { "\(athleteId)-\(phase)-\(starts)" }
    let athleteId: Int
    let athleteName: String
    let phase: String
    let starts: String

    init(athleteId: Int, athleteName: String, phase: String, starts: String) {
        self.athleteId = athleteId
        self.athleteName = athleteName
        self.phase = phase
        self.starts = starts
    }
}

struct WorkoutTypeMixEntry: Codable, Sendable, Identifiable, Equatable {
    var id: String { type }
    let type: String
    let count: Int
    let pct: Double

    init(type: String, count: Int, pct: Double) {
        self.type = type
        self.count = count
        self.pct = pct
    }
}

struct AdherenceTrendEntry: Codable, Sendable, Identifiable, Equatable {
    var id: Int { weekNumber }
    let weekNumber: Int
    let adherencePct: Double

    init(weekNumber: Int, adherencePct: Double) {
        self.weekNumber = weekNumber
        self.adherencePct = adherencePct
    }
}

struct MissedByDayEntry: Codable, Sendable, Identifiable, Equatable {
    var id: String { dayOfWeek }
    let dayOfWeek: String
    let count: Int

    init(dayOfWeek: String, count: Int) {
        self.dayOfWeek = dayOfWeek
        self.count = count
    }
}

struct RaceBreakdownAthlete: Codable, Sendable, Identifiable, Equatable {
    var id: Int { athleteId }
    let athleteId: Int
    let name: String

    init(athleteId: Int, name: String) {
        self.athleteId = athleteId
        self.name = name
    }
}

struct RaceBreakdownEntry: Codable, Sendable, Identifiable, Equatable {
    var id: String { raceName }
    let raceName: String
    let raceDate: String?
    let count: Int
    let athletes: [RaceBreakdownAthlete]

    init(raceName: String, raceDate: String?, count: Int, athletes: [RaceBreakdownAthlete]) {
        self.raceName = raceName
        self.raceDate = raceDate
        self.count = count
        self.athletes = athletes
    }
}

struct CoachRosterTotals: Codable, Sendable, Equatable {
    let distanceKm: Double?
    let durationHours: Double?
    let elevationGainM: Double?
    let workoutCount: Int?

    init(distanceKm: Double? = nil, durationHours: Double? = nil, elevationGainM: Double? = nil, workoutCount: Int? = nil) {
        self.distanceKm = distanceKm
        self.durationHours = durationHours
        self.elevationGainM = elevationGainM
        self.workoutCount = workoutCount
    }
}

struct CoachOverview: Codable, Sendable, Equatable {
    let athletes: [CoachOverviewAthlete]
    let actionItems: CoachActionItems
    let phaseAlerts: [CoachPhaseAlert]
    let workoutTypeMix: [WorkoutTypeMixEntry]
    let adherenceTrend: [AdherenceTrendEntry]
    let missedByDay: [MissedByDayEntry]
    let races: [RaceBreakdownEntry]
    let rosterTotals: CoachRosterTotals?
    let athletesWithoutRace: Int?

    init(
        athletes: [CoachOverviewAthlete] = [],
        actionItems: CoachActionItems = CoachActionItems(),
        phaseAlerts: [CoachPhaseAlert] = [],
        workoutTypeMix: [WorkoutTypeMixEntry] = [],
        adherenceTrend: [AdherenceTrendEntry] = [],
        missedByDay: [MissedByDayEntry] = [],
        races: [RaceBreakdownEntry] = [],
        rosterTotals: CoachRosterTotals? = nil,
        athletesWithoutRace: Int? = 0
    ) {
        self.athletes = athletes
        self.actionItems = actionItems
        self.phaseAlerts = phaseAlerts
        self.workoutTypeMix = workoutTypeMix
        self.adherenceTrend = adherenceTrend
        self.missedByDay = missedByDay
        self.races = races
        self.rosterTotals = rosterTotals
        self.athletesWithoutRace = athletesWithoutRace
    }
}

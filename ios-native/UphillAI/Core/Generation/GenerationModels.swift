import Foundation

enum JobKind: String, Codable, Sendable {
    case newPlan, nextWeek, adaptWeek
}

/// Every job-starting endpoint returns at least `job_id`.
struct JobStart: Decodable, Sendable, Equatable {
    let jobId: String
}

/// POST /api/auth/onboarding: a job when a plan is being built, the user when `skip_plan` was set.
struct OnboardingResult: Decodable, Sendable {
    let jobId: String?
    let user: User?
}

/// GET /api/coach/plan-status/{job_id}
struct JobStatus: Decodable, Sendable {
    let status: String
    let planId: Int?
    let plan: Plan?
    let workouts: [Workout]?
    let error: String?

    var snapshot: PlanSnapshot? {
        guard let plan else { return nil }
        return PlanSnapshot(plan: plan, workouts: workouts ?? [])
    }
}

enum JobOutcome: Equatable, Sendable {
    /// Finished. The snapshot is nil only if the server omitted the plan; reload in that case.
    case done(PlanSnapshot?)
    case failed(String)
    /// The server no longer knows the job (it restarted). Reload the active plan.
    case lost
    case cancelled
}

struct NextBlockBody: Encodable, Sendable {
    let planId: Int
    let blockNumber: Int
    let overallRpe: Int?
    let notes: String?
    let overrideGate: Bool
    let lang: String
}

struct AdaptWeekBody: Encodable, Sendable {
    let planId: Int
    let weekNumber: Int
    let overallRpe: Int?
    let fatigueLevel: String?
    let fatigueNotes: String?
    let lang: String
    let clientToday: String
    var preferredDays: [String]? = nil
    var longRunDay: String? = nil
    var daysPerWeek: Int? = nil
    var doubleSessionDays: [String]? = nil
    var hasGymAccess: Bool? = nil
    var useTreadmill: Bool? = nil
    var trainingEnvironment: String? = nil
    var maxContinuousJogMin: Int? = nil
}

import Foundation

protocol GenerationServicing: Sendable {
    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult
    func generatePlan(_ body: PlanBody) async throws -> JobStart
    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart
    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart
    func status(jobID: String) async throws -> JobStatus
    /// Next-block and adapt-week calls for a coached athlete (nil = the signed-in user).
    func scoped(toAthlete athleteId: Int?) -> any GenerationServicing
}

extension GenerationServicing {
    func scoped(toAthlete athleteId: Int?) -> any GenerationServicing { self }
}

struct GenerationService: GenerationServicing {
    let client: APIClient
    var athleteId: Int? = nil

    func scoped(toAthlete athleteId: Int?) -> any GenerationServicing {
        GenerationService(client: client, athleteId: athleteId)
    }

    private var prefix: String { athleteId.map { "/api/coaching/athletes/\($0)" } ?? "/api/coach" }

    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult {
        try await client.send(.send(.post, "/api/auth/onboarding", body: body))
    }

    func generatePlan(_ body: PlanBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/generate-plan", body: body))
    }

    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart {
        try await client.send(.send(.post, "\(prefix)/generate-next-block", body: body))
    }

    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart {
        try await client.send(.send(.post, "\(prefix)/adapt-week", body: body))
    }

    func status(jobID: String) async throws -> JobStatus {
        try await client.send(.get("/api/coach/plan-status/\(jobID)"))
    }
}

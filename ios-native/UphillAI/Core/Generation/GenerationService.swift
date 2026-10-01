import Foundation

protocol GenerationServicing: Sendable {
    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult
    func generatePlan(_ body: PlanBody) async throws -> JobStart
    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart
    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart
    func status(jobID: String) async throws -> JobStatus
}

struct GenerationService: GenerationServicing {
    let client: APIClient

    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult {
        try await client.send(.send(.post, "/api/auth/onboarding", body: body))
    }

    func generatePlan(_ body: PlanBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/generate-plan", body: body))
    }

    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/generate-next-block", body: body))
    }

    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart {
        try await client.send(.send(.post, "/api/coach/adapt-week", body: body))
    }

    func status(jobID: String) async throws -> JobStatus {
        try await client.send(.get("/api/coach/plan-status/\(jobID)"))
    }
}

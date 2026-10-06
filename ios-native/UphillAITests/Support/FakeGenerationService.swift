import Foundation
import Synchronization
@testable import UphillAI

/// Scriptable GenerationServicing. `statuses` is consumed in order, one per poll;
/// the last element repeats once the script runs out.
final class FakeGenerationService: GenerationServicing {
    let startResult = Mutex<Result<JobStart, APIError>>(.success(JobStart(jobId: "job-1")))
    let onboardingResult = Mutex<Result<OnboardingResult, APIError>>(.success(OnboardingResult(jobId: "job-1", user: nil)))
    let statuses = Mutex<[Result<JobStatus, APIError>]>([])
    let calls = Mutex<[String]>([])

    private func record(_ call: String) { calls.withLock { $0.append(call) } }

    func completeOnboarding(_ body: OnboardingBody) async throws -> OnboardingResult {
        record("onboarding skip=\(body.skipPlan)")
        return try onboardingResult.withLock { $0 }.get()
    }

    func generatePlan(_ body: PlanBody) async throws -> JobStart {
        record("generate \(body.goalType)")
        return try startResult.withLock { $0 }.get()
    }

    func generateNextBlock(_ body: NextBlockBody) async throws -> JobStart {
        record("next \(body.blockNumber) override=\(body.overrideGate)")
        return try startResult.withLock { $0 }.get()
    }

    func adaptWeek(_ body: AdaptWeekBody) async throws -> JobStart {
        record("adapt \(body.weekNumber) \(body.fatigueLevel ?? "-")")
        return try startResult.withLock { $0 }.get()
    }

    func status(jobID: String) async throws -> JobStatus {
        record("status \(jobID)")
        let next: Result<JobStatus, APIError> = statuses.withLock { list in
            if list.count > 1 { return list.removeFirst() }
            return list.first ?? .failure(.http(status: 404, message: "Job not found.", code: nil))
        }
        return try next.get()
    }
}

extension JobStatus {
    static func generating() -> JobStatus {
        try! JSONCoding.decoder.decode(JobStatus.self, from: json(["status": "generating", "plan_id": 7]))
    }

    static func done(_ snapshot: PlanSnapshot?) -> JobStatus {
        var object: [String: Any] = ["status": "done", "plan_id": snapshot?.plan.id ?? 7]
        if let snapshot {
            object["plan"] = try! JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(snapshot.plan))
            object["workouts"] = try! JSONSerialization.jsonObject(with: JSONCoding.encoder.encode(snapshot.workouts))
        }
        return try! JSONCoding.decoder.decode(JobStatus.self, from: json(object))
    }

    static func error(_ message: String?) -> JobStatus {
        var object: [String: Any] = ["status": "error", "plan_id": 7]
        if let message { object["error"] = message }
        return try! JSONCoding.decoder.decode(JobStatus.self, from: json(object))
    }
}

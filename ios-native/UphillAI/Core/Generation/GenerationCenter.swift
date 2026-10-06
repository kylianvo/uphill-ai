import Foundation
import Observation

@Observable
@MainActor
final class GenerationCenter {
    struct Running: Codable, Equatable {
        let kind: JobKind
        let jobID: String
        let startedAt: Date
        let summary: [String]
    }

    struct Finished: Equatable {
        let kind: JobKind
        let outcome: JobOutcome
    }

    static let defaultsKey = "UPHILL_RUNNING_JOB"

    private(set) var running: Running?
    private(set) var lastOutcome: Finished?
    var onFinished: (@MainActor (JobKind, JobOutcome) async -> Void)?

    private let service: any GenerationServicing
    private let defaults: UserDefaults
    private let makePoller: (any GenerationServicing) -> JobPoller
    private let now: () -> Date
    private var task: Task<Void, Never>?

    init(service: any GenerationServicing,
         defaults: UserDefaults = .standard,
         makePoller: @escaping (any GenerationServicing) -> JobPoller = { JobPoller(service: $0) },
         now: @escaping () -> Date = { .now }) {
        self.service = service
        self.defaults = defaults
        self.makePoller = makePoller
        self.now = now
    }

    func track(kind: JobKind, jobID: String, summary: [String]) {
        start(Running(kind: kind, jobID: jobID, startedAt: now(), summary: summary))
    }

    func resumeIfNeeded() {
        guard running == nil,
              let data = defaults.data(forKey: Self.defaultsKey),
              let saved = try? JSONDecoder().decode(Running.self, from: data) else { return }
        start(saved)
    }

    func clearOutcome() { lastOutcome = nil }

    /// Sign-out discards the previous athlete's job and cancels local polling.
    func reset() {
        task?.cancel()
        task = nil
        running = nil
        lastOutcome = nil
        defaults.removeObject(forKey: Self.defaultsKey)
    }

    private func start(_ job: Running) {
        task?.cancel()
        running = job
        lastOutcome = nil
        defaults.set(try? JSONEncoder().encode(job), forKey: Self.defaultsKey)
        let poller = makePoller(service)
        task = Task { [weak self] in
            let outcome = await poller.wait(jobID: job.jobID)
            guard let self, !Task.isCancelled, outcome != .cancelled else { return }
            await self.finish(job, outcome)
        }
    }

    private func finish(_ job: Running, _ outcome: JobOutcome) async {
        guard running?.jobID == job.jobID else { return }
        await onFinished?(job.kind, outcome)
        guard !Task.isCancelled, running?.jobID == job.jobID else { return }
        defaults.removeObject(forKey: Self.defaultsKey)
        running = nil
        lastOutcome = Finished(kind: job.kind, outcome: outcome)
    }
}

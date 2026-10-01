import Foundation

struct JobPoller: Sendable {
    static let slowMessage = "This is taking longer than usual. Your plan may still appear: pull down on the Plan tab in a minute to check."
    static let offlineMessage = "Lost connection while building your plan. It may still finish: pull down on the Plan tab to check."
    private static let defaultError = "We couldn't build this plan. Please try again."

    let service: any GenerationServicing
    let interval: Duration
    let timeout: Duration
    let sleep: @Sendable (Duration) async throws -> Void

    init(service: any GenerationServicing,
         interval: Duration = .seconds(2),
         timeout: Duration = .seconds(240),
         sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.service = service
        self.interval = interval
        self.timeout = timeout
        self.sleep = sleep
    }

    func wait(jobID: String) async -> JobOutcome {
        let attempts = max(1, Int(timeout / interval))
        var transportFailures = 0
        for attempt in 0..<attempts {
            if Task.isCancelled { return .cancelled }
            do {
                let status = try await service.status(jobID: jobID)
                transportFailures = 0
                switch status.status {
                case "done": return .done(status.snapshot)
                case "error": return .failed(status.error ?? Self.defaultError)
                default: break
                }
            } catch APIError.http(404, _, _) {
                return .lost
            } catch APIError.transport {
                transportFailures += 1
                if transportFailures >= 5 { return .failed(Self.offlineMessage) }
            } catch let error as APIError {
                return .failed(error.userMessage)
            } catch {
                return .failed(error.localizedDescription)
            }
            if attempt < attempts - 1 {
                do { try await sleep(interval) } catch { return .cancelled }
            }
        }
        return .failed(Self.slowMessage)
    }
}

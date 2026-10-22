import Foundation
import Testing
@testable import UphillAI

struct ProgressDecodingTests {
    @Test func decodesHealthSection() throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_health.json")
        #expect(response.cards.map(\.key) == ["coach_read", "sleep", "resting_hr", "hrv"])
        let sleep = try #require(response.card("sleep"))
        #expect(sleep.unit == "min")
        #expect(sleep.band?.count == 2)
        #expect(sleep.noteKey == "sleep.within")
        #expect(sleep.points.count == 28)
        #expect(sleep.source == "coros")
    }

    @Test func decodesTrainingSection() throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_training.json")
        #expect(response.cards.map(\.key) == ["durability", "load"])
        #expect(response.card("durability")?.points.count == 3)
    }

    @Test func decodesEmptyResponseWithPending() throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_empty.json")
        #expect(response.cards.isEmpty)
        #expect(!response.connected && !response.hasPlan)
        #expect(response.pending == [ProgressPending(key: "sleep", needs: 7, have: 0)])
    }
}

private actor StubProgressService: ProgressServicing {
    var result: Result<ProgressResponse, Error>
    private(set) var requests: [(ProgressSection, Int)] = []
    init(_ result: Result<ProgressResponse, Error>) { self.result = result }
    func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse {
        requests.append((section, days))
        return try result.get()
    }
}

@MainActor
struct ProgressViewModelTests {
    @Test func loadSetsLoaded() async throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_health.json")
        let service = StubProgressService(.success(response))
        let model = ProgressViewModel(service: service)
        await model.load()
        #expect(model.state == .loaded)
        #expect(model.response?.cards.count == 4)
    }

    @Test func errorSetsFailed() async {
        let model = ProgressViewModel(service: StubProgressService(.failure(URLError(.notConnectedToInternet))))
        await model.load()
        if case .failed = model.state {} else { Issue.record("expected failed, got \(model.state)") }
    }

    @Test func switchingSectionRequestsThatSection() async throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_training.json")
        let service = StubProgressService(.success(response))
        let model = ProgressViewModel(service: service)
        await model.select(.training)
        let requests = await service.requests
        #expect(requests.last?.0 == .training && requests.last?.1 == 28)
    }

    @Test func serviceHitsProgressEndpoint() async throws {
        let fixture = try Fixture.data("progress_health.json")
        let service = ProgressService(client: makeStubClient { request in
            #expect(request.url?.path() == "/api/progress")
            #expect(request.url?.query()?.contains("section=health") == true)
            #expect(request.url?.query()?.contains("days=90") == true)
            let c = Calendar.current.dateComponents([.year, .month, .day], from: Date())
            let localDay = String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
            #expect(request.url?.query()?.contains("client_today=\(localDay)") == true)
            return (200, fixture)
        })
        let response = try await service.progress(section: .health, days: 90)
        #expect(response.section == "health")
    }
}

@MainActor
struct ProgressResetTests {
    @Test func resetClearsTheAthletesData() async throws {
        let response = try Fixture.decode(ProgressResponse.self, "progress_health.json")
        let model = ProgressViewModel(service: StubProgressService(.success(response)))
        await model.select(.health)
        model.reset()
        #expect(model.response == nil && model.section == .training && model.state == .loading)
    }
}

/// Holds every request until `release()`, so a test can sign out while a load is in flight.
private actor GatedProgressService: ProgressServicing {
    let response: ProgressResponse
    private var waiters: [CheckedContinuation<Void, Never>] = []
    init(_ response: ProgressResponse) { self.response = response }
    func progress(section: ProgressSection, days: Int) async throws -> ProgressResponse {
        await withCheckedContinuation { waiters.append($0) }
        return response
    }
    func release() { waiters.forEach { $0.resume() }; waiters = [] }
    var waiting: Int { waiters.count }
}

@MainActor
struct ProgressSignOutRaceTests {
    @Test func aLoadFinishingAfterResetIsDiscarded() async throws {
        let service = GatedProgressService(try Fixture.decode(ProgressResponse.self, "progress_health.json"))
        let model = ProgressViewModel(service: service)
        let load = Task { await model.load() }
        while await service.waiting == 0 { await Task.yield() }
        model.reset()
        await service.release()
        await load.value
        #expect(model.response == nil)
        #expect(model.state == .loading)
    }
}

struct ProgressSnakeKeyTests {
    /// Dictionary keys inside series/note keep the backend's snake_case (only struct keys are converted).
    @Test func readsSnakeCaseKeysInsideSeriesAndNote() throws {
        let json = """
        {"key": "consistency", "value": 75, "unit": "%", "series": [{"week": 1, "km": 40, "km_planned": 45}],
         "band": null, "note": {"key": "consistency", "pct": 75, "top_missed_reason": "busy"}, "as_of": null, "source": null}
        """
        let card = try JSONCoding.decoder.decode(ProgressCard.self, from: Data(json.utf8))
        #expect(ProgressText.note(card) == L("Most missed because: %@", L("busy")))
        let next: [String: JSONValue] = ["title": .string("Tempo"), "date": .string("2026-10-23"), "duration_minutes": .int(60)]
        #expect(ProgressText.nextSession(next)?.hasSuffix(L("%lld min", 60)) == true)
    }
}

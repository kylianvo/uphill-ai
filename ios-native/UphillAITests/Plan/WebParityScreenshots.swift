import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Opt-in captures: set SCREENSHOT_DIR or touch docs/screenshots/web-parity/.capture-enabled before running.
@MainActor
@Suite(.serialized)
struct WebParityScreenshots {
    private var outDir: String {
        if let configured = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"] { return configured }
        let local = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("docs/screenshots/web-parity").path
        return FileManager.default.fileExists(atPath: local + "/.capture-enabled") ? local : ""
    }

    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        return c
    }()
    private var now: Date { cal.date(from: DateComponents(year: 2026, month: 10, day: 7, hour: 9))! }

    /// Renders after letting the view's `.task`s finish against the fakes.
    private func save<V: View>(_ view: V, name: String, height: CGFloat = 874) async throws {
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        try? await Task.sleep(for: .milliseconds(900))
        controller.view.layoutIfNeeded()
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let image = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try FileManager.default.createDirectory(atPath: outDir, withIntermediateDirectories: true)
        try #require(image.pngData()).write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    private func snapshot(matched: Bool) -> PlanSnapshot {
        let plan = TestData.plan(["id": 7, "start_date": "2026-09-28", "total_weeks": 12, "race_date": "2026-12-19",
                                  "race_name": "Vietnam Mountain Marathon 70K", "course_distance_km": 70])
        var tuesday: [String: Any] = ["id": 1, "plan_id": 7, "week_number": 2, "day_of_week": "Tuesday",
                                      "type": "Easy Run", "title": "Easy aerobic run", "duration_minutes": 50, "distance_km": 9,
                                      "approved_at": "2026-10-01T09:00:00"]
        if matched { tuesday["matched_activity_id"] = 555 }
        var workouts = [TestData.workout(tuesday)]
        for (i, day) in ["Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].enumerated() {
            workouts.append(TestData.workout(["id": 10 + i, "plan_id": 7, "week_number": 2, "day_of_week": day,
                                              "type": "Easy Run", "duration_minutes": 40]))
        }
        var snap = PlanSnapshot(plan: plan, workouts: workouts)
        if matched {
            snap.workouts[0].matchedDistanceKm = 9.3
            snap.workouts[0].matchedDurationSeconds = 3060
            snap.workouts[0].matchedAvgHr = 138
            snap.workouts[0].matchedDeviceModel = "COROS PACE 3"
        }
        return snap
    }

    private func model(_ service: FakePlanService, athlete: Int? = nil) async -> PlanViewModel {
        let now = self.now
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { now }, calendar: cal)
        if let athlete { await model.setAthleteScope(athlete) } else { await model.load() }
        return model
    }

    private var evaluation: BlockEvaluation {
        BlockEvaluation(blockNumber: 1, sessionsTotal: 10, sessionsCompleted: 8, sessionsMissed: 2, completionPct: 80,
                        plannedKm: 62, actualKm: 51.4, avgQualityScore: 84, qualityGrade: "B",
                        coachingTakeaways: ["Easy runs stayed in Zone 2 on the climbs."],
                        coachSummary: "Good consistency across Block 1. Keep the long run easy.",
                        coachNotes: ["Hold the long run at 2h next block."])
    }

    private let offer = NextWeekOffer(blockNumber: 2, weekStart: 3, weekEnd: 4, previousCompletionPct: 80, unlocked: true)

    @Test func captures() async throws {
        guard !outDir.isEmpty else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let suffix = lang == .en ? "en" : "vi"

            let service = FakePlanService()
            service.activeResult.withLock { $0 = .success(snapshot(matched: true)) }
            service.evaluationResult.withLock { $0 = .success(evaluation) }
            service.watchActivitiesResult.withLock {
                $0 = .success([
                    WatchActivity(activityId: 555, workoutId: 1, workoutTitle: "Easy aerobic run", distanceKm: 9.3,
                                  durationSeconds: 3060, avgHr: 138, startTime: "2026-10-06T06:10:00", deviceModel: nil, matchMethod: "auto"),
                    WatchActivity(activityId: 556, workoutId: nil, workoutTitle: nil, distanceKm: 4.1,
                                  durationSeconds: 1500, avgHr: 129, startTime: "2026-10-06T17:40:00", deviceModel: nil, matchMethod: nil),
                    WatchActivity(activityId: 557, workoutId: 10, workoutTitle: "Easy Run", distanceKm: 8.0,
                                  durationSeconds: 2820, avgHr: 141, startTime: "2026-10-05T06:00:00", deviceModel: nil, matchMethod: "suggest"),
                ])
            }
            let own = await model(service)
            let locale = lang.locale

            try await save(NextWeekSheet(model: own, offer: offer).environment(\.locale, locale), name: "next-block-evaluation-\(suffix)", height: 1200)
            try await save(WorkoutDetailSheet(model: own, workoutID: 1, deviceService: StubDevices()).environment(\.locale, locale),
                       name: "workout-wrong-run-\(suffix)")
            try await save(WatchMatchSheet(model: own, workout: own.snapshot!.workouts[0]).environment(\.locale, locale),
                       name: "watch-match-picker-\(suffix)")

            let coachService = FakePlanService()
            coachService.activeResult.withLock { $0 = .success(snapshot(matched: false)) }
            coachService.evaluationResult.withLock { $0 = .success(evaluation) }
            let coach = await model(coachService, athlete: 42)
            try await save(NextWeekSheet(model: coach, offer: offer).environment(\.locale, locale), name: "coach-next-block-\(suffix)", height: 1100)

            coachService.recentResult.withLock { $0 = .success([coach.snapshot!.plan, TestData.plan(["id": 8, "race_name": "Previous Race"])]) }
            try await save(ManagePlanSheet(model: coach, onStartNew: {}).environment(\.locale, locale),
                           name: "coach-manage-\(suffix)")
            try await save(WorkoutDetailSheet(model: coach, workoutID: 1).environment(\.locale, locale),
                           name: "coach-workout-\(suffix)", height: 1000)

            service.watchActivitiesResult.withLock { $0 = .success([]) }
            try await save(WatchMatchSheet(model: own, workout: own.snapshot!.workouts[0]).environment(\.locale, locale),
                           name: "watch-match-empty-\(suffix)")
            service.watchActivitiesResult.withLock { $0 = .failure(.transport("offline")) }
            try await save(WatchMatchSheet(model: own, workout: own.snapshot!.workouts[0]).environment(\.locale, locale),
                           name: "watch-match-failed-\(suffix)")

            try await save(PaceStrategySheet(service: StubPacing(), activePlan: own.snapshot?.plan).environment(\.locale, locale),
                       name: "pace-benchmarks-\(suffix)", height: 1400)
        }
    }
}

private struct StubPacing: PacingServicing {
    func calculatePacing(request: PacingRequest) async throws -> [PacedCheckpoint] {
        PacingCalculator.calculateCheckpointPaces(checkpoints: request.checkpoints, targetTimeMins: request.targetTimeMins,
                                                  targetFlatPaceMinKm: request.targetFlatPaceMinKm,
                                                  splitBias: request.splitBias ?? 0, runnerWeightKg: request.runnerWeightKg ?? 68)
    }
    func benchmarks(raceName: String, distanceKm: Double) async -> [RaceBenchmark] {
        [
            RaceBenchmark(year: 2025, finishers: 412, winnerTime: "7:41:00", winnerTimeWomen: "9:02:00",
                          percentiles: ["overall": PercentileSet(p25: "13:10:00", p50: "15:05:00", p75: "16:40:00")]),
            RaceBenchmark(year: 2024, finishers: 380, winnerTime: "7:55:00",
                          percentiles: ["overall": PercentileSet(p25: "13:30:00", p50: "15:20:00", p75: "16:55:00")]),
        ]
    }
}

private struct StubDevices: DeviceConnectionServicing {
    struct Unused: Error {}
    func fetchStatus() async throws -> DeviceConnectionStatus { throw Unused() }
    func connectCorosURL() async throws -> URL { throw Unused() }
    func completeCoros(state: String, token: String) async throws -> Bool { false }
    func syncNow(days: Int) async throws -> DeviceSyncResult { throw Unused() }
    func syncFitness() async throws -> FitnessSyncResult { throw Unused() }
    func disconnectCoros() async throws {}
    func fetchPushStatus(clientToday: String) async throws -> CorosPushStatus { throw Unused() }
    func pushToCoros(clientToday: String, lang: String) async throws -> CorosPushOutcome { throw Unused() }
}

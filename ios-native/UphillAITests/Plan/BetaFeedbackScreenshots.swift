import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct BetaFeedbackScreenshots {
    private let outDir: String = {
        if let dir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"], !dir.isEmpty {
            return dir
        }
        return "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/beta-feedback-1"
    }()

    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        c.locale = Locale(identifier: "en_US_POSIX")
        return c
    }()

    private var now: Date {
        cal.date(from: DateComponents(year: 2026, month: 10, day: 7, hour: 9, minute: 0))!
    }

    private func save<V: View>(_ view: V, name: String, size: CGSize = CGSize(width: 402, height: 874), scale: CGFloat = 2.0) {
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        controller.view.bounds = CGRect(origin: .zero, size: size)
        controller.view.backgroundColor = .systemBackground

        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()

        let format = UIGraphicsImageRendererFormat()
        format.scale = scale
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let img = renderer.image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        let dirUrl = URL(fileURLWithPath: outDir)
        try? FileManager.default.createDirectory(at: dirUrl, withIntermediateDirectories: true)
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        try? img.pngData()?.write(to: url)
    }

    private func makeFixturePlan() -> (PlanViewModel, Workout, Workout) {
        let plan = TestData.plan([
            "id": 101,
            "race_name": "Snowdonia Trail 50K",
            "race_date": "2026-12-19",
            "goal_type": "finish",
            "current_week": 1,
            "total_weeks": 8
        ])

        let trailRun = TestData.workout([
            "id": 1001,
            "plan_id": 101,
            "week_number": 1,
            "day_of_week": "Wednesday",
            "phase": "Build",
            "title": "Aerobic Build Run",
            "type": "Long Run",
            "duration_minutes": 75.0,
            "distance_km": 14.0,
            "target_zone": "Z2",
            "target_pace": "5:30-5:45",
            "elevation_gain_m": 320.0,
            "fueling_tip": "Aim for 60g carbs/hr. Drink electrolyte mix every 20 minutes to maintain hydration.",
            "description": """
Overall: A key aerobic endurance session to build continuous pacing discipline on rolling terrain.
Reason: Builds aerobic threshold and mitochondrial density for mountain ultras.
Benefit: Develops fatigue resistance while keeping muscle damage minimal.
Warning: Keep effort strictly in Zone 2 on all uphills; hike immediately if HR spikes over 152 bpm.

Warm-up: 10 mins easy jog at conversational pace.
Main set: 55 mins steady Zone 2 effort on rolling trails.
Cool-down: 10 mins relaxed jog and walk.
""",
            "is_completed": 0,
            "is_priority": true
        ])

        let strengthSession = TestData.workout([
            "id": 1002,
            "plan_id": 101,
            "week_number": 1,
            "day_of_week": "Friday",
            "phase": "Build",
            "title": "Mountain Strength & Core",
            "type": "Strength",
            "duration_minutes": 45.0,
            "distance_km": 0.0,
            "target_pace": "",
            "fueling_tip": "Pre-session protein and carb snack. Hydrate with water.",
            "description": """
Overall: Functional eccentric strength session targeting quad and calf resilience for steep descents.
Reason: Protects knees and reduces eccentric muscle breakdown on trail downhill sections.
Benefit: Increases joint stability and reduces late-race neuromuscular fatigue.
Warning: Focus on slow, controlled eccentric movements. Do not sacrifice form for heavier weight.

Warm-up: 5 mins mobility and glute bridges.
Main set: 35 mins circuit: goblet squats, Bulgarian split squats, calf raises, side planks.
Cool-down: 5 mins light stretching.
""",
            "is_completed": 0
        ])

        let week3Run = TestData.workout([
            "id": 1003,
            "plan_id": 101,
            "week_number": 3,
            "day_of_week": "Tuesday",
            "phase": "Build",
            "title": "Tempo Progression Run",
            "type": "Tempo",
            "duration_minutes": 60.0,
            "distance_km": 11.5,
            "target_zone": "Z3",
            "target_pace": "5:00-5:15",
            "is_completed": 0,
            "is_priority": true
        ])

        let fake = FakePlanService()
        let block1 = BlockCompletion(
            blockNumber: 1,
            weekStart: 1,
            weekEnd: 2,
            completionPct: 88,
            unlocked: true,
            aiLastWeekReview: "Strong aerobic consistency across your long run. Zone 2 discipline was well controlled.",
            aiThisWeekDescription: "Prioritize controlled climbing pace and focus on timely fueling during Wednesday's endurance build."
        )
        let block2 = BlockCompletion(
            blockNumber: 2,
            weekStart: 3,
            weekEnd: 4,
            completionPct: 75,
            unlocked: true,
            aiLastWeekReview: "Consistent foundation in block 1. Aerobic base is solidifying.",
            aiThisWeekDescription: "Week 3 focus: sustain tempo intervals and dial in your nutrition strategy."
        )
        let blockResp = BlockCompletionResponse(blocks: [block1, block2], maxGeneratedWeek: 6)

        let snapshot = PlanSnapshot(plan: plan, workouts: [trailRun, strengthSession, week3Run])
        fake.activeResult.withLock { $0 = .success(snapshot) }
        fake.completionResult.withLock { $0 = .success(blockResp) }

        let vm = PlanViewModel(service: fake, cache: .inMemory())
        return (vm, trailRun, strengthSession)
    }

    @Test func generateAllBetaFeedbackScreenshots() async {
        let (model, trailRun, strengthSession) = makeFixturePlan()
        await model.load()

        let stubClient = makeStubClient { request in
            if request.url?.path().contains("coros") == true {
                return (200, json(["connected": true, "email": "athlete@coros.com", "last_synced_at": "2026-10-06T12:00:00Z"]))
            }
            return (200, json([:]))
        }

        let genService = FakeGenerationService()
        let gen = GenerationCenter(service: genService, defaults: UserDefaults(suiteName: UUID().uuidString)!)

        // 1. Task 1: Tools opened without crashing
        let gearService = GearService(client: stubClient)
        let gearVault = GearVaultSheet(service: gearService, activePlan: model.snapshot?.plan, user: nil, isPresentedInSheet: false)
        save(gearVault, name: "task1-gear-vault-pushed")

        let nutritionService = NutritionService(client: stubClient)
        let nutritionLab = NutritionLabSheet(service: nutritionService, activePlan: model.snapshot?.plan, user: nil, isPresentedInSheet: false)
        save(nutritionLab, name: "task1-nutrition-lab-pushed")

        let goalService = GoalEstimateService(client: stubClient)
        let goalDeterminer = GoalDeterminerSheet(service: goalService, activePlan: model.snapshot?.plan, user: nil, isPresentedInSheet: false)
        save(goalDeterminer, name: "task1-goal-determiner-pushed")

        // 2. Task 2: Forced light appearance when system appearance is dark
        let planDarkForcedLight = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: true)
            .preferredColorScheme(.light)
            .environment(\.colorScheme, .dark)
        save(planDarkForcedLight, name: "task2-forced-light-in-dark-mode")

        // 3. Task 3: Workout detail format (About this session, Caution, Fueling tip, 5-level feeling, Send to COROS)
        let devService = DeviceConnectionService(client: stubClient)
        let workoutDetail = WorkoutDetailSheet(
            model: model,
            workoutID: trailRun.id,
            deviceService: devService,
            initialRpe: 6,
            initialNotes: "Felt smooth on the hills, nutrition on point."
        )
        save(workoutDetail, name: "task3-workout-detail-parsed-sections")

        // 3b. Task 3: Strength session showing calm "—" for pace & distance
        let strengthDetail = WorkoutDetailSheet(
            model: model,
            workoutID: strengthSession.id,
            deviceService: devService,
            initialRpe: 8
        )
        save(strengthDetail, name: "task3-workout-detail-strength-no-pace")

        // 4. Task 4: Plan screen with Coach Review takeaways ("THIS WEEK FOCUS" / "LAST WEEK REVIEW") & "Adapt Week 1"
        let planCoachReview = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: true)
        save(planCoachReview, name: "task4-plan-coach-review-takeaways")

        // 4b. Task 4: Coach's Review on a non-final week (Week 3 of 6 generated weeks)
        model.selectedWeek = 3
        let planWeek3Review = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: true)
        save(planWeek3Review, name: "task4-coach-review-non-final-week3")

        // 4c. Task 4: Week 7 ungenerated week CTA (replacing fake rest days)
        model.selectedWeek = 7
        let planWeek7CTA = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: false)
        save(planWeek7CTA, name: "task4-plan-week7-ungenerated-cta")
        model.selectedWeek = 1

        // 5. Task 5: Manage Plan sheet with real watch connection state & COROS push button
        let managePlan = ManagePlanSheet(
            model: model,
            deviceService: devService,
            onStartNew: {},
            onSchedule: {},
            onTool: { _ in }
        )
        save(managePlan, name: "task5-manage-plan-coros-sync-and-push")
    }
}

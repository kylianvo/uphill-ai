import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct PlanRedesignScreenshots {
    private let outDir = "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/plan-redesign"

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
        let url = URL(fileURLWithPath: "\(outDir)/\(name).png")
        try? img.pngData()?.write(to: url)
    }

    private func makeFixturePlan() -> (PlanViewModel, [Workout]) {
        let plan = TestData.plan([
            "id": 101,
            "race_name": "Snowdonia Trail 50K",
            "race_date": "2026-12-19",
            "goal_type": "finish",
            "total_weeks": 12,
            "current_week": 2,
            "start_date": "2026-09-28",
            "plan_status": "active"
        ])

        let descIntervals = """
Warm-up: 15 min easy jogging in Z1-Z2
Main set: 6 x 3 min uphill repeats at Z4 with 2 min easy jog recovery
Cool-down: 10 min easy jog in Z1

Coach Uphill note:
Drive your knees and keep your torso tall on each climb.

What it builds:
Develops aerobic power, high-end lactate clearance, and muscular stamina for sustained mountain climbs.

Common mistake:
Surging too hard on the first two reps and blowing up before rep 5. Keep effort metered.
"""

        let descEasy = """
Warm-up: 5 min gentle walk-jog
Main set: 40 min continuous easy running in Zone 2
Cool-down: 5 min walking

Coach Uphill note:
Keep it strictly conversational. If breathing gets heavy, ease the pace.

What it builds:
Aerobic base and mitochondrial density while keeping neuromuscular stress minimal.

Common mistake:
Creeping into Zone 3 on small rollers. Check your heart rate frequently.
"""

        let descLong = """
Warm-up: 15 min progressive warm-up into Z2
Main set: 100 min steady endurance on rolling trails
Cool-down: 5 min easy walk

Coach Uphill note:
Practice fueling every 30 minutes with 40g carbs and 300ml fluids.

What it builds:
Fat oxidation efficiency, joint resilience, and race-day pacing discipline.

Common mistake:
Neglecting hydration and caloric intake during the middle hour.
"""

        let descStrength = """
Warm-up: 5 min dynamic mobility
Main set: 4 sets of 12 Bulgarian split squats, 15 step-ups per leg with pack, and 30s calf raises
Cool-down: 5 min foam rolling

Coach Uphill note:
Control the eccentric phase. Focus on glute and quad stability.

What it builds:
Muscular endurance and knee stabilization for steep technical descents.

Common mistake:
Rushing through reps without full range of motion.
"""

        let wMonRest = TestData.workout(["id": 1, "week_number": 2, "day_of_week": "Monday", "type": "Rest", "duration_minutes": 0, "title": "Rest Day"])
        let wTueEasy = TestData.workout(["id": 2, "week_number": 2, "day_of_week": "Tuesday", "type": "Easy Run", "duration_minutes": 45.0, "distance_km": 7.5, "target_zone": "Z2", "title": "Aerobic Maintenance Run", "description": descEasy])
        let wWedIntervals = TestData.workout(["id": 3, "week_number": 2, "day_of_week": "Wednesday", "type": "Intervals", "duration_minutes": 60.0, "distance_km": 9.0, "target_zone": "Z4", "elevation_gain_m": 250.0, "is_priority": true, "title": "Hill Repeats 6x3m", "description": descIntervals])
        let wThuMorn = TestData.workout(["id": 4, "week_number": 2, "day_of_week": "Thursday", "type": "Easy Run", "duration_minutes": 35.0, "distance_km": 5.2, "target_zone": "Z2", "session_slot": "morning", "title": "Morning Recovery Jog", "description": descEasy])
        let wThuAft = TestData.workout(["id": 5, "week_number": 2, "day_of_week": "Thursday", "type": "Strength", "duration_minutes": 40.0, "distance_km": 0.0, "target_zone": "Z1", "session_slot": "afternoon", "title": "Mountain Muscular Endurance", "description": descStrength])
        let wFriRest = TestData.workout(["id": 6, "week_number": 2, "day_of_week": "Friday", "type": "Rest", "duration_minutes": 0, "title": "Rest Day"])
        let wSatLong = TestData.workout(["id": 7, "week_number": 2, "day_of_week": "Saturday", "type": "Long Run", "duration_minutes": 120.0, "distance_km": 20.0, "target_zone": "Z2", "elevation_gain_m": 500.0, "is_priority": true, "title": "Mountain Ridge Long Run", "description": descLong])
        let wSunRec = TestData.workout(["id": 8, "week_number": 2, "day_of_week": "Sunday", "type": "Recovery", "duration_minutes": 30.0, "distance_km": 4.5, "target_zone": "Z1", "title": "Flush Out Jog", "description": descEasy])

        // Completed workout with RPE and notes
        let wDoneRpe = TestData.workout(["id": 9, "week_number": 2, "day_of_week": "Wednesday", "type": "Intervals", "duration_minutes": 60.0, "distance_km": 9.2, "target_zone": "Z4", "elevation_gain_m": 260.0, "title": "Hill Repeats 6x3m", "description": descIntervals, "is_completed": 1, "rpe": 7, "notes": "Legs felt responsive on the climbs. Maintained target cadence throughout reps 4-6."])

        // Missed workout
        let wMissed = TestData.workout(["id": 10, "week_number": 2, "day_of_week": "Tuesday", "type": "Easy Run", "duration_minutes": 45.0, "distance_km": 7.5, "target_zone": "Z2", "title": "Aerobic Maintenance Run", "description": descEasy, "is_missed": 1])

        // COROS synced workout
        let wCorosMatched = TestData.workout([
            "id": 11,
            "week_number": 2,
            "day_of_week": "Tuesday",
            "type": "Easy Run",
            "duration_minutes": 50.0,
            "distance_km": 10.0,
            "target_zone": "Z2",
            "target_pace": "5:15 /km",
            "target_hr_range": "135-148 bpm",
            "title": "Aerobic Base Run",
            "description": descEasy,
            "is_completed": 1,
            "matched_activity_id": 9842,
            "matched_device_model": "COROS APEX 2 Pro",
            "matched_distance_km": 10.24,
            "matched_duration_seconds": 3134.0,
            "matched_avg_hr": 142
        ])

        // Additional weeks for multi-week trend progression
        let wW1 = [
            TestData.workout(["id": 101, "week_number": 1, "day_of_week": "Tuesday", "type": "Easy Run", "duration_minutes": 50.0, "distance_km": 8.0, "is_completed": 1]),
            TestData.workout(["id": 102, "week_number": 1, "day_of_week": "Thursday", "type": "Tempo", "duration_minutes": 55.0, "distance_km": 9.5, "is_completed": 1]),
            TestData.workout(["id": 103, "week_number": 1, "day_of_week": "Saturday", "type": "Long Run", "duration_minutes": 110.0, "distance_km": 18.0, "is_completed": 1])
        ]
        let wW3 = [
            TestData.workout(["id": 104, "week_number": 3, "day_of_week": "Tuesday", "type": "Easy Run", "duration_minutes": 55.0, "distance_km": 9.0]),
            TestData.workout(["id": 105, "week_number": 3, "day_of_week": "Wednesday", "type": "Intervals", "duration_minutes": 65.0, "distance_km": 10.5]),
            TestData.workout(["id": 106, "week_number": 3, "day_of_week": "Saturday", "type": "Long Run", "duration_minutes": 130.0, "distance_km": 22.0])
        ]
        let wW4 = [
            TestData.workout(["id": 107, "week_number": 4, "day_of_week": "Tuesday", "type": "Recovery", "duration_minutes": 40.0, "distance_km": 6.0]),
            TestData.workout(["id": 108, "week_number": 4, "day_of_week": "Thursday", "type": "Easy Run", "duration_minutes": 45.0, "distance_km": 7.0]),
            TestData.workout(["id": 109, "week_number": 4, "day_of_week": "Saturday", "type": "Long Run", "duration_minutes": 90.0, "distance_km": 14.0])
        ]

        let allWorkouts = [wMonRest, wTueEasy, wWedIntervals, wThuMorn, wThuAft, wFriRest, wSatLong, wSunRec, wDoneRpe, wMissed, wCorosMatched] + wW1 + wW3 + wW4

        let service = FakePlanService()
        let snapshot = PlanSnapshot(plan: plan, workouts: allWorkouts)
        service.activeResult.withLock { $0 = .success(snapshot) }
        service.recentResult.withLock { $0 = .success([
            plan,
            TestData.plan(["id": 99, "race_name": "UTMB OCC 55K", "race_date": "2026-08-28", "total_weeks": 16, "plan_status": "archived"])
        ])}

        let model = PlanViewModel(service: service, cache: .inMemory(), now: { [now] in now }, calendar: cal)
        return (model, allWorkouts)
    }

    @Test func generateAllPlanRedesignScreenshots() async {
        let (model, allWorkouts) = makeFixturePlan()
        await model.load()

        let genService = FakeGenerationService()
        let gen = GenerationCenter(service: genService, defaults: UserDefaults(suiteName: UUID().uuidString)!)

        // 1. plan-tab-top-collapsed.png
        let planTopCollapsed = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: false)
        save(planTopCollapsed, name: "plan-tab-top-collapsed")

        // 2. plan-tab-top-expanded.png (with Week Days Volume Chart)
        let planTopExpanded = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: true, initialVolumeMode: .weekDays)
        save(planTopExpanded, name: "plan-tab-top-expanded")

        // 2b. plan-tab-volume-trend.png (with Every Week Trend Volume Chart)
        let planTopTrend = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: true, initialVolumeMode: .weekTrend)
        save(planTopTrend, name: "plan-tab-volume-trend")

        // 3. calendar-month.png
        let planCalendar = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .calendar, initialCoachExpanded: false)
        save(planCalendar, name: "calendar-month")

        // 4. double-session-day.png & workout-cards-colored.png
        if let thuDay = model.days.first(where: { $0.weekday == .thursday }) {
            let doubleDayView = VStack(alignment: .leading, spacing: UH.Space.section) {
                Text("Double Session Day").font(UH.TextStyle.screenTitle).padding(.horizontal, UH.Space.regular)
                DayRow(day: thuDay, onToggleDone: { _ in }, onMoveOrSwap: { _ in }, onSelect: { _ in })
                    .padding(.horizontal, UH.Space.regular)
                Spacer()
            }
            .padding(.top, 40)
            .background(UH.Palette.surface.ignoresSafeArea())
            save(doubleDayView, name: "double-session-day")

            // Multi-workout colored showcase
            let coloredShowcase = ScrollView {
                VStack(alignment: .leading, spacing: UH.Space.compact) {
                    Text("Workout Cards Color Highlights")
                        .font(UH.TextStyle.screenTitle)
                        .padding(.horizontal, UH.Space.regular)
                    ForEach(model.days) { day in
                        DayRow(day: day, onToggleDone: { _ in }, onMoveOrSwap: { _ in }, onSelect: { _ in })
                            .padding(.horizontal, UH.Space.regular)
                    }
                }
                .padding(.vertical, UH.Space.regular)
            }
            .background(UH.Palette.surface.ignoresSafeArea())
            save(coloredShowcase, name: "workout-cards-colored")
        }

        // 5. locked-next-week.png
        let lockedOffer = NextWeekOffer(blockNumber: 2, weekStart: 3, weekEnd: 4, previousCompletionPct: 52.0, unlocked: false)
        let lockedNextWeekView = VStack(alignment: .leading, spacing: UH.Space.section) {
            Text("Next Block Status").font(UH.TextStyle.screenTitle).padding(.horizontal, UH.Space.regular)
            VStack(alignment: .leading, spacing: UH.Space.small) {
                HStack(spacing: UH.Space.compact) {
                    Image(systemName: "lock.fill").foregroundStyle(UH.Palette.secondary)
                    Text(lockedOffer.title).font(UH.TextStyle.sectionTitle)
                }
                Text("Complete the current block to unlock.").font(UH.TextStyle.body).foregroundStyle(UH.Palette.secondary)
                ProgressView(value: 52.0, total: 100).tint(UH.Palette.secondary)
                Text("52% / 70% completed").font(UH.TextStyle.caption).foregroundStyle(UH.Palette.muted)
                Button("Generate anyway") {}.buttonStyle(.uhSecondary)
            }
            .uhCard()
            .padding(.horizontal, UH.Space.regular)
            Spacer()
        }
        .padding(.top, 40)
        .background(UH.Palette.surface.ignoresSafeArea())
        save(lockedNextWeekView, name: "locked-next-week")

        // 6. block-review.png
        let blockReviewView = NextWeekSheet(model: model, offer: lockedOffer)
        save(blockReviewView, name: "block-review")

        // 7. manage-sheet.png
        let manageSheetView = ManagePlanSheet(
            model: model,
            onStartNew: {},
            onSchedule: {},
            initialPlans: [
                model.snapshot!.plan,
                TestData.plan(["id": 99, "race_name": "UTMB OCC 55K", "race_date": "2026-08-28", "total_weeks": 16, "plan_status": "archived"])
            ],
            initialConfirmDelete: false
        )
        save(manageSheetView, name: "manage-sheet")

        // 8. delete-confirm.png
        let deleteConfirmView = ManagePlanSheet(
            model: model,
            onStartNew: {},
            onSchedule: {},
            initialPlans: [model.snapshot!.plan],
            initialConfirmDelete: true
        )
        save(deleteConfirmView, name: "delete-confirm")

        // 9. workout-detail-easy.png
        let easyDetail = WorkoutDetailSheet(model: model, workoutID: 2)
        save(easyDetail, name: "workout-detail-easy")

        // 10. workout-detail-intervals.png
        let intervalDetail = WorkoutDetailSheet(model: model, workoutID: 3)
        save(intervalDetail, name: "workout-detail-intervals")

        // 11. workout-detail-long.png
        let longDetail = WorkoutDetailSheet(model: model, workoutID: 7)
        save(longDetail, name: "workout-detail-long")

        // 12. workout-detail-strength.png
        let strengthDetail = WorkoutDetailSheet(model: model, workoutID: 5)
        save(strengthDetail, name: "workout-detail-strength")

        // 13. workout-detail-treadmill.png
        let treadmillDetail = WorkoutDetailSheet(model: model, workoutID: 3, initialTreadmill: true)
        save(treadmillDetail, name: "workout-detail-treadmill")

        // 14. workout-detail-done-rpe.png
        let doneDetail = WorkoutDetailSheet(model: model, workoutID: 9, initialRpe: 7, initialNotes: "Legs felt responsive on the climbs. Maintained target cadence throughout reps 4-6.")
        save(doneDetail, name: "workout-detail-done-rpe")

        // 15. workout-detail-missed.png
        let missedDetail = WorkoutDetailSheet(model: model, workoutID: 10)
        save(missedDetail, name: "workout-detail-missed")

        // 16. plan-tab-xxxl.png
        let planTopXxxl = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil, initialViewMode: .list, initialCoachExpanded: false)
            .dynamicTypeSize(.accessibility3)
        save(planTopXxxl, name: "plan-tab-xxxl")

        // 17. workout-detail-xxxl.png
        let intervalXxxl = WorkoutDetailSheet(model: model, workoutID: 3)
            .dynamicTypeSize(.accessibility3)
        save(intervalXxxl, name: "workout-detail-xxxl")

        // 18. coros-synced-badge.png (Day row with compact COROS badge)
        let corosWorkout = allWorkouts.first { $0.id == 11 } ?? allWorkouts[0]
        let corosDay = PlanDay(week: 2, weekday: .tuesday, date: PlanCalendar.day(from: "2026-10-06"), workouts: [corosWorkout], eyebrow: nil)
        let corosBadgeView = VStack(alignment: .leading, spacing: UH.Space.section) {
            Text("COROS Synced Session").font(UH.TextStyle.screenTitle).padding(.horizontal, UH.Space.regular)
            DayRow(day: corosDay, onToggleDone: { _ in }, onMoveOrSwap: { _ in }, onSelect: { _ in })
                .padding(.horizontal, UH.Space.regular)
            Spacer()
        }
        .padding(.top, 40)
        .background(UH.Palette.surface.ignoresSafeArea())
        save(corosBadgeView, name: "coros-synced-badge")

        // 19. coros-workout-detail.png (Workout detail with matched telemetry comparison)
        let corosDetail = WorkoutDetailSheet(model: model, workoutID: 11)
        save(corosDetail, name: "coros-workout-detail")

        #expect(FileManager.default.fileExists(atPath: "\(outDir)/plan-tab-top-collapsed.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/plan-tab-top-expanded.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/calendar-month.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/double-session-day.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/locked-next-week.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/block-review.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/manage-sheet.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/delete-confirm.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-easy.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-intervals.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-long.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-strength.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-treadmill.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-done-rpe.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-missed.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/plan-tab-xxxl.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/workout-detail-xxxl.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/coros-synced-badge.png"))
        #expect(FileManager.default.fileExists(atPath: "\(outDir)/coros-workout-detail.png"))
    }
}

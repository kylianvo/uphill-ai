import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// Renders the month calendar in the states worth reviewing. Only writes when SCREENSHOT_DIR is set:
///   TEST_RUNNER_SCREENSHOT_DIR=$PWD/docs/screenshots/calendar-grid ios-native/scripts/test.sh -only-testing:UphillAITests/PlanCalendarScreenshots
@MainActor
struct PlanCalendarScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private let cal: Calendar = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")!
        c.locale = Locale(identifier: "en_US_POSIX")
        return c
    }()
    private var now: Date { cal.date(from: DateComponents(year: 2026, month: 10, day: 14, hour: 9))! }

    /// 12-week plan from Mon 28 Sep 2026, race Sat 19 Dec. Weeks 1-2 done (one missed, one double day), week 3 under way.
    private func makeModel(week: Int) async -> PlanViewModel {
        let plan = TestData.plan(["id": 101, "race_name": "Snowdonia Trail 50K", "race_date": "2026-12-19",
                                  "total_weeks": 12, "start_date": "2026-09-28"])
        var id = 0
        func w(_ week: Int, _ day: String, _ type: String, _ min: Double, _ km: Double, _ extra: [String: Any] = [:]) -> Workout {
            id += 1
            var o: [String: Any] = ["id": id, "week_number": week, "day_of_week": day, "type": type, "title": type,
                                    "duration_minutes": min, "distance_km": km, "target_zone": "Z2"]
            o.merge(extra) { _, new in new }
            return TestData.workout(o)
        }
        var ws: [Workout] = []
        for week in 1...11 {
            let f = 1 + Double(week % 4 == 0 ? -0.35 : Double(week) * 0.04)
            let done: [String: Any] = week <= 2 ? ["is_completed": 1] : [:]
            ws += [
                w(week, "Tuesday", "Easy Run", 45, (8 * f).rounded(), done),
                w(week, "Wednesday", "Intervals", 60, (9 * f).rounded(), ["target_zone": "Z4"].merging(done) { a, _ in a }),
                w(week, "Thursday", "Strength", 40, 0, ["target_zone": "Z1"].merging(done) { a, _ in a }),
                w(week, "Saturday", "Long Run", 120, (20 * f).rounded(), done),
                w(week, "Sunday", "Recovery", 30, 5, ["target_zone": "Z1"].merging(done) { a, _ in a }),
            ]
        }
        ws.append(w(2, "Tuesday", "Easy Run", 35, 6, ["session_slot": "afternoon", "is_missed": 1]))   // double day, second one missed
        ws.append(w(12, "Saturday", "Race", 480, 50, ["title": "TARGET EVENT", "target_zone": "Z3"]))
        let service = FakePlanService()
        service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: ws)) }
        service.recentResult.withLock { $0 = .success([plan]) }
        let model = PlanViewModel(service: service, cache: .inMemory(), now: { [now] in now }, calendar: cal)
        await model.load()
        model.selectedWeek = week
        return model
    }

    private func save<V: View>(_ view: V, name: String, width: CGFloat = 402, height: CGFloat, dark: Bool = false) {
        let size = CGSize(width: width, height: height)
        let controller = UIHostingController(rootView: view.frame(width: width, height: height))
        controller.overrideUserInterfaceStyle = dark ? .dark : .light
        controller.view.backgroundColor = dark ? UIColor(white: 0.07, alpha: 1) : UIColor(UH.Palette.surface)
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        controller.view.layoutIfNeeded()
        let format = UIGraphicsImageRendererFormat()
        format.scale = 2
        let img = UIGraphicsImageRenderer(size: size, format: format).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        guard let outDir else { return }
        try? img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    private func grid(_ model: PlanViewModel) -> some View {
        PlanCalendarGridView(model: model, onSelectDay: { _ in }, onOpenWeek: { _ in })
            .padding(.horizontal, UH.Space.regular)
            .padding(.top, UH.Space.regular)
            .frame(maxHeight: .infinity, alignment: .top)
    }

    @Test func renderCalendarStates() async {
        let oct = await makeModel(week: 3)
        save(grid(oct), name: "october-light", height: 560)
        save(grid(oct), name: "october-light-375", width: 375, height: 560)
        save(grid(oct), name: "october-dark", height: 560, dark: true)
        save(grid(oct).environment(\.dynamicTypeSize, .accessibility3), name: "october-ax3", height: 760)

        save(grid(await makeModel(week: 12)), name: "december-race", height: 560)

        UserDefaults.standard.set("vi", forKey: AppLanguage.storageKey)
        save(grid(oct).environment(\.locale, Locale(identifier: "vi")), name: "october-vi", height: 560)
        UserDefaults.standard.removeObject(forKey: AppLanguage.storageKey)

        let target = MoveTarget(week: 2, weekday: .tuesday, date: PlanCalendar.day(from: "2026-10-06")!)
        save(CalendarDaySheet(model: oct, target: target, onOpenWeek: { _ in }, onSelect: { _ in }), name: "day-sheet", height: 560)

        if let outDir { #expect(FileManager.default.fileExists(atPath: "\(outDir)/october-light.png")) }
    }

    @Test func renderPlanScreenDark() async {
        let model = await makeModel(week: 3)
        let gen = GenerationCenter(service: FakeGenerationService(), defaults: UserDefaults(suiteName: UUID().uuidString)!)
        for (mode, name) in [(PlanViewMode.list, "plan-list"), (.calendar, "plan-calendar")] {
            for dark in [false, true] {
                let v = PlanView(model: model, generation: gen, onBuildPlan: {}, onViewProgress: {}, user: nil,
                                 initialViewMode: mode, initialCoachExpanded: true)
                save(v, name: "\(name)-\(dark ? "dark" : "light")", height: 874, dark: dark)
            }
        }
    }
}

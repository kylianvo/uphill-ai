import SwiftUI
import Testing
import UIKit
@testable import UphillAI

/// The workout sheet's "Why today" and About this session. Written only when SCREENSHOT_DIR is set.
@MainActor
@Suite(.serialized)
struct SessionNotesScreenshots {
    private let outDir = ProcessInfo.processInfo.environment["SCREENSHOT_DIR"]

    private func save<V: View>(_ view: V, name: String, height: CGFloat) async throws {
        guard let outDir else { return }
        let size = CGSize(width: 402, height: height)
        let controller = UIHostingController(rootView: view.frame(width: size.width, height: size.height))
        let window = UIWindow(frame: CGRect(origin: .zero, size: size))
        window.rootViewController = controller
        window.makeKeyAndVisible()
        defer { window.isHidden = true }
        controller.view.layoutIfNeeded()
        try await Task.sleep(for: .milliseconds(900))
        let img = UIGraphicsImageRenderer(size: size).image { _ in
            controller.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: true)
        }
        try img.pngData()?.write(to: URL(fileURLWithPath: "\(outDir)/\(name).png"))
    }

    @Test func renderSessionNotes() async throws {
        guard outDir != nil else { return }
        let oldLanguage = UserDefaults.standard.string(forKey: AppLanguage.storageKey)
        defer { UserDefaults.standard.set(oldLanguage, forKey: AppLanguage.storageKey) }
        let texts: [AppLanguage: (String, String)] = [
            .en: ("Warm-up 15 min easy → 185 min steady Zone 2, power-hiking anything steeper than 10%, practise race fueling → 10 min easy cool-down. Overall: The week's longest run: steady Zone 2 from start to finish, walking the steep climbs. Reason: Week 6 of your long-run ladder: 3 h 30, 30 min more than last week. Benefit: Long, easy time on your feet builds the aerobic base and leg durability a long race depends on, and it is where you practise eating on the move. Warning: Slow down or walk when HR climbs above Zone 2. Stop if a pain sharpens or changes how you run.",
                  "3 h 30 on your feet, of the 29 h cutoff at VHT 100K."),
            .vi: ("Warm-up 15 phút nhẹ → 185 phút Zone 2 đều, power-hiking đoạn dốc trên 10%, tập fueling như ngày race → Cool-down 10 phút nhẹ. Tổng quan: Buổi chạy dài nhất tuần: Zone 2 đều từ đầu đến cuối, đi bộ nhanh ở các đoạn dốc. Lý do: Tuần 6 của ladder Long Run: 3 h 30, thêm 30 phút so với tuần trước. Lợi ích: Chạy dài và nhẹ xây nền aerobic và độ bền của chân, hai thứ quyết định một race dài; đây cũng là buổi để tập fueling khi đang chạy. Lưu ý: Chạy chậm lại hoặc đi bộ khi HR vượt Zone 2. Dừng lại nếu cơn đau tăng dần hoặc làm bạn đổi dáng chạy.",
                  "3 h 30 trên chân, so với cutoff 29 h của VHT 100K."),
        ]
        for lang in [AppLanguage.en, .vi] {
            UserDefaults.standard.set(lang.rawValue, forKey: AppLanguage.storageKey)
            let (desc, fit) = texts[lang]!
            let plan = TestData.plan(["id": 5, "race_name": "VHT 100K", "start_date": "2026-10-19", "current_week": 2])
            let workout = TestData.workout(["id": 77, "plan_id": 5, "week_number": 2, "day_of_week": "Saturday", "type": "Long Run",
                                            "title": "Mountain Long Run", "duration_minutes": 210, "target_zone": "Zone 2",
                                            "description": desc, "race_fit": fit, "approved_at": "2026-10-19"])
            let service = FakePlanService()
            service.activeResult.withLock { $0 = .success(PlanSnapshot(plan: plan, workouts: [workout])) }
            let model = PlanViewModel(service: service, cache: .inMemory())
            await model.load()
            try await save(WorkoutDetailSheet(model: model, workoutID: 77).environment(\.locale, lang.locale),
                           name: "session-notes-long-run-\(lang.rawValue)", height: 1900)
        }
    }
}

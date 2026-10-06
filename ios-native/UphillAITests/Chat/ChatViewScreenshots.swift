import SwiftUI
import Testing
import UIKit
@testable import UphillAI

@MainActor
struct ChatViewScreenshots {
    private let outDir = "/Users/vietvo/.codex/worktrees/ios-native-phase2b/uphill-ai/ios-native/docs/screenshots/coach-chat"

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

    private func makeTestPlan() -> Plan {
        TestData.plan([
            "id": 101,
            "race_name": "Dalat Ultra Trail 70K",
            "race_date": "2026-11-20",
            "goal_type": "finish",
            "total_weeks": 12,
            "current_week": 4,
            "start_date": "2026-09-01",
            "plan_status": "active"
        ])
    }

    @Test func renderCoachChatEmpty() throws {
        let client = makeStubClient { _ in (200, json(["messages": [], "has_more": false])) }
        let store = UserDefaultsChatStore(defaults: UserDefaults(suiteName: "ScreenshotsEmpty")!)
        store.clearMessages(for: 101)
        let service = ChatService(client: client, store: store)
        let plan = makeTestPlan()

        let view = ChatView(service: service, plan: plan)
        save(view, name: "coach-chat-empty")
    }

    @Test func renderCoachChatConversation() throws {
        let plan = makeTestPlan()
        let store = UserDefaultsChatStore(defaults: UserDefaults(suiteName: "ScreenshotsConversation")!)
        store.clearMessages(for: 101)

        let thread = try Fixture.decode(ChatThreadResponse.self, "chat_thread.json")
        store.saveMessages(thread.messages, for: 101)

        let client = makeStubClient { _ in (200, json(["messages": [], "has_more": false])) }
        let service = ChatService(client: client, store: store)

        // Preload cached messages
        service.loadMessagesDirectlyForScreenshot(thread.messages, proposals: [7: "proposed"], clarify: ["Looks good, apply it", "Keep Tuesday instead", "What about Wednesday?"])

        let view = ChatView(service: service, plan: plan)
        save(view, name: "coach-chat-conversation")
    }

    @Test func renderCoachChatSources() throws {
        let sources = try Fixture.decode(MessageSourcesResponse.self, "chat_sources.json")
        let view = ChatSourcesSheet(sources: sources)
        save(view, name: "coach-chat-sources")
    }
    @Test func renderCoachChatWeekSchedule() throws {
        let plan = makeTestPlan()
        let store = UserDefaultsChatStore(defaults: UserDefaults(suiteName: "ScreenshotsWeekSchedule")!)
        store.clearMessages(for: 101)

        let client = makeStubClient { _ in (200, json(["messages": [], "has_more": false])) }
        let service = ChatService(client: client, store: store)

        let userMsg = ChatMessage(id: "msg-user-1", numericId: 1, role: .user, content: "What is my plan this week?")

        let workouts = [
            TestData.workout(["id": 1, "day_of_week": "Monday", "title": "Rest Day", "type": "Rest", "duration_minutes": 0, "target_zone": "Rest", "is_priority": false]),
            TestData.workout(["id": 2, "day_of_week": "Tuesday", "title": "Hill Repeats", "type": "Hill Repeats", "duration_minutes": 60, "distance_km": 8.0, "elevation_gain_m": 350.0, "target_zone": "Z4", "is_priority": true]),
            TestData.workout(["id": 3, "day_of_week": "Wednesday", "title": "Aerobic Base Run", "type": "Easy Run", "duration_minutes": 50, "distance_km": 8.0, "elevation_gain_m": 120.0, "target_zone": "Z2", "is_priority": false]),
            TestData.workout(["id": 4, "day_of_week": "Thursday", "title": "Rest Day", "type": "Rest", "duration_minutes": 0, "target_zone": "Rest", "is_priority": false]),
            TestData.workout(["id": 5, "day_of_week": "Friday", "title": "Easy Run + Strides", "type": "Easy Run", "duration_minutes": 45, "distance_km": 7.0, "elevation_gain_m": 60.0, "target_zone": "Z2", "is_priority": false]),
            TestData.workout(["id": 6, "day_of_week": "Saturday", "title": "Mountain Long Run", "type": "Long Run", "duration_minutes": 135, "distance_km": 20.0, "elevation_gain_m": 750.0, "target_zone": "Z2", "is_priority": true]),
            TestData.workout(["id": 7, "day_of_week": "Sunday", "title": "Recovery Jog", "type": "Recovery Run", "duration_minutes": 35, "distance_km": 5.0, "elevation_gain_m": 40.0, "target_zone": "Z1", "is_priority": false])
        ]

        let weekScheduleData = WeekScheduleCardData(
            weekNumber: 4,
            totalDistanceKm: 48.0,
            totalElevationGainM: 1320.0,
            workouts: workouts
        )

        let encoded = try JSONCoding.encoder.encode(weekScheduleData)
        let cardDataJson = try JSONCoding.decoder.decode([String: JSONValue].self, from: encoded)

        let toolPayload = ToolResultPayload(
            toolCallId: "call_week_4",
            name: "get_week",
            status: "success",
            cardType: "week_schedule",
            cardData: cardDataJson
        )

        let assistantMsg = ChatMessage(
            id: "msg-assistant-1",
            numericId: 2,
            role: .assistant,
            content: "Here is your training schedule for **Week 4** of your Dalat Ultra Trail 70K build. You have two priority sessions: a **Tuesday Hill Repeats** workout to build uphill power, and a **Saturday Mountain Long Run** with +750 m gain.",
            toolCalls: [toolPayload]
        )

        service.loadMessagesDirectlyForScreenshot([userMsg, assistantMsg])

        let view = ChatView(service: service, plan: plan)
        save(view, name: "coach-chat-week-schedule")
    }
}

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
}
